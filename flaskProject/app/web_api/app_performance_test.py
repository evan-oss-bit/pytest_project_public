# -*- coding: utf-8 -*-
import threading

from flask import current_app, jsonify, request

from app.lib.lib_define import db
from app.models.test_api_models import PerfEndpoint, PerfRunResult, PerfScenario
from app.tools.api_common_tools import int_or_none, json_text, loads
from app.tools.audit_fields import apply_run_user
from app.tools.db_write_guard import guarded_commit
from app.tools.performance_execution_service import new_perf_run_id, start_performance_run, stop_performance_run
from app.tools.performance_payload_tools import (
    normalize_endpoint_ids,
    perf_endpoint_payload,
    perf_result_payload,
    perf_scenario_payload,
)
from app.web_api import performance_test


def _page_args(data):
    page = int(data.get("page") or data.get("page_no") or 1)
    size = int(data.get("size") or data.get("page_size") or 20)
    return max(page, 1), max(min(size, 200), 1)


@performance_test.route("/get_endpoint_info", methods=["POST"])
def get_endpoint_info():
    data = request.get_json(silent=True) or {}
    page, size = _page_args(data)
    query = PerfEndpoint.query.filter_by(is_delete=0)
    if data.get("project_id") not in (None, ""):
        query = query.filter(PerfEndpoint.project_id == int_or_none(data.get("project_id")))
    if data.get("keyword"):
        query = query.filter(PerfEndpoint.name.like("%{}%".format(data.get("keyword"))))
    total = query.count()
    rows = query.order_by(db.desc(PerfEndpoint.updated_time)).limit(size).offset((page - 1) * size).all()
    return jsonify({"code": 200, "msg": "请求成功", "data": [perf_endpoint_payload(item) for item in rows], "total": total})


@performance_test.route("/save_endpoint", methods=["POST"])
def save_endpoint():
    data = request.get_json(silent=True) or {}
    item = PerfEndpoint.query.get(data.get("id")) if data.get("id") else PerfEndpoint()
    item.name = data.get("name") or data.get("url") or "性能接口"
    item.project_id = int_or_none(data.get("project_id"))
    item.method = (data.get("method") or "GET").upper()
    item.url = data.get("url") or ""
    item.headers = json_text(data.get("headers") or {})
    item.params = json_text(data.get("params") or {})
    item.body_type = data.get("body_type") or "json"
    item.body = data.get("body") or ""
    item.weight = int_or_none(data.get("weight")) or 1
    item.description = data.get("description") or ""
    db.session.add(item)
    guarded_commit()
    return jsonify({"code": 200, "msg": "保存成功", "data": perf_endpoint_payload(item)})


@performance_test.route("/delete_endpoint", methods=["POST"])
def delete_endpoint():
    data = request.get_json(silent=True) or {}
    item = PerfEndpoint.query.get(data.get("id"))
    if not item:
        return jsonify({"code": 404, "msg": "接口不存在", "data": None})
    item.is_delete = 1
    guarded_commit()
    return jsonify({"code": 200, "msg": "删除成功", "data": None})


@performance_test.route("/get_scenario_info", methods=["POST"])
def get_scenario_info():
    data = request.get_json(silent=True) or {}
    page, size = _page_args(data)
    query = PerfScenario.query.filter_by(is_delete=0)
    if data.get("project_id") not in (None, ""):
        query = query.filter(PerfScenario.project_id == int_or_none(data.get("project_id")))
    if data.get("keyword"):
        query = query.filter(PerfScenario.name.like("%{}%".format(data.get("keyword"))))
    total = query.count()
    rows = query.order_by(db.desc(PerfScenario.updated_time)).limit(size).offset((page - 1) * size).all()
    return jsonify({"code": 200, "msg": "请求成功", "data": [perf_scenario_payload(item) for item in rows], "total": total})


@performance_test.route("/save_scenario", methods=["POST"])
def save_scenario():
    data = request.get_json(silent=True) or {}
    item = PerfScenario.query.get(data.get("id")) if data.get("id") else PerfScenario()
    item.name = data.get("name") or "性能测试场景"
    item.project_id = int_or_none(data.get("project_id"))
    item.endpoint_ids = json_text(normalize_endpoint_ids(data.get("endpoint_ids") or []))
    item.users = int_or_none(data.get("users")) or 1
    item.spawn_rate = float(data.get("spawn_rate") or 1)
    item.run_time = data.get("run_time") or "1m"
    item.host = data.get("host") or ""
    item.description = data.get("description") or ""
    db.session.add(item)
    guarded_commit()
    return jsonify({"code": 200, "msg": "保存成功", "data": perf_scenario_payload(item)})


@performance_test.route("/delete_scenario", methods=["POST"])
def delete_scenario():
    data = request.get_json(silent=True) or {}
    item = PerfScenario.query.get(data.get("id"))
    if not item:
        return jsonify({"code": 404, "msg": "场景不存在", "data": None})
    item.is_delete = 1
    guarded_commit()
    return jsonify({"code": 200, "msg": "删除成功", "data": None})


@performance_test.route("/run_scenario", methods=["POST"])
def run_scenario():
    data = request.get_json(silent=True) or {}
    scenario = PerfScenario.query.filter_by(id=data.get("scenario_id") or data.get("id"), is_delete=0).first()
    if not scenario:
        return jsonify({"code": 404, "msg": "场景不存在", "data": None})
    running = PerfRunResult.query.filter(
        PerfRunResult.scenario_id == scenario.id,
        PerfRunResult.run_status.in_(["queued", "running"]),
    ).order_by(db.desc(PerfRunResult.created_time)).first()
    if running:
        return jsonify({"code": 200, "msg": "已有运行中的性能测试", "data": perf_result_payload(running)})
    result = PerfRunResult(
        run_id=new_perf_run_id(),
        scenario_id=scenario.id,
        project_id=scenario.project_id,
        users=int_or_none(data.get("users")) or scenario.users or 1,
        spawn_rate=float(data.get("spawn_rate") or scenario.spawn_rate or 1),
        run_time=data.get("run_time") or scenario.run_time or "1m",
        host=data.get("host") or scenario.host or "",
        run_status="queued",
        status_text="排队中",
        metrics=json_text({"stats": [], "summary": {}}),
    )
    apply_run_user(result)
    db.session.add(result)
    guarded_commit()
    app = current_app._get_current_object()
    thread = threading.Thread(target=start_performance_run, args=(app, result.id, scenario.id), daemon=True)
    thread.start()
    return jsonify({"code": 200, "msg": "性能测试已启动", "data": perf_result_payload(result)})


@performance_test.route("/stop_run", methods=["POST"])
def stop_run():
    data = request.get_json(silent=True) or {}
    run_id = int_or_none(data.get("run_id"))
    result = PerfRunResult.query.filter_by(run_id=run_id).first()
    if not result:
        return jsonify({"code": 404, "msg": "运行记录不存在", "data": None})
    result.run_status = "stopped"
    result.status_text = "终止中"
    stopped = stop_performance_run(run_id)
    guarded_commit()
    return jsonify({"code": 200, "msg": "已发送终止请求" if stopped else "已标记终止", "data": perf_result_payload(result)})


@performance_test.route("/get_run_result", methods=["POST"])
def get_run_result():
    data = request.get_json(silent=True) or {}
    run_id = int_or_none(data.get("run_id"))
    result = PerfRunResult.query.filter_by(run_id=run_id).first()
    if not result:
        return jsonify({"code": 404, "msg": "运行记录不存在", "data": None})
    return jsonify({"code": 200, "msg": "请求成功", "data": perf_result_payload(result)})


@performance_test.route("/get_run_history", methods=["POST"])
def get_run_history():
    data = request.get_json(silent=True) or {}
    page, size = _page_args(data)
    query = PerfRunResult.query
    if data.get("scenario_id") not in (None, ""):
        query = query.filter(PerfRunResult.scenario_id == int_or_none(data.get("scenario_id")))
    if data.get("run_id") not in (None, ""):
        query = query.filter(PerfRunResult.run_id == int_or_none(data.get("run_id")))
    total = query.count()
    rows = query.order_by(db.desc(PerfRunResult.created_time)).limit(size).offset((page - 1) * size).all()
    return jsonify({"code": 200, "msg": "请求成功", "data": [perf_result_payload(item) for item in rows], "total": total})
