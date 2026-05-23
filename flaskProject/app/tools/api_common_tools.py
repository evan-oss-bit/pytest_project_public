# -*- coding: utf-8 -*-
import datetime
import json
import time


def json_text(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def loads(value, default=None):
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


def int_or_none(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except Exception:
        return None


def format_time(value):
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def run_id_text(value):
    return str(value) if value not in (None, "") else ""


def new_api_run_id():
    return int(datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:17] + str(int(time.time() * 1000000) % 100).zfill(2))


def api_run_id_from(data):
    run_id = int_or_none(data.get("run_id") or data.get("_api_run_id"))
    return run_id or new_api_run_id()


def normalize_dependency_strategy(value):
    value = str(value or "").strip()
    if value in ("once", "always", "retry_on_auth_fail"):
        return value
    return "retry_on_auth_fail"


def with_time(data):
    data["created_time"] = format_time(data.get("created_time"))
    data["updated_time"] = format_time(data.get("updated_time"))
    return data
