# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
import base64
import json
import os
import re
import threading
import time
import datetime
from html import escape

import requests
from flask import current_app, jsonify, request
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.lib.lib_define import db
from app.models.test_api_models import ApiCase, ApiEnvironment, ApiReport, ApiRunResult, ApiSuite, ApiSuiteRunResult, CaseResult
from app.web_api import api_test
from app.tools.audit_fields import apply_run_user
from app.tools.auth_permissions import allowed_project_ids, current_account, require_project_permission
from config import report_path


VAR_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)(?:\s*\|\s*([A-Za-z0-9_-]+))?\s*\}\}")
API_CASE_EXTRA_COLUMNS = {
    "pre_case_ids": "TEXT",
    "extractors": "TEXT",
}
API_RUNTIME_EXTRA_COLUMNS = {
    "api_suite": {
        "dependency_strategy": "VARCHAR(40) DEFAULT 'retry_on_auth_fail'",
    },
    "api_run_result": {
        "run_id": "BIGINT DEFAULT 0",
        "run_status": "VARCHAR(40) DEFAULT 'finished'",
        "status_text": "VARCHAR(191) DEFAULT ''",
    },
    "api_suite_run_result": {
        "run_id": "BIGINT DEFAULT 0",
        "run_status": "VARCHAR(40) DEFAULT 'finished'",
        "status_text": "VARCHAR(191) DEFAULT ''",
    },
    "api_report": {
        "run_id": "BIGINT DEFAULT 0",
        "report_path": "VARCHAR(1000)",
    },
    "caseresult": {
        "source_type": "VARCHAR(40) DEFAULT 'pytest'",
        "api_result_id": "INTEGER",
        "api_suite_result_id": "INTEGER",
    },
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


def _ensure_api_runtime_columns():
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    with db.engine.begin() as conn:
        for table_name, columns in API_RUNTIME_EXTRA_COLUMNS.items():
            if table_name not in table_names:
                continue
            existing = {item.get("name") for item in inspector.get_columns(table_name)}
            for name, column_type in columns.items():
                if name in existing:
                    continue
                try:
                    conn.execute(text("ALTER TABLE {} ADD COLUMN {} {}".format(table_name, name, column_type)))
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


def _run_id_text(value):
    return str(value) if value not in (None, "") else ""


def _new_api_run_id():
    return int(datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:17] + str(int(time.time() * 1000000) % 100).zfill(2))


def _api_run_id_from(data):
    run_id = _int_or_none(data.get("run_id") or data.get("_api_run_id"))
    return run_id or _new_api_run_id()


def _normalize_dependency_strategy(value):
    value = str(value or "").strip()
    if value in ("once", "always", "retry_on_auth_fail"):
        return value
    return "retry_on_auth_fail"


def _is_auth_failure(result):
    if not result:
        return False
    if result.response_status in (401, 403):
        return True
    body = result.response_body or ""
    try:
        parsed = json.loads(body)
        if _int_or_none(parsed.get("code")) in (401, 403):
            return True
    except Exception:
        pass
    return False


def _api_report_filename(target_type, run_id):
    if not run_id:
        raise ValueError("api report run_id is required")
    safe_type = re.sub(r"[^A-Za-z0-9_-]+", "_", str(target_type or "case")).strip("_") or "case"
    return "api_{}_{}.html".format(safe_type, run_id)


def _display_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
    return str(value)


def _html_pre(value):
    return escape(_display_text(value))


def _result_status_text(success):
    if success in (1, True, "1", "true", "True"):
        return "PASSED"
    if success in (0, False, "0", "false", "False"):
        return "FAILED"
    return "PENDING"


def _write_api_report_file(report, detail=None):
    detail = detail or _loads(report.detail, {})
    summary = _loads(report.summary, {})
    run_id = report.run_id
    if not run_id:
        raise ValueError("api report run_id is required")
    filename = report.report_path or _api_report_filename(report.target_type, run_id)
    os.makedirs(report_path, exist_ok=True)
    report_root = os.path.realpath(report_path)
    target_path = os.path.realpath(os.path.join(report_root, filename))
    if os.path.commonpath([report_root, target_path]) != report_root:
        raise ValueError("invalid api report path")
    steps = detail.get("step_results") or detail.get("chain_results") or []
    if not isinstance(steps, list):
        steps = []
    step_rows = []
    for index, item in enumerate(steps, start=1):
        step_rows.append(
            "<tr>"
            "<td>{}</td><td>{}</td><td><span class='status {}'>{}</span></td>"
            "<td>{}</td><td>{}</td><td>{}</td>"
            "</tr>".format(
                index,
                escape(str(item.get("case_name") or item.get("name") or item.get("url") or "-")),
                "pass" if item.get("success") else "fail",
                _result_status_text(item.get("success")),
                escape(str(item.get("response_status") or item.get("status") or "-")),
                escape(str(item.get("elapsed_ms") or 0)),
                escape(str(item.get("error_message") or "")),
            )
        )
    html = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color: #1f2937; background: #f5f7fb; }}
    .page {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    .header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 24px; }}
    .muted {{ color: #6b7280; font-size: 13px; }}
    .badge {{ display: inline-block; padding: 6px 10px; border-radius: 4px; font-weight: 700; }}
    .badge.pass, .status.pass {{ color: #16a34a; background: #dcfce7; }}
    .badge.fail, .status.fail {{ color: #dc2626; background: #fee2e2; }}
    .cards {{ display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 12px; margin: 18px 0; }}
    .card {{ background: #fff; border: 1px solid #dbe3ef; border-radius: 6px; padding: 14px; }}
    .card span {{ display: block; color: #6b7280; font-size: 12px; margin-bottom: 6px; }}
    .card strong {{ font-size: 22px; }}
    .section {{ background: #fff; border: 1px solid #dbe3ef; border-radius: 6px; margin-top: 14px; padding: 16px; }}
    .section h2 {{ margin: 0 0 12px; font-size: 16px; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th, td {{ border-bottom: 1px solid #e5edf6; padding: 10px; text-align: left; vertical-align: top; word-break: break-word; }}
    th {{ background: #eef3f9; }}
    .status {{ display: inline-block; padding: 3px 7px; border-radius: 4px; font-size: 12px; font-weight: 700; }}
    pre {{ margin: 0; padding: 12px; background: #0f172a; color: #e5e7eb; border-radius: 6px; overflow: auto; line-height: 1.55; }}
  </style>
</head>
<body>
  <div class="page">
    <div class="header">
      <div>
        <h1>{title}</h1>
        <div class="muted">run_id: {run_id} · target: {target_name}</div>
      </div>
      <span class="badge {status_class}">{status_text}</span>
    </div>
    <div class="cards">
      <div class="card"><span>全部</span><strong>{total}</strong></div>
      <div class="card"><span>通过</span><strong>{passed}</strong></div>
      <div class="card"><span>失败</span><strong>{failed}</strong></div>
      <div class="card"><span>耗时/ms</span><strong>{elapsed}</strong></div>
      <div class="card"><span>状态码</span><strong>{status_code}</strong></div>
    </div>
    <div class="section">
      <h2>执行步骤</h2>
      <table>
        <thead><tr><th style="width:60px;">#</th><th>接口</th><th style="width:100px;">结果</th><th style="width:100px;">状态码</th><th style="width:110px;">耗时/ms</th><th>错误</th></tr></thead>
        <tbody>{step_rows}</tbody>
      </table>
    </div>
    <div class="section">
      <h2>请求与响应详情</h2>
      <pre>{detail}</pre>
    </div>
    <div class="section">
      <h2>摘要</h2>
      <pre>{summary}</pre>
    </div>
  </div>
</body>
</html>""".format(
        title=escape(report.title or "API Report"),
        run_id=escape(str(run_id)),
        target_name=escape(str(report.target_name or "")),
        status_class="pass" if report.success else "fail",
        status_text=_result_status_text(report.success),
        total=report.total_count or 0,
        passed=report.pass_count or 0,
        failed=report.fail_count or 0,
        elapsed=report.elapsed_ms or 0,
        status_code=escape(str(summary.get("status") or "-")),
        step_rows="".join(step_rows) or "<tr><td>1</td><td>{}</td><td><span class='status {}'>{}</span></td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            escape(str(report.target_name or detail.get("url") or "-")),
            "pass" if report.success else "fail",
            _result_status_text(report.success),
            escape(str(summary.get("status") or detail.get("response_status") or "-")),
            escape(str(report.elapsed_ms or detail.get("elapsed_ms") or 0)),
            escape(str(detail.get("error_message") or "")),
        ),
        detail=_html_pre(detail),
        summary=_html_pre(summary),
    )
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(html)
    return filename


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
    data["run_id"] = _run_id_text(data.get("run_id"))
    data["request_headers"] = _loads(data.get("request_headers"), {})
    data["request_params"] = _loads(data.get("request_params"), {})
    data["response_headers"] = _loads(data.get("response_headers"), {})
    detail = _loads(data.get("assertion_result"), [])
    if isinstance(detail, dict):
        data["assertion_result"] = detail.get("assertions") or []
        data["extractor_result"] = detail.get("extractors") or []
        data["chain_results"] = detail.get("chain_results") or []
        data["context"] = detail.get("context") or {}
    else:
        data["assertion_result"] = detail or []
        data["extractor_result"] = []
        data["chain_results"] = []
        data["context"] = {}
    return data


def _copy_result_fields(target, payload):
    for name in [
        "run_id",
        "environment_id", "project_id", "method", "url", "request_headers", "request_params",
        "request_body", "response_status", "response_headers", "response_body", "elapsed_ms",
        "success", "assertion_result", "error_message",
    ]:
        if name in payload and hasattr(target, name):
            value = payload.get(name)
            if name == "run_id":
                value = _int_or_none(value)
            if name in ("request_headers", "request_params", "response_headers", "assertion_result") and not isinstance(value, str):
                value = _json_text(value)
            setattr(target, name, value)


def _suite_payload(item):
    data = _with_time(item.to_dict())
    data["case_ids"] = _loads(data.get("case_ids"), [])
    cases = _load_ordered_cases(data["case_ids"])
    data["case_list"] = [
        {
            "id": case.id,
            "name": case.name,
            "method": case.method,
            "url": case.url,
            "last_status": case.last_status,
            "last_success": case.last_success,
        }
        for case in cases
    ]
    data["stop_on_fail"] = 1 if data.get("stop_on_fail") else 0
    data["dependency_strategy"] = _normalize_dependency_strategy(data.get("dependency_strategy"))
    data["last_run_time"] = _format_time(data.get("last_run_time"))
    return data


def _suite_result_payload(item):
    data = _with_time(item.to_dict())
    data["run_id"] = _run_id_text(data.get("run_id"))
    data["context"] = _loads(data.get("context"), {})
    data["step_results"] = _loads(data.get("step_results"), [])
    for step in data["step_results"]:
        if isinstance(step, dict) and "run_id" in step:
            step["run_id"] = _run_id_text(step.get("run_id"))
    return data


def _api_report_payload(item):
    data = _with_time(item.to_dict())
    data["run_id"] = _run_id_text(data.get("run_id"))
    data["summary"] = _loads(data.get("summary"), {})
    data["detail"] = _loads(data.get("detail"), {})
    data["report_source"] = "api"
    data["report_source_name"] = "接口测试报告"
    return data


def _suite_pending_steps(cases, start_index=1):
    return [
        {
            "case_id": item.id,
            "case_name": item.name,
            "success": None,
            "run_status": "pending",
            "status_text": "待执行",
            "suite_index": start_index + index,
        }
        for index, item in enumerate(cases)
    ]


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


def _encode_base64(value):
    return base64.b64encode(str(value).encode("utf-8")).decode("ascii")


def _format_variable_value(name, variables, transform=None):
    if name not in variables:
        return "{{%s%s}}" % (name, ("|" + transform) if transform else "")
    value = variables.get(name)
    if transform in (None, ""):
        return value
    transform = transform.lower()
    if transform == "base64":
        return _encode_base64(value)
    if transform == "basic":
        return _encode_base64(str(value) + ":")
    if transform == "urlencode":
        from urllib.parse import quote_plus
        return quote_plus(str(value))
    return value


def _apply_variables(value, variables):
    if isinstance(value, str):
        return VAR_PATTERN.sub(lambda m: str(_format_variable_value(m.group(1), variables, m.group(2))), value)
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


CASE_SOURCE_FIELDS = [
    "name",
    "project_id",
    "environment_id",
    "method",
    "url",
    "headers",
    "params",
    "body_type",
    "body",
    "assertions",
    "pre_case_ids",
    "extractors",
]


def _case_source_from_request(case, data):
    source = _case_payload(case) if case else {}
    for key in CASE_SOURCE_FIELDS:
        if key in data:
            source[key] = data.get(key)
    return source or data


def _resolve_dependency_order_for_source(case, source):
    visiting = []
    visited = set()
    order = []

    def resolve(item, is_root=False):
        if not item:
            return
        if item.id in visited:
            return
        if item.id in visiting:
            cycle = visiting[visiting.index(item.id):] + [item.id]
            cycle_names = ["{}({})".format(_case_name(case_id), case_id) for case_id in cycle]
            raise ValueError("接口依赖存在循环：" + " -> ".join(cycle_names))
        visiting.append(item.id)
        if is_root:
            pre_case_ids = _normalize_case_ids(_loads(source.get("pre_case_ids"), []))
        else:
            pre_case_ids = _normalize_case_ids(_loads(item.pre_case_ids, []))
        for pre_case_id in pre_case_ids:
            pre_case = ApiCase.query.filter_by(id=pre_case_id, is_delete=0).first()
            if not pre_case:
                raise ValueError("依赖接口不存在：{}".format(pre_case_id))
            if item.project_id and pre_case.project_id and item.project_id != pre_case.project_id:
                raise ValueError("依赖接口不属于同一个项目：{}".format(pre_case.name))
            resolve(pre_case)
        visiting.pop()
        visited.add(item.id)
        order.append(item)

    resolve(case, is_root=True)
    return order


def _resolve_dependency_order(case, visiting=None, visited=None, order=None):
    if visiting is None:
        visiting = []
    if visited is None:
        visited = set()
    if order is None:
        order = []
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


def _assertion_failure_message(assertion_result):
    failed = [item for item in (assertion_result or []) if not item.get("success")]
    if not failed:
        return ""
    messages = []
    for item in failed[:3]:
        name = item.get("name") or item.get("type") or "断言"
        if item.get("error"):
            messages.append("{}：{}".format(name, item.get("error")))
        else:
            messages.append("{}失败，期望：{}，实际：{}".format(name, item.get("expected", ""), item.get("actual", "")))
    if len(failed) > 3:
        messages.append("还有{}个断言失败".format(len(failed) - 3))
    return "；".join(messages)


def _execute_case_source(source, case=None, environment_id=None, context=None, timeout=30, run_id=None):
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
        run_id=run_id or _new_api_run_id(),
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
        if not success:
            result.error_message = _assertion_failure_message(assertion_result)
        result.assertion_result = _json_text({
            "assertions": assertion_result,
            "extractors": extractor_result,
            "context": context,
            "context_variables": context,
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
        result.assertion_result = _json_text({"assertions": [], "extractors": extractor_result, "context": context, "context_variables": context})
    db.session.add(result)
    return result, extracted


def _run_case_payload(data):
    _ensure_api_case_columns()
    _ensure_api_runtime_columns()
    run_id = _api_run_id_from(data)
    data["_api_run_id"] = run_id
    case = ApiCase.query.filter_by(id=data.get("id"), is_delete=0).first() if data.get("id") else None
    source = _case_source_from_request(case, data)
    environment_id = _int_or_none(data.get("environment_id") or source.get("environment_id"))
    timeout = min(max(int(data.get("timeout") or 30), 1), 120)

    if not case:
        result, _ = _execute_case_source(source, case=None, environment_id=environment_id, context={}, timeout=timeout, run_id=run_id)
        result.run_status = "finished"
        result.status_text = "执行完成"
        db.session.flush()
        _create_api_case_execution_result(result)
        _create_api_case_report(result, _result_payload(result), title_prefix="接口临时请求")
        db.session.commit()
        return _result_payload(result)

    chain = _resolve_dependency_order_for_source(case, source)
    context = {}
    chain_results = []
    final_result = None
    for chain_case in chain:
        chain_source = source if chain_case.id == case.id else _case_payload(chain_case)
        result, extracted = _execute_case_source(
            chain_source,
            case=chain_case,
            environment_id=environment_id,
            context=context,
            timeout=timeout,
            run_id=run_id,
        )
        result.run_status = "finished"
        result.status_text = "执行完成"
        db.session.flush()
        _create_api_case_execution_result(result)
        context.update(extracted)
        payload = _result_payload(result)
        payload["case_name"] = chain_case.name
        payload["extracted_variables"] = extracted
        chain_results.append(payload)
        final_result = result
        if not result.success:
            if chain_case.id != case.id:
                result.error_message = "{}\n依赖接口执行失败，依赖链执行中断".format(result.error_message or "").strip()
            db.session.commit()
            break
        db.session.commit()
    final_payload = _result_payload(final_result)
    final_payload["chain_results"] = chain_results
    final_payload["context"] = context
    final_payload["dependency_order"] = [{"id": item.id, "name": item.name} for item in chain]
    _create_api_case_report(final_result, final_payload)
    db.session.commit()
    return final_payload


def _apply_account_info(target, account_info):
    if not account_info:
        return
    for prefix in ("created", "updated", "run"):
        id_field = "{}_by".format(prefix)
        name_field = "{}_by_name".format(prefix)
        if hasattr(target, id_field):
            setattr(target, id_field, account_info.get("id"))
        if hasattr(target, name_field):
            setattr(target, name_field, account_info.get("name"))


def _create_api_case_report(result, payload=None, title_prefix="接口用例"):
    payload = payload or _result_payload(result)
    case = ApiCase.query.filter_by(id=result.case_id, is_delete=0).first() if result.case_id else None
    assertions = payload.get("assertion_result") or []
    run_id = result.run_id
    if not run_id:
        raise ValueError("api case report run_id is required")
    report = ApiReport(
        title="{} - {} - {}".format(title_prefix, (case.name if case else payload.get("url") or "临时请求"), _format_time(datetime.datetime.now())),
        report_type="api",
        target_type="case",
        target_id=result.case_id,
        target_name=case.name if case else payload.get("url"),
        run_id=run_id,
        run_result_id=result.id,
        project_id=result.project_id,
        environment_id=result.environment_id,
        total_count=1,
        pass_count=1 if result.success else 0,
        fail_count=0 if result.success else 1,
        success=1 if result.success else 0,
        elapsed_ms=result.elapsed_ms,
        summary=_json_text({
            "source": "api_case",
            "status": result.response_status,
            "assertion_count": len(assertions),
            "extractor_count": len(payload.get("extractor_result") or []),
        }),
        detail=_json_text(payload),
    )
    report.report_path = _write_api_report_file(report, payload)
    _copy_audit_fields(report, result)
    db.session.add(report)
    return report


def _copy_audit_fields(target, source):
    for name in (
        "created_by",
        "created_by_name",
        "updated_by",
        "updated_by_name",
        "run_by",
        "run_by_name",
    ):
        if hasattr(target, name) and hasattr(source, name):
            setattr(target, name, getattr(source, name))


def _create_api_case_execution_result(result, suite_result_id=None):
    if not result or not result.id:
        return None
    exists = CaseResult.query.filter_by(source_type="api", api_result_id=result.id).first()
    if exists:
        return exists
    case = ApiCase.query.filter_by(id=result.case_id, is_delete=0).first() if result.case_id else None
    detail = _result_payload(result)
    run_id = result.run_id
    if not run_id:
        raise ValueError("api case result run_id is required")
    row = CaseResult(
        case_title=(case.name if case else result.url or "接口临时请求"),
        case_name="{} {}".format(result.method or "", result.url or "").strip(),
        project_name="接口测试",
        set_id=0,
        case_id=result.case_id or 0,
        config_id="[]",
        version_id=0,
        project_id=result.project_id or 0,
        run_info=result.response_body or "",
        longrepr=_json_text({
            "error_message": result.error_message,
            "assertion_result": detail.get("assertion_result") or [],
            "extractor_result": detail.get("extractor_result") or [],
            "request_method": result.method,
            "request_url": result.url,
            "request_headers": detail.get("request_headers") or {},
            "request_params": detail.get("request_params") or {},
            "request_body": result.request_body or "",
            "response_status": result.response_status,
            "response_headers": detail.get("response_headers") or {},
            "response_body": result.response_body or "",
        }),
        duration=round((result.elapsed_ms or 0) / 1000, 4),
        case_created="接口测试",
        file_path_name=result.url or "",
        file_name=result.url or "",
        run_case_result="passed" if result.success else "failed",
        source_type="api",
        api_result_id=result.id,
        api_suite_result_id=suite_result_id,
        mark="接口测试",
        run_id=run_id,
        class_name="API",
    )
    _copy_audit_fields(row, result)
    db.session.add(row)
    return row


def _create_api_suite_report(suite_result, suite=None):
    suite = suite or ApiSuite.query.filter_by(id=suite_result.suite_id, is_delete=0).first()
    step_results = _loads(suite_result.step_results, [])
    run_id = suite_result.run_id
    if not run_id:
        raise ValueError("api suite report run_id is required")
    report = ApiReport(
        title="接口集合 - {} - run_id {} - {}".format(
            (suite.name if suite else "集合{}".format(suite_result.suite_id)),
            run_id,
            _format_time(datetime.datetime.now()),
        ),
        report_type="api",
        target_type="suite",
        target_id=suite_result.suite_id,
        target_name=suite.name if suite else "",
        run_id=run_id,
        suite_result_id=suite_result.id,
        project_id=suite_result.project_id,
        environment_id=suite_result.environment_id,
        total_count=suite_result.total_count or len(step_results),
        pass_count=suite_result.pass_count or 0,
        fail_count=suite_result.fail_count or 0,
        success=1 if suite_result.success else 0,
        elapsed_ms=suite_result.elapsed_ms,
        summary=_json_text({
            "source": "api_suite",
            "step_count": len(step_results),
            "context": _loads(suite_result.context, {}),
        }),
        detail=_json_text(_suite_result_payload(suite_result)),
    )
    report.report_path = _write_api_report_file(report, _suite_result_payload(suite_result))
    _copy_audit_fields(report, suite_result)
    db.session.add(report)
    return report


def _run_case_background(app, result_id, data, account_info):
    with app.app_context():
        _ensure_api_case_columns()
        _ensure_api_runtime_columns()
        result = ApiRunResult.query.get(result_id)
        if not result:
            return
        started = time.time()
        try:
            result.run_status = "running"
            result.status_text = "执行中"
            db.session.commit()
            payload = _run_case_payload(data)
            result = ApiRunResult.query.get(result_id)
            _copy_result_fields(result, payload)
            result.run_status = "finished"
            result.status_text = "执行完成"
            result.elapsed_ms = payload.get("elapsed_ms") or int((time.time() - started) * 1000)
            result.assertion_result = _json_text({
                "assertions": payload.get("assertion_result") or [],
                "extractors": payload.get("extractor_result") or [],
                "chain_results": payload.get("chain_results") or [],
                "context": payload.get("context") or {},
            })
            _apply_account_info(result, account_info)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            result = ApiRunResult.query.get(result_id)
            if result:
                result.run_status = "failed"
                result.status_text = "执行异常"
                result.success = 0
                result.elapsed_ms = int((time.time() - started) * 1000)
                result.error_message = str(exc)
                _apply_account_info(result, account_info)
                db.session.commit()


def _run_suite_background(app, suite_result_id, suite_id, environment_id, timeout, account_info, run_id=None):
    with app.app_context():
        _ensure_api_runtime_columns()
        suite_result = ApiSuiteRunResult.query.get(suite_result_id)
        suite = ApiSuite.query.filter_by(id=suite_id, is_delete=0).first()
        if not suite_result or not suite:
            return
        started = time.time()
        try:
            suite_run_id = suite_result.run_id
            if not suite_run_id:
                raise ValueError("api suite run_id is required")
            suite_result.run_status = "running"
            suite_result.status_text = "执行中"
            db.session.commit()
            case_ids = _normalize_case_ids(_loads(suite.case_ids, []))
            cases = _load_ordered_cases(case_ids)
            context = {}
            step_results = []
            pass_count = 0
            fail_count = 0
            executed_success_case_ids = set()
            dependency_strategy = _normalize_dependency_strategy(suite.dependency_strategy)
            for index, case in enumerate(cases):
                try:
                    chain = _resolve_dependency_order(case)
                except ValueError as exc:
                    fail_count += 1
                    step_results.append({
                        "case_id": case.id,
                        "case_name": case.name,
                        "success": 0,
                        "run_status": "failed",
                        "status_text": "依赖异常",
                        "error_message": str(exc),
                        "index": index + 1,
                    })
                    suite_result.fail_count = fail_count
                    suite_result.total_count = len(step_results)
                    suite_result.step_results = _json_text(step_results + _suite_pending_steps(cases[index + 1:], index + 2))
                    db.session.commit()
                    if suite.stop_on_fail:
                        break
                    continue
                for chain_case in chain:
                    is_suite_item = chain_case.id == case.id
                    if dependency_strategy != "always" and not is_suite_item and chain_case.id in executed_success_case_ids:
                        continue
                    running_step = {
                        "case_id": chain_case.id,
                        "case_name": chain_case.name,
                        "is_suite_item": is_suite_item,
                        "step_type": "case" if is_suite_item else "dependency",
                        "step_type_name": "集合接口" if is_suite_item else "前置依赖",
                        "success": None,
                        "run_status": "running",
                        "status_text": "执行中",
                        "suite_index": index + 1,
                    }
                    suite_result.total_count = len(step_results) + 1
                    suite_result.step_results = _json_text(step_results + [running_step] + _suite_pending_steps(cases[index + 1:], index + 2))
                    db.session.commit()
                    source = _case_payload(chain_case)
                    result, extracted = _execute_case_source(source, case=chain_case, environment_id=environment_id, context=context, timeout=timeout, run_id=suite_run_id)
                    if is_suite_item and dependency_strategy == "retry_on_auth_fail" and _is_auth_failure(result):
                        db.session.expunge(result)
                        for refresh_case in chain[:-1]:
                            refresh_source = _case_payload(refresh_case)
                            refresh_result, refresh_extracted = _execute_case_source(
                                refresh_source,
                                case=refresh_case,
                                environment_id=environment_id,
                                context=context,
                                timeout=timeout,
                                run_id=suite_run_id,
                            )
                            refresh_result.run_status = "finished"
                            refresh_result.status_text = "执行完成"
                            _apply_account_info(refresh_result, account_info)
                            db.session.flush()
                            _create_api_case_execution_result(refresh_result, suite_result_id=suite_result_id)
                            context.update(refresh_extracted)
                            refresh_payload = _result_payload(refresh_result)
                            refresh_payload["case_name"] = refresh_case.name
                            refresh_payload["case_id"] = refresh_case.id
                            refresh_payload["suite_index"] = index + 1
                            refresh_payload["is_suite_item"] = False
                            refresh_payload["step_type"] = "dependency"
                            refresh_payload["step_type_name"] = "刷新依赖"
                            refresh_payload["extracted_variables"] = refresh_extracted
                            refresh_payload["run_status"] = "finished" if refresh_result.success else "failed"
                            refresh_payload["status_text"] = "通过" if refresh_result.success else "失败"
                            step_results.append(refresh_payload)
                            if refresh_result.success:
                                pass_count += 1
                                executed_success_case_ids.add(refresh_case.id)
                            else:
                                fail_count += 1
                                if suite.stop_on_fail:
                                    break
                        if not suite.stop_on_fail or not step_results or step_results[-1].get("success"):
                            result, extracted = _execute_case_source(source, case=chain_case, environment_id=environment_id, context=context, timeout=timeout, run_id=suite_run_id)
                        else:
                            break
                    result.run_status = "finished"
                    result.status_text = "执行完成"
                    _apply_account_info(result, account_info)
                    db.session.flush()
                    _create_api_case_execution_result(result, suite_result_id=suite_result_id)
                    context.update(extracted)
                    payload = _result_payload(result)
                    payload["case_name"] = chain_case.name
                    payload["case_id"] = chain_case.id
                    payload["suite_index"] = index + 1
                    payload["is_suite_item"] = is_suite_item
                    payload["step_type"] = "case" if is_suite_item else "dependency"
                    payload["step_type_name"] = "集合接口" if is_suite_item else "前置依赖"
                    payload["extracted_variables"] = extracted
                    payload["run_status"] = "finished" if result.success else "failed"
                    payload["status_text"] = "通过" if result.success else "失败"
                    step_results.append(payload)
                    if result.success:
                        pass_count += 1
                        executed_success_case_ids.add(chain_case.id)
                    else:
                        fail_count += 1
                    suite_result.pass_count = pass_count
                    suite_result.fail_count = fail_count
                    suite_result.total_count = len(step_results)
                    suite_result.context = _json_text(context)
                    suite_result.step_results = _json_text(step_results + _suite_pending_steps(cases[index + 1:], index + 2))
                    suite_result.elapsed_ms = int((time.time() - started) * 1000)
                    db.session.commit()
                    if not result.success and suite.stop_on_fail:
                        break
                if suite.stop_on_fail and step_results and not step_results[-1].get("success"):
                    break
            elapsed_ms = int((time.time() - started) * 1000)
            suite_result.total_count = len(step_results)
            suite_result.pass_count = pass_count
            suite_result.fail_count = fail_count
            suite_result.elapsed_ms = elapsed_ms
            suite_result.success = 1 if fail_count == 0 else 0
            suite_result.run_status = "finished"
            suite_result.status_text = "执行完成"
            suite_result.context = _json_text(context)
            suite_result.step_results = _json_text(step_results)
            suite.last_success = suite_result.success
            suite.last_elapsed_ms = elapsed_ms
            suite.last_run_time = datetime.datetime.now()
            _apply_account_info(suite_result, account_info)
            _apply_account_info(suite, account_info)
            db.session.flush()
            _create_api_suite_report(suite_result, suite)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            suite_result = ApiSuiteRunResult.query.get(suite_result_id)
            if suite_result:
                suite_result.run_status = "failed"
                suite_result.status_text = "执行异常"
                suite_result.success = 0
            suite_result.error_message = str(exc)
            suite_result.elapsed_ms = int((time.time() - started) * 1000)
            _apply_account_info(suite_result, account_info)
            db.session.flush()
            _create_api_suite_report(suite_result, suite)
            db.session.commit()


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
    run_status = data.get("run_status")
    if run_status == "passed":
        query = query.filter(ApiCase.last_success == 1)
    elif run_status == "failed":
        query = query.filter(ApiCase.last_success == 0)
    elif run_status == "not_run":
        query = query.filter(ApiCase.last_success.is_(None))
    status_code = _int_or_none(data.get("status_code"))
    if status_code is not None:
        query = query.filter(ApiCase.last_status == status_code)
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
    _ensure_api_runtime_columns()
    data = request.get_json(silent=True) or {}
    data = dict(data)
    run_id = _api_run_id_from(data)
    data["_api_run_id"] = run_id
    case = ApiCase.query.filter_by(id=data.get("id"), is_delete=0).first() if data.get("id") else None
    source = _case_source_from_request(case, data)
    project_id = _int_or_none(source.get("project_id"))
    permission_error = _check_project(project_id, "run")
    if permission_error:
        return permission_error
    if data.get("async"):
        result = ApiRunResult(
            run_id=run_id,
            case_id=case.id if case else None,
            environment_id=_int_or_none(data.get("environment_id") or source.get("environment_id")),
            project_id=project_id,
            method=(source.get("method") or "GET").upper(),
            url=source.get("url") or "",
            request_headers=_json_text(source.get("headers") or {}),
            request_params=_json_text(source.get("params") or {}),
            request_body=source.get("body") or "",
            run_status="queued",
            status_text="排队中",
            success=0,
        )
        apply_run_user(result)
        db.session.add(result)
        db.session.commit()
        app = current_app._get_current_object()
        account = current_account()
        account_info = {"id": account.id, "name": account.username} if account else None
        thread = threading.Thread(target=_run_case_background, args=(app, result.id, data, account_info), daemon=True)
        thread.start()
        return jsonify({"code": 200, "msg": "已开始异步执行", "data": _result_payload(result)})
    try:
        payload = _run_case_payload(data)
    except ValueError as exc:
        return jsonify({"code": 404, "msg": str(exc), "data": None})
    return jsonify({"code": 200, "msg": "执行完成", "data": payload})


@api_test.route('/get_run_history', methods=["POST"])
def get_run_history():
    _ensure_api_case_columns()
    _ensure_api_runtime_columns()
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


@api_test.route('/get_run_result', methods=["POST"])
def get_run_result():
    _ensure_api_runtime_columns()
    data = request.get_json(silent=True) or {}
    result = ApiRunResult.query.filter_by(id=data.get("id")).first()
    if not result:
        return jsonify({"code": 404, "msg": "执行结果不存在", "data": None})
    if result.project_id:
        permission_error = _check_project(result.project_id, "view")
        if permission_error:
            return permission_error
    return jsonify({"code": 200, "msg": "请求成功", "data": _result_payload(result)})


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
    run_status = data.get("run_status")
    if run_status == "passed":
        query = query.filter(ApiSuite.last_success == 1)
    elif run_status == "failed":
        query = query.filter(ApiSuite.last_success == 0)
    elif run_status == "not_run":
        query = query.filter(ApiSuite.last_success.is_(None))
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
    suite.dependency_strategy = _normalize_dependency_strategy(data.get("dependency_strategy"))
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
    _ensure_api_runtime_columns()
    data = request.get_json(silent=True) or {}
    data = dict(data)
    run_id = _api_run_id_from(data)
    data["_api_run_id"] = run_id
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
    if data.get("async"):
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
            context=_json_text({}),
            step_results=_json_text(_suite_pending_steps(cases)),
        )
        apply_run_user(suite_result)
        db.session.add(suite_result)
        db.session.commit()
        app = current_app._get_current_object()
        account = current_account()
        account_info = {"id": account.id, "name": account.username} if account else None
        thread = threading.Thread(
            target=_run_suite_background,
            args=(app, suite_result.id, suite.id, environment_id, timeout, account_info, run_id),
            daemon=True,
        )
        thread.start()
        return jsonify({"code": 200, "msg": "已开始异步执行", "data": _suite_result_payload(suite_result)})
    started = time.time()
    context = {}
    step_results = []
    pass_count = 0
    fail_count = 0
    executed_success_case_ids = set()
    dependency_strategy = _normalize_dependency_strategy(suite.dependency_strategy)
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
            is_suite_item = chain_case.id == case.id
            if dependency_strategy != "always" and not is_suite_item and chain_case.id in executed_success_case_ids:
                continue
            source = _case_payload(chain_case)
            result, extracted = _execute_case_source(source, case=chain_case, environment_id=environment_id, context=context, timeout=timeout, run_id=run_id)
            if is_suite_item and dependency_strategy == "retry_on_auth_fail" and _is_auth_failure(result):
                db.session.expunge(result)
                for refresh_case in chain[:-1]:
                    refresh_source = _case_payload(refresh_case)
                    refresh_result, refresh_extracted = _execute_case_source(
                        refresh_source,
                        case=refresh_case,
                        environment_id=environment_id,
                        context=context,
                        timeout=timeout,
                        run_id=run_id,
                    )
                    db.session.flush()
                    _create_api_case_execution_result(refresh_result)
                    context.update(refresh_extracted)
                    refresh_payload = _result_payload(refresh_result)
                    refresh_payload["case_name"] = refresh_case.name
                    refresh_payload["case_id"] = refresh_case.id
                    refresh_payload["suite_index"] = index + 1
                    refresh_payload["is_suite_item"] = False
                    refresh_payload["step_type"] = "dependency"
                    refresh_payload["step_type_name"] = "刷新依赖"
                    refresh_payload["extracted_variables"] = refresh_extracted
                    step_results.append(refresh_payload)
                    if refresh_result.success:
                        pass_count += 1
                        executed_success_case_ids.add(refresh_case.id)
                    else:
                        fail_count += 1
                        db.session.commit()
                        if suite.stop_on_fail:
                            break
                if not suite.stop_on_fail or not step_results or step_results[-1].get("success"):
                    result, extracted = _execute_case_source(source, case=chain_case, environment_id=environment_id, context=context, timeout=timeout, run_id=run_id)
                else:
                    break
            db.session.flush()
            _create_api_case_execution_result(result)
            context.update(extracted)
            payload = _result_payload(result)
            payload["case_name"] = chain_case.name
            payload["case_id"] = chain_case.id
            payload["suite_index"] = index + 1
            payload["is_suite_item"] = is_suite_item
            payload["step_type"] = "case" if is_suite_item else "dependency"
            payload["step_type_name"] = "集合接口" if is_suite_item else "前置依赖"
            payload["extracted_variables"] = extracted
            step_results.append(payload)
            if result.success:
                pass_count += 1
                executed_success_case_ids.add(chain_case.id)
            else:
                fail_count += 1
                db.session.commit()
                if suite.stop_on_fail:
                    break
            db.session.commit()
        if suite.stop_on_fail and step_results and not step_results[-1].get("success"):
            break
    elapsed_ms = int((time.time() - started) * 1000)
    suite_result = ApiSuiteRunResult(
        run_id=run_id,
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
    db.session.flush()
    CaseResult.query.filter(
        CaseResult.source_type == "api",
        CaseResult.run_id == run_id,
        CaseResult.api_suite_result_id.is_(None),
    ).update({"api_suite_result_id": suite_result.id}, synchronize_session=False)
    _create_api_suite_report(suite_result, suite)
    db.session.commit()
    return jsonify({"code": 200, "msg": "执行完成", "data": _suite_result_payload(suite_result)})


@api_test.route('/get_suite_history', methods=["POST"])
def get_suite_history():
    _ensure_api_runtime_columns()
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


@api_test.route('/get_suite_result', methods=["POST"])
def get_suite_result():
    _ensure_api_runtime_columns()
    data = request.get_json(silent=True) or {}
    result = ApiSuiteRunResult.query.filter_by(id=data.get("id")).first()
    if not result:
        return jsonify({"code": 404, "msg": "集合执行结果不存在", "data": None})
    if result.project_id:
        permission_error = _check_project(result.project_id, "view")
        if permission_error:
            return permission_error
    return jsonify({"code": 200, "msg": "请求成功", "data": _suite_result_payload(result)})


@api_test.route('/get_api_report_info', methods=["POST"])
def get_api_report_info():
    data = request.get_json(silent=True) or {}
    page_no = int(data.get("page_no", 0) or 0)
    page_size = int(data.get("page_size", 20) or 20)
    project_id = _int_or_none(data.get("project_id"))
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
    return jsonify({"code": 200, "msg": "请求成功", "data": [_api_report_payload(item) for item in rows], "total": total})


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
    return jsonify({"code": 200, "msg": "请求成功", "data": _api_report_payload(report)})
