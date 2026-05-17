# -*- coding: utf-8 -*-
import uuid

from flask import Blueprint, jsonify, request
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from werkzeug.security import check_password_hash, generate_password_hash

from app.lib.lib_define import db
from app.models.test_api_models import Account, AccountProject, Project
from app.tools.auth_permissions import (
    ADMIN_ROLE,
    PROJECT_USER_ROLE,
    current_account,
    require_login,
    seed_admin,
)

auth = Blueprint("auth", __name__)


def _ensure_project_department_column():
    inspector = inspect(db.engine)
    columns = {item.get("name") for item in inspector.get_columns("project")}
    try:
        with db.engine.begin() as conn:
            if "business_department_id" not in columns:
                conn.execute(text("ALTER TABLE project ADD COLUMN business_department_id INTEGER"))
            if "business_department" not in columns:
                conn.execute(text("ALTER TABLE project ADD COLUMN business_department VARCHAR(255) DEFAULT ''"))
            if "product_line" in columns:
                conn.execute(text(
                    "UPDATE project SET business_department = product_line "
                    "WHERE (business_department IS NULL OR business_department = '') "
                    "AND product_line IS NOT NULL AND product_line != ''"
                ))
    except OperationalError as e:
        if "duplicate column" not in str(e).lower():
            raise


def _is_password_hash(value):
    value = value or ""
    return value.startswith("pbkdf2:") or value.startswith("scrypt:")


def _hash_password(password):
    return generate_password_hash(password or "")


def _password_matches(account, password):
    stored_password = account.password or ""
    if _is_password_hash(stored_password):
        return check_password_hash(stored_password, password or "")
    return stored_password == (password or "")


DEFAULT_ACCOUNT_PASSWORD = "123456789"


def _account_payload(account):
    _ensure_project_department_column()
    permissions = AccountProject.query.filter_by(account_id=account.id).all()
    project_ids = [item.project_id for item in permissions]
    projects = Project.query.filter(Project.id.in_(project_ids)).all() if project_ids else []
    project_map = {item.id: item.name for item in projects}
    department_map = {item.id: item.business_department or "" for item in projects}
    department_id_map = {item.id: item.business_department_id for item in projects}
    return {
        "id": account.id,
        "username": account.username,
        "nickname": account.nickname or account.username,
        "role": account.role,
        "project_ids": project_ids,
        "permissions": [
            {
                "project_id": item.project_id,
                "project_name": project_map.get(item.project_id, "项目{}".format(item.project_id)),
                "business_department_id": department_id_map.get(item.project_id),
                "business_department": department_map.get(item.project_id, ""),
                "can_view": item.can_view,
                "can_edit": item.can_edit,
                "can_run": item.can_run,
            }
            for item in permissions
        ],
    }


@auth.route('/login', methods=["POST"])
def login():
    seed_admin(db)
    data = request.get_json(silent=True) or {}
    basic_auth = request.authorization
    username = (data.get("username") or (basic_auth.username if basic_auth else "") or "").strip()
    password = data.get("password") or (basic_auth.password if basic_auth else "")
    account = Account.query.filter_by(username=username, is_delete=0).first()
    if not account or not _password_matches(account, password):
        return jsonify({"code": 404, "msg": "账号或密码错误", "token": None, "name": None})
    if not _is_password_hash(account.password):
        account.password = _hash_password(password)
    account.token = str(uuid.uuid4())
    db.session.commit()
    payload = _account_payload(account)
    return jsonify({
        "code": 200,
        "msg": "登录成功",
        "token": account.token,
        "name": account.nickname or account.username,
        "user": payload,
    })


@auth.route('/auth/me', methods=["GET", "POST"])
def me():
    login_error = require_login()
    if login_error:
        return login_error
    return jsonify({"code": 200, "msg": "请求成功", "data": _account_payload(current_account())})


@auth.route('/auth/get_account_info', methods=["POST"])
def get_account_info():
    login_error = require_login()
    if login_error:
        return login_error
    if current_account().role != ADMIN_ROLE:
        return jsonify({"code": 403, "msg": "只有管理员可以查看账号", "data": []})
    accounts = Account.query.filter_by(is_delete=0).order_by(Account.id.desc()).all()
    return jsonify({"code": 200, "msg": "请求成功", "data": [_account_payload(item) for item in accounts]})


@auth.route('/auth/save_account', methods=["POST"])
def save_account():
    login_error = require_login()
    if login_error:
        return login_error
    if current_account().role != ADMIN_ROLE:
        return jsonify({"code": 403, "msg": "只有管理员可以维护账号", "data": None})
    data = request.get_json(silent=True) or {}
    account_id = data.get("id")
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"code": 404, "msg": "账号不能为空", "data": None})
    role = data.get("role") or PROJECT_USER_ROLE
    password = data.get("password") or DEFAULT_ACCOUNT_PASSWORD
    if account_id:
        account = Account.query.filter_by(id=account_id, is_delete=0).first()
        if not account:
            return jsonify({"code": 404, "msg": "账号不存在", "data": None})
        account.username = username
        if data.get("password"):
            account.password = _hash_password(password)
    else:
        if Account.query.filter_by(username=username, is_delete=0).first():
            return jsonify({"code": 404, "msg": "账号已存在", "data": None})
        account = Account(username=username, password=_hash_password(password), token=str(uuid.uuid4()), is_delete=0)
        db.session.add(account)
        db.session.flush()
    account.nickname = data.get("nickname") or username
    account.role = role
    AccountProject.query.filter_by(account_id=account.id).delete()
    if role != ADMIN_ROLE:
        for item in data.get("permissions") or []:
            project_id = item.get("project_id")
            if not project_id or not Project.query.filter_by(id=project_id).first():
                continue
            db.session.add(AccountProject(
                account_id=account.id,
                project_id=project_id,
                can_view=1,
                can_edit=1 if item.get("can_edit") else 0,
                can_run=1 if item.get("can_run") else 0,
            ))
    db.session.commit()
    return jsonify({"code": 200, "msg": "保存成功", "data": _account_payload(account)})


@auth.route('/auth/change_password', methods=["POST"])
def change_password():
    login_error = require_login()
    if login_error:
        return login_error
    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password") or data.get("oldpass") or ""
    new_password = data.get("new_password") or data.get("newpass") or ""
    confirm_password = data.get("confirm_password") or data.get("confirpass") or ""
    account = current_account()
    if not _password_matches(account, old_password):
        return jsonify({"code": 404, "msg": "原密码不正确", "data": None})
    if len(new_password) < 8:
        return jsonify({"code": 404, "msg": "新密码长度不能小于8位", "data": None})
    if new_password != confirm_password:
        return jsonify({"code": 404, "msg": "两次输入密码不一致", "data": None})
    account.password = _hash_password(new_password)
    db.session.commit()
    return jsonify({"code": 200, "msg": "密码修改成功", "data": None})


@auth.route('/auth/reset_account_password', methods=["POST"])
def reset_account_password():
    login_error = require_login()
    if login_error:
        return login_error
    if current_account().role != ADMIN_ROLE:
        return jsonify({"code": 403, "msg": "只有管理员可以重置密码", "data": None})
    account_id = (request.get_json(silent=True) or {}).get("id")
    account = Account.query.filter_by(id=account_id, is_delete=0).first()
    if not account:
        return jsonify({"code": 404, "msg": "账号不存在", "data": None})
    account.password = _hash_password(DEFAULT_ACCOUNT_PASSWORD)
    db.session.commit()
    return jsonify({"code": 200, "msg": "密码已重置为初始密码：{}".format(DEFAULT_ACCOUNT_PASSWORD), "data": None})


@auth.route('/auth/delete_account', methods=["POST"])
def delete_account():
    login_error = require_login()
    if login_error:
        return login_error
    if current_account().role != ADMIN_ROLE:
        return jsonify({"code": 403, "msg": "只有管理员可以删除账号", "data": None})
    account_id = (request.get_json(silent=True) or {}).get("id")
    account = Account.query.filter_by(id=account_id, is_delete=0).first()
    if not account or account.role == ADMIN_ROLE:
        return jsonify({"code": 404, "msg": "账号不存在或管理员不能删除", "data": None})
    account.is_delete = 1
    db.session.commit()
    return jsonify({"code": 200, "msg": "删除成功", "data": None})
