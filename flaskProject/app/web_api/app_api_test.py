# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
import json
import re
import time

import requests
from flask import jsonify, request

from app.lib.lib_define import db
from app.models.test_api_models import ApiCase, ApiEnvironment, ApiRunResult
from app.web_api import api_test
from app.tools.audit_fields import apply_run_user
from app.tools.auth_permissions import allowed_project_ids, require_project_permission


VAR_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")


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
    data = _with_time(item.to_dict())
    data["headers"] = _loads(data.get("headers"), {})
    data["params"] = _loads(data.get("params"), {})
    data["assertions"] = _loads(data.get("assertions"), [])
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
    data["assertion_result"] = _loads(data.get("assertion_result"), [])
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
    item.description = data.get("description") or ""
    db.session.add(item)
    db.session.commit()
    return jsonify({"code": 200, "msg": "保存成功", "data": _case_payload(item)})


@api_test.route('/delete_case', methods=["POST"])
def delete_case():
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
    data = request.get_json(silent=True) or {}
    case = ApiCase.query.filter_by(id=data.get("id"), is_delete=0).first() if data.get("id") else None
    source = _case_payload(case) if case else data
    project_id = _int_or_none(source.get("project_id"))
    permission_error = _check_project(project_id, "run")
    if permission_error:
        return permission_error
    environment_id = _int_or_none(data.get("environment_id") or source.get("environment_id"))
    variables = _variables_for(environment_id)
    method = (source.get("method") or "GET").upper()
    url = _apply_variables(source.get("url") or "", variables)
    headers = _apply_variables(source.get("headers") or {}, variables)
    params = _apply_variables(source.get("params") or {}, variables)
    body_type = source.get("body_type") or "json"
    body = _apply_variables(source.get("body") or "", variables)
    assertions = _apply_variables(source.get("assertions") or [], variables)
    timeout = min(max(int(data.get("timeout") or 30), 1), 120)
    result = ApiRunResult(
        case_id=case.id if case else None,
        environment_id=environment_id,
        project_id=project_id,
        method=method,
        url=url,
        request_headers=_json_text(headers),
        request_params=_json_text(params),
        request_body=body,
    )
    apply_run_user(result)
    started = time.time()
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
        success = all(item.get("success") for item in assertion_result)
        result.response_status = response.status_code
        result.response_headers = _json_text(dict(response.headers))
        result.response_body = body_text[:200000]
        result.elapsed_ms = int((time.time() - started) * 1000)
        result.success = 1 if success else 0
        result.assertion_result = _json_text(assertion_result)
        if case:
            case.last_status = response.status_code
            case.last_success = result.success
            case.last_elapsed_ms = result.elapsed_ms
            apply_run_user(case)
    except Exception as exc:
        result.elapsed_ms = int((time.time() - started) * 1000)
        result.success = 0
        result.error_message = str(exc)
    db.session.add(result)
    db.session.commit()
    return jsonify({"code": 200, "msg": "执行完成", "data": _result_payload(result)})


@api_test.route('/get_run_history', methods=["POST"])
def get_run_history():
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
