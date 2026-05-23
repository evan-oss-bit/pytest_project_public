# -*- coding: utf-8 -*-
import json
import re

import jsonschema


def json_path(data, path):
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


def extract_variables(response, body_text, extractors):
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
                value = json_path(json_body, path)
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


def run_assertions(response, body_text, assertions, elapsed_ms=0):
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
                actual = json_path(json_body, item.get("path"))
                success = str(actual) == str(expected)
            elif assertion_type == "header_exists":
                actual = item.get("path") or item.get("name") or item.get("header")
                success = actual in response.headers
            elif assertion_type == "response_time_lt":
                actual = elapsed_ms
                success = int(actual) < int(expected)
            elif assertion_type == "response_time_lte":
                actual = elapsed_ms
                success = int(actual) <= int(expected)
            elif assertion_type == "json_schema":
                if json_body is None:
                    json_body = response.json()
                schema = item.get("schema")
                if schema in (None, ""):
                    schema = expected
                if isinstance(schema, str):
                    schema = json.loads(schema)
                jsonschema.validate(instance=json_body, schema=schema)
                actual = "schema valid"
                success = True
            else:
                error = "不支持的断言类型"
        except Exception as exc:
            error = str(exc)
        results.append({"name": name, "type": assertion_type, "success": success, "actual": actual, "expected": expected, "error": error})
    return results
