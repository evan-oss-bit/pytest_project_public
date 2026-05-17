# -*- coding: utf-8 -*-
import base64
import uuid
from functools import wraps

from flask import g, jsonify, request
from werkzeug.security import generate_password_hash

from app.models.test_api_models import Account, AccountProject, Cases, Reports, TestSet, TestTask

ADMIN_ROLE = "admin"
PROJECT_USER_ROLE = "project_user"


def seed_admin(db):
    if Account.query.filter_by(is_delete=0).first():
        return
    admin = Account(
        username="admin",
        password=generate_password_hash("123456789"),
        nickname="管理员",
        role=ADMIN_ROLE,
        token=str(uuid.uuid4()),
        is_delete=0,
    )
    db.session.add(admin)
    db.session.commit()


def normalize_token(value):
    if value is None:
        return ""
    value = str(value).strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    return value


def get_request_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Basic "):
        return ""
    try:
        raw = base64.b64decode(auth_header.split(" ", 1)[1]).decode("utf-8")
    except Exception:
        return ""
    return normalize_token(raw.split(":", 1)[0])


def current_account():
    if hasattr(g, "current_account"):
        return g.current_account
    token = get_request_token()
    account = None
    if token:
        account = Account.query.filter_by(token=token, is_delete=0).first()
    g.current_account = account
    return account


def is_admin(account=None):
    account = account or current_account()
    return bool(account and account.role == ADMIN_ROLE)


def allowed_project_ids(permission="view", account=None):
    account = account or current_account()
    if not account:
        return []
    if account.role == ADMIN_ROLE:
        return None
    query = AccountProject.query.filter_by(account_id=account.id)
    if permission == "edit":
        query = query.filter_by(can_edit=1)
    elif permission == "run":
        query = query.filter_by(can_run=1)
    else:
        query = query.filter_by(can_view=1)
    return [item.project_id for item in query.all()]


def has_project_permission(project_id, permission="view", account=None):
    account = account or current_account()
    if not account or not project_id:
        return False
    if account.role == ADMIN_ROLE:
        return True
    query = AccountProject.query.filter_by(account_id=account.id, project_id=int(project_id))
    if permission == "edit":
        query = query.filter_by(can_edit=1)
    elif permission == "run":
        query = query.filter_by(can_run=1)
    else:
        query = query.filter_by(can_view=1)
    return query.first() is not None


def forbidden_response():
    return jsonify({"code": 403, "msg": "没有该项目权限", "data": None})


def require_project_permission(project_id, permission="view"):
    if has_project_permission(project_id, permission=permission):
        return None
    return forbidden_response()


def require_login():
    if current_account():
        return None
    return jsonify({"code": 401, "msg": "请先登录", "data": None}), 401


def require_login_decorator(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        login_error = require_login()
        if login_error:
            return login_error
        return fn(*args, **kwargs)

    return wrapper


def filter_project_query(query, model, permission="view"):
    ids = allowed_project_ids(permission=permission)
    if ids is None:
        return query
    if not ids:
        return query.filter(False)
    return query.filter(model.project_id.in_(ids))


def filter_project_model_query(query, model):
    ids = allowed_project_ids()
    if ids is None:
        return query
    if not ids:
        return query.filter(False)
    return query.filter(model.id.in_(ids))


def filter_task_list(tasks):
    ids = allowed_project_ids()
    if ids is None:
        return tasks
    if not ids:
        return []
    project_set_ids = {
        item.id for item in TestSet.query.with_entities(TestSet.id).filter(
            TestSet.project_id.in_(ids), TestSet.is_delete == 0
        ).all()
    }
    result = []
    for task in tasks:
        try:
            set_ids = eval(task.test_set_ids) if task.test_set_ids else []
        except Exception:
            set_ids = []
        if project_set_ids.intersection(set(set_ids)):
            result.append(task)
    return result


def project_id_from_case(case_id):
    item = Cases.query.filter_by(id=case_id, is_delete=0).first()
    return item.project_id if item else None


def project_id_from_testset(set_id):
    item = TestSet.query.filter_by(id=set_id, is_delete=0).first()
    return item.project_id if item else None


def project_id_from_report_path(report_path):
    item = Reports.query.filter_by(report_path=report_path).order_by(Reports.updated_time.desc()).first()
    return item.project_id if item else None


def project_ids_from_task(task_id):
    task = TestTask.query.filter_by(id=task_id, is_delete=0).first()
    if not task or not task.test_set_ids:
        return []
    try:
        set_ids = eval(task.test_set_ids)
    except Exception:
        set_ids = []
    rows = TestSet.query.with_entities(TestSet.project_id).filter(TestSet.id.in_(set_ids)).all() if set_ids else []
    return list({item.project_id for item in rows})
