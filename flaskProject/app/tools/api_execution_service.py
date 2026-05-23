# -*- coding: utf-8 -*-
import datetime
import json
import time

from app.lib.lib_define import db
from app.models.test_api_models import ApiCase, ApiEnvironment, ApiReport, ApiRunResult, ApiSuite, ApiSuiteRunResult, CaseResult
from app.tools.audit_fields import apply_run_user
from app.tools.api_assertion_tools import extract_variables, run_assertions
from app.tools.api_common_tools import api_run_id_from, format_time, int_or_none, json_text, loads, normalize_dependency_strategy, run_id_text
from app.tools.api_payload_tools import case_name, case_payload, copy_result_fields, load_ordered_cases, normalize_case_ids, result_payload, suite_pending_steps, suite_result_payload
from app.tools.api_report_tools import write_api_report_file
from app.tools.api_schema_tools import ensure_api_case_columns, ensure_api_runtime_columns
from app.tools.api_variable_tools import apply_variables, cookie_snapshot, public_context, session_for_context


def is_auth_failure(result):
    if not result:
        return False
    if result.response_status in (401, 403):
        return True
    body = result.response_body or ""
    try:
        parsed = json.loads(body)
        if int_or_none(parsed.get("code")) in (401, 403):
            return True
    except Exception:
        pass
    return False



def variables_for(environment_id):
    if not environment_id:
        return {}
    env = ApiEnvironment.query.filter_by(id=environment_id, is_delete=0).first()
    return loads(env.variables, {}) if env else {}


CASE_SOURCE_FIELDS = [
    "name",
    "project_id",
    "environment_id",
    "method",
    "url",
    "headers",
    "params",
    "body_type",
    "body",
    "assertions",
    "pre_case_ids",
    "extractors",
    "data_rows",
]


def case_source_from_request(case, data):
    source = case_payload(case) if case else {}
    for key in CASE_SOURCE_FIELDS:
        if key in data:
            source[key] = data.get(key)
    return source or data


def resolve_dependency_order_for_source(case, source):
    visiting = []
    visited = set()
    order = []

    def resolve(item, is_root=False):
        if not item:
            return
        if item.id in visited:
            return
        if item.id in visiting:
            cycle = visiting[visiting.index(item.id):] + [item.id]
            cycle_names = ["{}({})".format(case_name(case_id), case_id) for case_id in cycle]
            raise ValueError("接口依赖存在循环：" + " -> ".join(cycle_names))
        visiting.append(item.id)
        if is_root:
            pre_case_ids = normalize_case_ids(loads(source.get("pre_case_ids"), []))
        else:
            pre_case_ids = normalize_case_ids(loads(item.pre_case_ids, []))
        for pre_case_id in pre_case_ids:
            pre_case = ApiCase.query.filter_by(id=pre_case_id, is_delete=0).first()
            if not pre_case:
                raise ValueError("依赖接口不存在：{}".format(pre_case_id))
            if item.project_id and pre_case.project_id and item.project_id != pre_case.project_id:
                raise ValueError("依赖接口不属于同一个项目：{}".format(pre_case.name))
            resolve(pre_case)
        visiting.pop()
        visited.add(item.id)
        order.append(item)

    resolve(case, is_root=True)
    return order


def resolve_dependency_order(case, visiting=None, visited=None, order=None):
    if visiting is None:
        visiting = []
    if visited is None:
        visited = set()
    if order is None:
        order = []
    if not case:
        return order
    if case.id in visited:
        return order
    if case.id in visiting:
        cycle = visiting[visiting.index(case.id):] + [case.id]
        cycle_names = ["{}({})".format(case_name(item), item) for item in cycle]
        raise ValueError("接口依赖存在循环：" + " -> ".join(cycle_names))
    visiting.append(case.id)
    pre_case_ids = normalize_case_ids(loads(case.pre_case_ids, []))
    for pre_case_id in pre_case_ids:
        pre_case = ApiCase.query.filter_by(id=pre_case_id, is_delete=0).first()
        if not pre_case:
            raise ValueError("依赖接口不存在：{}".format(pre_case_id))
        if case.project_id and pre_case.project_id and case.project_id != pre_case.project_id:
            raise ValueError("依赖接口不属于同一个项目：{}".format(pre_case.name))
        resolve_dependency_order(pre_case, visiting, visited, order)
    visiting.pop()
    visited.add(case.id)
    order.append(case)
    return order


def assertion_failure_message(assertion_result):
    failed = [item for item in (assertion_result or []) if not item.get("success")]
    if not failed:
        return ""
    messages = []
    for item in failed[:3]:
        name = item.get("name") or item.get("type") or "断言"
        if item.get("error"):
            messages.append("{}：{}".format(name, item.get("error")))
        else:
            messages.append("{}失败，期望：{}，实际：{}".format(name, item.get("expected", ""), item.get("actual", "")))
    if len(failed) > 3:
        messages.append("还有{}个断言失败".format(len(failed) - 3))
    return "；".join(messages)


def execute_case_source(source, case=None, environment_id=None, context=None, timeout=30, run_id=None):
    context = context or {}
    session = session_for_context(context)
    project_id = int_or_none(source.get("project_id"))
    variables = {}
    variables.update(variables_for(environment_id or source.get("environment_id")))
    variables.update(public_context(context))
    method = (source.get("method") or "GET").upper()
    url = apply_variables(source.get("url") or "", variables)
    headers = apply_variables(source.get("headers") or {}, variables)
    params = apply_variables(source.get("params") or {}, variables)
    body_type = source.get("body_type") or "json"
    body = apply_variables(source.get("body") or "", variables)
    assertions = apply_variables(source.get("assertions") or [], variables)
    extractors = apply_variables(source.get("extractors") or [], variables)
    result = ApiRunResult(
        run_id=run_id or _new_api_run_id(),
        case_id=case.id if case else None,
        environment_id=environment_id or source.get("environment_id"),
        project_id=project_id,
        method=method,
        url=url,
        request_headers=json_text(headers),
        request_params=json_text(params),
        request_body=body,
    )
    apply_run_user(result)
    started = time.time()
    extracted = {}
    extractor_result = []
    try:
        request_kwargs = {"headers": headers, "params": params, "timeout": timeout}
        if method not in ("GET", "DELETE", "HEAD"):
            if body_type == "json" and body:
                request_kwargs["json"] = loads(body, {})
            elif body_type == "form":
                request_kwargs["data"] = loads(body, {})
            elif body_type == "raw":
                request_kwargs["data"] = body
        response = session.request(method, url, **request_kwargs)
        body_text = response.text
        elapsed_ms = int((time.time() - started) * 1000)
        result.response_status = response.status_code
        result.response_headers = json_text(dict(response.headers))
        result.response_body = body_text[:200000]
        result.elapsed_ms = elapsed_ms
        assertion_result = run_assertions(response, body_text, assertions, elapsed_ms)
        extracted, extractor_result = extract_variables(response, body_text, extractors)
        success = all(item.get("success") for item in assertion_result)
        result.success = 1 if success else 0
        if not success:
            result.error_message = assertion_failure_message(assertion_result)
        result.assertion_result = json_text({
            "assertions": assertion_result,
            "extractors": extractor_result,
            "context": public_context(context),
            "context_variables": public_context(context),
            "cookies": cookie_snapshot(session),
        })
        if case:
            case.last_status = response.status_code
            case.last_success = result.success
            case.last_elapsed_ms = result.elapsed_ms
            apply_run_user(case)
    except Exception as exc:
        result.elapsed_ms = int((time.time() - started) * 1000)
        result.success = 0
        result.error_message = str(exc)
        result.assertion_result = json_text({
            "assertions": [],
            "extractors": extractor_result,
            "context": public_context(context),
            "context_variables": public_context(context),
            "cookies": cookie_snapshot(session),
        })
    db.session.add(result)
    return result, extracted


def normalize_data_rows(value):
    rows = loads(value, [])
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list):
        return []
    normalized = []
    for index, row in enumerate(rows):
        item = dict(row) if isinstance(row, dict) else {"value": row}
        item.setdefault("_data_index", index + 1)
        normalized.append(item)
    return normalized


def run_case_chain(case, source, environment_id, timeout, run_id, base_context=None, data_row=None):
    context = dict(base_context or {})
    if data_row:
        context.update(data_row)
        context["data_row"] = data_row

    if not case:
        result, extracted = execute_case_source(source, case=None, environment_id=environment_id, context=context, timeout=timeout, run_id=run_id)
        result.run_status = "finished"
        result.status_text = "执行完成"
        db.session.flush()
        create_api_case_execution_result(result)
        payload = result_payload(result)
        payload["extracted_variables"] = extracted
        payload["context"] = public_context(context)
        if data_row:
            payload["data_row"] = data_row
            payload["data_index"] = data_row.get("_data_index")
        return result, payload

    chain = resolve_dependency_order_for_source(case, source)
    chain_results = []
    final_result = None
    for chain_case in chain:
        chain_source = source if chain_case.id == case.id else case_payload(chain_case)
        result, extracted = execute_case_source(
            chain_source,
            case=chain_case,
            environment_id=environment_id,
            context=context,
            timeout=timeout,
            run_id=run_id,
        )
        result.run_status = "finished"
        result.status_text = "执行完成"
        db.session.flush()
        create_api_case_execution_result(result)
        context.update(extracted)
        payload = result_payload(result)
        payload["case_name"] = chain_case.name
        payload["extracted_variables"] = extracted
        if data_row:
            payload["data_row"] = data_row
            payload["data_index"] = data_row.get("_data_index")
        chain_results.append(payload)
        final_result = result
        if not result.success:
            if chain_case.id != case.id:
                result.error_message = "{}\n依赖接口执行失败，依赖链执行中断".format(result.error_message or "").strip()
            break

    final_payload = result_payload(final_result)
    final_payload["chain_results"] = chain_results
    final_payload["context"] = public_context(context)
    final_payload["dependency_order"] = [{"id": item.id, "name": item.name} for item in chain]
    if data_row:
        final_payload["data_row"] = data_row
        final_payload["data_index"] = data_row.get("_data_index")
    return final_result, final_payload


def run_case_data_driven(case, source, environment_id, timeout, run_id, data_rows):
    started = time.time()
    row_payloads = []
    pass_count = 0
    fail_count = 0
    final_result = None
    for row in data_rows:
        result, payload = run_case_chain(case, source, environment_id, timeout, run_id, data_row=row)
        final_result = result
        row_payloads.append(payload)
        if result and result.success:
            pass_count += 1
        else:
            fail_count += 1
        db.session.commit()
    aggregate = {
        "id": final_result.id if final_result else None,
        "run_id": run_id_text(run_id),
        "case_id": case.id if case else None,
        "case_name": case.name if case else source.get("name") or source.get("url"),
        "run_status": "finished",
        "status_text": "执行完成",
        "success": 1 if fail_count == 0 else 0,
        "total_count": len(row_payloads),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "elapsed_ms": int((time.time() - started) * 1000),
        "data_results": row_payloads,
        "assertion_result": [],
        "extractor_result": [],
        "context": {},
    }
    if final_result:
        create_api_case_report(final_result, aggregate, title_prefix="接口数据驱动")
    db.session.commit()
    return aggregate


def run_case_payload(data):
    ensure_api_case_columns()
    ensure_api_runtime_columns()
    run_id = api_run_id_from(data)
    data["_api_run_id"] = run_id
    case = ApiCase.query.filter_by(id=data.get("id"), is_delete=0).first() if data.get("id") else None
    source = case_source_from_request(case, data)
    environment_id = int_or_none(data.get("environment_id") or source.get("environment_id"))
    timeout = min(max(int(data.get("timeout") or 30), 1), 120)
    data_rows = normalize_data_rows(source.get("data_rows") or data.get("data_rows"))
    if data.get("data_driven") and data_rows:
        return run_case_data_driven(case, source, environment_id, timeout, run_id, data_rows)

    if not case:
        result, _ = execute_case_source(source, case=None, environment_id=environment_id, context={}, timeout=timeout, run_id=run_id)
        result.run_status = "finished"
        result.status_text = "执行完成"
        db.session.flush()
        create_api_case_execution_result(result)
        create_api_case_report(result, result_payload(result), title_prefix="接口临时请求")
        db.session.commit()
        return result_payload(result)

    chain = resolve_dependency_order_for_source(case, source)
    context = {}
    chain_results = []
    final_result = None
    for chain_case in chain:
        chain_source = source if chain_case.id == case.id else case_payload(chain_case)
        result, extracted = execute_case_source(
            chain_source,
            case=chain_case,
            environment_id=environment_id,
            context=context,
            timeout=timeout,
            run_id=run_id,
        )
        result.run_status = "finished"
        result.status_text = "执行完成"
        db.session.flush()
        create_api_case_execution_result(result)
        context.update(extracted)
        payload = result_payload(result)
        payload["case_name"] = chain_case.name
        payload["extracted_variables"] = extracted
        chain_results.append(payload)
        final_result = result
        if not result.success:
            if chain_case.id != case.id:
                result.error_message = "{}\n依赖接口执行失败，依赖链执行中断".format(result.error_message or "").strip()
            db.session.commit()
            break
        db.session.commit()
    final_payload = result_payload(final_result)
    final_payload["chain_results"] = chain_results
    final_payload["context"] = context
    final_payload["dependency_order"] = [{"id": item.id, "name": item.name} for item in chain]
    create_api_case_report(final_result, final_payload)
    db.session.commit()
    return final_payload


def apply_account_info(target, account_info):
    if not account_info:
        return
    for prefix in ("created", "updated", "run"):
        id_field = "{}_by".format(prefix)
        name_field = "{}_by_name".format(prefix)
        if hasattr(target, id_field):
            setattr(target, id_field, account_info.get("id"))
        if hasattr(target, name_field):
            setattr(target, name_field, account_info.get("name"))


def create_api_case_report(result, payload=None, title_prefix="接口用例"):
    payload = payload or result_payload(result)
    case = ApiCase.query.filter_by(id=result.case_id, is_delete=0).first() if result.case_id else None
    assertions = payload.get("assertion_result") or []
    run_id = result.run_id
    if not run_id:
        raise ValueError("api case report run_id is required")
    report = ApiReport(
        title="{} - {} - {}".format(title_prefix, (case.name if case else payload.get("url") or "临时请求"), format_time(datetime.datetime.now())),
        report_type="api",
        target_type="case",
        target_id=result.case_id,
        target_name=case.name if case else payload.get("url"),
        run_id=run_id,
        run_result_id=result.id,
        project_id=result.project_id,
        environment_id=result.environment_id,
        total_count=payload.get("total_count") or 1,
        pass_count=payload.get("pass_count") if payload.get("pass_count") is not None else (1 if result.success else 0),
        fail_count=payload.get("fail_count") if payload.get("fail_count") is not None else (0 if result.success else 1),
        success=payload.get("success") if payload.get("success") is not None else (1 if result.success else 0),
        elapsed_ms=payload.get("elapsed_ms") or result.elapsed_ms,
        summary=json_text({
            "source": "api_case",
            "status": result.response_status,
            "assertion_count": len(assertions),
            "extractor_count": len(payload.get("extractor_result") or []),
        }),
        detail=json_text(payload),
    )
    report.report_path = write_api_report_file(report, payload)
    copy_audit_fields(report, result)
    db.session.add(report)
    return report


def copy_audit_fields(target, source):
    for name in (
        "created_by",
        "created_by_name",
        "updated_by",
        "updated_by_name",
        "run_by",
        "run_by_name",
    ):
        if hasattr(target, name) and hasattr(source, name):
            setattr(target, name, getattr(source, name))


def create_api_case_execution_result(result, suite_result_id=None):
    if not result or not result.id:
        return None
    exists = CaseResult.query.filter_by(source_type="api", api_result_id=result.id).first()
    if exists:
        return exists
    case = ApiCase.query.filter_by(id=result.case_id, is_delete=0).first() if result.case_id else None
    detail = result_payload(result)
    run_id = result.run_id
    if not run_id:
        raise ValueError("api case result run_id is required")
    row = CaseResult(
        case_title=(case.name if case else result.url or "接口临时请求"),
        case_name="{} {}".format(result.method or "", result.url or "").strip(),
        project_name="接口测试",
        set_id=0,
        case_id=result.case_id or 0,
        config_id="[]",
        version_id=0,
        project_id=result.project_id or 0,
        run_info=result.response_body or "",
        longrepr=json_text({
            "error_message": result.error_message,
            "assertion_result": detail.get("assertion_result") or [],
            "extractor_result": detail.get("extractor_result") or [],
            "request_method": result.method,
            "request_url": result.url,
            "request_headers": detail.get("request_headers") or {},
            "request_params": detail.get("request_params") or {},
            "request_body": result.request_body or "",
            "response_status": result.response_status,
            "response_headers": detail.get("response_headers") or {},
            "response_body": result.response_body or "",
        }),
        duration=round((result.elapsed_ms or 0) / 1000, 4),
        case_created="接口测试",
        file_path_name=result.url or "",
        file_name=result.url or "",
        run_case_result="passed" if result.success else "failed",
        source_type="api",
        api_result_id=result.id,
        api_suite_result_id=suite_result_id,
        mark="接口测试",
        run_id=run_id,
        class_name="API",
    )
    copy_audit_fields(row, result)
    db.session.add(row)
    return row


def create_api_suite_report(suite_result, suite=None):
    suite = suite or ApiSuite.query.filter_by(id=suite_result.suite_id, is_delete=0).first()
    step_results = loads(suite_result.step_results, [])
    run_id = suite_result.run_id
    if not run_id:
        raise ValueError("api suite report run_id is required")
    report = ApiReport(
        title="接口集合 - {} - run_id {} - {}".format(
            (suite.name if suite else "集合{}".format(suite_result.suite_id)),
            run_id,
            format_time(datetime.datetime.now()),
        ),
        report_type="api",
        target_type="suite",
        target_id=suite_result.suite_id,
        target_name=suite.name if suite else "",
        run_id=run_id,
        suite_result_id=suite_result.id,
        project_id=suite_result.project_id,
        environment_id=suite_result.environment_id,
        total_count=suite_result.total_count or len(step_results),
        pass_count=suite_result.pass_count or 0,
        fail_count=suite_result.fail_count or 0,
        success=1 if suite_result.success else 0,
        elapsed_ms=suite_result.elapsed_ms,
        summary=json_text({
            "source": "api_suite",
            "step_count": len(step_results),
            "context": loads(suite_result.context, {}),
        }),
        detail=json_text(suite_result_payload(suite_result)),
    )
    report.report_path = write_api_report_file(report, suite_result_payload(suite_result))
    copy_audit_fields(report, suite_result)
    db.session.add(report)
    return report


def run_case_background(app, result_id, data, account_info):
    with app.app_context():
        ensure_api_case_columns()
        ensure_api_runtime_columns()
        result = ApiRunResult.query.get(result_id)
        if not result:
            return
        started = time.time()
        try:
            result.run_status = "running"
            result.status_text = "执行中"
            db.session.commit()
            payload = run_case_payload(data)
            result = ApiRunResult.query.get(result_id)
            copy_result_fields(result, payload)
            result.run_status = "finished"
            result.status_text = "执行完成"
            result.elapsed_ms = payload.get("elapsed_ms") or int((time.time() - started) * 1000)
            result.assertion_result = json_text({
                "assertions": payload.get("assertion_result") or [],
                "extractors": payload.get("extractor_result") or [],
                "chain_results": payload.get("chain_results") or [],
                "data_results": payload.get("data_results") or [],
                "context": payload.get("context") or {},
            })
            apply_account_info(result, account_info)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            result = ApiRunResult.query.get(result_id)
            if result:
                result.run_status = "failed"
                result.status_text = "执行异常"
                result.success = 0
                result.elapsed_ms = int((time.time() - started) * 1000)
                result.error_message = str(exc)
                apply_account_info(result, account_info)
                db.session.commit()


def run_suite_background(app, suite_result_id, suite_id, environment_id, timeout, account_info, run_id=None):
    with app.app_context():
        ensure_api_runtime_columns()
        suite_result = ApiSuiteRunResult.query.get(suite_result_id)
        suite = ApiSuite.query.filter_by(id=suite_id, is_delete=0).first()
        if not suite_result or not suite:
            return
        started = time.time()
        try:
            suite_run_id = suite_result.run_id
            if not suite_run_id:
                raise ValueError("api suite run_id is required")
            suite_result.run_status = "running"
            suite_result.status_text = "执行中"
            db.session.commit()
            case_ids = normalize_case_ids(loads(suite.case_ids, []))
            cases = load_ordered_cases(case_ids)
            context = {}
            step_results = []
            pass_count = 0
            fail_count = 0
            executed_success_case_ids = set()
            dependency_strategy = normalize_dependency_strategy(suite.dependency_strategy)
            for index, case in enumerate(cases):
                try:
                    chain = resolve_dependency_order(case)
                except ValueError as exc:
                    fail_count += 1
                    step_results.append({
                        "case_id": case.id,
                        "case_name": case.name,
                        "success": 0,
                        "run_status": "failed",
                        "status_text": "依赖异常",
                        "error_message": str(exc),
                        "index": index + 1,
                    })
                    suite_result.fail_count = fail_count
                    suite_result.total_count = len(step_results)
                    suite_result.step_results = json_text(step_results + suite_pending_steps(cases[index + 1:], index + 2))
                    db.session.commit()
                    if suite.stop_on_fail:
                        break
                    continue
                for chain_case in chain:
                    is_suite_item = chain_case.id == case.id
                    if dependency_strategy != "always" and not is_suite_item and chain_case.id in executed_success_case_ids:
                        continue
                    running_step = {
                        "case_id": chain_case.id,
                        "case_name": chain_case.name,
                        "is_suite_item": is_suite_item,
                        "step_type": "case" if is_suite_item else "dependency",
                        "step_type_name": "集合接口" if is_suite_item else "前置依赖",
                        "success": None,
                        "run_status": "running",
                        "status_text": "执行中",
                        "suite_index": index + 1,
                    }
                    suite_result.total_count = len(step_results) + 1
                    suite_result.step_results = json_text(step_results + [running_step] + suite_pending_steps(cases[index + 1:], index + 2))
                    db.session.commit()
                    source = case_payload(chain_case)
                    result, extracted = execute_case_source(source, case=chain_case, environment_id=environment_id, context=context, timeout=timeout, run_id=suite_run_id)
                    if is_suite_item and dependency_strategy == "retry_on_auth_fail" and is_auth_failure(result):
                        db.session.expunge(result)
                        for refresh_case in chain[:-1]:
                            refresh_source = case_payload(refresh_case)
                            refresh_result, refresh_extracted = execute_case_source(
                                refresh_source,
                                case=refresh_case,
                                environment_id=environment_id,
                                context=context,
                                timeout=timeout,
                                run_id=suite_run_id,
                            )
                            refresh_result.run_status = "finished"
                            refresh_result.status_text = "执行完成"
                            apply_account_info(refresh_result, account_info)
                            db.session.flush()
                            create_api_case_execution_result(refresh_result, suite_result_id=suite_result_id)
                            context.update(refresh_extracted)
                            refresh_payload = result_payload(refresh_result)
                            refresh_payload["case_name"] = refresh_case.name
                            refresh_payload["case_id"] = refresh_case.id
                            refresh_payload["suite_index"] = index + 1
                            refresh_payload["is_suite_item"] = False
                            refresh_payload["step_type"] = "dependency"
                            refresh_payload["step_type_name"] = "刷新依赖"
                            refresh_payload["extracted_variables"] = refresh_extracted
                            refresh_payload["run_status"] = "finished" if refresh_result.success else "failed"
                            refresh_payload["status_text"] = "通过" if refresh_result.success else "失败"
                            step_results.append(refresh_payload)
                            if refresh_result.success:
                                pass_count += 1
                                executed_success_case_ids.add(refresh_case.id)
                            else:
                                fail_count += 1
                                if suite.stop_on_fail:
                                    break
                        if not suite.stop_on_fail or not step_results or step_results[-1].get("success"):
                            result, extracted = execute_case_source(source, case=chain_case, environment_id=environment_id, context=context, timeout=timeout, run_id=suite_run_id)
                        else:
                            break
                    result.run_status = "finished"
                    result.status_text = "执行完成"
                    apply_account_info(result, account_info)
                    db.session.flush()
                    create_api_case_execution_result(result, suite_result_id=suite_result_id)
                    context.update(extracted)
                    payload = result_payload(result)
                    payload["case_name"] = chain_case.name
                    payload["case_id"] = chain_case.id
                    payload["suite_index"] = index + 1
                    payload["is_suite_item"] = is_suite_item
                    payload["step_type"] = "case" if is_suite_item else "dependency"
                    payload["step_type_name"] = "集合接口" if is_suite_item else "前置依赖"
                    payload["extracted_variables"] = extracted
                    payload["run_status"] = "finished" if result.success else "failed"
                    payload["status_text"] = "通过" if result.success else "失败"
                    step_results.append(payload)
                    if result.success:
                        pass_count += 1
                        executed_success_case_ids.add(chain_case.id)
                    else:
                        fail_count += 1
                    suite_result.pass_count = pass_count
                    suite_result.fail_count = fail_count
                    suite_result.total_count = len(step_results)
                    suite_result.context = json_text(public_context(context))
                    suite_result.step_results = json_text(step_results + suite_pending_steps(cases[index + 1:], index + 2))
                    suite_result.elapsed_ms = int((time.time() - started) * 1000)
                    db.session.commit()
                    if not result.success and suite.stop_on_fail:
                        break
                if suite.stop_on_fail and step_results and not step_results[-1].get("success"):
                    break
            elapsed_ms = int((time.time() - started) * 1000)
            suite_result.total_count = len(step_results)
            suite_result.pass_count = pass_count
            suite_result.fail_count = fail_count
            suite_result.elapsed_ms = elapsed_ms
            suite_result.success = 1 if fail_count == 0 else 0
            suite_result.run_status = "finished"
            suite_result.status_text = "执行完成"
            suite_result.context = json_text(public_context(context))
            suite_result.step_results = json_text(step_results)
            suite.last_success = suite_result.success
            suite.last_elapsed_ms = elapsed_ms
            suite.last_run_time = datetime.datetime.now()
            apply_account_info(suite_result, account_info)
            apply_account_info(suite, account_info)
            db.session.flush()
            create_api_suite_report(suite_result, suite)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            suite_result = ApiSuiteRunResult.query.get(suite_result_id)
            if suite_result:
                suite_result.run_status = "failed"
                suite_result.status_text = "执行异常"
                suite_result.success = 0
            suite_result.error_message = str(exc)
            suite_result.elapsed_ms = int((time.time() - started) * 1000)
            apply_account_info(suite_result, account_info)
            db.session.flush()
            create_api_suite_report(suite_result, suite)
            db.session.commit()


def run_suite_payload(suite, environment_id, timeout, run_id):
    started = time.time()
    case_ids = normalize_case_ids(loads(suite.case_ids, []))
    cases = load_ordered_cases(case_ids)
    context = {}
    step_results = []
    pass_count = 0
    fail_count = 0
    executed_success_case_ids = set()
    dependency_strategy = normalize_dependency_strategy(suite.dependency_strategy)
    for index, case in enumerate(cases):
        try:
            chain = resolve_dependency_order(case)
        except ValueError as exc:
            fail_count += 1
            step_results.append({"case_id": case.id, "case_name": case.name, "success": 0, "error_message": str(exc), "index": index + 1})
            if suite.stop_on_fail:
                break
            continue
        for chain_case in chain:
            is_suite_item = chain_case.id == case.id
            if dependency_strategy != "always" and not is_suite_item and chain_case.id in executed_success_case_ids:
                continue
            source = case_payload(chain_case)
            result, extracted = execute_case_source(source, case=chain_case, environment_id=environment_id, context=context, timeout=timeout, run_id=run_id)
            if is_suite_item and dependency_strategy == "retry_on_auth_fail" and is_auth_failure(result):
                db.session.expunge(result)
                for refresh_case in chain[:-1]:
                    refresh_source = case_payload(refresh_case)
                    refresh_result, refresh_extracted = execute_case_source(
                        refresh_source,
                        case=refresh_case,
                        environment_id=environment_id,
                        context=context,
                        timeout=timeout,
                        run_id=run_id,
                    )
                    db.session.flush()
                    create_api_case_execution_result(refresh_result)
                    context.update(refresh_extracted)
                    refresh_payload = result_payload(refresh_result)
                    refresh_payload["case_name"] = refresh_case.name
                    refresh_payload["case_id"] = refresh_case.id
                    refresh_payload["suite_index"] = index + 1
                    refresh_payload["is_suite_item"] = False
                    refresh_payload["step_type"] = "dependency"
                    refresh_payload["step_type_name"] = "刷新依赖"
                    refresh_payload["extracted_variables"] = refresh_extracted
                    step_results.append(refresh_payload)
                    if refresh_result.success:
                        pass_count += 1
                        executed_success_case_ids.add(refresh_case.id)
                    else:
                        fail_count += 1
                        db.session.commit()
                        if suite.stop_on_fail:
                            break
                if not suite.stop_on_fail or not step_results or step_results[-1].get("success"):
                    result, extracted = execute_case_source(source, case=chain_case, environment_id=environment_id, context=context, timeout=timeout, run_id=run_id)
                else:
                    break
            db.session.flush()
            create_api_case_execution_result(result)
            context.update(extracted)
            payload = result_payload(result)
            payload["case_name"] = chain_case.name
            payload["case_id"] = chain_case.id
            payload["suite_index"] = index + 1
            payload["is_suite_item"] = is_suite_item
            payload["step_type"] = "case" if is_suite_item else "dependency"
            payload["step_type_name"] = "集合接口" if is_suite_item else "前置依赖"
            payload["extracted_variables"] = extracted
            step_results.append(payload)
            if result.success:
                pass_count += 1
                executed_success_case_ids.add(chain_case.id)
            else:
                fail_count += 1
                db.session.commit()
                if suite.stop_on_fail:
                    break
            db.session.commit()
        if suite.stop_on_fail and step_results and not step_results[-1].get("success"):
            break
    elapsed_ms = int((time.time() - started) * 1000)
    suite_result = ApiSuiteRunResult(
        run_id=run_id,
        suite_id=suite.id,
        project_id=suite.project_id,
        environment_id=environment_id,
        total_count=len(step_results),
        pass_count=pass_count,
        fail_count=fail_count,
        elapsed_ms=elapsed_ms,
        success=1 if fail_count == 0 else 0,
        context=json_text(public_context(context)),
        step_results=json_text(step_results),
    )
    apply_run_user(suite_result)
    suite.last_success = suite_result.success
    suite.last_elapsed_ms = elapsed_ms
    suite.last_run_time = datetime.datetime.now()
    db.session.add(suite_result)
    db.session.flush()
    CaseResult.query.filter(
        CaseResult.source_type == "api",
        CaseResult.run_id == run_id,
        CaseResult.api_suite_result_id.is_(None),
    ).update({"api_suite_result_id": suite_result.id}, synchronize_session=False)
    create_api_suite_report(suite_result, suite)
    db.session.commit()
    return suite_result_payload(suite_result)

