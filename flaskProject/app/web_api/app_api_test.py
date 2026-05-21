# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
import json
import re
import time
import datetime

import requests
from flask import jsonify, request
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.lib.lib_define import db
from app.models.test_api_models import ApiCase, ApiEnvironment, ApiRunResult, ApiSuite, ApiSuiteRunResult
from app.web_api import api_test
from app.tools.audit_fields import apply_run_user
from app.tools.auth_permissions import allowed_project_ids, require_project_permission


VAR_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")
API_CASE_EXTRA_COLUMNS = {
    "pre_case_ids": "TEXT",
    "extractors": "TEXT",
}


def _json_text(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def _loads(value, default=None):
    if default is None:
        default = {}
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _ensure_api_case_columns():
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    if "api_case" not in table_names:
        return
    existing = {item.get("name") for item in inspector.get_columns("api_case")}
    with db.engine.begin() as conn:
        for name, column_type in API_CASE_EXTRA_COLUMNS.items():
            if name in existing:
                continue
            try:
                conn.execute(text("ALTER TABLE api_case ADD COLUMN {} {}".format(name, column_type)))
            except OperationalError as exc:
                if "duplicate column" not in str(exc).lower():
                    raise


def _int_or_none(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except Exception:
        return None


def _format_time(value):
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def _with_time(data):
    data["created_time"] = _format_time(data.get("created_time"))
    data["updated_time"] = _format_time(data.get("updated_time"))
    return data


def _case_payload(item):
    _ensure_api_case_columns()
    data = _with_time(item.to_dict())
    data["headers"] = _loads(data.get("headers"), {})
    data["params"] = _loads(data.get("params"), {})
    data["assertions"] = _loads(data.get("assertions"), [])
    data["pre_case_ids"] = _loads(data.get("pre_case_ids"), [])
    data["extractors"] = _loads(data.get("extractors"), [])
    return data


def _environment_payload(item):
    data = _with_time(item.to_dict())
    data["variables"] = _loads(data.get("variables"), {})
    return data


def _result_payload(item):
    data = _with_time(item.to_dict())
    data["request_headers"] = _loads(data.get("request_headers"), {})
    data["request_params"] = _loads(data.get("request_params"), {})
    data["response_headers"] = _loads(data.get("response_headers"), {})
    detail = _loads(data.get("assertion_result"), [])
    if isinstance(detail, dict):
        data["assertion_result"] = detail.get("assertions") or []
        data["extractor_result"] = detail.get("extractors") or []
    else:
        data["assertion_result"] = detail or []
        data["extractor_result"] = []
    return data


def _suite_payload(item):
    data = _with_time(item.to_dict())
    data["case_ids"] = _loads(data.get("case_ids"), [])
    data["stop_on_fail"] = 1 if data.get("stop_on_fail") else 0
    data["last_run_time"] = _format_time(data.get("last_run_time"))
    return data


def _suite_result_payload(item):
    data = _with_time(item.to_dict())
    data["context"] = _loads(data.get("context"), {})
    data["step_results"] = _loads(data.get("step_results"), [])
    return data


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


def _variables_for(environment_id):
    if not environment_id:
        return {}
    env = ApiEnvironment.query.filter_by(id=environment_id, is_delete=0).first()
    return _loads(env.variables, {}) if env else {}


def _apply_variables(value, variables):
    if isinstance(value, str):
        return VAR_PATTERN.sub(lambda m: str(variables.get(m.group(1), m.group(0))), value)
    if isinstance(value, dict):
        return {key: _apply_variables(item, variables) for key, item in value.items()}
    if isinstance(value, list):
        return [_apply_variables(item, variables) for item in value]
    return value


def _case_name(case_id):
    item = ApiCase.query.filter_by(id=case_id, is_delete=0).first()
    return item.name if item else str(case_id)


def _normalize_case_ids(values):
    result = []
    for value in values or []:
        case_id = _int_or_none(value)
        if case_id and case_id not in result:
            result.append(case_id)
    return result


def _load_ordered_cases(case_ids):
    normalized = _normalize_case_ids(case_ids)
    if not normalized:
        return []
    rows = ApiCase.query.filter(ApiCase.id.in_(normalized), ApiCase.is_delete == 0).all()
    case_map = {item.id: item for item in rows}
    return [case_map[item] for item in normalized if item in case_map]


def _resolve_dependency_order(case, visiting=None, visited=None, order=None):
    visiting = visiting or []
    visited = visited or set()
    order = order or []
    if not case:
        return order
    if case.id in visited:
        return order
    if case.id in visiting:
        cycle = visiting[visiting.index(case.id):] + [case.id]
        cycle_names = ["{}({})".format(_case_name(item), item) for item in cycle]
        raise ValueError("接口依赖存在循环：" + " -> ".join(cycle_names))
    visiting.append(case.id)
    pre_case_ids = _normalize_case_ids(_loads(case.pre_case_ids, []))
    for pre_case_id in pre_case_ids:
        pre_case = ApiCase.query.filter_by(id=pre_case_id, is_delete=0).first()
        if not pre_case:
            raise ValueError("依赖接口不存在：{}".format(pre_case_id))
        if case.project_id and pre_case.project_id and case.project_id != pre_case.project_id:
            raise ValueError("依赖接口不属于同一个项目：{}".format(pre_case.name))
        _resolve_dependency_order(pre_case, visiting, visited, order)
    visiting.pop()
    visited.add(case.id)
    order.append(case)
    return order


def _json_path(data, path):
    if not path:
        return data
    current = data
    for part in str(path).lstrip("$.").split("."):
        if part == "":
            continue
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def _extract_variables(response, body_text, extractors):
    variables = {}
    results = []
    json_body = None
    for index, item in enumerate(extractors or []):
        name = (item.get("name") or "").strip()
        source = item.get("from") or "json"
        path = item.get("path") or ""
        pattern = item.get("pattern") or ""
        success = False
        value = None
        error = ""
        if not name:
            results.append({"name": "", "success": False, "error": "变量名不能为空"})
            continue
        try:
            if source == "json":
                if json_body is None:
                    json_body = response.json()
                value = _json_path(json_body, path)
            elif source == "header":
                value = response.headers.get(path)
            elif source == "regex":
                match = re.search(pattern or path, body_text, re.S)
                value = match.group(1) if match and match.groups() else (match.group(0) if match else None)
            elif source == "body":
                value = body_text
            else:
                error = "不支持的提取来源"
            success = value is not None and error == ""
            if success:
                variables[name] = value
        except Exception as exc:
            error = str(exc)
        results.append({
            "name": name,
            "from": source,
            "path": path,
            "success": success,
            "value": value,
            "error": error,
            "index": index + 1,
        })
    return variables, results


def _run_assertions(response, body_text, assertions):
    results = []
    if not assertions:
        return [{"name": "HTTP状态小于400", "success": response.status_code < 400, "actual": response.status_code}]
    json_body = None
    for index, item in enumerate(assertions):
        assertion_type = item.get("type")
        expected = item.get("expected")
        name = item.get("name") or "断言{}".format(index + 1)
        success = False
        actual = None
        error = ""
        try:
            if assertion_type == "status_code":
                actual = response.status_code
                success = int(actual) == int(expected)
            elif assertion_type == "body_contains":
                actual = expected
                success = str(expected) in body_text
            elif assertion_type == "json_equals":
                if json_body is None:
                    json_body = response.json()
                actual = _json_path(json_body, item.get("path"))
                success = str(actual) == str(expected)
            elif assertion_type == "header_exists":
                actual = item.get("path") or item.get("name") or item.get("header")
                success = actual in response.headers
            else:
                error = "不支持的断言类型"
        except Exception as exc:
            error = str(exc)
        results.append({"name": name, "type": assertion_type, "success": success, "actual": actual, "expected": expected, "error": error})
    return results


def _execute_case_source(source, case=None, environment_id=None, context=None, timeout=30):
    context = context or {}
    project_id = _int_or_none(source.get("project_id"))
    variables = {}
    variables.update(_variables_for(environment_id or source.get("environment_id")))
    variables.update(context)
    method = (source.get("method") or "GET").upper()
    url = _apply_variables(source.get("url") or "", variables)
    headers = _apply_variables(source.get("headers") or {}, variables)
    params = _apply_variables(source.get("params") or {}, variables)
    body_type = source.get("body_type") or "json"
    body = _apply_variables(source.get("body") or "", variables)
    assertions = _apply_variables(source.get("assertions") or [], variables)
    extractors = _apply_variables(source.get("extractors") or [], variables)
    result = ApiRunResult(
        case_id=case.id if case else None,
        environment_id=environment_id or source.get("environment_id"),
        project_id=project_id,
        method=method,
        url=url,
        request_headers=_json_text(headers),
        request_params=_json_text(params),
        request_body=body,
    )
    apply_run_user(result)
    started = time.time()
    extracted = {}
    extractor_result = []
    try:
        request_kwargs = {"headers": headers, "params": params, "timeout": timeout}
        if method not in ("GET", "DELETE", "HEAD"):
            if body_type == "json" and body:
                request_kwargs["json"] = _loads(body, {})
            elif body_type == "form":
                request_kwargs["data"] = _loads(body, {})
            elif body_type == "raw":
                request_kwargs["data"] = body
        response = requests.request(method, url, **request_kwargs)
        body_text = response.text
        assertion_result = _run_assertions(response, body_text, assertions)
        extracted, extractor_result = _extract_variables(response, body_text, extractors)
        success = all(item.get("success") for item in assertion_result)
        result.response_status = response.status_code
        result.response_headers = _json_text(dict(response.headers))
        result.response_body = body_text[:200000]
        result.elapsed_ms = int((time.time() - started) * 1000)
        result.success = 1 if success else 0
        result.assertion_result = _json_text({
            "assertions": assertion_result,
            "extractors": extractor_result,
        })
        if case:
            case.last_status = response.status_code
            case.last_success = result.success
            case.last_elapsed_ms = result.elapsed_ms
            apply_run_user(case)
    except Exception as exc:
        result.elapsed_ms = int((time.time() - started) * 1000)
        result.success = 0
        result.error_message = str(exc)
        result.assertion_result = _json_text({"assertions": [], "extractors": extractor_result})
    db.session.add(result)
    return result, extracted


@api_test.route('/get_environment_info', methods=["POST"])
def get_environment_info():
    data = request.get_json(silent=True) or {}
    project_id = _int_or_none(data.get("project_id"))
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
    return jsonify({"code": 200, "msg": "请求成功", "data": [_environment_payload(item) for item in rows]})


@api_test.route('/save_environment', methods=["POST"])
def save_environment():
    data = request.get_json(silent=True) or {}
    project_id = _int_or_none(data.get("project_id"))
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
    item.variables = _json_text(variables)
    item.description = data.get("description") or ""
    db.session.add(item)
    db.session.commit()
    return jsonify({"code": 200, "msg": "保存成功", "data": _environment_payload(item)})


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
    db.session.commit()
    return jsonify({"code": 200, "msg": "删除成功", "data": None})


@api_test.route('/get_case_info', methods=["POST"])
def get_case_info():
    _ensure_api_case_columns()
    data = request.get_json(silent=True) or {}
    page_no = int(data.get("page_no", 0) or 0)
    page_size = int(data.get("page_size", 20) or 20)
    project_id = _int_or_none(data.get("project_id"))
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
    total = query.count()
    rows = query.order_by(db.desc(ApiCase.updated_time)).limit(page_size).offset(page_no).all()
    return jsonify({"code": 200, "msg": "请求成功", "data": [_case_payload(item) for item in rows], "total": total})


@api_test.route('/save_case', methods=["POST"])
def save_case():
    _ensure_api_case_columns()
    data = request.get_json(silent=True) or {}
    project_id = _int_or_none(data.get("project_id"))
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
    item.headers = _json_text(data.get("headers") or {})
    item.params = _json_text(data.get("params") or {})
    item.body_type = data.get("body_type") or "json"
    item.body = data.get("body") or ""
    item.assertions = _json_text(data.get("assertions") or [])
    item.pre_case_ids = _json_text(_normalize_case_ids(data.get("pre_case_ids") or []))
    item.extractors = _json_text(data.get("extractors") or [])
    item.description = data.get("description") or ""
    db.session.add(item)
    db.session.commit()
    return jsonify({"code": 200, "msg": "保存成功", "data": _case_payload(item)})


@api_test.route('/delete_case', methods=["POST"])
def delete_case():
    _ensure_api_case_columns()
    data = request.get_json(silent=True) or {}
    item = ApiCase.query.filter_by(id=data.get("id"), is_delete=0).first()
    if not item:
        return jsonify({"code": 404, "msg": "接口用例不存在", "data": None})
    permission_error = _check_project(item.project_id, "edit")
    if permission_error:
        return permission_error
    item.is_delete = 1
    db.session.commit()
    return jsonify({"code": 200, "msg": "删除成功", "data": None})


@api_test.route('/run_case', methods=["POST"])
def run_case():
    _ensure_api_case_columns()
    data = request.get_json(silent=True) or {}
    case = ApiCase.query.filter_by(id=data.get("id"), is_delete=0).first() if data.get("id") else None
    source = _case_payload(case) if case else data
    project_id = _int_or_none(source.get("project_id"))
    permission_error = _check_project(project_id, "run")
    if permission_error:
        return permission_error
    environment_id = _int_or_none(data.get("environment_id") or source.get("environment_id"))
    timeout = min(max(int(data.get("timeout") or 30), 1), 120)

    if not case:
        result, _ = _execute_case_source(source, case=None, environment_id=environment_id, context={}, timeout=timeout)
        db.session.commit()
        return jsonify({"code": 200, "msg": "执行完成", "data": _result_payload(result)})

    try:
        chain = _resolve_dependency_order(case)
    except ValueError as exc:
        return jsonify({"code": 404, "msg": str(exc), "data": None})

    context = {}
    chain_results = []
    final_result = None
    for chain_case in chain:
        chain_source = _case_payload(chain_case)
        result, extracted = _execute_case_source(
            chain_source,
            case=chain_case,
            environment_id=environment_id,
            context=context,
            timeout=timeout,
        )
        context.update(extracted)
        payload = _result_payload(result)
        payload["case_name"] = chain_case.name
        payload["extracted_variables"] = extracted
        chain_results.append(payload)
        final_result = result
        if not result.success:
            result.error_message = (result.error_message or "") + "\n依赖链执行中断"
            break
    db.session.commit()
    final_payload = _result_payload(final_result)
    final_payload["chain_results"] = chain_results
    final_payload["context"] = context
    final_payload["dependency_order"] = [{"id": item.id, "name": item.name} for item in chain]
    return jsonify({"code": 200, "msg": "执行完成", "data": final_payload})


@api_test.route('/get_run_history', methods=["POST"])
def get_run_history():
    _ensure_api_case_columns()
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
    return jsonify({"code": 200, "msg": "请求成功", "data": [_result_payload(item) for item in rows]})


@api_test.route('/get_suite_info', methods=["POST"])
def get_suite_info():
    data = request.get_json(silent=True) or {}
    page_no = int(data.get("page_no", 0) or 0)
    page_size = int(data.get("page_size", 20) or 20)
    project_id = _int_or_none(data.get("project_id"))
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
    total = query.count()
    rows = query.order_by(db.desc(ApiSuite.updated_time)).limit(page_size).offset(page_no).all()
    return jsonify({"code": 200, "msg": "请求成功", "data": [_suite_payload(item) for item in rows], "total": total})


@api_test.route('/save_suite', methods=["POST"])
def save_suite():
    data = request.get_json(silent=True) or {}
    project_id = _int_or_none(data.get("project_id"))
    permission_error = _check_project(project_id, "edit")
    if permission_error:
        return permission_error
    name = (data.get("name") or "").strip()
    case_ids = _normalize_case_ids(data.get("case_ids") or [])
    if not name:
        return jsonify({"code": 404, "msg": "集合名称不能为空", "data": None})
    if not case_ids:
        return jsonify({"code": 404, "msg": "请至少选择一个接口", "data": None})
    cases = _load_ordered_cases(case_ids)
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
    suite.environment_id = _int_or_none(data.get("environment_id"))
    suite.case_ids = _json_text(case_ids)
    suite.stop_on_fail = 1 if data.get("stop_on_fail", 1) else 0
    suite.description = data.get("description") or ""
    db.session.add(suite)
    db.session.commit()
    return jsonify({"code": 200, "msg": "保存成功", "data": _suite_payload(suite)})


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
    db.session.commit()
    return jsonify({"code": 200, "msg": "删除成功", "data": None})


@api_test.route('/run_suite', methods=["POST"])
def run_suite():
    data = request.get_json(silent=True) or {}
    suite = ApiSuite.query.filter_by(id=data.get("id"), is_delete=0).first()
    if not suite:
        return jsonify({"code": 404, "msg": "接口集合不存在", "data": None})
    permission_error = _check_project(suite.project_id, "run")
    if permission_error:
        return permission_error
    environment_id = _int_or_none(data.get("environment_id") or suite.environment_id)
    timeout = min(max(int(data.get("timeout") or 30), 1), 120)
    case_ids = _normalize_case_ids(_loads(suite.case_ids, []))
    cases = _load_ordered_cases(case_ids)
    started = time.time()
    context = {}
    step_results = []
    pass_count = 0
    fail_count = 0
    for index, case in enumerate(cases):
        try:
            chain = _resolve_dependency_order(case)
        except ValueError as exc:
            fail_count += 1
            step_results.append({"case_id": case.id, "case_name": case.name, "success": 0, "error_message": str(exc), "index": index + 1})
            if suite.stop_on_fail:
                break
            continue
        for chain_case in chain:
            source = _case_payload(chain_case)
            result, extracted = _execute_case_source(source, case=chain_case, environment_id=environment_id, context=context, timeout=timeout)
            context.update(extracted)
            payload = _result_payload(result)
            payload["case_name"] = chain_case.name
            payload["case_id"] = chain_case.id
            payload["suite_index"] = index + 1
            payload["extracted_variables"] = extracted
            step_results.append(payload)
            if result.success:
                pass_count += 1
            else:
                fail_count += 1
                if suite.stop_on_fail:
                    break
        if suite.stop_on_fail and step_results and not step_results[-1].get("success"):
            break
    elapsed_ms = int((time.time() - started) * 1000)
    suite_result = ApiSuiteRunResult(
        suite_id=suite.id,
        project_id=suite.project_id,
        environment_id=environment_id,
        total_count=len(step_results),
        pass_count=pass_count,
        fail_count=fail_count,
        elapsed_ms=elapsed_ms,
        success=1 if fail_count == 0 else 0,
        context=_json_text(context),
        step_results=_json_text(step_results),
    )
    apply_run_user(suite_result)
    suite.last_success = suite_result.success
    suite.last_elapsed_ms = elapsed_ms
    suite.last_run_time = datetime.datetime.now()
    db.session.add(suite_result)
    db.session.commit()
    return jsonify({"code": 200, "msg": "执行完成", "data": _suite_result_payload(suite_result)})


@api_test.route('/get_suite_history', methods=["POST"])
def get_suite_history():
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
    return jsonify({"code": 200, "msg": "请求成功", "data": [_suite_result_payload(item) for item in rows]})
