# -*- coding: utf-8 -*-
"""Seed this platform's own HTTP APIs into the API test module.

Run from flaskProject:
    venv\Scripts\python.exe scripts\seed_platform_api_cases.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from app.lib.lib_define import db
from app.models.test_api_models import ApiCase, ApiEnvironment, ApiSuite


HOST_VAR = "{{host}}"
ENV_NAME = "本地测试平台"
SUITE_NAME = "平台接口全量冒烟"
PUBLIC_PATHS = {"/login", "/captcha"}
EXCLUDED_ENDPOINT_PREFIXES = ("flasgger.", "static", "echo")
EXCLUDED_PATH_PREFIXES = (
    "/traffic/apidocs",
    "/apispec",
    "/flasgger_static",
    "/oauth2-redirect",
    "/logs/",
)
EXCLUDED_PATHS = {"/echo", "/testset/ws"}


def dumps(value):
    return json.dumps(value, ensure_ascii=False)


def loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def get_or_create_environment():
    env = ApiEnvironment.query.filter_by(name=ENV_NAME, is_delete=0).first()
    if not env:
        env = ApiEnvironment(name=ENV_NAME, is_delete=0)
        db.session.add(env)
    variables = loads(env.variables, {})
    variables.setdefault("host", "http://127.0.0.1:5400")
    variables.setdefault("login_username", "admin")
    variables.setdefault("login_password", "123456789")
    variables.setdefault("project_id", 1)
    variables.setdefault("department_id", 1)
    variables.setdefault("version_id", 1)
    variables.setdefault("module_id", 1)
    variables.setdefault("case_id", 1)
    variables.setdefault("testset_id", 1)
    variables.setdefault("testtask_id", 1)
    variables.setdefault("report_id", 1)
    variables.setdefault("config_id", 1)
    variables.setdefault("api_case_id", 1)
    variables.setdefault("api_suite_id", 1)
    variables.setdefault("account_id", 1)
    variables.setdefault("preview_path", "README.md")
    variables.setdefault("log_file", "")
    env.variables = dumps(variables)
    env.description = "平台自身接口测试使用的本地环境变量，可按实际账号和数据ID调整。"
    return env


def clean_rule(rule):
    path = rule.rule
    # Dynamic file/static/websocket endpoints are intentionally skipped elsewhere.
    return path


def should_skip(rule):
    if rule.endpoint.startswith(EXCLUDED_ENDPOINT_PREFIXES):
        return True
    if rule.rule in EXCLUDED_PATHS:
        return True
    if any(rule.rule.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES):
        return True
    if "<" in rule.rule and ">" in rule.rule:
        return True
    return False


def methods_for(rule):
    return sorted(method for method in rule.methods if method not in ("HEAD", "OPTIONS"))


def endpoint_name(endpoint):
    return endpoint.split(".")[-1]


def request_body(path, method):
    if method == "GET":
        return "", "none"
    if path == "/login":
        return dumps({"username": "{{login_username}}", "password": "{{login_password}}"}), "json"

    body_map = {
        "/auth/change_password": {"old_password": "", "new_password": "", "confirm_password": ""},
        "/auth/delete_account": {"id": "{{account_id}}"},
        "/auth/reset_account_password": {"id": "{{account_id}}"},
        "/auth/save_account": {"username": "demo_user", "nickname": "demo_user", "role": "project_user", "project_permissions": []},
        "/business_department/delete_business_department": {"id": "{{department_id}}"},
        "/business_department/get_business_department_dashboard": {"id": "{{department_id}}"},
        "/business_department/save_business_department": {"id": "{{department_id}}", "name": "示例业务部门", "remark": "接口测试示例"},
        "/cases/add_case": {"project_id": "{{project_id}}", "case_path": "", "case_name": "示例用例"},
        "/cases/case_mark": {"id": "{{case_id}}", "remark": "接口测试备注"},
        "/cases/case_review": {"id": "{{case_id}}"},
        "/cases/delete_case": {"id": ["{{case_id}}"]},
        "/cases/get_cases_info": {"project_id": "{{project_id}}", "page": 1, "limit": 10},
        "/cases/update_case_source": {"id": "{{case_id}}", "source_code": ""},
        "/cases/update_cases": {"id": "{{case_id}}", "case_name": "示例用例"},
        "/caseresult/get_caseresult_info": {"page": 1, "limit": 10},
        "/caseresult/get_log_info": {"log_file": "{{log_file}}"},
        "/config/add_config": {"name": "示例配置", "project_id": "{{project_id}}", "config": {}},
        "/config/deletes_config": {"id": ["{{config_id}}"]},
        "/config/update_config": {"id": "{{config_id}}", "name": "示例配置", "config": {}},
        "/module/add_module": {"project_id": "{{project_id}}", "name": "示例模块"},
        "/module/update_module": {"id": "{{module_id}}", "name": "示例模块"},
        "/project/check_ini": {"id": "{{project_id}}"},
        "/project/check_script_changes": {"project_id": "{{project_id}}"},
        "/project/clear_ini": {"id": "{{project_id}}"},
        "/project/get_project_dashboard": {"project_id": "{{project_id}}"},
        "/project/get_project_git_branches": {"project_id": "{{project_id}}"},
        "/project/get_project_tree": {"project_id": "{{project_id}}"},
        "/project/preview_project_file": {"project_id": "{{project_id}}", "path": "{{preview_path}}"},
        "/project/pull_project_git": {"project_id": "{{project_id}}"},
        "/project/sync_project_scripts": {"project_id": "{{project_id}}"},
        "/project/update_project": {"id": "{{project_id}}", "name": "示例项目"},
        "/report/get_report_failure_analysis": {"project_id": "{{project_id}}"},
        "/report/report_content": {"report_id": "{{report_id}}"},
        "/report/report_mark": {"id": "{{report_id}}", "remark": "接口测试备注"},
        "/report/send_email": {"id": "{{report_id}}"},
        "/test_task/add_testtask": {"project_id": "{{project_id}}", "task_name": "示例测试任务", "test_set_ids": ["{{testset_id}}"]},
        "/test_task/delete_testtask": {"id": ["{{testtask_id}}"]},
        "/test_task/get_testtask_config_snapshot": {"id": "{{testtask_id}}"},
        "/test_task/get_testtask_history": {"id": "{{testtask_id}}"},
        "/test_task/get_testtask_set": {"id": "{{testtask_id}}"},
        "/test_task/get_testtask_timeline": {"id": "{{testtask_id}}"},
        "/test_task/run_testtask": {"id": "{{testtask_id}}"},
        "/test_task/stop_testtask": {"id": ["{{testtask_id}}"]},
        "/testset/add_testset": {"project_id": "{{project_id}}", "testset_title": "示例测试集", "case_ids": ["{{case_id}}"]},
        "/testset/delete_testset": {"id": ["{{testset_id}}"]},
        "/testset/get_job_list": {},
        "/testset/run_testset": {"id": "{{testset_id}}"},
        "/testset/stop_testset": {"id": ["{{testset_id}}"]},
        "/testset/union_testask": {"project_id": "{{project_id}}"},
        "/testset/update_testset": {"id": "{{testset_id}}", "testset_title": "示例测试集", "case_ids": ["{{case_id}}"]},
        "/version/add_version": {"project_id": "{{project_id}}", "name": "示例版本"},
        "/version/update_version": {"id": "{{version_id}}", "name": "示例版本"},
    }
    return dumps(body_map.get(path, {"page": 1, "limit": 10})), "json"


def assertions_for(path):
    if path == "/login":
        return [{"type": "status_code", "expected": "200", "name": "登录成功"}]
    return [{"type": "status_code", "expected": "200", "name": "HTTP 200"}]


def find_case(method, path):
    suffix = path
    candidates = ApiCase.query.filter(ApiCase.method == method, ApiCase.is_delete == 0).all()
    for item in candidates:
        url = item.url or ""
        if url == HOST_VAR + path or url.endswith(suffix):
            return item
    return None


def upsert_case(method, path, endpoint, env_id, login_case_id=None):
    item = find_case(method, path)
    if not item:
        item = ApiCase(name="", method=method, url="", is_delete=0)
        db.session.add(item)

    item.name = "平台接口 - {} [{}]".format(endpoint_name(endpoint), method)
    item.environment_id = env_id
    item.method = method
    item.url = HOST_VAR + path
    body, body_type = request_body(path, method)
    item.body_type = body_type
    item.body = body
    item.params = dumps({})
    item.headers = dumps({} if path in PUBLIC_PATHS else {"Authorization": "Basic {{token|basic}}"})
    item.assertions = dumps(assertions_for(path))
    item.extractors = dumps([{"from": "json", "name": "token", "path": "token"}] if path == "/login" else [])
    item.pre_case_ids = dumps([] if path in PUBLIC_PATHS or not login_case_id else [login_case_id])
    item.description = "由 scripts/seed_platform_api_cases.py 自动同步的平台接口用例。"
    return item


def upsert_suite(case_ids, env_id):
    suite = ApiSuite.query.filter_by(name=SUITE_NAME, is_delete=0).first()
    if not suite:
        suite = ApiSuite(name=SUITE_NAME, is_delete=0)
        db.session.add(suite)
    suite.environment_id = env_id
    suite.case_ids = dumps(case_ids)
    suite.stop_on_fail = 0
    suite.description = "平台自身 HTTP 接口全量清单，包含登录依赖；部分增删改接口需要按环境变量补充真实ID后再执行。"
    return suite


def main():
    app = create_app(register_blueprint=True)
    with app.app_context():
        env = get_or_create_environment()
        db.session.flush()

        login = upsert_case("POST", "/login", "auth.login", env.id)
        db.session.flush()

        case_ids = [login.id]
        created_or_updated = 1
        for rule in sorted(app.url_map.iter_rules(), key=lambda item: item.rule):
            if should_skip(rule):
                continue
            path = clean_rule(rule)
            for method in methods_for(rule):
                if method == "POST" and path == "/login":
                    continue
                item = upsert_case(method, path, rule.endpoint, env.id, login.id)
                db.session.flush()
                if item.id not in case_ids:
                    case_ids.append(item.id)
                created_or_updated += 1

        suite = upsert_suite(case_ids, env.id)
        db.session.commit()
        print("环境: {} ID={}".format(env.name, env.id))
        print("登录用例 ID={}".format(login.id))
        print("同步接口用例数量: {}".format(created_or_updated))
        print("接口集合: {} ID={} 用例数={}".format(suite.name, suite.id, len(case_ids)))


if __name__ == "__main__":
    main()
