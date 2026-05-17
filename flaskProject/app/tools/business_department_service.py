# !/usr/bin/python3.8
# -*- coding: utf-8 -*-

import ast
from datetime import datetime

from sqlalchemy import inspect, or_, text
from sqlalchemy.exc import OperationalError

from app.lib.lib_define import db
from app.models.test_api_models import BusinessDepartment, Cases, Project, Reports, TestSet, TestTask


PROJECT_META_COLUMNS = {
    "business_department_id": "INTEGER",
    "business_department": "VARCHAR(255) DEFAULT ''",
    "environment": "VARCHAR(80) DEFAULT 'test'",
    "priority": "VARCHAR(80) DEFAULT 'P2'",
    "maint_status": "VARCHAR(80) DEFAULT 'normal'",
    "tags": "VARCHAR(500) DEFAULT ''",
    "git_repo_url": "VARCHAR(1000) DEFAULT ''",
    "git_branch": "VARCHAR(191) DEFAULT ''",
    "git_auto_sync": "INTEGER DEFAULT 1",
}


def clean_project_value(value, default=""):
    if value is None:
        return default
    return str(value).strip()


def format_time(value):
    if not value:
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def safe_id_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        data = ast.literal_eval(str(value))
        if isinstance(data, list):
            return data
        if isinstance(data, int):
            return [data]
    except Exception:
        return []
    return []


def ensure_project_meta_columns():
    inspector = inspect(db.engine)
    columns = {item.get("name") for item in inspector.get_columns("project")}
    missing = [name for name in PROJECT_META_COLUMNS if name not in columns]
    with db.engine.begin() as conn:
        for name in missing:
            try:
                conn.execute(text(f"ALTER TABLE project ADD COLUMN {name} {PROJECT_META_COLUMNS[name]}"))
            except OperationalError as e:
                error_args = getattr(getattr(e, "orig", None), "args", ())
                if error_args and error_args[0] == 1060:
                    continue
                if "duplicate column" in str(e).lower():
                    continue
                raise
        if "product_line" in columns and "business_department" in PROJECT_META_COLUMNS:
            conn.execute(text(
                "UPDATE project SET business_department = product_line "
                "WHERE (business_department IS NULL OR business_department = '') "
                "AND product_line IS NOT NULL AND product_line != ''"
            ))


def ensure_business_department_schema():
    ensure_project_meta_columns()
    BusinessDepartment.__table__.create(db.engine, checkfirst=True)
    names = [
        item[0] for item in db.session.query(Project.business_department)
        .filter(Project.business_department.isnot(None), Project.business_department != "")
        .distinct()
        .all()
    ]
    changed = False
    for name in names:
        dept = BusinessDepartment.query.filter_by(name=name, is_delete=0).first()
        if not dept:
            dept = BusinessDepartment(name=name)
            db.session.add(dept)
            db.session.flush()
            changed = True
        updated = Project.query.filter(
            Project.business_department == name,
            or_(Project.business_department_id.is_(None), Project.business_department_id == 0)
        ).update({"business_department_id": dept.id}, synchronize_session=False)
        if updated:
            changed = True
    if changed:
        db.session.commit()


def department_name_by_id(department_id):
    if not department_id:
        return ""
    dept = BusinessDepartment.query.filter_by(id=department_id, is_delete=0).first()
    return dept.name if dept else ""


def department_project_query(dept):
    return Project.query.filter(
        or_(
            Project.business_department_id == dept.id,
            Project.business_department == dept.name,
        )
    )


def task_belongs_to_project(task, project_set_ids):
    if not project_set_ids:
        return False
    set_ids = set(safe_id_list(task.test_set_ids))
    return bool(project_set_ids.intersection(set_ids))


def project_stats(project_id):
    case_count = Cases.query.filter_by(project_id=project_id, is_delete=0).count()
    testset_count = TestSet.query.filter_by(project_id=project_id, is_delete=0).count()
    running_count = TestSet.query.filter_by(project_id=project_id, is_delete=0, run_status=1).count()
    report_count = Reports.query.filter_by(project_id=project_id).count()
    project_set_ids = set([
        item.id for item in TestSet.query.with_entities(TestSet.id)
        .filter_by(project_id=project_id, is_delete=0)
        .all()
    ])
    task_count = 0
    running_task_count = 0
    for task in TestTask.query.filter_by(is_delete=0).all():
        if task_belongs_to_project(task, project_set_ids):
            task_count += 1
            if getattr(task, "run_status", 0) == 1:
                running_task_count += 1
    return {
        "case_count": case_count,
        "testset_count": testset_count,
        "task_count": task_count,
        "report_count": report_count,
        "running_count": running_count,
        "running_task_count": running_task_count,
    }


def department_stats(dept):
    projects = department_project_query(dept).all()
    project_ids = [item.id for item in projects]
    if not project_ids:
        return {
            "project_count": 0,
            "case_count": 0,
            "testset_count": 0,
            "task_count": 0,
            "report_count": 0,
            "running_count": 0,
            "running_task_count": 0,
        }
    project_set_ids = set([
        item.id for item in TestSet.query.with_entities(TestSet.id)
        .filter(TestSet.project_id.in_(project_ids), TestSet.is_delete == 0)
        .all()
    ])
    task_count = 0
    running_task_count = 0
    for task in TestTask.query.filter_by(is_delete=0).all():
        if task_belongs_to_project(task, project_set_ids):
            task_count += 1
            if getattr(task, "run_status", 0) == 1:
                running_task_count += 1
    return {
        "project_count": len(projects),
        "case_count": Cases.query.filter(Cases.project_id.in_(project_ids), Cases.is_delete == 0).count(),
        "testset_count": TestSet.query.filter(TestSet.project_id.in_(project_ids), TestSet.is_delete == 0).count(),
        "task_count": task_count,
        "report_count": Reports.query.filter(Reports.project_id.in_(project_ids)).count(),
        "running_count": TestSet.query.filter(
            TestSet.project_id.in_(project_ids),
            TestSet.is_delete == 0,
            TestSet.run_status == 1
        ).count(),
        "running_task_count": running_task_count,
    }


def department_payload(dept, include_projects=False):
    data = dept.to_dict()
    data["created_time"] = format_time(data.get("created_time"))
    data["updated_time"] = format_time(data.get("updated_time"))
    data.update(department_stats(dept))
    if include_projects:
        projects = department_project_query(dept).order_by(db.desc(Project.updated_time)).all()
        data["projects"] = [item.to_dict() for item in projects]
        for project_item in data["projects"]:
            project_item["created_time"] = format_time(project_item.get("created_time"))
            project_item["updated_time"] = format_time(project_item.get("updated_time"))
            project_item.update(project_stats(project_item.get("id")))
    return data
