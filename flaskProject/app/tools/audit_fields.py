# !/usr/bin/python3.8
# -*- coding: utf-8 -*-

from flask import has_request_context
from sqlalchemy import event, inspect, text
from sqlalchemy.exc import OperationalError

from app.lib.lib_define import db
from app.models.base import Base


AUDIT_COLUMNS = {
    "created_by": "INTEGER",
    "created_by_name": "VARCHAR(191)",
    "updated_by": "INTEGER",
    "updated_by_name": "VARCHAR(191)",
    "run_by": "INTEGER",
    "run_by_name": "VARCHAR(191)",
}


def _current_account():
    if not has_request_context():
        return None
    try:
        from app.tools.auth_permissions import current_account
        return current_account()
    except Exception:
        return None


def _account_name(account):
    if not account:
        return ""
    return account.username or str(account.id)


def _apply_user_fields(target, prefix, account=None, only_empty=False):
    account = account or _current_account()
    if not account:
        return
    id_field = f"{prefix}_by"
    name_field = f"{prefix}_by_name"
    if not hasattr(target, id_field) or not hasattr(target, name_field):
        return
    if only_empty and getattr(target, id_field, None):
        return
    setattr(target, id_field, account.id)
    setattr(target, name_field, _account_name(account))


def apply_run_user(target, account=None):
    _apply_user_fields(target, "run", account=account)


@event.listens_for(Base, "before_insert", propagate=True)
def _set_create_user(mapper, connection, target):
    account = _current_account()
    _apply_user_fields(target, "created", account=account, only_empty=True)
    _apply_user_fields(target, "updated", account=account)


@event.listens_for(Base, "before_update", propagate=True)
def _set_update_user(mapper, connection, target):
    _apply_user_fields(target, "updated")


def ensure_audit_columns():
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    with db.engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in table_names:
                continue
            existing = {item.get("name") for item in inspector.get_columns(table.name)}
            missing = [name for name in AUDIT_COLUMNS if name not in existing]
            for name in missing:
                try:
                    conn.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {name} {AUDIT_COLUMNS[name]}"))
                except OperationalError as e:
                    error_args = getattr(getattr(e, "orig", None), "args", ())
                    if error_args and error_args[0] == 1060:
                        continue
                    if "duplicate column" in str(e).lower():
                        continue
                    raise
