# -*- coding: utf-8 -*-
import csv
import datetime
import os
import shutil
import subprocess
import sys
import tempfile
import time

from app.lib.lib_define import db
from app.models.test_api_models import PerfRunResult, PerfScenario
from app.tools.api_common_tools import json_text, loads, new_api_run_id
from app.tools.audit_fields import apply_run_user
from app.tools.db_write_guard import guarded_commit, guarded_rollback
from app.tools.performance_payload_tools import load_ordered_endpoints, normalize_endpoint_ids
from app.tools.performance_report_tools import write_perf_report_file


PERF_RUN_PROCESSES = {}


def new_perf_run_id():
    return new_api_run_id()


def _parse_csv_stats(prefix):
    stats_file = prefix + "_stats.csv"
    history_file = prefix + "_stats_history.csv"
    if not os.path.exists(stats_file):
        return {"stats": [], "summary": {}, "history": []}
    rows = []
    with open(stats_file, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    history_rows = []
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("Name") == "Aggregated":
                    history_rows.append(
                        {
                            "timestamp": row.get("Timestamp"),
                            "user_count": row.get("User Count"),
                            "requests_per_second": row.get("Requests/s"),
                            "failures_per_second": row.get("Failures/s"),
                            "total_request_count": row.get("Total Request Count"),
                            "total_failure_count": row.get("Total Failure Count"),
                            "total_average_response_time": row.get("Total Average Response Time"),
                        }
                    )
    summary = {}
    for row in rows:
        if row.get("Name") == "Aggregated":
            summary = row
            break
    return {
        "stats": [
            {
                "method": row.get("Type"),
                "name": row.get("Name"),
                "num_requests": row.get("Request Count"),
                "num_failures": row.get("Failure Count"),
                "avg_response_time": row.get("Average Response Time"),
                "min_response_time": row.get("Min Response Time"),
                "max_response_time": row.get("Max Response Time"),
                "current_rps": row.get("Current RPS"),
                "total_rps": row.get("Requests/s"),
            }
            for row in rows
            if row.get("Name")
        ],
        "summary": summary,
        "history": history_rows[-30:],
    }


def _locustfile_content(endpoints):
    tasks = []
    for index, endpoint in enumerate(endpoints):
        method = (endpoint.method or "GET").lower()
        if method not in ("get", "post", "put", "patch", "delete", "head"):
            method = "get"
        headers = loads(endpoint.headers, {}) if endpoint.headers else {}
        params = loads(endpoint.params, {}) if endpoint.params else {}
        body = endpoint.body or ""
        body_type = endpoint.body_type or "json"
        weight = endpoint.weight or 1
        request_kwargs = {
            "headers": headers,
            "params": params,
            "name": endpoint.name or endpoint.url,
            "catch_response": True,
        }
        if method not in ("get", "delete", "head"):
            if body_type == "json" and body:
                try:
                    request_kwargs["json"] = loads(body, body)
                except Exception:
                    request_kwargs["data"] = body
            elif body_type == "form" and body:
                try:
                    request_kwargs["data"] = loads(body, body)
                except Exception:
                    request_kwargs["data"] = body
            elif body:
                request_kwargs["data"] = body
        tasks.append(
            """
    @task({weight})
    def endpoint_{index}(self):
        with self.client.{method}({url!r}, **{kwargs!r}) as response:
            if response.status_code >= 400:
                response.failure("HTTP %s" % response.status_code)
            else:
                response.success()
""".format(weight=weight, index=index, method=method, url=endpoint.url, kwargs=request_kwargs)
        )
    return "from locust import HttpUser, task, between\n\nclass PerfUser(HttpUser):\n    wait_time = between(0.1, 1)\n" + "".join(tasks)


def start_performance_run(app, result_id, scenario_id):
    with app.app_context():
        result = PerfRunResult.query.get(result_id)
        scenario = PerfScenario.query.filter_by(id=scenario_id, is_delete=0).first()
        if not result or not scenario:
            return
        started = time.time()
        temp_dir = tempfile.mkdtemp(prefix="perf_{}_".format(result.run_id))
        try:
            endpoints = load_ordered_endpoints(normalize_endpoint_ids(loads(scenario.endpoint_ids, [])))
            if not endpoints:
                raise ValueError("性能测试场景没有接口")
            locust_file = os.path.join(temp_dir, "locustfile.py")
            csv_prefix = os.path.join(temp_dir, "locust")
            with open(locust_file, "w", encoding="utf-8") as f:
                f.write(_locustfile_content(endpoints))
            cmd = [
                sys.executable,
                "-m",
                "locust",
                "-f",
                locust_file,
                "--headless",
                "-u",
                str(result.users or 1),
                "-r",
                str(result.spawn_rate or 1),
                "--run-time",
                result.run_time or "1m",
                "--csv",
                csv_prefix,
                "--csv-full-history",
            ]
            if result.host:
                cmd.extend(["--host", result.host])
            result.run_status = "running"
            result.status_text = "运行中"
            result.metrics = json_text({"stats": [], "summary": {}, "message": "Locust 启动中"})
            guarded_commit()
            stdout_path = os.path.join(temp_dir, "locust_stdout.log")
            stderr_path = os.path.join(temp_dir, "locust_stderr.log")
            stdout_file = open(stdout_path, "w", encoding="utf-8", errors="replace")
            stderr_file = open(stderr_path, "w", encoding="utf-8", errors="replace")
            process = subprocess.Popen(
                cmd,
                cwd=temp_dir,
                stdout=stdout_file,
                stderr=stderr_file,
            )
            PERF_RUN_PROCESSES[result.run_id] = process
            while process.poll() is None:
                metrics = _parse_csv_stats(csv_prefix)
                result = PerfRunResult.query.get(result_id)
                if result and result.run_status == "stopped":
                    process.terminate()
                    break
                if result:
                    result.metrics = json_text(metrics)
                    result.elapsed_ms = int((time.time() - started) * 1000)
                    guarded_commit()
                time.sleep(2)
            stdout, stderr = "", ""
            if process.poll() is None:
                process.wait(timeout=10)
            else:
                try:
                    process.wait(timeout=1)
                except Exception:
                    pass
            stdout_file.close()
            stderr_file.close()
            if os.path.exists(stdout_path):
                with open(stdout_path, "r", encoding="utf-8", errors="replace") as f:
                    stdout = f.read()
            if os.path.exists(stderr_path):
                with open(stderr_path, "r", encoding="utf-8", errors="replace") as f:
                    stderr = f.read()
            result = PerfRunResult.query.get(result_id)
            metrics = _parse_csv_stats(csv_prefix)
            result.metrics = json_text(metrics)
            result.elapsed_ms = int((time.time() - started) * 1000)
            if result.run_status == "stopped":
                result.status_text = "已终止"
                result.success = 0
            elif process.returncode == 0:
                result.run_status = "finished"
                result.status_text = "执行完成"
                failures = int(float((metrics.get("summary") or {}).get("Failure Count") or 0))
                result.success = 1 if failures == 0 else 0
            else:
                result.run_status = "failed"
                result.status_text = "执行失败"
                result.success = 0
            if result.run_status == "failed" and not result.error_message:
                result.error_message = (stderr or stdout or "Locust execution failed")[-4000:]
            result.report_path = write_perf_report_file(result, scenario, endpoints)
            scenario.last_status = result.run_status
            scenario.last_run_id = result.run_id
            scenario.last_run_time = datetime.datetime.now()
            apply_run_user(result)
            guarded_commit()
        except Exception as exc:
            guarded_rollback()
            result = PerfRunResult.query.get(result_id)
            if result:
                result.run_status = "failed"
                result.status_text = "执行异常"
                result.error_message = str(exc)
                result.elapsed_ms = int((time.time() - started) * 1000)
                guarded_commit()
        finally:
            PERF_RUN_PROCESSES.pop(result.run_id if result else None, None)
            shutil.rmtree(temp_dir, ignore_errors=True)

def stop_performance_run(run_id):
    process = PERF_RUN_PROCESSES.get(int(run_id)) if run_id else None
    if process and process.poll() is None:
        process.terminate()
        return True
    return False
