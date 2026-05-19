# !/usr/bin/python3.8
# -*- coding: utf-8 -*-

import json

from flask import has_request_context, request

from app.lib.lib_define import db
from app.models.test_api_models import OperationLog


SENSITIVE_KEYS = {"password", "old_password", "new_password", "confirm_password", "oldpass", "newpass", "confirpass", "token", "authorization", "cookie", "set-cookie", "api_key", "secret"}

ACTION_RULES = [
    ("case_mark", "remark", "用例备注"),
    ("case_upload", "upload", "上传用例"),
    ("case_review", "preview", "预览源码"),
    ("update_case_source", "update", "编辑源码"),
    ("add", "create", "新增"),
    ("save", "save", "保存"),
    ("update", "update", "编辑"),
    ("delete", "delete", "删除"),
    ("deletes", "delete", "删除"),
    ("run", "run", "运行"),
    ("stop", "stop", "终止"),
    ("pull", "pull", "Git拉取"),
    ("sync", "sync", "同步"),
    ("reset", "reset", "重置"),
    ("change_password", "change_password", "修改密码"),
    ("report_mark", "remark", "报告备注"),
    ("clear", "clear", "清空"),
]

TARGET_RULES = [
    ("/api_test/", "api_test", "接口测试"),
    ("/business_department/", "business_department", "业务部门"),
    ("/project/", "project", "脚本项目"),
    ("/version/", "version", "项目版本"),
    ("/module/", "module", "项目模块"),
    ("/config/", "config", "配置"),
    ("/cases/", "case", "用例"),
    ("/testset/", "testset", "测试集"),
    ("/test_task/", "testtask", "测试任务"),
    ("/auth/", "account", "账号"),
]


def _json_text(value, limit=8000):
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        text = str(value)
    return text[:limit] if text else ""


def _clean_data(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                cleaned[key] = "***"
            else:
                cleaned[key] = _clean_data(item)
        return cleaned
    if isinstance(value, list):
        return [_clean_data(item) for item in value]
    return value


def _action_from_path(path):
    lower_path = path.lower()
    for keyword, action, action_name in ACTION_RULES:
        if keyword in lower_path:
            return action, action_name
    return "", ""


def _target_from_path(path):
    for prefix, target_type, target_name in TARGET_RULES:
        if path.startswith(prefix):
            return target_type, target_name
    return "", ""


def _target_id_from_data(data):
    if not isinstance(data, dict):
        return ""
    for key in ("id", "project_id", "task_id", "set_id", "case_id", "config_id"):
        value = data.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _target_name_from_data(data):
    if not isinstance(data, dict):
        return ""
    for key in ("name", "title", "task_name", "testset_title", "cfg_name", "username", "project_name", "case_name"):
        value = data.get(key)
        if value not in (None, ""):
            return str(value)[:500]
    return ""


def should_record_operation(path, method):
    if method != "POST":
        return False
    if path.startswith(("/auth/me", "/auth/get_operation_log")):
        return False
    action, _ = _action_from_path(path)
    return bool(action)


def record_operation_log(response):
    if not has_request_context():
        return response
    path = request.path or ""
    if not should_record_operation(path, request.method):
        return response
    try:
        from app.tools.auth_permissions import current_account
        account = current_account()
        if not account:
            return response
        request_data = request.get_json(silent=True) or {}
        response_data = response.get_json(silent=True) or {}
        action, action_name = _action_from_path(path)
        target_type, target_type_name = _target_from_path(path)
        result_msg = response_data.get("msg") if isinstance(response_data, dict) else ""
        result_code = response_data.get("code") if isinstance(response_data, dict) else None
        log = OperationLog(
            user_id=account.id,
            username=account.username,
            action=action,
            action_name=action_name,
            target_type=target_type,
            target_id=_target_id_from_data(request_data),
            target_name=_target_name_from_data(request_data) or target_type_name,
            method=request.method,
            path=path,
            status_code=response.status_code,
            result_code=result_code,
            result_msg=str(result_msg or "")[:1000],
            request_data=_json_text(_clean_data(request_data)),
            response_data=_json_text(_clean_data(response_data)),
            after_data=_json_text(_clean_data(response_data)),
            ip=(request.headers.get("X-Forwarded-For") or request.remote_addr or "").split(",")[0].strip(),
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
    return response
