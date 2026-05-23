# -*- coding: utf-8 -*-
from app.lib.lib_define import db
from app.models.test_api_models import ApiCase, ApiReport
from app.tools.api_common_tools import int_or_none, json_text, loads, normalize_dependency_strategy, run_id_text, with_time
from app.tools.api_schema_tools import ensure_api_case_columns


def normalize_case_ids(values):
    result = []
    for value in values or []:
        case_id = int_or_none(value)
        if case_id and case_id not in result:
            result.append(case_id)
    return result


def load_ordered_cases(case_ids):
    normalized = normalize_case_ids(case_ids)
    if not normalized:
        return []
    rows = ApiCase.query.filter(ApiCase.id.in_(normalized), ApiCase.is_delete == 0).all()
    case_map = {item.id: item for item in rows}
    return [case_map[item] for item in normalized if item in case_map]


def case_name(case_id):
    item = ApiCase.query.filter_by(id=case_id, is_delete=0).first()
    return item.name if item else str(case_id)


def case_payload(item):
    ensure_api_case_columns()
    data = with_time(item.to_dict())
    data["headers"] = loads(data.get("headers"), {})
    data["params"] = loads(data.get("params"), {})
    data["assertions"] = loads(data.get("assertions"), [])
    data["pre_case_ids"] = loads(data.get("pre_case_ids"), [])
    data["extractors"] = loads(data.get("extractors"), [])
    data["data_rows"] = loads(data.get("data_rows"), [])
    return data


def environment_payload(item):
    data = with_time(item.to_dict())
    data["variables"] = loads(data.get("variables"), {})
    return data


def result_payload(item):
    data = with_time(item.to_dict())
    data["run_id"] = run_id_text(data.get("run_id"))
    data["request_headers"] = loads(data.get("request_headers"), {})
    data["request_params"] = loads(data.get("request_params"), {})
    data["response_headers"] = loads(data.get("response_headers"), {})
    detail = loads(data.get("assertion_result"), [])
    if isinstance(detail, dict):
        data["assertion_result"] = detail.get("assertions") or []
        data["extractor_result"] = detail.get("extractors") or []
        data["chain_results"] = detail.get("chain_results") or []
        data["context"] = detail.get("context") or {}
        data["data_results"] = detail.get("data_results") or []
    else:
        data["assertion_result"] = detail or []
        data["extractor_result"] = []
        data["chain_results"] = []
        data["context"] = {}
        data["data_results"] = []
    return data


def copy_result_fields(target, payload):
    for name in [
        "run_id",
        "environment_id", "project_id", "method", "url", "request_headers", "request_params",
        "request_body", "response_status", "response_headers", "response_body", "elapsed_ms",
        "success", "assertion_result", "error_message",
    ]:
        if name in payload and hasattr(target, name):
            value = payload.get(name)
            if name == "run_id":
                value = int_or_none(value)
            if name in ("request_headers", "request_params", "response_headers", "assertion_result") and not isinstance(value, str):
                value = json_text(value)
            setattr(target, name, value)


def suite_payload(item):
    data = with_time(item.to_dict())
    data["case_ids"] = loads(data.get("case_ids"), [])
    cases = load_ordered_cases(data["case_ids"])
    data["case_list"] = [
        {
            "id": case.id,
            "name": case.name,
            "method": case.method,
            "url": case.url,
            "last_status": case.last_status,
            "last_success": case.last_success,
        }
        for case in cases
    ]
    data["stop_on_fail"] = 1 if data.get("stop_on_fail") else 0
    data["dependency_strategy"] = normalize_dependency_strategy(data.get("dependency_strategy"))
    data["last_run_time"] = data.get("last_run_time").strftime("%Y-%m-%d %H:%M:%S") if data.get("last_run_time") else ""
    return data


def suite_result_payload(item):
    data = with_time(item.to_dict())
    data["run_id"] = run_id_text(data.get("run_id"))
    data["context"] = loads(data.get("context"), {})
    data["step_results"] = loads(data.get("step_results"), [])
    for step in data["step_results"]:
        if isinstance(step, dict) and "run_id" in step:
            step["run_id"] = run_id_text(step.get("run_id"))
    steps = [step for step in data["step_results"] if isinstance(step, dict)]
    if steps:
        missing_total = not data.get("total_count")
        if missing_total:
            data["total_count"] = len(steps)
        if data.get("pass_count") in (None, "") or missing_total:
            data["pass_count"] = len([step for step in steps if step.get("success") in (1, True, "1", "true", "True")])
        if data.get("fail_count") in (None, "") or missing_total:
            data["fail_count"] = len([step for step in steps if step.get("success") in (0, False, "0", "false", "False")])
    data["stats_text"] = "总 {} / 过 {} / 败 {}".format(
        data.get("total_count") or 0,
        data.get("pass_count") or 0,
        data.get("fail_count") or 0,
    )
    report = ApiReport.query.filter_by(
        report_type="api",
        target_type="suite",
        suite_result_id=item.id,
        is_delete=0,
    ).order_by(db.desc(ApiReport.updated_time)).first()
    if not report and item.run_id:
        report = ApiReport.query.filter_by(
            report_type="api",
            target_type="suite",
            run_id=item.run_id,
            is_delete=0,
        ).order_by(db.desc(ApiReport.updated_time)).first()
    data["report_id"] = report.id if report else None
    data["report_path"] = report.report_path if report else ""
    data["report_title"] = report.title if report else ""
    return data


def suite_result_brief(item):
    payload = suite_result_payload(item)
    total = payload.get("total_count") or 0
    passed = payload.get("pass_count") or 0
    payload["pass_rate"] = round(passed / total * 100, 2) if total else 0
    payload["failed_cases"] = [
        {
            "case_id": step.get("case_id"),
            "case_name": step.get("case_name"),
            "status": step.get("response_status"),
            "error_message": step.get("error_message"),
            "step_type_name": step.get("step_type_name"),
        }
        for step in payload.get("step_results", [])
        if isinstance(step, dict) and step.get("success") in (0, False, "0", "false", "False")
    ]
    return payload


def suite_history_compare_payload(rows):
    briefs = [suite_result_brief(item) for item in rows]
    if len(briefs) < 2:
        return {
            "current": briefs[0] if briefs else None,
            "previous": None,
            "delta": {},
            "recent": briefs,
        }
    current, previous = briefs[0], briefs[1]
    current_failed = {str(item.get("case_id") or item.get("case_name")): item for item in current.get("failed_cases", [])}
    previous_failed = {str(item.get("case_id") or item.get("case_name")): item for item in previous.get("failed_cases", [])}
    return {
        "current": current,
        "previous": previous,
        "delta": {
            "pass_rate": round((current.get("pass_rate") or 0) - (previous.get("pass_rate") or 0), 2),
            "pass_count": (current.get("pass_count") or 0) - (previous.get("pass_count") or 0),
            "fail_count": (current.get("fail_count") or 0) - (previous.get("fail_count") or 0),
            "elapsed_ms": (current.get("elapsed_ms") or 0) - (previous.get("elapsed_ms") or 0),
            "new_failed": [item for key, item in current_failed.items() if key not in previous_failed],
            "fixed": [item for key, item in previous_failed.items() if key not in current_failed],
            "still_failed": [item for key, item in current_failed.items() if key in previous_failed],
        },
        "recent": briefs,
    }


def api_report_payload(item):
    data = with_time(item.to_dict())
    data["run_id"] = run_id_text(data.get("run_id"))
    data["summary"] = loads(data.get("summary"), {})
    data["detail"] = loads(data.get("detail"), {})
    data["report_source"] = "api"
    data["report_source_name"] = "接口测试报告"
    return data


def suite_pending_steps(cases, start_index=1):
    return [
        {
            "case_id": item.id,
            "case_name": item.name,
            "success": None,
            "run_status": "pending",
            "status_text": "待执行",
            "suite_index": start_index + index,
        }
        for index, item in enumerate(cases)
    ]
