# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
import datetime
import os
import traceback

import yagmail
from flask import Response, jsonify, request

from app.lib import image
from app.lib.lib_define import db
from app.models.test_api_models import CaseResult, Cfgs, Reports, TestSet
from app.tools import request_details
from app.tools.auth_permissions import allowed_project_ids, project_id_from_report_path, require_project_permission
from app.tools.util import EmailThread
from app.web_api import report
from config import report_path


def _safe_report_file_path(filename):
    if not filename:
        return None
    report_root = os.path.realpath(report_path)
    target_path = os.path.realpath(os.path.join(report_root, filename))
    try:
        if os.path.commonpath([report_root, target_path]) != report_root:
            return None
    except ValueError:
        return None
    return target_path


def _report_mimetype(report_name):
    ext = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "cr2": "image/x-canon-cr2",
        "tiff": "image/tiff",
        "bmp": "image/bmp",
        "jxr": "image/vnd.ms-photo",
        "psd": "image/vnd.adobe.photoshop",
        "ico": "image/x-icon",
        "epub": "application/epub+zip",
        "zip": "application/zip",
        "tar": "application/x-tar",
        "rar": "application/x-rar-compressed",
        "pdf": "application/pdf",
        "doc": "application/msword",
        "rtf": "application/rtf",
        "html": "text/html",
        "htm": "text/html",
        "stm": "text/html",
        "xlsx": "application/vnd.ms-excel",
        "xls": "application/vnd.ms-excel",
        "css": "text/css",
    }
    suffix = str(report_name or "").split(".")[-1].lower()
    return ext.get(suffix, "text/html")


@report.route('/get_report_info', methods=["POST"])
def get_report_info():
    """获取报告列表"""
    set_id = request.json.get("set_id")
    title = request.json.get("title", "")
    run_id = request.json.get("run_id")
    title = title.strip()
    page_no = request.json.get("page", 0)
    page_size = request.json.get("page_size", 10)
    project_id = request.json.get("project_id")
    allowed_ids = allowed_project_ids()
    if project_id:
        permission_error = require_project_permission(project_id, "view")
        if permission_error:
            return permission_error
    try:
        if set_id:
            if title:
                query = Reports.query.filter_by(set_id=set_id).filter(Reports.title.like(f"%{title}%")).order_by(
                    db.desc(Reports.updated_time)).limit(page_size).offset(
                    page_no).all()
            else:
                query = Reports.query.filter_by(set_id=set_id).order_by(db.desc(Reports.updated_time)).limit(
                    page_size).offset(
                    page_no).all()
        elif project_id:
            query = Reports.query.filter_by(project_id=project_id).order_by(
                db.desc(Reports.updated_time)).limit(page_size).offset(
                page_no).all()
        elif title:
            query = Reports.query.filter(Reports.title.like(f"%{title}%")).order_by(
                db.desc(Reports.updated_time)).limit(page_size).offset(
                page_no).all()
        elif run_id:
            query = Reports.query.filter_by(run_id=run_id).order_by(
                Reports.updated_time).limit(page_size).offset(
                page_no).all()
        else:
            query = Reports.query.order_by(db.desc(Reports.updated_time)).limit(page_size).offset(page_no).all()
        if allowed_ids is not None:
            query = [item for item in query if item.project_id in allowed_ids]
        query = [i.to_dict() for i in query]
        set_ids = image.get_values_by_key(query, "set_id", values=[])
        if isinstance(set_ids, int):
            set_ids = [set_ids]
        set_id_list = None
        if set_ids:
            set_id_list = TestSet.query.filter(TestSet.id.in_(set_ids)).all()
        if set_id_list:
            set_id_list = [i.to_dict() for i in set_id_list]
            for i in range(len(query)):
                for j in set_id_list:
                    if query[i].get("set_id") == j.get("id"):
                        query[i].update({"set_title": j.get("title")})
        cfg_ids = image.get_values_by_key(query, "config_id", values=[])
        if isinstance(cfg_ids, str):
            cfg_ids = [cfg_ids]
        config_id_list = None
        ex_ids = list()
        if cfg_ids:
            for i in cfg_ids:
                if isinstance(i, str):
                    i = eval(i)
                    if isinstance(i, list):
                        ex_ids.extend(i)
                    if isinstance(i, int):
                        ex_ids.append(i)
            config_id_list = Cfgs.query.filter(Cfgs.id.in_(ex_ids)).all()
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
        for i in query:
            if i.get("updated_time"):
                i.update({"updated_time": i.get("updated_time").strftime("%Y-%m-%d %H:%M:%S")})
        return jsonify({'code': 200, 'msg': '请求成功', 'data': query})
    except Exception:
        print(traceback.print_exc())
        return jsonify({'code': 404, 'msg': '内部错误', 'data': None})


@report.route('/report_content', methods=["POST"])
@request_details.log_request_response(module="report_content")
def report_content():
    """获取测试报告内容"""
    filename = request.json.get("filename")
    set_id = request.json.get("set_id")
    if not filename:
        return jsonify({"code": 404, "msg": "没有测试报告", "data": None})
    query = Reports.query.filter_by(report_path=filename).order_by(
        db.desc(Reports.updated_time)).first()
    if not query:
        return jsonify({"code": 404, "msg": "没有测试报告", "data": None})
    if set_id:
        query = Reports.query.filter_by(report_path=filename).filter_by(set_id=set_id).order_by(
            db.desc(Reports.updated_time)).first()
    if not query:
        return jsonify({"code": 404, "msg": "没有测试报告", "data": None})
    permission_error = require_project_permission(query.project_id, "view")
    if permission_error:
        return permission_error

    report_allpath = _safe_report_file_path(query.report_path)
    if not report_allpath:
        return jsonify({"code": 404, "msg": "测试报告路径不合法！", "data": None})
    if not os.path.exists(report_allpath):
        return jsonify({"code": 404, "msg": "测试报告不存在！", "data": None})
    with open(report_allpath, "rb") as f:
        return Response(f.read(), mimetype=_report_mimetype(query.report_path))


@report.route('/report_mark', methods=["POST"])
def report_mark():
    mark = request.json.get("mark", "")
    report_id = request.json.get("id")
    if not report_id:
        return {'code': 404, 'msg': '没有report_id', 'data': None}
    query = Reports.query.filter_by(id=report_id).first()
    if not query:
        return {'code': 404, 'msg': '报告不存在', 'data': None}
    permission_error = require_project_permission(query.project_id, "edit")
    if permission_error:
        return permission_error
    query.mark = mark
    db.session.commit()
    return {'code': 200, 'msg': '请求成功！', 'data': None}


@report.route('/send_email', methods=["POST"])
def send_email_a():
    email_title = request.json.get("email_title", "")
    email_to = request.json.get("email_to")
    report_name = request.json.get("report_path")
    project_name = request.json.get("project_name", "")
    set_title = request.json.get("set_title", "")
    try:
        permission_error = require_project_permission(project_id_from_report_path(report_name), "view")
        if permission_error:
            return permission_error
        dir_path = _safe_report_file_path(report_name)
        if not dir_path or not os.path.exists(dir_path):
            return {'code': 404, 'msg': '报告文件不存在或路径不合法', 'data': None}
        if email_title:
            contents = ['您好：', email_title, yagmail.inline(r"{dir_path}".format(dir_path=dir_path))]
        else:
            contents = ['您好：',
                        f'请查收{project_name}项目的{set_title}测试集的自动化测试报告:',
                        yagmail.inline(r"{dir_path}".format(dir_path=dir_path))]
        t = EmailThread(email_to, subject="自动化测试报告", contents=contents, attachments=None)
        t.start()
        return {'code': 200, 'msg': '请求成功！', 'data': None}
    except Exception as e:
        print(e)
        return {'code': 404, 'msg': f'发送失败>>>>{e}', 'data': None}


def _failure_reason_text(item):
    raw = item.longrepr or item.run_info or ""
    if not raw:
        return "未记录失败原因"
    lines = [line.strip() for line in str(raw).replace("\r", "\n").split("\n") if line.strip()]
    if not lines:
        return "未记录失败原因"
    for line in lines:
        if line.startswith(("E   ", "E\t", "AssertionError", "Exception", "Error", "Failed", "Timeout")):
            return line[:180]
    return lines[0][:180]


def _case_failure_key(item):
    if item.case_id:
        return f"id:{item.case_id}"
    return f"name:{item.case_title or item.case_name or item.file_path_name or item.id}"


@report.route('/get_report_failure_analysis', methods=["POST"])
def get_report_failure_analysis():
    """获取报告失败分析"""
    project_id = request.json.get("project_id")
    set_id = request.json.get("set_id")
    run_id = request.json.get("run_id")
    recent_runs = request.json.get("recent_runs", 10)
    limit = request.json.get("limit", 8)
    try:
        recent_runs = max(1, min(int(recent_runs or 10), 50))
    except (TypeError, ValueError):
        recent_runs = 10
    try:
        limit = max(1, min(int(limit or 8), 30))
    except (TypeError, ValueError):
        limit = 8

    allowed_ids = allowed_project_ids()
    if project_id:
        permission_error = require_project_permission(project_id, "view")
        if permission_error:
            return permission_error

    report_query = Reports.query
    if project_id:
        report_query = report_query.filter_by(project_id=project_id)
    elif allowed_ids is not None:
        report_query = report_query.filter(Reports.project_id.in_(allowed_ids))
    if set_id:
        report_query = report_query.filter_by(set_id=set_id)
    if run_id:
        report_query = report_query.filter_by(run_id=run_id)
    else:
        report_query = report_query.filter(Reports.run_id.isnot(None)).order_by(
            db.desc(Reports.updated_time)
        ).limit(recent_runs)

    reports = report_query.all()
    run_ids = [item.run_id for item in reports if item.run_id]
    if not run_ids:
        return jsonify({'code': 200, 'msg': '请求成功', 'data': {
            'recent_runs': recent_runs,
            'run_ids': [],
            'failure_top': [],
            'repeat_failures': [],
            'reason_groups': [],
        }})

    result_query = CaseResult.query.filter(
        CaseResult.run_id.in_(run_ids),
        CaseResult.run_case_result.in_(["failed", "error"])
    )
    if project_id:
        result_query = result_query.filter_by(project_id=project_id)
    elif allowed_ids is not None:
        result_query = result_query.filter(CaseResult.project_id.in_(allowed_ids))
    if set_id:
        result_query = result_query.filter_by(set_id=set_id)

    rows = result_query.order_by(db.desc(CaseResult.updated_time)).all()
    case_map = {}
    reason_map = {}
    for item in rows:
        key = _case_failure_key(item)
        bucket = case_map.setdefault(key, {
            "case_id": item.case_id,
            "case_title": item.case_title or item.case_name or "",
            "case_name": item.case_name or "",
            "project_name": item.project_name or "",
            "set_id": item.set_id,
            "file_name": item.file_name or item.file_path_name or "",
            "failure_count": 0,
            "failed_count": 0,
            "error_count": 0,
            "run_ids": set(),
            "latest_run_id": item.run_id,
            "latest_result": item.run_case_result,
            "latest_time": item.updated_time,
            "latest_reason": _failure_reason_text(item),
        })
        bucket["failure_count"] += 1
        if item.run_case_result == "error":
            bucket["error_count"] += 1
        else:
            bucket["failed_count"] += 1
        bucket["run_ids"].add(item.run_id)
        if item.updated_time and (not bucket["latest_time"] or item.updated_time > bucket["latest_time"]):
            bucket["latest_run_id"] = item.run_id
            bucket["latest_result"] = item.run_case_result
            bucket["latest_time"] = item.updated_time
            bucket["latest_reason"] = _failure_reason_text(item)

        reason = _failure_reason_text(item)
        reason_bucket = reason_map.setdefault(reason, {
            "reason": reason,
            "count": 0,
            "case_count": set(),
            "sample_case": item.case_title or item.case_name or "",
            "latest_run_id": item.run_id,
            "latest_time": item.updated_time,
        })
        reason_bucket["count"] += 1
        reason_bucket["case_count"].add(key)
        if item.updated_time and (not reason_bucket["latest_time"] or item.updated_time > reason_bucket["latest_time"]):
            reason_bucket["latest_run_id"] = item.run_id
            reason_bucket["latest_time"] = item.updated_time
            reason_bucket["sample_case"] = item.case_title or item.case_name or ""

    def _case_payload(item):
        data = dict(item)
        data["run_count"] = len(data.pop("run_ids"))
        data["is_repeated"] = data["run_count"] >= 2
        data["latest_time"] = data["latest_time"].strftime("%Y-%m-%d %H:%M:%S") if data.get("latest_time") else ""
        return data

    sorted_cases = [_case_payload(item) for item in sorted(
        case_map.values(),
        key=lambda row: (row["failure_count"], len(row["run_ids"]), row.get("latest_time") or datetime.datetime.min),
        reverse=True
    )]
    failure_top = sorted_cases[:limit]
    repeat_failures = [item for item in sorted_cases if item.get("is_repeated")][:limit]
    reason_groups = []
    for item in sorted(reason_map.values(), key=lambda row: row["count"], reverse=True)[:limit]:
        reason_groups.append({
            "reason": item["reason"],
            "count": item["count"],
            "case_count": len(item["case_count"]),
            "sample_case": item["sample_case"],
            "latest_run_id": item["latest_run_id"],
            "latest_time": item["latest_time"].strftime("%Y-%m-%d %H:%M:%S") if item.get("latest_time") else "",
        })

    return jsonify({'code': 200, 'msg': '请求成功', 'data': {
        'recent_runs': recent_runs,
        'run_ids': run_ids,
        'failure_top': failure_top,
        'repeat_failures': repeat_failures,
        'reason_groups': reason_groups,
    }})
