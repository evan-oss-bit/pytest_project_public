# !/usr/bin/python3.8
# -*- coding: utf-8 -*-

from flask import jsonify, request
from app.web_api import project
from app.models.test_api_models import *
from flasgger import swag_from
from app.commom.add_test_case import get_test_project
import config
import os
from app.lib import image
from app.tools.util import read_ini_file
from app.tools.util import clear_ini_file
import ast
import subprocess
from datetime import datetime, timedelta
import importlib
import time
from sqlalchemy import or_, func
from app.tools.auth_permissions import allowed_project_ids, filter_project_model_query, filter_task_list, is_admin, require_project_permission
from app.tools.business_department_service import (
    clean_project_value as _clean_project_value,
    department_project_query as _department_project_query,
    department_name_by_id as _department_name_by_id,
    ensure_business_department_schema as _ensure_business_department_schema,
    ensure_project_meta_columns as _ensure_project_meta_columns,
)


def _project_payload():
    _ensure_business_department_schema()
    department_id = request.json.get("business_department_id")
    department_name = _clean_project_value(request.json.get("business_department", request.json.get("product_line")))
    if department_id:
        try:
            department_id = int(department_id)
        except (TypeError, ValueError):
            department_id = None
        resolved_name = _department_name_by_id(department_id)
        if resolved_name:
            department_name = resolved_name
    elif department_name:
        dept = BusinessDepartment.query.filter_by(name=department_name, is_delete=0).first()
        if dept:
            department_id = dept.id
    return {
        "business_department_id": department_id,
        "business_department": department_name,
        "environment": _clean_project_value(request.json.get("environment"), "test") or "test",
        "priority": _clean_project_value(request.json.get("priority"), "P2") or "P2",
        "maint_status": _clean_project_value(request.json.get("maint_status"), "normal") or "normal",
        "tags": _clean_project_value(request.json.get("tags")),
        "git_repo_url": _clean_project_value(request.json.get("git_repo_url")),
        "git_branch": _clean_project_value(request.json.get("git_branch")),
        "git_auto_sync": 1 if request.json.get("git_auto_sync", 1) in (1, "1", True, "true", "True") else 0,
    }


def _fill_project_meta(project_obj, payload):
    for key, value in payload.items():
        setattr(project_obj, key, value)


def _format_time(value):
    if not value:
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _safe_id_list(value):
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


def _count_py_files(project_path):
    count = 0
    if not os.path.isdir(project_path):
        return count
    for _, _, files in os.walk(project_path):
        count += len([name for name in files if name.endswith(".py")])
    return count


def _split_nodeid(value):
    if not value:
        return "", "", ""
    parts = str(value).replace("/", os.sep).split("::")
    script_path = os.path.normpath(parts[0]) if parts else ""
    class_name = parts[1] if len(parts) > 1 else ""
    case_name = parts[2] if len(parts) > 2 else ""
    return script_path, class_name, case_name


def _normalize_nodeid(value):
    script_path, class_name, case_name = _split_nodeid(value)
    nodeid = script_path
    if class_name:
        nodeid += f"::{class_name}"
    if case_name:
        nodeid += f"::{case_name}"
    return nodeid


def _scan_project_case_nodes(project_name):
    project_path = os.path.join(config.testscriptproject, project_name)
    scanned = {}
    parse_errors = []
    if not os.path.isdir(project_path):
        return scanned, parse_errors
    for root, _, files in os.walk(project_path):
        for filename in files:
            if not filename.endswith(".py") or filename == "__init__.py" or not filename.startswith("test_"):
                continue
            script_path = os.path.join(root, filename)
            relative_path = os.path.normpath(os.path.relpath(script_path, config.home_path))
            try:
                with open(script_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=script_path)
            except Exception as e:
                parse_errors.append({
                    "path": relative_path,
                    "error": str(e),
                })
                continue
            for node in tree.body:
                if not isinstance(node, ast.ClassDef) or not node.name.startswith("Test"):
                    continue
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
                        nodeid = f"{relative_path}::{node.name}::{item.name}"
                        scanned[_normalize_nodeid(nodeid)] = {
                            "title": f"{filename}::{node.name}::{item.name}",
                            "relative_case_path": nodeid,
                            "relative_path": relative_path,
                            "class_name": node.name,
                            "case_name": ast.get_docstring(item) or "",
                            "docs": ast.get_docstring(item) or "",
                            "case": os.path.abspath(script_path) + f"::{node.name}::{item.name}",
                            "mtime": os.path.getmtime(script_path),
                            "mtime_text": _format_time(os.path.getmtime(script_path)),
                        }
    return scanned, parse_errors


def _scan_project_cases(project_name):
    scanned, parse_errors = _scan_project_case_nodes(project_name)
    return list(scanned.values()), parse_errors


def _project_script_changes(project):
    scanned, parse_errors = _scan_project_case_nodes(project.name)
    db_cases = Cases.query.filter_by(project_id=project.id, is_delete=0).all()
    db_map = {}
    for item in db_cases:
        nodeid = item.relative_case_path or item.case_path
        db_map[_normalize_nodeid(nodeid)] = item

    scanned_keys = set(scanned.keys())
    db_keys = set(db_map.keys())
    added = [scanned[key] for key in sorted(scanned_keys - db_keys)]
    deleted = []
    for key in sorted(db_keys - scanned_keys):
        item = db_map[key]
        deleted.append({
            "id": item.id,
            "title": item.title,
            "case_name": item.case_name,
            "relative_case_path": item.relative_case_path,
            "relative_path": item.relative_path,
            "updated_time": _format_time(item.updated_time),
        })

    modified_map = {}
    for key in sorted(scanned_keys & db_keys):
        item = db_map[key]
        scan_item = scanned[key]
        if not item.updated_time:
            continue
        if scan_item["mtime"] > time.mktime(item.updated_time.timetuple()) + 1:
            modified_map[scan_item["relative_path"]] = {
                "relative_path": scan_item["relative_path"],
                "mtime": scan_item["mtime_text"],
                "case_updated_time": _format_time(item.updated_time),
            }

    return {
        "project_id": project.id,
        "project_name": project.name,
        "scanned_case_count": len(scanned),
        "db_case_count": len(db_cases),
        "added_case_count": len(added),
        "deleted_case_count": len(deleted),
        "modified_script_count": len(modified_map),
        "parse_error_count": len(parse_errors),
        "added_cases": added[:50],
        "deleted_cases": deleted[:50],
        "modified_scripts": list(modified_map.values())[:50],
        "parse_errors": parse_errors[:20],
        "checked_time": _format_time(datetime.now()),
    }


def _project_health(project, file_status=None, stats=None, script_changes=None):
    file_status = file_status or _project_file_status(project.name)
    stats = stats or _project_stats(project.id)
    script_changes = script_changes or _project_script_changes(project)
    checks = []

    def add_check(key, name, status, message):
        checks.append({
            "key": key,
            "name": name,
            "status": status,
            "message": message,
        })

    add_check(
        "project_dir",
        "项目目录",
        "ok" if file_status.get("exists") else "error",
        "项目目录存在" if file_status.get("exists") else "项目目录不存在",
    )
    add_check(
        "data_ini",
        "data.ini",
        "ok" if file_status.get("has_data_ini") else "error",
        "data.ini 存在" if file_status.get("has_data_ini") else "data.ini 缺失",
    )
    add_check(
        "pytest_ini",
        "pytest.ini",
        "ok" if file_status.get("has_pytest_ini") else "warning",
        "pytest.ini 存在" if file_status.get("has_pytest_ini") else "pytest.ini 未配置",
    )
    add_check(
        "script_files",
        "脚本文件",
        "ok" if file_status.get("py_file_count", 0) > 0 else "error",
        f"Python 脚本文件 {file_status.get('py_file_count', 0)} 个",
    )
    add_check(
        "cases",
        "平台用例",
        "ok" if stats.get("case_count", 0) > 0 else "error",
        f"平台用例 {stats.get('case_count', 0)} 条",
    )
    add_check(
        "parse_errors",
        "脚本解析",
        "ok" if script_changes.get("parse_error_count", 0) == 0 else "error",
        f"解析错误 {script_changes.get('parse_error_count', 0)} 个",
    )
    change_count = (
            script_changes.get("added_case_count", 0)
            + script_changes.get("deleted_case_count", 0)
            + script_changes.get("modified_script_count", 0)
    )
    add_check(
        "script_changes",
        "脚本同步",
        "ok" if change_count == 0 else "warning",
        f"待处理变更 {change_count} 项",
    )
    last_pass_rate = stats.get("last_pass_rate")
    if last_pass_rate is None:
        run_status = "warning"
        run_message = "暂无执行记录"
    elif last_pass_rate >= 90:
        run_status = "ok"
        run_message = f"最近通过率 {last_pass_rate:.2f}%"
    elif last_pass_rate >= 70:
        run_status = "warning"
        run_message = f"最近通过率 {last_pass_rate:.2f}%"
    else:
        run_status = "error"
        run_message = f"最近通过率 {last_pass_rate:.2f}%"
    add_check("last_run", "最近执行", run_status, run_message)

    error_count = len([item for item in checks if item.get("status") == "error"])
    warning_count = len([item for item in checks if item.get("status") == "warning"])
    if error_count:
        status = "error"
        label = "异常"
    elif warning_count:
        status = "warning"
        label = "需关注"
    else:
        status = "ok"
        label = "健康"

    return {
        "status": status,
        "label": label,
        "score": max(0, 100 - error_count * 25 - warning_count * 10),
        "error_count": error_count,
        "warning_count": warning_count,
        "checks": checks,
        "summary": f"{label}，{error_count} 个异常，{warning_count} 个提醒",
    }


def _project_failure_trend(project_id, limit=5):
    reports = Reports.query.filter_by(project_id=project_id).order_by(
        db.desc(Reports.updated_time)
    ).limit(limit).all()
    ordered_reports = list(reversed(reports))
    pass_rates = []
    fail_counts = []
    error_counts = []
    report_names = []
    run_times = []
    for item in ordered_reports:
        pass_rates.append(float(item.pass_rate) if item.pass_rate is not None else 0)
        fail_counts.append(int(item.fail_count) if item.fail_count is not None else 0)
        error_counts.append(int(item.error_count) if item.error_count is not None else 0)
        report_names.append(item.title)
        run_times.append(_format_time(item.updated_time))

    consecutive_failed = 0
    for item in reports:
        fail_count = int(item.fail_count) if item.fail_count is not None else 0
        error_count = int(item.error_count) if item.error_count is not None else 0
        if fail_count + error_count > 0:
            consecutive_failed += 1
        else:
            break

    return {
        "pass_rates": pass_rates,
        "fail_counts": fail_counts,
        "error_counts": error_counts,
        "report_names": report_names,
        "run_times": run_times,
        "consecutive_failed": consecutive_failed,
        "is_continuous_failed": consecutive_failed >= 2,
        "latest_failed": bool(fail_counts[-1] + error_counts[-1]) if fail_counts else False,
        "sample_count": len(reports),
    }


def _project_stats(project_id):
    case_count = Cases.query.filter_by(project_id=project_id, is_delete=0).count()
    testset_count = TestSet.query.filter_by(project_id=project_id, is_delete=0).count()
    running_count = TestSet.query.filter_by(project_id=project_id, is_delete=0, run_status=1).count()
    report_count = Reports.query.filter_by(project_id=project_id).count()
    last_report = Reports.query.filter_by(project_id=project_id).order_by(db.desc(Reports.updated_time)).first()
    failure_trend = _project_failure_trend(project_id)
    project_set_ids = [
        item.id for item in TestSet.query.with_entities(TestSet.id).filter_by(project_id=project_id, is_delete=0).all()
    ]
    project_set_ids = set(project_set_ids)
    task_count = 0
    running_task_count = 0
    if project_set_ids:
        tasks = TestTask.query.filter_by(is_delete=0).all()
        for task in tasks:
            set_ids = set(_safe_id_list(task.test_set_ids))
            if project_set_ids.intersection(set_ids):
                task_count += 1
                if task.run_status == 1:
                    running_task_count += 1
    return {
        "case_count": case_count,
        "testset_count": testset_count,
        "task_count": task_count,
        "report_count": report_count,
        "running_count": running_count,
        "running_task_count": running_task_count,
        "last_run_id": last_report.run_id if last_report else None,
        "last_pass_rate": float(last_report.pass_rate) if last_report and last_report.pass_rate is not None else None,
        "last_report_name": last_report.title if last_report else "",
        "last_report_path": last_report.report_path if last_report else "",
        "last_all_count": int(last_report.all_count) if last_report and last_report.all_count is not None else 0,
        "last_pass_count": int(last_report.pass_count) if last_report and last_report.pass_count is not None else 0,
        "last_fail_count": int(last_report.fail_count) if last_report and last_report.fail_count is not None else 0,
        "last_error_count": int(last_report.error_count) if last_report and last_report.error_count is not None else 0,
        "last_case_all_time": float(
            last_report.case_all_time) if last_report and last_report.case_all_time is not None else 0,
        "last_run_time": _format_time(last_report.updated_time) if last_report else "",
        "last_execution_summary": {
            "run_id": last_report.run_id if last_report else None,
            "report_name": last_report.title if last_report else "",
            "report_path": last_report.report_path if last_report else "",
            "pass_rate": float(last_report.pass_rate) if last_report and last_report.pass_rate is not None else None,
            "all_count": int(last_report.all_count) if last_report and last_report.all_count is not None else 0,
            "pass_count": int(last_report.pass_count) if last_report and last_report.pass_count is not None else 0,
            "fail_count": int(last_report.fail_count) if last_report and last_report.fail_count is not None else 0,
            "error_count": int(last_report.error_count) if last_report and last_report.error_count is not None else 0,
            "case_all_time": float(
                last_report.case_all_time) if last_report and last_report.case_all_time is not None else 0,
            "run_time": _format_time(last_report.updated_time) if last_report else "",
        },
        "failure_trend": failure_trend,
    }


def _home_empty_stats():
    empty_trend = [
        {'hour': f'{hour:02d}:00', 'run_count': 0, 'pass_rate': 0, 'failed_count': 0}
        for hour in range(24)
    ]
    return {
        'project_count': 0,
        'case_count': 0,
        'testset_count': 0,
        'task_count': 0,
        'today_run_count': 0,
        'today_pass_rate': 0,
        'running_count': 0,
        'running_testset_count': 0,
        'running_task_count': 0,
        'failed_pending_count': 0,
        'today_trend': empty_trend,
        'running_testsets': [],
        'running_tasks': [],
        'recent_failures': [],
        'continuous_failures': [],
        'project_health_summary': {'ok': 0, 'warning': 0, 'error': 0},
        'project_health_items': [],
        'department_quality': [],
        'process_pool_status': _empty_process_pool_status(),
    }


def _empty_process_pool_status():
    empty_detail = {
        'name': '',
        'max_workers': 0,
        'running': 0,
        'queued': 0,
        'idle': 0,
        'pending': 0,
    }
    return {
        'running': 0,
        'queued': 0,
        'idle': 0,
        'max_workers': 0,
        'pending': 0,
        'testset': dict(empty_detail, name='测试集进程池'),
        'testtask': dict(empty_detail, name='测试任务进程池'),
    }


def _executor_pool_status(module_name, display_name):
    try:
        module = importlib.import_module(module_name)
        executor = getattr(module, "executor", None)
    except Exception:
        executor = None
    if executor is None:
        return {
            'name': display_name,
            'max_workers': 0,
            'running': 0,
            'queued': 0,
            'idle': 0,
            'pending': 0,
        }
    max_workers = int(getattr(executor, "_max_workers", 0) or 0)
    pending_items = getattr(executor, "_pending_work_items", None) or {}
    pending = len(pending_items)
    running = min(pending, max_workers)
    queued = max(pending - max_workers, 0)
    idle = max(max_workers - running, 0)
    return {
        'name': display_name,
        'max_workers': max_workers,
        'running': running,
        'queued': queued,
        'idle': idle,
        'pending': pending,
    }


def _process_pool_status():
    testset_status = _executor_pool_status("app.web_api.app_test_testset", "测试集进程池")
    testtask_status = _executor_pool_status("app.web_api.app_test_testtask", "测试任务进程池")
    return {
        'running': testset_status.get('running', 0) + testtask_status.get('running', 0),
        'queued': testset_status.get('queued', 0) + testtask_status.get('queued', 0),
        'idle': testset_status.get('idle', 0) + testtask_status.get('idle', 0),
        'max_workers': testset_status.get('max_workers', 0) + testtask_status.get('max_workers', 0),
        'pending': testset_status.get('pending', 0) + testtask_status.get('pending', 0),
        'testset': testset_status,
        'testtask': testtask_status,
    }


def _recent_failure_payload(report):
    return {
        'id': report.id,
        'title': report.title,
        'project_id': report.project_id,
        'project_name': report.project_name,
        'set_id': report.set_id,
        'run_id': report.run_id,
        'all_count': int(report.all_count or 0),
        'pass_count': int(report.pass_count or 0),
        'fail_count': int(report.fail_count or 0),
        'error_count': int(report.error_count or 0),
        'pass_rate': float(report.pass_rate) if report.pass_rate is not None else 0,
        'updated_time': _format_time(report.updated_time),
    }


def _light_project_health(project, stats=None):
    stats = stats or _project_stats(project.id)
    warnings = []
    errors = []
    last_pass_rate = stats.get("last_pass_rate")
    failed_count = int(stats.get("last_fail_count") or 0) + int(stats.get("last_error_count") or 0)

    if stats.get("case_count", 0) <= 0:
        errors.append("暂无用例")
    if stats.get("testset_count", 0) <= 0:
        warnings.append("暂无测试集")
    if stats.get("report_count", 0) <= 0:
        warnings.append("暂无执行记录")
    elif failed_count > 0:
        errors.append(f"最近执行失败/错误 {failed_count} 个")
    if last_pass_rate is not None:
        if last_pass_rate < 70:
            errors.append(f"最近通过率 {last_pass_rate:.2f}%")
        elif last_pass_rate < 90:
            warnings.append(f"最近通过率 {last_pass_rate:.2f}%")

    failure_trend = stats.get("failure_trend") or {}
    consecutive_failed = int(failure_trend.get("consecutive_failed") or 0)
    if consecutive_failed >= 2:
        errors.append(f"连续失败 {consecutive_failed} 次")

    if errors:
        status = "error"
        label = "异常"
    elif warnings:
        status = "warning"
        label = "需关注"
    else:
        status = "ok"
        label = "健康"

    return {
        'project_id': project.id,
        'project_name': project.name,
        'business_department': project.business_department or "",
        'status': status,
        'label': label,
        'summary': "；".join(errors + warnings) or "最近状态正常",
        'last_pass_rate': last_pass_rate,
        'last_run_id': stats.get("last_run_id"),
        'last_run_time': stats.get("last_run_time") or "",
        'case_count': stats.get("case_count", 0),
        'testset_count': stats.get("testset_count", 0),
        'report_count': stats.get("report_count", 0),
        'consecutive_failed': consecutive_failed,
    }


def _department_quality_payload(dept, allowed_ids, since_time):
    projects = _department_project_query(dept).all()
    project_ids = [item.id for item in projects]
    if allowed_ids is not None:
        allowed_set = set(allowed_ids)
        project_ids = [item for item in project_ids if item in allowed_set]
    if not project_ids:
        return {
            'id': dept.id,
            'name': dept.name,
            'project_count': 0,
            'report_count': 0,
            'all_count': 0,
            'pass_count': 0,
            'fail_count': 0,
            'error_count': 0,
            'pass_rate': 0,
        }
    summary = Reports.query.filter(
        Reports.project_id.in_(project_ids),
        Reports.created_time >= since_time,
    ).with_entities(
        func.count(Reports.id),
        func.coalesce(func.sum(Reports.all_count), 0),
        func.coalesce(func.sum(Reports.pass_count), 0),
        func.coalesce(func.sum(Reports.fail_count), 0),
        func.coalesce(func.sum(Reports.error_count), 0),
    ).first()
    all_count = int(summary[1] or 0)
    pass_count = int(summary[2] or 0)
    return {
        'id': dept.id,
        'name': dept.name,
        'project_count': len(project_ids),
        'report_count': int(summary[0] or 0),
        'all_count': all_count,
        'pass_count': pass_count,
        'fail_count': int(summary[3] or 0),
        'error_count': int(summary[4] or 0),
        'pass_rate': round(pass_count / all_count * 100, 2) if all_count else 0,
    }


def _project_file_status(project_name):
    project_path = os.path.join(config.testscriptproject, project_name)
    data_ini_path = os.path.join(project_path, config.config_name)
    pytest_ini_path = os.path.join(project_path, "pytest.ini")
    return {
        "path": project_path,
        "exists": os.path.isdir(project_path),
        "has_data_ini": os.path.exists(data_ini_path),
        "has_pytest_ini": os.path.exists(pytest_ini_path),
        "py_file_count": _count_py_files(project_path),
        "mtime": _format_time(os.path.getmtime(project_path)) if os.path.exists(project_path) else "",
    }


def _project_root_path(project_name):
    script_root = os.path.abspath(config.testscriptproject)
    project_path = os.path.abspath(os.path.join(script_root, project_name))
    if not project_path.startswith(script_root + os.sep) and project_path != script_root:
        return None
    return project_path


def _run_git(project_path, args, timeout=180):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
        return {
            "returncode": result.returncode,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
        }
    except FileNotFoundError:
        return {"returncode": 127, "stdout": "", "stderr": "未找到 git 命令，请先安装 Git 并加入 PATH"}
    except subprocess.TimeoutExpired:
        return {"returncode": 124, "stdout": "", "stderr": "Git 命令执行超时"}


def _run_git_command(args, timeout=60, cwd=None):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
        return {
            "returncode": result.returncode,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
        }
    except FileNotFoundError:
        return {"returncode": 127, "stdout": "", "stderr": "未找到 git 命令，请先安装 Git 并加入 PATH"}
    except subprocess.TimeoutExpired:
        return {"returncode": 124, "stdout": "", "stderr": "Git 命令执行超时"}


def _parse_remote_branches(output):
    branches = []
    seen = set()
    for line in (output or "").splitlines():
        line = line.strip()
        if not line or "refs/heads/" not in line:
            continue
        branch = line.split("refs/heads/", 1)[1].strip()
        if not branch or branch in seen:
            continue
        seen.add(branch)
        branches.append(branch)
    return branches


def _project_git_status(project):
    project_path = _project_root_path(project.name)
    status = {
        "enabled": bool(project.git_repo_url or project.git_branch),
        "is_git_repo": False,
        "repo_url": project.git_repo_url or "",
        "branch": project.git_branch or "",
        "commit": "",
        "dirty": False,
        "message": "",
    }
    if not project_path or not os.path.isdir(project_path):
        status["message"] = "项目目录不存在"
        return status
    if not os.path.isdir(os.path.join(project_path, ".git")):
        status["message"] = "项目目录不是 Git 仓库"
        return status
    status["is_git_repo"] = True
    remote = _run_git(project_path, ["config", "--get", "remote.origin.url"], timeout=15)
    branch = _run_git(project_path, ["rev-parse", "--abbrev-ref", "HEAD"], timeout=15)
    commit = _run_git(project_path, ["rev-parse", "--short", "HEAD"], timeout=15)
    dirty = _run_git(project_path, ["status", "--porcelain"], timeout=15)
    if remote.get("returncode") == 0 and remote.get("stdout"):
        status["repo_url"] = remote.get("stdout")
    if branch.get("returncode") == 0 and branch.get("stdout"):
        status["branch"] = branch.get("stdout")
    if commit.get("returncode") == 0 and commit.get("stdout"):
        status["commit"] = commit.get("stdout")
    if dirty.get("returncode") == 0:
        status["dirty"] = bool(dirty.get("stdout"))
    status["enabled"] = True
    status["message"] = "Git 仓库正常"
    return status


def _build_project_tree(root_path, current_path=None, depth=0, max_depth=8):
    current_path = current_path or root_path
    if depth > max_depth:
        return []
    exclude_dirs = {".git", ".idea", ".vscode", "__pycache__", ".pytest_cache", "node_modules", "venv", ".venv"}
    try:
        entries = os.listdir(current_path)
    except Exception:
        return []
    dirs = []
    files = []
    for name in entries:
        full_path = os.path.join(current_path, name)
        if os.path.isdir(full_path):
            if name in exclude_dirs:
                continue
            dirs.append(name)
        else:
            files.append(name)
    tree = []
    for name in sorted(dirs, key=lambda item: item.lower()):
        full_path = os.path.join(current_path, name)
        tree.append({
            "label": name,
            "path": os.path.relpath(full_path, root_path),
            "type": "dir",
            "mtime": _format_time(os.path.getmtime(full_path)) if os.path.exists(full_path) else "",
            "children": _build_project_tree(root_path, full_path, depth + 1, max_depth),
        })
    for name in sorted(files, key=lambda item: item.lower()):
        full_path = os.path.join(current_path, name)
        ext = os.path.splitext(name)[1].lower().replace(".", "")
        tree.append({
            "label": name,
            "path": os.path.relpath(full_path, root_path),
            "type": "file",
            "ext": ext,
            "size": os.path.getsize(full_path) if os.path.exists(full_path) else 0,
            "mtime": _format_time(os.path.getmtime(full_path)) if os.path.exists(full_path) else "",
        })
    return tree


def _safe_project_file_path(project_name, relative_path):
    root_path = os.path.abspath(os.path.join(config.testscriptproject, project_name))
    target_path = os.path.abspath(os.path.join(root_path, relative_path or ""))
    if not target_path.startswith(root_path + os.sep) and target_path != root_path:
        return None, root_path, "文件路径不合法"
    if not os.path.isfile(target_path):
        return None, root_path, "文件不存在"
    return target_path, root_path, None


def _is_previewable_file(file_path):
    preview_exts = {
        ".py", ".txt", ".ini", ".cfg", ".conf", ".json", ".yaml", ".yml",
        ".md", ".csv", ".xml", ".html", ".css", ".js", ".log"
    }
    return os.path.splitext(file_path)[1].lower() in preview_exts


def _task_belongs_to_project(task, project_set_ids):
    if not project_set_ids:
        return False
    set_ids = set(_safe_id_list(task.test_set_ids))
    return bool(project_set_ids.intersection(set_ids))


def _sync_project_script_cases(query, project_id, description="", script_type=1, version_id=0, module_id=None):
    scanned_cases, parse_errors = _scan_project_cases(query.name)
    if not scanned_cases:
        return None, {
            "code": 404,
            "msg": f"{query.name}项目下没有可同步的pytest用例",
            "data": {
                "cases": [],
                "parse_errors": parse_errors,
            },
        }

    unique_cases = {}
    for item in scanned_cases:
        unique_cases[item.get("case")] = item
    scanned_cases = list(unique_cases.values())
    case_paths = [item.get("case") for item in scanned_cases if item.get("case")]
    relative_case_paths = [item.get("relative_case_path") for item in scanned_cases if item.get("relative_case_path")]
    existing_cases = Cases.query.filter(
        or_(Cases.case_path.in_(case_paths), Cases.relative_case_path.in_(relative_case_paths))
    ).all()
    existing_by_case_path = {item.case_path: item for item in existing_cases if item.case_path}
    existing_by_relative_path = {item.relative_case_path: item for item in existing_cases if item.relative_case_path}

    created_count = 0
    updated_count = 0
    for case_path in scanned_cases:
        case = existing_by_relative_path.get(case_path.get("relative_case_path"))
        if not case:
            case = existing_by_case_path.get(case_path.get("case"))
        if case and case.is_delete:
            case.is_delete = 0
        if case:
            updated_count += 1
            case.case_name = case_path.get("docs")
            case.title = case_path.get("title")
            case.type = script_type
            if description:
                case.remark = description
            case.project_id = project_id
            case.project_name = query.name
            case.module_id = case.module_id or module_id
            case.version_id = case.version_id or version_id
            case.relative_case_path = case_path.get("relative_case_path")
            case.case_path = case_path.get("case")
            case.relative_path = case_path.get("relative_path")
            case.previous_level = case_path.get("previous_level")
            case.class_name = case_path.get("class_name")
            case.relative_cla_case_path = case_path.get("relative_cla_case_path")
        else:
            created_count += 1
            case = Cases(
                project_id=project_id,
                module_id=module_id,
                version_id=version_id,
                project_name=query.name,
                type=script_type,
                remark=description,
                relative_case_path=case_path.get("relative_case_path"),
                case_path=case_path.get("case"),
                title=case_path.get("title"),
                case_name=case_path.get("docs"),
                relative_path=case_path.get("relative_path"),
                previous_level=case_path.get("previous_level"),
                class_name=case_path.get("class_name"),
                relative_cla_case_path=case_path.get("relative_cla_case_path"),
            )
            db.session.add(case)
            existing_by_case_path[case.case_path] = case
            existing_by_relative_path[case.relative_case_path] = case
    db.session.flush()
    ids = [case.id for case in existing_by_case_path.values() if case.case_path in case_paths]
    db.session.commit()
    return {
        "project_id": project_id,
        "project_name": query.name,
        "scanned_count": len(scanned_cases),
        "created_count": created_count,
        "updated_count": updated_count,
        "parse_error_count": len(parse_errors),
        "parse_errors": parse_errors,
        "ids": ids,
    }, None


@project.route('/get_project_info', methods=["POST"])
@swag_from('../apidocs/get_project_info.yml')
def get_project_info():
    """获取项目列表"""
    _ensure_project_meta_columns(backfill_legacy=False)
    page_no = request.json.get("page_no", request.json.get("page", 0))
    page_size = request.json.get("page_size", 100)
    name = request.json.get("name", "")
    business_department_id = request.json.get("business_department_id")
    business_department = _clean_project_value(request.json.get("business_department"))
    name = name.strip()
    base_query = filter_project_model_query(Project.query, Project)
    if name:
        base_query = base_query.filter(Project.name.like(f"%{name}%"))
    if business_department_id:
        base_query = base_query.filter(Project.business_department_id == business_department_id)
    if business_department:
        base_query = base_query.filter(Project.business_department == business_department)
    total = base_query.count()
    if name or business_department or business_department_id:
        query = base_query.order_by(db.desc(Project.updated_time)).all()
    else:
        query = base_query.order_by(db.desc(Project.updated_time)).limit(page_size).offset(page_no)
    if query:
        query = [i.to_dict() for i in query]
    for i in query:
        if i.get("updated_time"):
            i.update({"updated_time": _format_time(i.get("updated_time"))})
        if i.get("created_time"):
            i.update({"created_time": _format_time(i.get("created_time"))})
        project_obj = Project.query.filter_by(id=i.get("id")).first()
        stats = _project_stats(i.get("id"))
        i.update(stats)
        if project_obj:
            file_status = _project_file_status(project_obj.name)
            changes = _project_script_changes(project_obj)
            health = _project_health(project_obj, file_status=file_status, stats=stats, script_changes=changes)
            i.update({
                "health_status": health.get("status"),
                "health_label": health.get("label"),
                "health_score": health.get("score"),
                "health_summary": health.get("summary"),
                "script_added_count": changes.get("added_case_count", 0),
                "script_deleted_count": changes.get("deleted_case_count", 0),
                "script_modified_count": changes.get("modified_script_count", 0),
                "script_parse_error_count": changes.get("parse_error_count", 0),
                "script_scanned_case_count": changes.get("scanned_case_count", 0),
                "git_status": _project_git_status(project_obj),
            })
    return_dict = {'code': 200, 'msg': '请求成功', 'data': query, 'total': total}
    return jsonify(return_dict)


@project.route('/get_project_dashboard', methods=["POST"])
@swag_from('../apidocs/get_project_dashboard.yml')
def get_project_dashboard():
    """获取项目总览"""
    _ensure_project_meta_columns()
    project_id = request.json.get("id") or request.json.get("project_id")
    if not project_id:
        return jsonify({'code': 404, 'msg': '缺少项目id', 'data': None})
    permission_error = require_project_permission(project_id, "view")
    if permission_error:
        return permission_error
    query = Project.query.filter_by(id=project_id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '项目不存在', 'data': None})

    project_info = query.to_dict()
    project_info["created_time"] = _format_time(project_info.get("created_time"))
    project_info["updated_time"] = _format_time(project_info.get("updated_time"))
    stats = _project_stats(query.id)
    file_status = _project_file_status(query.name)
    script_changes = _project_script_changes(query)
    health = _project_health(query, file_status=file_status, stats=stats, script_changes=script_changes)

    recent_reports = Reports.query.filter_by(project_id=query.id).order_by(
        db.desc(Reports.updated_time)
    ).limit(5).all()
    recent_reports = [
        {
            "id": item.id,
            "title": item.title,
            "report_path": item.report_path,
            "run_id": item.run_id,
            "pass_rate": float(item.pass_rate) if item.pass_rate is not None else None,
            "all_count": item.all_count,
            "pass_count": item.pass_count,
            "fail_count": item.fail_count,
            "error_count": item.error_count,
            "case_all_time": float(item.case_all_time) if item.case_all_time is not None else None,
            "created_by_name": item.created_by_name,
            "updated_by_name": item.updated_by_name,
            "run_by_name": item.run_by_name,
            "updated_time": _format_time(item.updated_time),
        }
        for item in recent_reports
    ]

    running_testsets = TestSet.query.filter_by(project_id=query.id, is_delete=0, run_status=1).order_by(
        db.desc(TestSet.updated_time)
    ).limit(10).all()
    running_testsets = [
        {
            "id": item.id,
            "title": item.title,
            "schedule": item.schedule,
            "run_id": item.run_id,
            "run_type": item.run_type,
            "created_by_name": item.created_by_name,
            "updated_by_name": item.updated_by_name,
            "run_by_name": item.run_by_name,
            "updated_time": _format_time(item.updated_time),
        }
        for item in running_testsets
    ]

    project_set_ids = set([
        item.id for item in TestSet.query.with_entities(TestSet.id).filter_by(project_id=query.id, is_delete=0).all()
    ])
    running_tasks = []
    for item in TestTask.query.filter_by(is_delete=0, run_status=1).order_by(db.desc(TestTask.updated_time)).all():
        if _task_belongs_to_project(item, project_set_ids):
            running_tasks.append({
                "id": item.id,
                "name": item.name,
                "schedule": item.schedule,
                "progress": item.progress,
                "run_id": item.run_id,
                "created_by_name": item.created_by_name,
                "updated_by_name": item.updated_by_name,
                "run_by_name": item.run_by_name,
                "updated_time": _format_time(item.updated_time),
            })
        if len(running_tasks) >= 10:
            break

    return jsonify({
        'code': 200,
        'msg': '请求成功',
        'data': {
            "project": project_info,
            "stats": stats,
            "file_status": file_status,
            "git_status": _project_git_status(query),
            "script_changes": script_changes,
            "health": health,
            "recent_reports": recent_reports,
            "running_testsets": running_testsets,
            "running_tasks": running_tasks,
        }
    })


@project.route('/check_script_changes', methods=["POST"])
@swag_from('../apidocs/check_script_changes.yml')
def check_script_changes():
    """检测脚本文件和平台用例之间的差异"""
    _ensure_project_meta_columns()
    project_id = request.json.get("id") or request.json.get("project_id")
    if not project_id:
        return jsonify({'code': 404, 'msg': '缺少项目id', 'data': None})
    permission_error = require_project_permission(project_id, "view") if project_id else None
    if permission_error:
        return permission_error
    query = Project.query.filter_by(id=project_id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '项目不存在', 'data': None})
    return jsonify({
        'code': 200,
        'msg': '请求成功',
        'data': _project_script_changes(query),
    })


@project.route('/get_project_tree', methods=["POST"])
@swag_from('../apidocs/get_project_tree.yml')
def get_project_tree():
    """获取脚本项目文件树"""
    _ensure_project_meta_columns()
    project_id = request.json.get("id") or request.json.get("project_id")
    if not project_id:
        return jsonify({'code': 404, 'msg': '缺少项目id', 'data': None})
    permission_error = require_project_permission(project_id, "view") if project_id else None
    if permission_error:
        return permission_error
    query = Project.query.filter_by(id=project_id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '项目不存在', 'data': None})
    root_path = os.path.abspath(os.path.join(config.testscriptproject, query.name))
    script_root = os.path.abspath(config.testscriptproject)
    if not root_path.startswith(script_root + os.sep):
        return jsonify({'code': 400, 'msg': '项目路径不合法', 'data': None})
    if not os.path.isdir(root_path):
        return jsonify({'code': 404, 'msg': '项目目录不存在', 'data': None})
    return jsonify({
        'code': 200,
        'msg': '请求成功',
        'data': {
            "name": query.name,
            "path": root_path,
            "tree": _build_project_tree(root_path),
        },
    })


@project.route('/preview_project_file', methods=["POST"])
@swag_from('../apidocs/preview_project_file.yml')
def preview_project_file():
    """预览脚本项目内的文本文件"""
    _ensure_project_meta_columns()
    project_id = request.json.get("id") or request.json.get("project_id")
    relative_path = request.json.get("path", "")
    if not project_id:
        return jsonify({'code': 404, 'msg': '缺少项目id', 'data': None})
    permission_error = require_project_permission(project_id, "view") if project_id else None
    if permission_error:
        return permission_error
    query = Project.query.filter_by(id=project_id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '项目不存在', 'data': None})
    file_path, root_path, error_msg = _safe_project_file_path(query.name, relative_path)
    if error_msg:
        return jsonify({'code': 404, 'msg': error_msg, 'data': None})
    if not _is_previewable_file(file_path):
        return jsonify({'code': 400, 'msg': '该文件类型暂不支持在线预览', 'data': None})
    if os.path.getsize(file_path) > 1024 * 1024:
        return jsonify({'code': 400, 'msg': '文件超过 1MB，暂不支持在线预览', 'data': None})
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="gbk", errors="replace") as f:
            content = f.read()
    return jsonify({
        'code': 200,
        'msg': '请求成功',
        'data': {
            "name": os.path.basename(file_path),
            "path": os.path.relpath(file_path, root_path),
            "ext": os.path.splitext(file_path)[1].lower().replace(".", ""),
            "size": os.path.getsize(file_path),
            "mtime": _format_time(os.path.getmtime(file_path)),
            "content": content,
        },
    })


@project.route('/sync_project_scripts', methods=["POST"])
@swag_from('../apidocs/sync_project_scripts.yml')
def sync_project_scripts():
    """扫描并同步项目脚本用例"""
    _ensure_project_meta_columns()
    project_id = request.json.get("id") or request.json.get("project_id")
    description = request.json.get("description", "")
    script_type = request.json.get("script_type", 1)
    version_id = request.json.get("version_id", 0)
    module_id = request.json.get("module_id")
    if not project_id:
        return jsonify({'code': 404, 'msg': '缺少项目id', 'data': None})
    permission_error = require_project_permission(project_id, "edit") if project_id else None
    if permission_error:
        return permission_error
    query = Project.query.filter_by(id=project_id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '项目不存在', 'data': None})
    sync_data, sync_error = _sync_project_script_cases(
        query, project_id, description=description, script_type=script_type, version_id=version_id, module_id=module_id
    )
    if sync_error:
        return jsonify(sync_error)
    return jsonify({
        'code': 200,
        'msg': f'同步完成：新增{sync_data.get("created_count", 0)}条，更新{sync_data.get("updated_count", 0)}条',
        'data': sync_data
    })


@project.route('/get_project_git_branches', methods=["POST"])
@swag_from('../apidocs/get_project_git_branches.yml')
def get_project_git_branches():
    """获取脚本项目 Git 远端分支列表"""
    _ensure_project_meta_columns()
    project_id = request.json.get("id") or request.json.get("project_id")
    repo_url = _clean_project_value(request.json.get("repo_url") or request.json.get("git_repo_url"))
    project_path = None
    query = None

    if project_id:
        permission_error = require_project_permission(project_id, "view")
        if permission_error:
            return permission_error
        query = Project.query.filter_by(id=project_id).first()
        if not query:
            return jsonify({'code': 404, 'msg': '项目不存在', 'data': None})
        project_path = _project_root_path(query.name)
        repo_url = repo_url or query.git_repo_url

    if not repo_url and project_path and os.path.isdir(os.path.join(project_path, ".git")):
        remote_result = _run_git(project_path, ["config", "--get", "remote.origin.url"], timeout=15)
        if remote_result.get("returncode") == 0:
            repo_url = remote_result.get("stdout")

    if not repo_url:
        return jsonify({'code': 400, 'msg': '请先填写 Git 仓库地址', 'data': {"branches": []}})

    result = _run_git_command(["ls-remote", "--heads", repo_url], timeout=60)
    branches = _parse_remote_branches(result.get("stdout"))
    if result.get("returncode") != 0:
        return jsonify({'code': 500, 'msg': '获取 Git 远端分支失败，请检查仓库地址、网络或权限', 'data': {
            "repo_url": repo_url,
            "branches": [],
            "git": result,
        }})

    default_branch = ""
    if query and query.git_branch:
        default_branch = query.git_branch
    elif branches:
        default_branch = "main" if "main" in branches else ("master" if "master" in branches else branches[0])

    return jsonify({
        'code': 200,
        'msg': '请求成功',
        'data': {
            "repo_url": repo_url,
            "branches": branches,
            "default_branch": default_branch,
            "git": result,
        }
    })


@project.route('/pull_project_git', methods=["POST"])
@swag_from('../apidocs/pull_project_git.yml')
def pull_project_git():
    """拉取脚本项目 Git 最新代码"""
    _ensure_project_meta_columns()
    project_id = request.json.get("id") or request.json.get("project_id")
    auto_sync = request.json.get("auto_sync")
    if not project_id:
        return jsonify({'code': 404, 'msg': '缺少项目id', 'data': None})
    permission_error = require_project_permission(project_id, "edit") if project_id else None
    if permission_error:
        return permission_error
    query = Project.query.filter_by(id=project_id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '项目不存在', 'data': None})
    project_path = _project_root_path(query.name)
    if not project_path or not os.path.isdir(project_path):
        return jsonify({'code': 404, 'msg': '项目目录不存在', 'data': None})
    if not os.path.isdir(os.path.join(project_path, ".git")):
        return jsonify({'code': 400, 'msg': '该脚本项目目录不是 Git 仓库，不能执行 pull', 'data': {
            "git_status": _project_git_status(query),
        }})

    before_status = _project_git_status(query)
    branch = _clean_project_value(request.json.get("branch")) or query.git_branch or before_status.get("branch")
    if branch and branch != before_status.get("branch"):
        checkout_result = _run_git(project_path, ["checkout", branch])
        if checkout_result.get("returncode") != 0:
            return jsonify({'code': 500, 'msg': '切换 Git 分支失败', 'data': {
                "git": checkout_result,
                "git_status": before_status,
            }})

    pull_args = ["pull", "--ff-only"]
    if branch:
        pull_args.extend(["origin", branch])
    pull_result = _run_git(project_path, pull_args, timeout=240)
    after_status = _project_git_status(query)
    if pull_result.get("returncode") != 0:
        return jsonify({'code': 500, 'msg': 'Git 拉取失败，请检查分支、网络、权限或本地未提交改动', 'data': {
            "git": pull_result,
            "before": before_status,
            "after": after_status,
        }})

    if auto_sync is None:
        auto_sync = query.git_auto_sync != 0
    else:
        auto_sync = auto_sync in (1, "1", True, "true", "True")
    sync_data = None
    sync_error = None
    if auto_sync:
        sync_data, sync_error = _sync_project_script_cases(query, project_id)

    return jsonify({
        'code': 200,
        'msg': 'Git 拉取完成' + ('，脚本同步完成' if auto_sync and not sync_error else ''),
        'data': {
            "project_id": project_id,
            "project_name": query.name,
            "git": pull_result,
            "before": before_status,
            "after": after_status,
            "auto_sync": auto_sync,
            "sync": sync_data,
            "sync_error": sync_error,
        }
    })


@project.route('/get_project_list', methods=["GET"])
@swag_from('../apidocs/get_project_list.yml')
def get_project_list():
    """获取项目脚本列表"""
    _ensure_project_meta_columns()
    try:
        new_project_list = list()
        project_list = get_test_project(config.testscriptproject)
        query = filter_project_model_query(Project.query, Project).order_by(db.desc(Project.updated_time))
        if query:
            query = [i.to_dict() for i in query]
            names = image.get_values_by_key(query, "name", values=[])
            if not isinstance(names, list):
                if names:
                    names = [names]
            # print(names)
            names = names or []
            for item in project_list:
                project_name = item.get("name")
                if allowed_project_ids() is not None and project_name not in names:
                    continue
                project_path = os.path.join(config.testscriptproject, project_name)
                data_ini_path = os.path.join(project_path, config.config_name)
                pytest_ini_path = os.path.join(project_path, "pytest.ini")
                item.update({
                    "status": "已新建" if project_name in names else "未新建",
                    "path": project_path,
                    "has_data_ini": os.path.exists(data_ini_path),
                    "has_pytest_ini": os.path.exists(pytest_ini_path),
                    "py_file_count": _count_py_files(project_path),
                    "mtime": _format_time(os.path.getmtime(project_path)) if os.path.exists(project_path) else "",
                })
                new_project_list.append(item)
        return_dict = {'code': 200, 'msg': '请求成功', 'data': new_project_list, 'total': len(new_project_list)}
    except Exception as e:
        print(e)
        return_dict = {'code': 404, 'msg': '没有找到项目！', 'data': []}
    return jsonify(return_dict)


@project.route('/update_project', methods=["POST"])
@swag_from('../apidocs/update_project.yml')
def update_project():
    """更新项目"""
    _ensure_project_meta_columns()
    id = request.json.get("id")
    name = request.json.get("name")
    description = request.json.get("description")
    controller = request.json.get("controller")
    meta_payload = _project_payload()
    query = Project.query.filter_by(id=id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '项目不存在', 'data': None})
    permission_error = require_project_permission(id, "edit")
    if permission_error:
        return permission_error
    query.name = name
    query.description = description
    query.controller = controller
    _fill_project_meta(query, meta_payload)
    db.session.commit()

    return_dict = {'code': 200, 'msg': '请求成功', 'data': id}
    return jsonify(return_dict)


@project.route('/add_project', methods=["POST"])
@swag_from('../apidocs/add_project.yml')
def add_projec():
    """新增或修改项目"""
    _ensure_project_meta_columns()
    id = request.json.get("id")
    name = request.json.get("name", "")
    description = request.json.get("description", "")
    controller = request.json.get("controller", "")
    meta_payload = _project_payload()
    if not is_admin():
        return jsonify({'code': 403, 'msg': '只有管理员可以新增脚本项目', 'data': None})
    name = name.strip()
    description = description.strip()
    controller = controller.strip()
    if not name or not description or not controller:
        return jsonify({'code': 404, 'msg': '缺少必填参数', 'data': ""})
    path = os.path.join(config.testscriptproject, name)
    if not os.path.exists(path):
        return jsonify({'code': 404, 'msg': f'该脚本项目不存在:{name}', 'data': ""})
    if not id:
        query = Project.query.filter_by(name=str(name)).first()
        if query:
            return jsonify({'code': 404, 'msg': '该脚本项目已存在', 'data': ""})
        new_project = Project(name=str(name), description=description, controller=controller)
        _fill_project_meta(new_project, meta_payload)
        db.session.add(new_project)
        db.session.flush()
        id = new_project.id
    else:
        query = Project.query.filter_by(id=id).first()
        query.name = name
        query.description = description
        query.controller = controller
        _fill_project_meta(query, meta_payload)
    db.session.commit()
    return_dict = {'code': 200, 'msg': '请求成功', 'data': id}
    return jsonify(return_dict)


@project.route('/check_ini', methods=["POST"])
@swag_from('../apidocs/check_ini.yml')
def check_ini():
    """查看当前项目配置信息"""
    _ensure_project_meta_columns()
    project_id = request.json.get("id")
    if not project_id:
        return jsonify({'code': 404, 'msg': '缺少必填参数', 'data': ""})
    query = Project.query.filter_by(id=project_id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '没有添加该项目', 'data': ""})
    permission_error = require_project_permission(project_id, "view")
    if permission_error:
        return permission_error
    path = os.path.join(config.testscriptproject, query.name, config.config_name)
    if not os.path.exists(path):
        return jsonify({'code': 404, 'msg': f'该脚本项目配置文件不存在:{query.name}', 'data': ""})
    config_dict = read_ini_file(path)
    return_dict = {'code': 200, 'msg': '请求成功', 'data': config_dict}
    return return_dict


@project.route('/clear_ini', methods=["POST"])
@swag_from('../apidocs/clear_ini.yml')
def clear_ini():
    """清空配置"""
    _ensure_project_meta_columns()
    project_id = request.json.get("id")
    if not project_id:
        return jsonify({'code': 404, 'msg': '缺少必填参数', 'data': ""})
    query = Project.query.filter_by(id=project_id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '没有添加该项目', 'data': ""})
    permission_error = require_project_permission(project_id, "edit")
    if permission_error:
        return permission_error
    path = os.path.join(config.testscriptproject, query.name, config.config_name)
    if not os.path.exists(path):
        return jsonify({'code': 404, 'msg': f'该脚本项目配置文件不存在:{query.name}', 'data': ""})
    config_dict = clear_ini_file(path)
    return_dict = {'code': 200, 'msg': '请求成功', 'data': config_dict}
    return return_dict


@project.route('/get_home_stats', methods=["POST"])
def get_home_stats():
    """获取首页看板统计"""
    ids = allowed_project_ids()
    project_query = Project.query
    case_query = Cases.query.filter_by(is_delete=0)
    testset_query = TestSet.query.filter_by(is_delete=0)
    report_query = Reports.query
    if ids is not None:
        if not ids:
            return jsonify({'code': 200, 'msg': '请求成功', 'data': _home_empty_stats()})
        project_query = project_query.filter(Project.id.in_(ids))
        case_query = case_query.filter(Cases.project_id.in_(ids))
        testset_query = testset_query.filter(TestSet.project_id.in_(ids))
        report_query = report_query.filter(Reports.project_id.in_(ids))

    today_start = datetime.combine(datetime.now().date(), datetime.min.time())
    today_report_query = report_query.filter(Reports.created_time >= today_start)
    today_summary = today_report_query.with_entities(
        func.count(Reports.id),
        func.coalesce(func.sum(Reports.all_count), 0),
        func.coalesce(func.sum(Reports.pass_count), 0),
        func.coalesce(func.sum(Reports.fail_count), 0),
        func.coalesce(func.sum(Reports.error_count), 0),
    ).first()
    today_run_count = int(today_summary[0] or 0)
    today_all_count = int(today_summary[1] or 0)
    today_pass_count = int(today_summary[2] or 0)
    today_fail_count = int(today_summary[3] or 0)
    today_error_count = int(today_summary[4] or 0)
    trend_map = {
        hour: {'hour': f'{hour:02d}:00', 'run_count': 0, 'pass_count': 0, 'all_count': 0, 'failed_count': 0}
        for hour in range(24)
    }
    for item in today_report_query.with_entities(
            Reports.created_time,
            Reports.all_count,
            Reports.pass_count,
            Reports.fail_count,
            Reports.error_count,
    ).all():
        created_time = item.created_time
        if not created_time:
            continue
        hour = created_time.hour
        trend_map[hour]['run_count'] += 1
        trend_map[hour]['all_count'] += int(item.all_count or 0)
        trend_map[hour]['pass_count'] += int(item.pass_count or 0)
        trend_map[hour]['failed_count'] += int(item.fail_count or 0) + int(item.error_count or 0)
    today_trend = []
    for hour in range(24):
        item = trend_map[hour]
        all_count = item.pop('all_count')
        pass_count = item.pop('pass_count')
        item['pass_rate'] = round(pass_count / all_count * 100, 2) if all_count else 0
        today_trend.append(item)

    tasks = TestTask.query.filter_by(is_delete=0).all()
    tasks = filter_task_list(tasks)
    running_task_count = len([item for item in tasks if item.run_status == 1])
    running_testset_count = testset_query.filter(TestSet.run_status == 1).count()
    running_testsets = []
    for item in testset_query.filter(TestSet.run_status == 1).order_by(db.desc(TestSet.updated_time)).limit(8).all():
        running_testsets.append({
            'id': item.id,
            'title': item.title,
            'project_name': item.project_name,
            'run_id': item.run_id,
            'schedule': item.schedule or 0,
            'run_status': item.run_status,
            'run_by_name': item.run_by_name,
            'updated_time': _format_time(item.updated_time),
        })
    running_tasks = []
    for item in sorted([task for task in tasks if task.run_status == 1], key=lambda task: task.updated_time or datetime.min, reverse=True)[:8]:
        running_tasks.append({
            'id': item.id,
            'name': item.name,
            'run_id': item.run_id,
            'schedule': item.schedule or 0,
            'set_schedule': getattr(item, 'set_schedule', None) or 0,
            'progress': item.progress or '',
            'run_status': item.run_status,
            'run_by_name': item.run_by_name,
            'updated_time': _format_time(item.updated_time),
        })

    projects = project_query.order_by(db.desc(Project.updated_time)).all()
    project_health_summary = {'ok': 0, 'warning': 0, 'error': 0}
    project_health_items = []
    continuous_failures = []
    for project_item in projects:
        stats = _project_stats(project_item.id)
        health = _light_project_health(project_item, stats)
        project_health_summary[health['status']] += 1
        project_health_items.append(health)
        if health.get('consecutive_failed', 0) >= 2:
            continuous_failures.append({
                'project_id': project_item.id,
                'project_name': project_item.name,
                'business_department': project_item.business_department or "",
                'consecutive_failed': health.get('consecutive_failed', 0),
                'last_run_id': stats.get("last_run_id"),
                'last_pass_rate': stats.get("last_pass_rate"),
                'last_fail_count': stats.get("last_fail_count", 0),
                'last_error_count': stats.get("last_error_count", 0),
                'last_run_time': stats.get("last_run_time") or "",
            })
    project_health_items = sorted(
        project_health_items,
        key=lambda item: (
            {'error': 0, 'warning': 1, 'ok': 2}.get(item.get('status'), 3),
            -(item.get('consecutive_failed') or 0),
            item.get('last_pass_rate') if item.get('last_pass_rate') is not None else 101,
        )
    )[:10]
    continuous_failures = sorted(
        continuous_failures,
        key=lambda item: (item.get('consecutive_failed') or 0, item.get('last_run_time') or ""),
        reverse=True
    )[:8]
    recent_failures = [
        _recent_failure_payload(item)
        for item in report_query.filter(or_(Reports.fail_count > 0, Reports.error_count > 0))
        .order_by(db.desc(Reports.updated_time)).limit(8).all()
    ]
    week_start = datetime.now() - timedelta(days=7)
    department_quality = [
        _department_quality_payload(item, ids, week_start)
        for item in BusinessDepartment.query.filter_by(is_delete=0).order_by(BusinessDepartment.name.asc()).all()
    ]
    department_quality = sorted(
        [item for item in department_quality if item.get('project_count', 0) > 0],
        key=lambda item: (
            item.get('fail_count', 0) + item.get('error_count', 0),
            -item.get('pass_rate', 0)
        ),
        reverse=True
    )[:8]

    return jsonify({'code': 200, 'msg': '请求成功', 'data': {
        'project_count': len(projects),
        'case_count': case_query.count(),
        'testset_count': testset_query.count(),
        'task_count': len(tasks),
        'today_run_count': today_run_count,
        'today_pass_rate': round(today_pass_count / today_all_count * 100, 2) if today_all_count else 0,
        'running_count': running_testset_count + running_task_count,
        'running_testset_count': running_testset_count,
        'running_task_count': running_task_count,
        'failed_pending_count': today_fail_count + today_error_count,
        'today_trend': today_trend,
        'running_testsets': running_testsets,
        'running_tasks': running_tasks,
        'recent_failures': recent_failures,
        'continuous_failures': continuous_failures,
        'project_health_summary': project_health_summary,
        'project_health_items': project_health_items,
        'department_quality': department_quality,
        'process_pool_status': _process_pool_status(),
    }})


@project.route('/get_process_pool_status', methods=["POST"])
def get_process_pool_status():
    """获取进程池占用情况"""
    return jsonify({'code': 200, 'msg': '请求成功', 'data': _process_pool_status()})
