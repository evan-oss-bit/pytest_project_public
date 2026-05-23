# -*- coding: utf-8 -*-
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.lib.lib_define import db


API_CASE_EXTRA_COLUMNS = {
    "pre_case_ids": "TEXT",
    "extractors": "TEXT",
    "data_rows": "TEXT",
}

API_RUNTIME_EXTRA_COLUMNS = {
    "api_suite": {
        "dependency_strategy": "VARCHAR(40) DEFAULT 'retry_on_auth_fail'",
    },
    "api_run_result": {
        "run_id": "BIGINT DEFAULT 0",
        "run_status": "VARCHAR(40) DEFAULT 'finished'",
        "status_text": "VARCHAR(191) DEFAULT ''",
    },
    "api_suite_run_result": {
        "run_id": "BIGINT DEFAULT 0",
        "run_status": "VARCHAR(40) DEFAULT 'finished'",
        "status_text": "VARCHAR(191) DEFAULT ''",
    },
    "api_report": {
        "run_id": "BIGINT DEFAULT 0",
        "report_path": "VARCHAR(1000)",
    },
    "caseresult": {
        "source_type": "VARCHAR(40) DEFAULT 'pytest'",
        "api_result_id": "INTEGER",
        "api_suite_result_id": "INTEGER",
    },
}


def ensure_api_case_columns():
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    if "api_case" not in table_names:
        return
    existing = {item.get("name") for item in inspector.get_columns("api_case")}
    with db.engine.begin() as conn:
        for name, column_type in API_CASE_EXTRA_COLUMNS.items():
            if name in existing:
                continue
            try:
                conn.execute(text("ALTER TABLE api_case ADD COLUMN {} {}".format(name, column_type)))
            except OperationalError as exc:
                if "duplicate column" not in str(exc).lower():
                    raise


def ensure_api_runtime_columns():
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    with db.engine.begin() as conn:
        for table_name, columns in API_RUNTIME_EXTRA_COLUMNS.items():
            if table_name not in table_names:
                continue
            existing = {item.get("name") for item in inspector.get_columns(table_name)}
            for name, column_type in columns.items():
                if name in existing:
                    continue
                try:
                    conn.execute(text("ALTER TABLE {} ADD COLUMN {} {}".format(table_name, name, column_type)))
                except OperationalError as exc:
                    if "duplicate column" not in str(exc).lower():
                        raise
