# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
import threading

from flask import current_app, jsonify, request
from app.lib.lib_define import db
from app.models.test_api_models import ApiCase, ApiEnvironment, ApiReport, ApiRunResult, ApiSuite, ApiSuiteRunResult
from app.web_api import api_test
from app.tools.audit_fields import apply_run_user
from app.tools.auth_permissions import allowed_project_ids, current_account, require_project_permission
from app.tools.api_common_tools import api_run_id_from, int_or_none, json_text, loads, normalize_dependency_strategy
from app.tools.api_execution_service import (
    case_source_from_request,
    normalize_data_rows,
    run_case_background,
    run_case_payload,
    run_suite_background,
    run_suite_payload,
)
from app.tools.api_schema_tools import ensure_api_case_columns, ensure_api_runtime_columns
from app.tools.api_payload_tools import api_report_payload, case_payload, environment_payload, load_ordered_cases, normalize_case_ids, result_payload, suite_history_compare_payload, suite_payload, suite_pending_steps, suite_result_payload
from app.tools.db_write_guard import guarded_commit


def _check_project(project_id, permission="view"):
    if not project_id:
        return None
    return require_project_permission(project_id, permission)


def _filter_project_scope(query, model):
    ids = allowed_project_ids()
    if ids is None:
        return query
    if not ids:
        return query.filter(False)
    return query.filter((model.project_id.in_(ids)) | (model.project_id.is_(None)))


@api_test.route('/get_environment_info', methods=["POST"])
def get_environment_info():
    data = request.get_json(silent=True) or {}
    project_id = int_or_none(data.get("project_id"))
    permission_error = _check_project(project_id, "view")
    if permission_error:
        return permission_error
    query = ApiEnvironment.query.filter_by(is_delete=0)
    query = _filter_project_scope(query, ApiEnvironment)
    if project_id:
        query = query.filter((ApiEnvironment.project_id == project_id) | (ApiEnvironment.project_id.is_(None)))
    keyword = (data.get("keyword") or "").strip()
    if keyword:
        query = query.filter(ApiEnvironment.name.like("%{}%".format(keyword)))
    rows = query.order_by(db.desc(ApiEnvironment.updated_time)).all()
    return jsonify({"code": 200, "msg": "请求成功", "data": [environment_payload(item) for item in rows]})


@api_test.route('/save_environment', methods=["POST"])
def save_environment():
    data = request.get_json(silent=True) or {}
    project_id = int_or_none(data.get("project_id"))
    permission_error = _check_project(project_id, "edit")
    if permission_error:
        return permission_error
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"code": 404, "msg": "环境名称不能为空", "data": None})
    variables = data.get("variables") or {}
    if not isinstance(variables, dict):
        return jsonify({"code": 404, "msg": "环境变量必须是JSON对象", "data": None})
    env_id = data.get("id")
    item = ApiEnvironment.query.filter_by(id=env_id, is_delete=0).first() if env_id else ApiEnvironment()
    if not item:
        return jsonify({"code": 404, "msg": "环境不存在", "data": None})
    item.name = name
    item.project_id = project_id
    item.variables = json_text(variables)
    item.description = data.get("description") or ""
    db.session.add(item)
    guarded_commit()
    return jsonify({"code": 200, "msg": "保存成功", "data": environment_payload(item)})


@api_test.route('/delete_environment', methods=["POST"])
def delete_environment():
    data = request.get_json(silent=True) or {}
    item = ApiEnvironment.query.filter_by(id=data.get("id"), is_delete=0).first()
    if not item:
        return jsonify({"code": 404, "msg": "环境不存在", "data": None})
    permission_error = _check_project(item.project_id, "edit")
    if permission_error:
        return permission_error
    item.is_delete = 1
    guarded_commit()
    return jsonify({"code": 200, "msg": "删除成功", "data": None})


@api_test.route('/get_case_info', methods=["POST"])
def get_case_info():
    ensure_api_case_columns()
    data = request.get_json(silent=True) or {}
    page_no = int(data.get("page_no", 0) or 0)
    page_size = int(data.get("page_size", 20) or 20)
    project_id = int_or_none(data.get("project_id"))
    permission_error = _check_project(project_id, "view")
    if permission_error:
        return permission_error
    query = ApiCase.query.filter_by(is_delete=0)
    query = _filter_project_scope(query, ApiCase)
    if project_id:
        query = query.filter(ApiCase.project_id == project_id)
    keyword = (data.get("keyword") or "").strip()
    if keyword:
        query = query.filter(ApiCase.name.like("%{}%".format(keyword)))
    run_status = data.get("run_status")
    if run_status == "passed":
        query = query.filter(ApiCase.last_success == 1)
    elif run_status == "failed":
        query = query.filter(ApiCase.last_success == 0)
    elif run_status == "not_run":
        query = query.filter(ApiCase.last_success.is_(None))
    status_code = int_or_none(data.get("status_code"))
    if status_code is not None:
        query = query.filter(ApiCase.last_status == status_code)
    total = query.count()
    rows = query.order_by(db.desc(ApiCase.updated_time)).limit(page_size).offset(page_no).all()
    return jsonify({"code": 200, "msg": "请求成功", "data": [case_payload(item) for item in rows], "total": total})


@api_test.route('/save_case', methods=["POST"])
def save_case():
    ensure_api_case_columns()
    data = request.get_json(silent=True) or {}
    project_id = int_or_none(data.get("project_id"))
    permission_error = _check_project(project_id, "edit")
    if permission_error:
        return permission_error
    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    if not name or not url:
        return jsonify({"code": 404, "msg": "接口名称和URL不能为空", "data": None})
    item_id = data.get("id")
    item = ApiCase.query.filter_by(id=item_id, is_delete=0).first() if item_id else ApiCase()
    if not item:
        return jsonify({"code": 404, "msg": "接口用例不存在", "data": None})
    item.name = name
    item.project_id = project_id
    item.environment_id = data.get("environment_id")
    item.method = (data.get("method") or "GET").upper()
    item.url = url
    item.headers = json_text(data.get("headers") or {})
    item.params = json_text(data.get("params") or {})
    item.body_type = data.get("body_type") or "json"
    item.body = data.get("body") or ""
    item.assertions = json_text(data.get("assertions") or [])
    item.pre_case_ids = json_text(normalize_case_ids(data.get("pre_case_ids") or []))
    item.extractors = json_text(data.get("extractors") or [])
    item.data_rows = json_text(normalize_data_rows(data.get("data_rows") or []))
    item.description = data.get("description") or ""
    db.session.add(item)
    guarded_commit()
    return jsonify({"code": 200, "msg": "保存成功", "data": case_payload(item)})


@api_test.route('/delete_case', methods=["POST"])
def delete_case():
    ensure_api_case_columns()
    data = request.get_json(silent=True) or {}
    item = ApiCase.query.filter_by(id=data.get("id"), is_delete=0).first()
    if not item:
        return jsonify({"code": 404, "msg": "接口用例不存在", "data": None})
    permission_error = _check_project(item.project_id, "edit")
    if permission_error:
        return permission_error
    item.is_delete = 1
    guarded_commit()
    return jsonify({"code": 200, "msg": "删除成功", "data": None})


@api_test.route('/run_case', methods=["POST"])
def run_case():
    ensure_api_case_columns()
    ensure_api_runtime_columns()
    data = request.get_json(silent=True) or {}
    data = dict(data)
    run_id = api_run_id_from(data)
    data["_api_run_id"] = run_id
    case = ApiCase.query.filter_by(id=data.get("id"), is_delete=0).first() if data.get("id") else None
    source = case_source_from_request(case, data)
    project_id = int_or_none(source.get("project_id"))
    permission_error = _check_project(project_id, "run")
    if permission_error:
        return permission_error
    if data.get("async"):
        result = ApiRunResult(
            run_id=run_id,
            case_id=case.id if case else None,
            environment_id=int_or_none(data.get("environment_id") or source.get("environment_id")),
            project_id=project_id,
            method=(source.get("method") or "GET").upper(),
            url=source.get("url") or "",
            request_headers=json_text(source.get("headers") or {}),
            request_params=json_text(source.get("params") or {}),
            request_body=source.get("body") or "",
            run_status="queued",
            status_text="排队中",
            success=0,
        )
        apply_run_user(result)
        db.session.add(result)
        guarded_commit()
        app = current_app._get_current_object()
        account = current_account()
        account_info = {"id": account.id, "name": account.username} if account else None
        thread = threading.Thread(target=run_case_background, args=(app, result.id, data, account_info), daemon=True)
        thread.start()
        return jsonify({"code": 200, "msg": "已开始异步执行", "data": result_payload(result)})
    try:
        payload = run_case_payload(data)
    except ValueError as exc:
        return jsonify({"code": 404, "msg": str(exc), "data": None})
    return jsonify({"code": 200, "msg": "执行完成", "data": payload})


@api_test.route('/get_run_history', methods=["POST"])
def get_run_history():
    ensure_api_case_columns()
    ensure_api_runtime_columns()
    data = request.get_json(silent=True) or {}
    case_id = data.get("case_id")
    query = ApiRunResult.query
    if case_id:
        case = ApiCase.query.filter_by(id=case_id, is_delete=0).first()
        if case:
            permission_error = _check_project(case.project_id, "view")
            if permission_error:
                return permission_error
        query = query.filter_by(case_id=case_id)
    query = _filter_project_scope(query, ApiRunResult)
    rows = query.order_by(db.desc(ApiRunResult.created_time)).limit(int(data.get("limit") or 20)).all()
    return jsonify({"code": 200, "msg": "请求成功", "data": [result_payload(item) for item in rows]})


@api_test.route('/get_run_result', methods=["POST"])
def get_run_result():
    ensure_api_runtime_columns()
    data = request.get_json(silent=True) or {}
    result = ApiRunResult.query.filter_by(id=data.get("id")).first()
    if not result:
        return jsonify({"code": 404, "msg": "执行结果不存在", "data": None})
    if result.project_id:
        permission_error = _check_project(result.project_id, "view")
        if permission_error:
            return permission_error
    return jsonify({"code": 200, "msg": "请求成功", "data": result_payload(result)})


@api_test.route('/get_suite_info', methods=["POST"])
def get_suite_info():
    data = request.get_json(silent=True) or {}
    page_no = int(data.get("page_no", 0) or 0)
    page_size = int(data.get("page_size", 20) or 20)
    project_id = int_or_none(data.get("project_id"))
    permission_error = _check_project(project_id, "view")
    if permission_error:
        return permission_error
    query = ApiSuite.query.filter_by(is_delete=0)
    query = _filter_project_scope(query, ApiSuite)
    if project_id:
        query = query.filter(ApiSuite.project_id == project_id)
    keyword = (data.get("keyword") or "").strip()
    if keyword:
        query = query.filter(ApiSuite.name.like("%{}%".format(keyword)))
    run_status = data.get("run_status")
    if run_status == "passed":
        query = query.filter(ApiSuite.last_success == 1)
    elif run_status == "failed":
        query = query.filter(ApiSuite.last_success == 0)
    elif run_status == "not_run":
        query = query.filter(ApiSuite.last_success.is_(None))
    elif run_status == "running":
        running_suite_ids = [
            item[0] for item in db.session.query(ApiSuiteRunResult.suite_id)
            .filter(ApiSuiteRunResult.run_status.in_(["queued", "running"]))
            .distinct()
            .all()
        ]
        query = query.filter(ApiSuite.id.in_(running_suite_ids or [0]))
    elif run_status == "stopped":
        stopped_suite_ids = [
            item[0] for item in db.session.query(ApiSuiteRunResult.suite_id)
            .filter(ApiSuiteRunResult.run_status == "stopped")
            .distinct()
            .all()
        ]
        query = query.filter(ApiSuite.id.in_(stopped_suite_ids or [0]))
    total = query.count()
    rows = query.order_by(db.desc(ApiSuite.updated_time)).limit(page_size).offset(page_no).all()
    return jsonify({"code": 200, "msg": "请求成功", "data": [suite_payload(item) for item in rows], "total": total})


@api_test.route('/save_suite', methods=["POST"])
def save_suite():
    data = request.get_json(silent=True) or {}
    project_id = int_or_none(data.get("project_id"))
    permission_error = _check_project(project_id, "edit")
    if permission_error:
        return permission_error
    name = (data.get("name") or "").strip()
    case_ids = normalize_case_ids(data.get("case_ids") or [])
    if not name:
        return jsonify({"code": 404, "msg": "集合名称不能为空", "data": None})
    if not case_ids:
        return jsonify({"code": 404, "msg": "请至少选择一个接口", "data": None})
    cases = load_ordered_cases(case_ids)
    if len(cases) != len(case_ids):
        return jsonify({"code": 404, "msg": "集合中存在已删除或不存在的接口", "data": None})
    for item in cases:
        if project_id and item.project_id and item.project_id != project_id:
            return jsonify({"code": 404, "msg": "集合接口必须属于同一个项目", "data": None})
    suite_id = data.get("id")
    suite = ApiSuite.query.filter_by(id=suite_id, is_delete=0).first() if suite_id else ApiSuite()
    if not suite:
        return jsonify({"code": 404, "msg": "接口集合不存在", "data": None})
    suite.name = name
    suite.project_id = project_id
    suite.environment_id = int_or_none(data.get("environment_id"))
    suite.case_ids = json_text(case_ids)
    suite.stop_on_fail = 1 if data.get("stop_on_fail", 1) else 0
    suite.dependency_strategy = normalize_dependency_strategy(data.get("dependency_strategy"))
    suite.description = data.get("description") or ""
    db.session.add(suite)
    guarded_commit()
    return jsonify({"code": 200, "msg": "保存成功", "data": suite_payload(suite)})


@api_test.route('/delete_suite', methods=["POST"])
def delete_suite():
    data = request.get_json(silent=True) or {}
    suite = ApiSuite.query.filter_by(id=data.get("id"), is_delete=0).first()
    if not suite:
        return jsonify({"code": 404, "msg": "接口集合不存在", "data": None})
    permission_error = _check_project(suite.project_id, "edit")
    if permission_error:
        return permission_error
    suite.is_delete = 1
    guarded_commit()
    return jsonify({"code": 200, "msg": "删除成功", "data": None})


@api_test.route('/run_suite', methods=["POST"])
def run_suite():
    ensure_api_runtime_columns()
    data = request.get_json(silent=True) or {}
    data = dict(data)
    run_id = api_run_id_from(data)
    data["_api_run_id"] = run_id
    suite = ApiSuite.query.filter_by(id=data.get("id"), is_delete=0).first()
    if not suite:
        return jsonify({"code": 404, "msg": "接口集合不存在", "data": None})
    permission_error = _check_project(suite.project_id, "run")
    if permission_error:
        return permission_error
    environment_id = int_or_none(data.get("environment_id") or suite.environment_id)
    timeout = min(max(int(data.get("timeout") or 30), 1), 120)
    case_ids = normalize_case_ids(loads(suite.case_ids, []))
    cases = load_ordered_cases(case_ids)
    if data.get("async"):
        running_result = ApiSuiteRunResult.query.filter(
            ApiSuiteRunResult.suite_id == suite.id,
            ApiSuiteRunResult.run_status.in_(["queued", "running"]),
        ).order_by(db.desc(ApiSuiteRunResult.created_time)).first()
        if running_result:
            return jsonify({"code": 200, "msg": "接口集合正在执行中", "data": suite_result_payload(running_result)})
        suite_result = ApiSuiteRunResult(
            run_id=run_id,
            suite_id=suite.id,
            project_id=suite.project_id,
            environment_id=environment_id,
            total_count=len(cases),
            pass_count=0,
            fail_count=0,
            elapsed_ms=0,
            success=0,
            run_status="queued",
            status_text="排队中",
            context=json_text({}),
            step_results=json_text(suite_pending_steps(cases)),
        )
        apply_run_user(suite_result)
        db.session.add(suite_result)
        guarded_commit()
        app = current_app._get_current_object()
        account = current_account()
        account_info = {"id": account.id, "name": account.username} if account else None
        thread = threading.Thread(
            target=run_suite_background,
            args=(app, suite_result.id, suite.id, environment_id, timeout, account_info, run_id),
            daemon=True,
        )
        thread.start()
        return jsonify({"code": 200, "msg": "已开始异步执行", "data": suite_result_payload(suite_result)})
    payload = run_suite_payload(suite, environment_id, timeout, run_id)
    return jsonify({"code": 200, "msg": "执行完成", "data": payload})


@api_test.route('/stop_suite', methods=["POST"])
def stop_suite():
    ensure_api_runtime_columns()
    data = request.get_json(silent=True) or {}
    result_id = int_or_none(data.get("result_id") or data.get("id"))
    suite_id = int_or_none(data.get("suite_id"))
    query = ApiSuiteRunResult.query
    if result_id:
        query = query.filter(ApiSuiteRunResult.id == result_id)
    elif suite_id:
        query = query.filter(
            ApiSuiteRunResult.suite_id == suite_id,
            ApiSuiteRunResult.run_status.in_(["queued", "running"]),
        )
    else:
        return jsonify({"code": 400, "msg": "suite_id不能为空", "data": None})
    result = query.order_by(db.desc(ApiSuiteRunResult.created_time)).first()
    if not result:
        return jsonify({"code": 404, "msg": "没有运行中的接口集合", "data": None})
    if result.project_id:
        permission_error = _check_project(result.project_id, "run")
        if permission_error:
            return permission_error
    if result.run_status not in ("queued", "running"):
        return jsonify({"code": 200, "msg": "当前接口集合未在执行中", "data": suite_result_payload(result)})
    result.run_status = "stopped"
    result.status_text = "已终止"
    result.success = 0
    result.error_message = "用户手动终止"
    guarded_commit()
    return jsonify({"code": 200, "msg": "已发送终止指令", "data": suite_result_payload(result)})


@api_test.route('/get_suite_history', methods=["POST"])
def get_suite_history():
    ensure_api_runtime_columns()
    data = request.get_json(silent=True) or {}
    suite_id = data.get("suite_id")
    query = ApiSuiteRunResult.query
    if suite_id:
        suite = ApiSuite.query.filter_by(id=suite_id, is_delete=0).first()
        if suite:
            permission_error = _check_project(suite.project_id, "view")
            if permission_error:
                return permission_error
        query = query.filter_by(suite_id=suite_id)
    query = _filter_project_scope(query, ApiSuiteRunResult)
    rows = query.order_by(db.desc(ApiSuiteRunResult.created_time)).limit(int(data.get("limit") or 20)).all()
    return jsonify({"code": 200, "msg": "请求成功", "data": [suite_result_payload(item) for item in rows]})


@api_test.route('/get_suite_result', methods=["POST"])
def get_suite_result():
    ensure_api_runtime_columns()
    data = request.get_json(silent=True) or {}
    result = ApiSuiteRunResult.query.filter_by(id=data.get("id")).first()
    if not result:
        return jsonify({"code": 404, "msg": "集合执行结果不存在", "data": None})
    if result.project_id:
        permission_error = _check_project(result.project_id, "view")
        if permission_error:
            return permission_error
    return jsonify({"code": 200, "msg": "请求成功", "data": suite_result_payload(result)})


@api_test.route('/get_suite_history_compare', methods=["POST"])
def get_suite_history_compare():
    ensure_api_runtime_columns()
    data = request.get_json(silent=True) or {}
    suite_id = int_or_none(data.get("suite_id") or data.get("id"))
    if not suite_id:
        return jsonify({"code": 400, "msg": "suite_id不能为空", "data": None})
    suite = ApiSuite.query.filter_by(id=suite_id, is_delete=0).first()
    if not suite:
        return jsonify({"code": 404, "msg": "接口集合不存在", "data": None})
    if suite.project_id:
        permission_error = _check_project(suite.project_id, "view")
        if permission_error:
            return permission_error
    limit = min(max(int(data.get("limit") or 10), 2), 50)
    query = ApiSuiteRunResult.query.filter_by(suite_id=suite_id)
    environment_id = int_or_none(data.get("environment_id"))
    if environment_id:
        query = query.filter(ApiSuiteRunResult.environment_id == environment_id)
    rows = query.order_by(db.desc(ApiSuiteRunResult.created_time)).limit(limit).all()
    return jsonify({
        "code": 200,
        "msg": "请求成功",
        "data": suite_history_compare_payload(rows),
    })


@api_test.route('/get_api_report_info', methods=["POST"])
def get_api_report_info():
    data = request.get_json(silent=True) or {}
    page_no = int(data.get("page_no", 0) or 0)
    page_size = int(data.get("page_size", 20) or 20)
    project_id = int_or_none(data.get("project_id"))
    permission_error = _check_project(project_id, "view")
    if permission_error:
        return permission_error
    query = ApiReport.query.filter_by(is_delete=0, report_type="api")
    query = _filter_project_scope(query, ApiReport)
    if project_id:
        query = query.filter(ApiReport.project_id == project_id)
    target_type = (data.get("target_type") or "").strip()
    if target_type:
        query = query.filter(ApiReport.target_type == target_type)
    keyword = (data.get("keyword") or "").strip()
    if keyword:
        query = query.filter(ApiReport.title.like("%{}%".format(keyword)))
    success = data.get("success")
    if success in (0, 1, "0", "1"):
        query = query.filter(ApiReport.success == int(success))
    total = query.count()
    rows = query.order_by(db.desc(ApiReport.created_time)).limit(page_size).offset(page_no).all()
    return jsonify({"code": 200, "msg": "请求成功", "data": [api_report_payload(item) for item in rows], "total": total})


@api_test.route('/get_api_report_detail', methods=["POST"])
def get_api_report_detail():
    data = request.get_json(silent=True) or {}
    report = ApiReport.query.filter_by(id=data.get("id"), is_delete=0, report_type="api").first()
    if not report:
        return jsonify({"code": 404, "msg": "接口测试报告不存在", "data": None})
    if report.project_id:
        permission_error = _check_project(report.project_id, "view")
        if permission_error:
            return permission_error
    return jsonify({"code": 200, "msg": "请求成功", "data": api_report_payload(report)})

