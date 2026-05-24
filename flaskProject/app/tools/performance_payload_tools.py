# -*- coding: utf-8 -*-
from app.models.test_api_models import PerfEndpoint
from app.tools.api_common_tools import int_or_none, loads, run_id_text, with_time


def normalize_endpoint_ids(values):
    result = []
    for value in values or []:
        endpoint_id = int_or_none(value)
        if endpoint_id and endpoint_id not in result:
            result.append(endpoint_id)
    return result


def load_ordered_endpoints(endpoint_ids):
    normalized = normalize_endpoint_ids(endpoint_ids)
    if not normalized:
        return []
    rows = PerfEndpoint.query.filter(PerfEndpoint.id.in_(normalized), PerfEndpoint.is_delete == 0).all()
    item_map = {item.id: item for item in rows}
    return [item_map[item] for item in normalized if item in item_map]


def perf_endpoint_payload(item):
    data = with_time(item.to_dict())
    data["headers"] = loads(data.get("headers"), {})
    data["params"] = loads(data.get("params"), {})
    return data


def perf_scenario_payload(item):
    data = with_time(item.to_dict())
    data["run_id"] = run_id_text(data.get("last_run_id"))
    data["endpoint_ids"] = normalize_endpoint_ids(loads(data.get("endpoint_ids"), []))
    endpoints = load_ordered_endpoints(data["endpoint_ids"])
    data["endpoint_list"] = [perf_endpoint_payload(endpoint) for endpoint in endpoints]
    return data


def perf_result_payload(item):
    data = with_time(item.to_dict())
    data["run_id"] = run_id_text(data.get("run_id"))
    data["metrics"] = loads(data.get("metrics"), {})
    return data
