# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
import json
import re
import hashlib
from html import escape

from flask import jsonify, request
from app.web_api import caseresult
from app.models.test_api_models import *
from flasgger import swag_from
import os
from app.lib import image
import traceback
from config import logs
from flask import render_template_string
from sqlalchemy import inspect, text
from app.tools import cache_operatios
from app.tools.auth_permissions import allowed_project_ids, project_id_from_testset, require_project_permission


def _cache_scope(allowed_ids):
    if allowed_ids is None:
        return "admin"
    if not allowed_ids:
        return "projects:none"
    return "projects:" + ",".join([str(item) for item in sorted(allowed_ids)])


def _caseresult_cache_key(allowed_ids, kind, payload):
    raw_key = json.dumps({
        "scope": _cache_scope(allowed_ids),
        "kind": kind,
        "payload": payload,
    }, sort_keys=True, default=str)
    return "caseresult:" + hashlib.md5(raw_key.encode("utf-8")).hexdigest()


def _empty_caseresult_response():
    return {
        'code': 200,
        'msg': '请求成功',
        'data': [],
        'count': {'pass_count': 0, 'fail_count': 0, 'error_count': 0, 'all_count': 0, 'pass_rate': 0},
    }


def _ensure_caseresult_source_columns():
    columns = {column["name"] for column in inspect(db.engine).get_columns("caseresult")}
    changed = False
    ddl_map = {
        "source_type": "ALTER TABLE caseresult ADD COLUMN source_type VARCHAR(40) DEFAULT 'pytest'",
        "api_result_id": "ALTER TABLE caseresult ADD COLUMN api_result_id INTEGER",
        "api_suite_result_id": "ALTER TABLE caseresult ADD COLUMN api_suite_result_id INTEGER",
    }
    for column_name, ddl in ddl_map.items():
        if column_name not in columns:
            db.session.execute(text(ddl))
            changed = True
    if "source_type" in columns or changed:
        empty_count = db.session.execute(
            text("SELECT COUNT(1) FROM caseresult WHERE source_type IS NULL OR source_type = ''")
        ).scalar() or 0
        if empty_count:
            db.session.execute(text("UPDATE caseresult SET source_type = 'pytest' WHERE source_type IS NULL OR source_type = ''"))
            changed = True
    if changed:
        db.session.commit()


def _normalize_source_type(value):
    value = str(value or "").strip()
    lower_value = value.lower()
    if lower_value in ("api", "interface") or value in ("接口测试", "接口"):
        return "api"
    if lower_value in ("pytest", "py") or value in ("pytest测试",):
        return "pytest"
    return lower_value


def _normalize_run_id_filter(value):
    if value in (None, ""):
        return None
    text_value = str(value).strip()
    if not text_value:
        return None
    digit_match = re.search(r"\d{8,}", text_value)
    if digit_match:
        return int(digit_match.group(0))
    try:
        return int(text_value)
    except Exception:
        return None


def _run_id_text(value):
    return str(value) if value not in (None, "") else ""


def _safe_log_file_path(file_name):
    if not file_name:
        return None
    log_root = os.path.realpath(logs)
    log_path = os.path.realpath(os.path.join(log_root, file_name))
    try:
        if os.path.commonpath([log_root, log_path]) != log_root:
            return None
    except ValueError:
        return None
    return log_path


def _highlight_log_text(log_text):
    highlighted_lines = []
    for line_number, line in enumerate(log_text.splitlines() or ["无日志！"], start=1):
        level_class = ""
        if re.search(r'\b(error|failed|fail|exception|assertionerror|traceback|critical)\b', line, re.IGNORECASE):
            level_class = " is-error"
        elif re.search(r'\b(warning|warn)\b', line, re.IGNORECASE):
            level_class = " is-warning"
        elif re.search(r'\bdebug\b', line, re.IGNORECASE):
            level_class = " is-debug"
        escaped_line = escape(line)
        escaped_line = re.sub(
            r'(\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)',
            r'<span class="log-time">\1</span>',
            escaped_line
        )
        escaped_line = re.sub(
            r'(File &quot;.*?&quot;, line \d+)',
            r'<span class="log-file">\1</span>',
            escaped_line
        )
        escaped_line = re.sub(
            r'\b(INFO|Info|info|PASSED|Passed|passed)\b',
            r'<span class="log-info">\1</span>',
            escaped_line
        )
        escaped_line = re.sub(
            r'\b(DEBUG|Debug|debug)\b',
            r'<span class="log-debug">\1</span>',
            escaped_line
        )
        escaped_line = re.sub(
            r'\b(WARNING|Warning|warning|WARN|Warn|warn)\b',
            r'<span class="log-warning">\1</span>',
            escaped_line
        )
        escaped_line = re.sub(
            r'\b(ERROR|Error|error|FAILED|Failed|failed|FAIL|Fail|fail|Exception|exception|AssertionError|Traceback|traceback|CRITICAL|Critical|critical)\b',
            r'<span class="log-error">\1</span>',
            escaped_line
        )
        escaped_line = re.sub(
            r'(&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;|setup&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;|call&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;|teardown&gt;&gt;&gt;&gt;&gt;&gt;)',
            r'<span class="log-stage">\1</span>',
            escaped_line
        )
        highlighted_lines.append(
            f'<div class="log-line{level_class}"><span class="line-no">{line_number}</span>'
            f'<span class="line-text">{escaped_line or " "}</span></div>'
        )
    return "\n".join(highlighted_lines)


def _loads_json(value, default=None):
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


def _pretty_json(value):
    if value in (None, ""):
        return ""
    if isinstance(value, str):
        parsed = _loads_json(value, None)
        if parsed is not None:
            return json.dumps(parsed, ensure_ascii=False, indent=2, default=str)
        return value
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _api_detail_from_result(result):
    detail = _loads_json(result.longrepr, {})
    api_run = ApiRunResult.query.filter_by(id=result.api_result_id).first() if result.api_result_id else None
    if api_run:
        assertion_detail = _loads_json(api_run.assertion_result, {})
        context_variables = assertion_detail.get("context_variables") or assertion_detail.get("context") or {} if isinstance(assertion_detail, dict) else {}
        detail.update({
            "error_message": api_run.error_message,
            "assertion_result": assertion_detail.get("assertions") if isinstance(assertion_detail, dict) else assertion_detail,
            "extractor_result": assertion_detail.get("extractors", []) if isinstance(assertion_detail, dict) else [],
            "context_variables": context_variables,
            "request_method": api_run.method,
            "request_url": api_run.url,
            "request_headers": _loads_json(api_run.request_headers, {}),
            "request_params": _loads_json(api_run.request_params, {}),
            "request_body": api_run.request_body or "",
            "response_status": api_run.response_status,
            "response_headers": _loads_json(api_run.response_headers, {}),
            "response_body": api_run.response_body or "",
            "elapsed_ms": api_run.elapsed_ms,
        })
    if not detail.get("context_variables") and result.run_id:
        chain_variables = {}
        query = ApiRunResult.query.filter_by(run_id=result.run_id)
        if result.api_result_id:
            query = query.filter(ApiRunResult.id <= result.api_result_id)
        for item in query.order_by(ApiRunResult.id).all():
            assertion_detail = _loads_json(item.assertion_result, {})
            if not isinstance(assertion_detail, dict):
                continue
            for extractor in assertion_detail.get("extractors") or []:
                if isinstance(extractor, dict) and extractor.get("success") and extractor.get("name"):
                    chain_variables[extractor.get("name")] = extractor.get("value")
        detail["context_variables"] = chain_variables
    return detail


def _api_log_text(result):
    detail = _api_detail_from_result(result)
    assertions = detail.get("assertion_result") or []
    extractors = detail.get("extractor_result") or []
    lines = [
        "接口用例执行日志",
        "=" * 80,
        "结果ID: {}".format(result.id),
        "run_id: {}".format(result.run_id or ""),
        "用例名称: {}".format(result.case_title or result.case_name or ""),
        "执行结果: {}".format(result.run_case_result or ""),
        "耗时/s: {}".format(result.duration or 0),
        "",
        "[请求信息]",
        "方法: {}".format(detail.get("request_method") or ""),
        "URL: {}".format(detail.get("request_url") or result.file_path_name or result.case_name or ""),
        "Headers:",
        _pretty_json(detail.get("request_headers") or {}),
        "Params:",
        _pretty_json(detail.get("request_params") or {}),
        "Body:",
        _pretty_json(detail.get("request_body") or ""),
        "",
        "[响应信息]",
        "Status: {}".format(detail.get("response_status") if detail.get("response_status") is not None else ""),
        "Headers:",
        _pretty_json(detail.get("response_headers") or {}),
        "Body:",
        _pretty_json(detail.get("response_body") or result.run_info or ""),
        "",
        "[断言结果]",
    ]
    if assertions:
        for index, item in enumerate(assertions, start=1):
            if isinstance(item, dict):
                status = "PASSED" if item.get("success") else "FAILED"
                lines.append("{}. [{}] {} type={} expected={} actual={} error={}".format(
                    index,
                    status,
                    item.get("name") or "assertion",
                    item.get("type") or "",
                    item.get("expected"),
                    item.get("actual"),
                    item.get("error") or "",
                ))
            else:
                lines.append("{}. {}".format(index, item))
    else:
        lines.append("无断言结果")
    lines.extend(["", "[变量提取结果]"])
    if extractors:
        lines.append(_pretty_json(extractors))
    else:
        lines.append("当前接口无变量提取结果")
    context_variables = detail.get("context_variables") or {}
    lines.extend(["", "[依赖链/上下文变量]"])
    if context_variables:
        lines.append(_pretty_json(context_variables))
    else:
        lines.append("无依赖链变量")
    if detail.get("error_message"):
        lines.extend(["", "[错误信息]", str(detail.get("error_message"))])
    return "\n".join(lines)


def _render_log_preview(log_text, file_name):
    highlighted_code = _highlight_log_text(log_text or "无日志！")
    return render_template_string("""
                <html>
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <title>日志预览</title>
                        <style>
                            body {
                                margin: 0;
                                padding: 24px;
                                background: #0f172a;
                                color: #d1d5db;
                                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
                            }
                            .log-shell {
                                max-width: 1440px;
                                margin: 0 auto;
                                border: 1px solid #263244;
                                border-radius: 10px;
                                overflow: hidden;
                                background: #111827;
                                box-shadow: 0 18px 45px rgba(0, 0, 0, 0.35);
                            }
                            .log-header {
                                display: flex;
                                justify-content: space-between;
                                gap: 16px;
                                padding: 14px 18px;
                                background: #1f2937;
                                border-bottom: 1px solid #334155;
                            }
                            .log-title {
                                color: #f8fafc;
                                font-size: 16px;
                                font-weight: 800;
                            }
                            .log-file-name {
                                color: #94a3b8;
                                font-size: 13px;
                                word-break: break-all;
                            }
                            .log-content {
                                min-height: 640px;
                                max-height: calc(100vh - 120px);
                                overflow: auto;
                                padding: 14px 0;
                                font-family: Consolas, "Courier New", monospace;
                                font-size: 15px;
                                line-height: 1.75;
                                white-space: pre;
                            }
                            .log-line {
                                display: flex;
                                min-width: max-content;
                                padding: 0 18px;
                            }
                            .log-line:hover {
                                background: rgba(148, 163, 184, 0.12);
                            }
                            .log-line.is-debug {
                                background: rgba(167, 139, 250, 0.08);
                            }
                            .log-line.is-warning {
                                background: rgba(245, 158, 11, 0.10);
                            }
                            .log-line.is-error {
                                background: rgba(251, 113, 133, 0.14);
                            }
                            .line-no {
                                width: 58px;
                                flex: 0 0 58px;
                                padding-right: 16px;
                                color: #64748b;
                                text-align: right;
                                user-select: none;
                            }
                            .line-text {
                                min-width: 0;
                            }
                            .log-time {
                                color: #38bdf8;
                                font-weight: 700;
                            }
                            .log-file {
                                color: #c084fc;
                                font-weight: 700;
                            }
                            .log-info {
                                color: #22c55e;
                                font-weight: 800;
                            }
                            .log-debug {
                                color: #a78bfa;
                                font-weight: 800;
                            }
                            .log-warning {
                                color: #f59e0b;
                                font-weight: 800;
                            }
                            .log-error {
                                color: #fb7185;
                                font-weight: 900;
                            }
                            .log-stage {
                                color: #facc15;
                                font-weight: 900;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="log-shell">
                            <div class="log-header">
                                <div class="log-title">日志预览</div>
                                <div class="log-file-name">{{ file_name }}</div>
                            </div>
                            <div class="log-content">{{ highlighted_code|safe }}</div>
                        </div>
                    </body>
                </html>
                """, highlighted_code=highlighted_code, file_name=file_name)


def _render_api_case_preview(result):
    detail = _api_detail_from_result(result)
    api_run = ApiRunResult.query.filter_by(id=result.api_result_id).first() if result.api_result_id else None
    api_case = ApiCase.query.filter_by(id=result.case_id, is_delete=0).first() if result.case_id else None
    title = (api_case.name if api_case else result.case_title) or "接口用例详情"
    method = (api_case.method if api_case else None) or detail.get("request_method") or ""
    url = (api_case.url if api_case else None) or detail.get("request_url") or result.file_path_name or ""
    headers = _loads_json(api_case.headers, {}) if api_case else detail.get("request_headers") or {}
    params = _loads_json(api_case.params, {}) if api_case else detail.get("request_params") or {}
    body_type = (api_case.body_type if api_case else "") or ""
    body = (api_case.body if api_case else None) or detail.get("request_body") or ""
    assertions = _loads_json(api_case.assertions, []) if api_case else detail.get("assertion_result") or []
    pre_case_ids = _loads_json(api_case.pre_case_ids, []) if api_case else []
    extractors = _loads_json(api_case.extractors, []) if api_case else detail.get("extractor_result") or []
    runtime = {
        "result_id": result.id,
        "api_result_id": result.api_result_id,
        "run_id": result.run_id,
        "response_status": detail.get("response_status"),
        "elapsed_ms": detail.get("elapsed_ms") if detail.get("elapsed_ms") is not None else (api_run.elapsed_ms if api_run else ""),
        "result": result.run_case_result,
        "error_message": detail.get("error_message") or "",
    }
    sections = [
        ("Headers", _pretty_json(headers)),
        ("Params", _pretty_json(params)),
        ("Body ({})".format(body_type or "raw"), _pretty_json(body)),
        ("断言", _pretty_json(assertions)),
        ("依赖接口ID", _pretty_json(pre_case_ids)),
        ("变量提取", _pretty_json(extractors)),
        ("最近执行", _pretty_json(runtime)),
    ]
    return render_template_string("""
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>接口用例详情</title>
            <style>
                body {
                    margin: 0;
                    padding: 24px;
                    background: #f4f7fb;
                    color: #1f2d3d;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
                }
                .shell {
                    max-width: 1280px;
                    margin: 0 auto;
                    background: #fff;
                    border: 1px solid #dfe7f1;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 16px 40px rgba(31, 45, 61, 0.10);
                }
                .head {
                    padding: 18px 22px;
                    background: #172033;
                    color: #fff;
                }
                .method {
                    display: inline-block;
                    min-width: 56px;
                    margin-right: 10px;
                    padding: 4px 10px;
                    border-radius: 4px;
                    background: #2f80ed;
                    text-align: center;
                    font-weight: 800;
                }
                h1 {
                    margin: 10px 0 8px;
                    font-size: 22px;
                    line-height: 1.35;
                }
                .url {
                    color: #cbd5e1;
                    word-break: break-all;
                    font-family: Consolas, "Courier New", monospace;
                }
                .content {
                    padding: 18px 22px 24px;
                }
                .section {
                    margin-top: 14px;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    overflow: hidden;
                }
                .section-title {
                    padding: 10px 14px;
                    background: #f8fafc;
                    border-bottom: 1px solid #e2e8f0;
                    font-weight: 800;
                }
                pre {
                    min-height: 40px;
                    margin: 0;
                    padding: 14px;
                    overflow: auto;
                    color: #203247;
                    background: #fbfdff;
                    font-size: 14px;
                    line-height: 1.6;
                    font-family: Consolas, "Courier New", monospace;
                    white-space: pre-wrap;
                    word-break: break-word;
                }
            </style>
        </head>
        <body>
            <div class="shell">
                <div class="head">
                    <div><span class="method">{{ method }}</span>接口测试用例</div>
                    <h1>{{ title }}</h1>
                    <div class="url">{{ url }}</div>
                </div>
                <div class="content">
                    {% for name, value in sections %}
                    <div class="section">
                        <div class="section-title">{{ name }}</div>
                        <pre>{{ value }}</pre>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </body>
        </html>
    """, title=title, method=method, url=url, sections=sections)


@caseresult.route('/get_caseresult_info', methods=["POST"])
@swag_from('../apidocs/get_caseresult_info.yml')
def get_caseresult_info():
    """获取测试集合最新执行结果"""
    set_id = request.json.get("set_id")
    case_name = request.json.get("case_name", "")
    case_name = case_name.strip()
    run_id = request.json.get("run_id")
    run_id_value = _normalize_run_id_filter(run_id)
    run_case_result = request.json.get("run_case_result")
    source_type = _normalize_source_type(request.json.get("source_type", ""))
    page_no = request.json.get("page", 0)
    page_size = request.json.get("page_size", 10)
    # start_date = request.json.get("start_date", None)
    # end_date = request.json.get("end_date", None)
    time_value = request.json.get("time_value", None)
    case_id = request.json.get("case_id", None)
    allowed_ids = allowed_project_ids()
    if set_id:
        permission_error = require_project_permission(project_id_from_testset(set_id), "view")
        if permission_error:
            return permission_error
    if allowed_ids is not None and not allowed_ids:
        return jsonify(_empty_caseresult_response())
    _ensure_caseresult_source_columns()
    all_data = _caseresult_cache_key(allowed_ids, "all_data", {
        "page": page_no,
        "page_size": page_size,
    })
    run_cache_key = _caseresult_cache_key(allowed_ids, "run_id", {
        "run_id": run_id_value,
        "page": page_no,
        "page_size": page_size,
    }) if run_id_value else None
    case_cache_key = _caseresult_cache_key(allowed_ids, "case_id", {
        "case_id": case_id,
        "page": page_no,
        "page_size": page_size,
    }) if case_id else None
    # cache_status = page_size = request.json.get("cache_status", 1)
    try:
        # if set_id:
        #     if run_id:
        #         query = CaseResult.query.filter_by(set_id=set_id).filter_by(run_id=int(run_id)).order_by(
        #             db.desc(CaseResult.run_id)).order_by(db.desc(CaseResult.updated_time)).limit(page_size).offset(
        #             page_no).all()
        #         if run_case_result:
        #             query = CaseResult.query.filter_by(set_id=set_id).filter_by(
        #                 run_case_result=run_case_result).filter_by(run_id=int(run_id)).order_by(
        #                 db.desc(CaseResult.run_id)).order_by(db.desc(CaseResult.updated_time)).limit(page_size).offset(
        #                 page_no).all()
        #     elif run_case_result:
        #         query = CaseResult.query.filter_by(set_id=set_id).filter_by(run_case_result=run_case_result).order_by(
        #             db.desc(CaseResult.run_id)).order_by(db.desc(CaseResult.updated_time)).limit(page_size).offset(
        #             page_no).all()
        #     else:
        #         query = CaseResult.query.filter_by(set_id=set_id).order_by(
        #             db.desc(CaseResult.run_id)).order_by(db.desc(CaseResult.updated_time)).limit(page_size).offset(
        #             page_no).all()
        # elif case_name:
        #     query = CaseResult.query.filter(CaseResult.case_name.like(f"%{case_name}%")).order_by(
        #         db.desc(CaseResult.updated_time)).limit(
        #         page_size).offset(page_no).all()
        #     if not query:
        #         query = CaseResult.query.filter(CaseResult.case_title.like(f"%{case_name}%")).order_by(
        #             db.desc(CaseResult.updated_time)).limit(
        #             page_size).offset(page_no).all()
        # elif run_id:
        #     query = CaseResult.query.filter_by(run_id=int(run_id)).order_by(
        #         db.desc(CaseResult.run_id)).order_by(db.desc(CaseResult.updated_time)).limit(page_size).offset(
        #         page_no).all()
        #     if run_case_result:
        #         query = CaseResult.query.filter_by(
        #             run_case_result=run_case_result).filter_by(run_id=int(run_id)).order_by(
        #             db.desc(CaseResult.run_id)).order_by(db.desc(CaseResult.updated_time)).limit(page_size).offset(
        #             page_no).all()
        # else:
        #     query = CaseResult.query.order_by(db.desc(CaseResult.updated_time)).limit(page_size).offset(page_no).all()
        if page_size and not case_name and not set_id and not time_value and not run_case_result and not run_id_value and not case_id and not source_type:
            return_dict = cache_operatios.new_conn.get(all_data)
            if return_dict:
                print("获取缓存数据2")
                return_dict = json.loads(return_dict)
                return_dict.update({"cache_msg": "这是直接从redis缓存中获取的数据"})
                return return_dict
        if run_id_value and not case_name and not set_id and not time_value and not run_case_result and not source_type:
            return_dict = cache_operatios.new_conn.get(run_cache_key)
            if return_dict:
                print("获取缓存数据1")
                return_dict = json.loads(return_dict)
                return_dict.update({"cache_msg": "这是直接从redis缓存中获取的数据"})
                return return_dict
        if case_id and not case_name and not set_id and not time_value and not run_case_result and not run_id_value and not source_type:
            return_dict = cache_operatios.new_conn.get(case_cache_key)
            if return_dict:
                print("获取缓存数据3>>>>case_id")
                return_dict = json.loads(return_dict)
                return_dict.update({"cache_msg": "这是直接从redis缓存中获取的数据"})
                return return_dict
        query = CaseResult.query
        if allowed_ids is not None:
            query = query.filter(CaseResult.project_id.in_(allowed_ids))
        if source_type == "api":
            query = query.filter(CaseResult.source_type == "api")
        elif source_type == "pytest":
            query = query.filter((CaseResult.source_type == "pytest") | (CaseResult.source_type.is_(None)))

        if set_id:
            query = query.filter_by(set_id=set_id)
            # if run_id_value:
            #     query = query.filter_by(run_id=run_id_value)
            # if run_case_result:
            #     query = query.filter_by(run_case_result=run_case_result)
        if run_case_result:
            query = query.filter_by(run_case_result=run_case_result)
        if time_value and len(time_value) > 1:
            query = query.filter(CaseResult.created_time.between(time_value[0], time_value[1]))
        if case_name:
            query = query.filter(
                CaseResult.case_name.like(f"%{case_name}%") | CaseResult.case_title.like(f"%{case_name}%")
            )
        if run_id_value:
            query = query.filter_by(run_id=run_id_value)
        if case_id is not None:
            query = query.filter_by(case_id=int(case_id))
            # if run_case_result:
            #     query = query.filter_by(run_case_result=run_case_result)

        query = query.order_by(
            db.desc(CaseResult.run_id), db.desc(CaseResult.updated_time)
        ).limit(page_size).offset(page_no).all()

        query = [i.to_dict() for i in query]
        set_ids = image.get_values_by_key(query, "set_id", values=[])
        config_ids = image.get_values_by_key(query, "config_id", values=[])
        version_ids = image.get_values_by_key(query, "version_id", values=[])
        # print(type(config_ids))
        if isinstance(config_ids, str):
            config_ids = [config_ids]
        if isinstance(set_ids, int):
            set_ids = [set_ids]
        if isinstance(config_ids, int):
            config_ids = [config_ids]
        if isinstance(version_ids, int):
            version_ids = [version_ids]
        set_id_list = config_id_list = version_id_list = None
        if set_ids:
            set_id_list = TestSet.query.filter(TestSet.id.in_(set_ids)).all()
        ex_ids = list()
        # print(config_ids)
        if config_ids:
            for i in config_ids:
                if isinstance(i, str):
                    i = eval(i)
                    if isinstance(i, list):
                        ex_ids.extend(i)
                    if isinstance(i, int):
                        ex_ids.append(i)
            config_id_list = Cfgs.query.filter(Cfgs.id.in_(ex_ids)).all()
        if version_ids:
            version_id_list = Version.query.filter(Version.id.in_(version_ids)).all()
        if set_id_list:
            set_id_list = [i.to_dict() for i in set_id_list]
            for i in range(len(query)):
                for j in set_id_list:
                    if query[i].get("set_id") == j.get("id"):
                        query[i].update({"set_title": j.get("title")})
        if config_id_list:
            config_id_list = [i.to_dict() for i in config_id_list]
            for i in range(len(query)):
                check_ids = eval(query[i].get("config_id"))
                if isinstance(check_ids, int):
                    check_ids = [check_ids]
                names = list()
                for j in config_id_list:
                    if j.get("id") in check_ids:
                        names.append(j.get("cfg_name"))
                query[i].update({"cfg_name": names})
        if version_id_list:
            version_id_list = [i.to_dict() for i in version_id_list]
            for i in range(len(query)):
                for j in version_id_list:
                    if query[i].get("version_id") == j.get("id"):
                        query[i].update({"version": j.get("version")})
        for i in query:
            i["source_type"] = i.get("source_type") or "pytest"
            i["run_id"] = _run_id_text(i.get("run_id"))
            i["source_type_name"] = "接口测试" if i.get("source_type") == "api" else "pytest"
            if i.get("updated_time"):
                i.update({"updated_time": i.get("updated_time").strftime("%Y-%m-%d %H:%M:%S")})
        pass_count = fail_count = error_count = 0
        try:
            for each in query:
                if each["run_case_result"] == "passed":
                    pass_count += 1
                if each["run_case_result"] == "failed":
                    fail_count += 1
                if each["run_case_result"] == "error":
                    error_count += 1
        except:
            pass
        # print(pass_count, len(query), query)
        if not len(query):
            pass_rate = 0
        else:
            pass_rate = round(pass_count / len(query) * 100, 2)
        return_dict = {'code': 200, 'msg': '请求成功', 'data': query,
                       'count': {'pass_count': pass_count, 'fail_count': fail_count, 'error_count': error_count,
                                 'all_count': len(query), 'pass_rate': pass_rate}}
        if run_id_value and not case_name and not set_id and not time_value and not run_case_result and not source_type:
            cache_dict = json.dumps(return_dict, cls=cache_operatios.DecimalEncoder)
            cache_operatios.new_conn.set(run_cache_key, cache_dict, ex=60 * 1)
            print("存储缓存数据1")
        if page_size and not case_name and not set_id and not time_value and not run_case_result and not run_id_value and not case_id and not source_type:
            cache_dict = json.dumps(return_dict, cls=cache_operatios.DecimalEncoder)
            cache_operatios.new_conn.set(all_data, cache_dict, ex=60 * 1)
            print("存储缓存数据2")
        if case_id and not case_name and not set_id and not time_value and not run_case_result and not run_id_value and not source_type:
            cache_dict = json.dumps(return_dict, cls=cache_operatios.DecimalEncoder)
            cache_operatios.new_conn.set(case_cache_key, cache_dict, ex=60 * 1)
            print("存储缓存数据3>>>>case_id")
        return jsonify(return_dict)
    except Exception as e:
        traceback.print_exc()
        return_dict = {'code': 404, 'msg': f'内部错误:{str(e)}', 'data': None, 'count': None}
        return jsonify(return_dict)


@caseresult.route('/get_api_log_info', methods=["POST"])
def get_api_log_info():
    result_id = request.json.get("id") or request.json.get("result_id")
    if not result_id:
        return jsonify({"code": 404, "msg": "结果ID不能为空！", "data": None})
    result = CaseResult.query.filter_by(id=result_id).first()
    if not result:
        return jsonify({"code": 404, "msg": "日志关联的用例结果不存在！", "data": None})
    if result.project_id:
        permission_error = require_project_permission(result.project_id, "view")
        if permission_error:
            return permission_error
    if _normalize_source_type(result.source_type or "pytest") != "api":
        return jsonify({"code": 404, "msg": "不是接口测试结果！", "data": None})
    return _render_log_preview(_api_log_text(result), "api_result_{}_run_{}".format(result.id, result.run_id or ""))


@caseresult.route('/get_api_case_source_info', methods=["POST"])
def get_api_case_source_info():
    result_id = request.json.get("id") or request.json.get("result_id")
    if not result_id:
        return jsonify({"code": 404, "msg": "结果ID不能为空！", "data": None})
    result = CaseResult.query.filter_by(id=result_id).first()
    if not result:
        return jsonify({"code": 404, "msg": "接口测试结果不存在！", "data": None})
    if result.project_id:
        permission_error = require_project_permission(result.project_id, "view")
        if permission_error:
            return permission_error
    if _normalize_source_type(result.source_type or "pytest") != "api":
        return jsonify({"code": 404, "msg": "不是接口测试结果！", "data": None})
    return _render_api_case_preview(result)


@caseresult.route('/get_log_info', methods=["POST"])
@swag_from('../apidocs/get_log_info.yml')
def get_log_info():
    """日志文件查看"""
    file_name = request.json.get("file_name")
    if not file_name:
        return jsonify({"code": 404, "msg": "日志文件不能为空！", "data": None})
    result = CaseResult.query.filter_by(file_name=file_name).order_by(db.desc(CaseResult.updated_time)).first()
    if not result:
        return jsonify({"code": 404, "msg": "日志关联的用例结果不存在！", "data": None})
    permission_error = require_project_permission(result.project_id, "view")
    if permission_error:
        return permission_error
    log_path = _safe_log_file_path(file_name)
    if not log_path:
        return jsonify({"code": 404, "msg": "日志文件路径不合法！", "data": None})
    if not os.path.exists(log_path):
        return jsonify({"code": 404, "msg": "日志文件不存在！", "data": None})
    try:
        with open(log_path, "r", encoding="utf8") as f:
            code = f.read()
    except UnicodeDecodeError:
        with open(log_path, "r", encoding="gbk", errors="replace") as f:
            code = f.read()
    if not code.strip():
        code = "无日志！"
    highlighted_code = _highlight_log_text(code)
    return render_template_string("""
                <html>
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <title>日志预览</title>
                        <style>
                            body {
                                margin: 0;
                                padding: 24px;
                                background: #0f172a;
                                color: #d1d5db;
                                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
                            }
                            .log-shell {
                                max-width: 1440px;
                                margin: 0 auto;
                                border: 1px solid #263244;
                                border-radius: 10px;
                                overflow: hidden;
                                background: #111827;
                                box-shadow: 0 18px 45px rgba(0, 0, 0, 0.35);
                            }
                            .log-header {
                                display: flex;
                                justify-content: space-between;
                                gap: 16px;
                                padding: 14px 18px;
                                background: #1f2937;
                                border-bottom: 1px solid #334155;
                            }
                            .log-title {
                                color: #f8fafc;
                                font-size: 16px;
                                font-weight: 800;
                            }
                            .log-file-name {
                                color: #94a3b8;
                                font-size: 13px;
                                word-break: break-all;
                            }
                            .log-content {
                                min-height: 640px;
                                max-height: calc(100vh - 120px);
                                overflow: auto;
                                padding: 14px 0;
                                font-family: Consolas, "Courier New", monospace;
                                font-size: 15px;
                                line-height: 1.75;
                                white-space: pre;
                            }
                            .log-line {
                                display: flex;
                                min-width: max-content;
                                padding: 0 18px;
                            }
                            .log-line:hover {
                                background: rgba(148, 163, 184, 0.12);
                            }
                            .log-line.is-debug {
                                background: rgba(167, 139, 250, 0.08);
                            }
                            .log-line.is-warning {
                                background: rgba(245, 158, 11, 0.10);
                            }
                            .log-line.is-error {
                                background: rgba(251, 113, 133, 0.14);
                            }
                            .line-no {
                                width: 58px;
                                flex: 0 0 58px;
                                padding-right: 16px;
                                color: #64748b;
                                text-align: right;
                                user-select: none;
                            }
                            .line-text {
                                min-width: 0;
                            }
                            .log-time {
                                color: #38bdf8;
                                font-weight: 700;
                            }
                            .log-file {
                                color: #c084fc;
                                font-weight: 700;
                            }
                            .log-info {
                                color: #22c55e;
                                font-weight: 800;
                            }
                            .log-debug {
                                color: #a78bfa;
                                font-weight: 800;
                            }
                            .log-warning {
                                color: #f59e0b;
                                font-weight: 800;
                            }
                            .log-error {
                                color: #fb7185;
                                font-weight: 900;
                            }
                            .log-stage {
                                color: #facc15;
                                font-weight: 900;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="log-shell">
                            <div class="log-header">
                                <div class="log-title">日志预览</div>
                                <div class="log-file-name">{{ file_name }}</div>
                            </div>
                            <div class="log-content">{{ highlighted_code|safe }}</div>
                        </div>
                    </body>
                </html>
                """, highlighted_code=highlighted_code, file_name=file_name)
