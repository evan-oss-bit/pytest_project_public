# -*- coding: utf-8 -*-
import base64
import datetime
import random
import re
import string
import time
import uuid
from urllib.parse import quote_plus

import requests


VAR_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_.$-]+(?:\([^{}]*\))?)(?:\s*\|\s*([A-Za-z0-9_-]+))?\s*\}\}")


def public_context(context):
    return {key: value for key, value in (context or {}).items() if not str(key).startswith("_")}


def session_for_context(context):
    if context is None:
        return requests.Session()
    session = context.get("_requests_session")
    if not session:
        session = requests.Session()
        context["_requests_session"] = session
    return session


def cookie_snapshot(session):
    if not session:
        return {}
    try:
        return requests.utils.dict_from_cookiejar(session.cookies)
    except Exception:
        return {}


def _encode_base64(value):
    return base64.b64encode(str(value).encode("utf-8")).decode("ascii")


def _parse_builtin_args(raw_args):
    if raw_args is None or raw_args.strip() == "":
        return []
    args = []
    for item in raw_args.split(","):
        item = item.strip()
        if len(item) >= 2 and item[0] == item[-1] and item[0] in ("'", '"'):
            item = item[1:-1]
        args.append(item)
    return args


def _builtin_random_string(length=16):
    length = int(length or 16)
    length = max(1, min(length, 128))
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def _builtin_random_int(start=0, end=999999):
    start = int(start)
    end = int(end)
    if start > end:
        start, end = end, start
    return random.randint(start, end)


def call_builtin_variable_function(expression):
    match = re.fullmatch(r"\$([A-Za-z_][A-Za-z0-9_]*)(?:\((.*)\))?", str(expression).strip())
    if not match:
        return None
    name = match.group(1).lower()
    args = _parse_builtin_args(match.group(2))
    now = datetime.datetime.now()
    functions = {
        "timestamp": lambda: int(time.time()),
        "timestamp_ms": lambda: int(time.time() * 1000),
        "uuid": lambda: str(uuid.uuid4()),
        "random_string": lambda: _builtin_random_string(*(args or [16])),
        "random_int": lambda: _builtin_random_int(*(args or [0, 999999])),
        "date": lambda: now.strftime(args[0] if args else "%Y-%m-%d"),
        "datetime": lambda: now.strftime(args[0] if args else "%Y-%m-%d %H:%M:%S"),
    }
    if name not in functions:
        return "{{%s}}" % expression
    try:
        return functions[name]()
    except Exception as exc:
        return "{{%s_error:%s}}" % (expression, exc)


def format_variable_value(name, variables, transform=None):
    if str(name).startswith("$"):
        value = call_builtin_variable_function(name)
    else:
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
        return quote_plus(str(value))
    return value


def apply_variables(value, variables):
    if isinstance(value, str):
        return VAR_PATTERN.sub(lambda m: str(format_variable_value(m.group(1), variables, m.group(2))), value)
    if isinstance(value, dict):
        return {key: apply_variables(item, variables) for key, item in value.items()}
    if isinstance(value, list):
        return [apply_variables(item, variables) for item in value]
    return value
