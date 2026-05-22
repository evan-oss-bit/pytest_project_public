# -*- coding: utf-8 -*-
import json

from sqlalchemy import inspect, text

from app.lib.lib_define import db
from app.models.test_api_models import (
    ApiCase,
    ApiReport,
    ApiRunResult,
    ApiSuite,
    ApiSuiteRunResult,
    CaseResult,
)


def _loads(value, default=None):
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


def _json_text(value):
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _format_time(value):
    return value.strftime("%Y%m%d%H%M%S") if value else ""


def ensure_api_result_tables():
    table_names = set(inspect(db.engine).get_table_names())
    if "api_report" not in table_names:
        db.create_all()
        table_names = set(inspect(db.engine).get_table_names())
    changed = False
    if "caseresult" in table_names:
        columns = {column["name"] for column in inspect(db.engine).get_columns("caseresult")}
        ddl_map = {
            "source_type": "ALTER TABLE caseresult ADD COLUMN source_type VARCHAR(40) DEFAULT 'pytest'",
            "api_result_id": "ALTER TABLE caseresult ADD COLUMN api_result_id INTEGER",
            "api_suite_result_id": "ALTER TABLE caseresult ADD COLUMN api_suite_result_id INTEGER",
        }
        for column_name, ddl in ddl_map.items():
            if column_name not in columns:
                db.session.execute(text(ddl))
                changed = True
        empty_count = db.session.execute(
            text("SELECT COUNT(1) FROM caseresult WHERE source_type IS NULL OR source_type = ''")
        ).scalar() or 0
        if empty_count:
            db.session.execute(text("UPDATE caseresult SET source_type = 'pytest' WHERE source_type IS NULL OR source_type = ''"))
            changed = True
    for table_name in ("api_run_result", "api_suite_run_result"):
        if table_name in table_names:
            columns = {column["name"] for column in inspect(db.engine).get_columns(table_name)}
            if "run_id" not in columns:
                db.session.execute(text("ALTER TABLE {} ADD COLUMN run_id BIGINT DEFAULT 0".format(table_name)))
                changed = True
    if "api_report" in table_names:
        columns = {column["name"] for column in inspect(db.engine).get_columns("api_report")}
        ddl_map = {
            "run_id": "ALTER TABLE api_report ADD COLUMN run_id BIGINT DEFAULT 0",
            "report_path": "ALTER TABLE api_report ADD COLUMN report_path VARCHAR(1000)",
        }
        for column_name, ddl in ddl_map.items():
            if column_name not in columns:
                db.session.execute(text(ddl))
                changed = True
    if changed:
        db.session.commit()


def _case_payload(result):
    data = result.to_dict()
    assertion_detail = _loads(result.assertion_result, {})
    if isinstance(assertion_detail, dict):
        data["assertion_result"] = assertion_detail.get("assertions") or []
        data["extractor_result"] = assertion_detail.get("extractors") or []
        data["chain_results"] = assertion_detail.get("chain_results") or []
        data["context"] = assertion_detail.get("context") or {}
    else:
        data["assertion_result"] = assertion_detail or []
        data["extractor_result"] = []
        data["chain_results"] = []
        data["context"] = {}
    data["request_headers"] = _loads(result.request_headers, {})
    data["request_params"] = _loads(result.request_params, {})
    data["response_headers"] = _loads(result.response_headers, {})
    return data


def _suite_payload(result):
    data = result.to_dict()
    data["context"] = _loads(result.context, {})
    data["step_results"] = _loads(result.step_results, [])
    return data


def _suite_result_map(limit=500):
    mapping = {}
    suite_results = ApiSuiteRunResult.query.order_by(db.desc(ApiSuiteRunResult.id)).limit(limit).all()
    for suite_result in suite_results:
        for step in _loads(suite_result.step_results, []):
            result_id = step.get("id") or step.get("result_id")
            if result_id:
                mapping[int(result_id)] = suite_result.id
    return mapping


def _copy_audit(target, source):
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


def _sync_case_result(result, suite_result_id=None):
    if CaseResult.query.filter_by(source_type="api", api_result_id=result.id).first():
        return False
    case = ApiCase.query.filter_by(id=result.case_id, is_delete=0).first() if result.case_id else None
    detail = _case_payload(result)
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
        longrepr=_json_text({
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
        file_name="",
        run_case_result="passed" if result.success else "failed",
        source_type="api",
        api_result_id=result.id,
        api_suite_result_id=suite_result_id,
        mark="接口测试",
        run_id=result.run_id or suite_result_id or result.id,
        class_name="API",
    )
    _copy_audit(row, result)
    db.session.add(row)
    return True


def _sync_case_report(result, suite_result_ids):
    if result.id in suite_result_ids:
        return False
    if ApiReport.query.filter_by(report_type="api", target_type="case", run_result_id=result.id, is_delete=0).first():
        return False
    case = ApiCase.query.filter_by(id=result.case_id, is_delete=0).first() if result.case_id else None
    detail = _case_payload(result)
    report = ApiReport(
        title="接口用例 - {} - {}".format(case.name if case else result.url or "临时请求", _format_time(result.created_time)),
        report_type="api",
        target_type="case",
        target_id=result.case_id,
        target_name=case.name if case else result.url,
        run_id=result.run_id or result.id,
        run_result_id=result.id,
        project_id=result.project_id,
        environment_id=result.environment_id,
        total_count=1,
        pass_count=1 if result.success else 0,
        fail_count=0 if result.success else 1,
        success=1 if result.success else 0,
        elapsed_ms=result.elapsed_ms,
        summary=_json_text({
            "source": "api_case",
            "status": result.response_status,
            "assertion_count": len(detail.get("assertion_result") or []),
            "extractor_count": len(detail.get("extractor_result") or []),
        }),
        detail=_json_text(detail),
    )
    _copy_audit(report, result)
    db.session.add(report)
    return True


def _sync_suite_report(result):
    if ApiReport.query.filter_by(report_type="api", target_type="suite", suite_result_id=result.id, is_delete=0).first():
        return False
    suite = ApiSuite.query.filter_by(id=result.suite_id, is_delete=0).first() if result.suite_id else None
    detail = _suite_payload(result)
    report = ApiReport(
        title="接口集合 - {} - {}".format(suite.name if suite else "集合{}".format(result.suite_id), _format_time(result.created_time)),
        report_type="api",
        target_type="suite",
        target_id=result.suite_id,
        target_name=suite.name if suite else "",
        run_id=result.run_id or result.id,
        suite_result_id=result.id,
        project_id=result.project_id,
        environment_id=result.environment_id,
        total_count=result.total_count or len(detail.get("step_results") or []),
        pass_count=result.pass_count or 0,
        fail_count=result.fail_count or 0,
        success=1 if result.success else 0,
        elapsed_ms=result.elapsed_ms,
        summary=_json_text({
            "source": "api_suite",
            "step_count": len(detail.get("step_results") or []),
            "context": detail.get("context") or {},
        }),
        detail=_json_text(detail),
    )
    _copy_audit(report, result)
    db.session.add(report)
    return True


def sync_api_execution_records(limit=500):
    ensure_api_result_tables()
    changed = False
    suite_result_ids = _suite_result_map(limit=limit)
    api_results = ApiRunResult.query.order_by(db.desc(ApiRunResult.id)).limit(limit).all()
    for result in api_results:
        if result.run_status not in (None, "", "finished", "failed"):
            continue
        suite_result_id = suite_result_ids.get(result.id)
        changed = _sync_case_result(result, suite_result_id=suite_result_id) or changed
        changed = _sync_case_report(result, suite_result_ids) or changed
    suite_results = ApiSuiteRunResult.query.order_by(db.desc(ApiSuiteRunResult.id)).limit(limit).all()
    for result in suite_results:
        if result.run_status not in (None, "", "finished", "failed"):
            continue
        changed = _sync_suite_report(result) or changed
    if changed:
        db.session.commit()
    return changed
