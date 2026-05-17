# -*- coding: utf-8 -*-
import json
import time
from decimal import Decimal

import config
from app.models.test_api_models import Cases, TestSet, TestTask


def _number(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def _time_text(value):
    if not value:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _testset_status_text(status):
    return {0: "未运行", 1: "运行中", 2: "已完成"}.get(status, str(status))


def _collect_execution_state(session):
    testsets = session.query(TestSet).filter_by(is_delete=0).filter(
        TestSet.run_status.in_([1, 2])
    ).order_by(TestSet.updated_time.desc()).limit(20).all()
    tasks = session.query(TestTask).filter_by(is_delete=0).filter(
        TestTask.run_status.in_([1, 2])
    ).order_by(TestTask.updated_time.desc()).limit(20).all()
    cases = session.query(Cases).filter_by(is_delete=0).filter(
        Cases.run_status.in_(["测试中", "passed", "failed", "error"])
    ).order_by(Cases.updated_time.desc()).limit(40).all()

    return {
        "type": "execution_state",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "testsets": [
            {
                "id": item.id,
                "title": item.title,
                "project_name": item.project_name,
                "run_status": item.run_status,
                "run_status_text": _testset_status_text(item.run_status),
                "schedule": _number(item.schedule),
                "run_id": item.run_id,
                "run_type": item.run_type,
                "updated_time": _time_text(item.updated_time),
            }
            for item in testsets
        ],
        "tasks": [
            {
                "id": item.id,
                "name": item.name,
                "run_status": item.run_status,
                "run_status_text": _testset_status_text(item.run_status),
                "schedule": _number(item.schedule),
                "progress": item.progress,
                "progress_set_id": item.progress_set_id,
                "updated_time": _time_text(item.updated_time),
            }
            for item in tasks
        ],
        "cases": [
            {
                "id": item.id,
                "title": item.title,
                "case_name": item.case_name,
                "project_name": item.project_name,
                "run_status": item.run_status,
                "updated_time": _time_text(item.updated_time),
            }
            for item in cases
        ],
    }


def execution_notify(ws):
    session = config.db_work(db_path=config.AppConFig.sql_url)
    last_payload = ""
    try:
        ws.send(json.dumps({
            "type": "connected",
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "msg": "执行通知已连接"
        }, ensure_ascii=False))
        while True:
            state = _collect_execution_state(session)
            payload = json.dumps(state, ensure_ascii=False, sort_keys=True)
            if payload != last_payload:
                ws.send(payload)
                last_payload = payload
            session.expire_all()
            time.sleep(1)
    except Exception:
        pass
    finally:
        session.close()
