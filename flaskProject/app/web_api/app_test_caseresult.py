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


@caseresult.route('/get_caseresult_info', methods=["POST"])
@swag_from('../apidocs/get_caseresult_info.yml')
def get_caseresult_info():
    """获取测试集合最新执行结果"""
    set_id = request.json.get("set_id")
    case_name = request.json.get("case_name", "")
    case_name = case_name.strip()
    run_id = request.json.get("run_id")
    run_case_result = request.json.get("run_case_result")
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
    all_data = _caseresult_cache_key(allowed_ids, "all_data", {
        "page": page_no,
        "page_size": page_size,
    })
    run_cache_key = _caseresult_cache_key(allowed_ids, "run_id", {
        "run_id": run_id,
        "page": page_no,
        "page_size": page_size,
    }) if run_id else None
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
        if page_size and not case_name and not set_id and not time_value and not run_case_result and not run_id and not case_id:
            return_dict = cache_operatios.new_conn.get(all_data)
            if return_dict:
                print("获取缓存数据2")
                return_dict = json.loads(return_dict)
                return_dict.update({"cache_msg": "这是直接从redis缓存中获取的数据"})
                return return_dict
        if run_id and not case_name and not set_id and not time_value and not run_case_result:
            return_dict = cache_operatios.new_conn.get(run_cache_key)
            if return_dict:
                print("获取缓存数据1")
                return_dict = json.loads(return_dict)
                return_dict.update({"cache_msg": "这是直接从redis缓存中获取的数据"})
                return return_dict
        if case_id and not case_name and not set_id and not time_value and not run_case_result and not run_id:
            return_dict = cache_operatios.new_conn.get(case_cache_key)
            if return_dict:
                print("获取缓存数据3>>>>case_id")
                return_dict = json.loads(return_dict)
                return_dict.update({"cache_msg": "这是直接从redis缓存中获取的数据"})
                return return_dict
        query = CaseResult.query
        if allowed_ids is not None:
            query = query.filter(CaseResult.project_id.in_(allowed_ids))

        if set_id:
            query = query.filter_by(set_id=set_id)
            # if run_id:
            #     query = query.filter_by(run_id=int(run_id))
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
        if run_id:
            query = query.filter_by(run_id=int(run_id))
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
        if run_id and not case_name and not set_id and not time_value and not run_case_result:
            cache_dict = json.dumps(return_dict, cls=cache_operatios.DecimalEncoder)
            cache_operatios.new_conn.set(run_cache_key, cache_dict, ex=60 * 1)
            print("存储缓存数据1")
        if page_size and not case_name and not set_id and not time_value and not run_case_result and not run_id and not case_id:
            cache_dict = json.dumps(return_dict, cls=cache_operatios.DecimalEncoder)
            cache_operatios.new_conn.set(all_data, cache_dict, ex=60 * 1)
            print("存储缓存数据2")
        if case_id and not case_name and not set_id and not time_value and not run_case_result and not run_id:
            cache_dict = json.dumps(return_dict, cls=cache_operatios.DecimalEncoder)
            cache_operatios.new_conn.set(case_cache_key, cache_dict, ex=60 * 1)
            print("存储缓存数据3>>>>case_id")
        return jsonify(return_dict)
    except Exception as e:
        traceback.print_exc()
        return_dict = {'code': 404, 'msg': f'内部错误:{str(e)}', 'data': None, 'count': None}
        return jsonify(return_dict)


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
