# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
# 从app模块中即从__init__.py中导入创建的app应用
# 测试任务相关接口测配置多个测试集在一个任务里面执行，包括前置测试环境数据准备，后置清理
import json
import ast

from flask import jsonify, request
from app.web_api import test_task
from app.models.test_api_models import *
from flasgger import swag_from
from app.lib import image
import time
from app.tools import sched_task
from app.commom.test_script_run import th_run_task, update_config_file
from concurrent.futures import ProcessPoolExecutor
import traceback
from sqlalchemy import func
from app.tools.auth_permissions import (
    filter_task_list,
    project_ids_from_task,
    require_project_permission,
)

workers = 3
executor = ProcessPoolExecutor(workers)
scheduler_job = {}


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


def _task_belongs_to_project(task, project_set_ids):
    if not project_set_ids:
        return False
    set_ids = set(_safe_id_list(task.test_set_ids))
    return bool(project_set_ids.intersection(set_ids))


def _project_ids_from_set_ids(set_ids):
    set_ids = _safe_id_list(set_ids)
    if not set_ids:
        return []
    rows = TestSet.query.with_entities(TestSet.project_id).filter(
        TestSet.id.in_(set_ids),
        TestSet.is_delete == 0
    ).all()
    return list({item.project_id for item in rows})


def _require_project_ids_permission(project_ids, permission):
    for project_id in project_ids:
        permission_error = require_project_permission(project_id, permission)
        if permission_error:
            return permission_error
    return None


def _timed_testtask_job_id(task_id, run_id):
    return f"testtask:{task_id}:{run_id}"


def _remove_scheduler_job(job_ids):
    for job_id in job_ids:
        if not job_id:
            continue
        try:
            sched_task.sched.remove_job(str(job_id), jobstore='redis')
            scheduler_job.pop(str(job_id), None)
            return True
        except Exception as e:
            print(e)
    return False


def _format_time(value):
    if not value:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


@test_task.route('/get_task_info', methods=["POST"])
@swag_from('../apidocs/get_task_info.yml')
def get_task_info():
    """获取任务信息列表"""

    page_no = request.json.get("page_no", 0)
    page_size = request.json.get("page_size", 10)
    task_name = request.json.get("task_name", "")
    task_name = task_name.strip()
    run_status = request.json.get("run_status")
    project_id = request.json.get("project_id")
    if project_id:
        permission_error = require_project_permission(project_id, "view")
        if permission_error:
            return permission_error
        project_set_ids = set([
            item.id for item in TestSet.query.with_entities(TestSet.id).filter_by(
                project_id=project_id, is_delete=0
            ).all()
        ])
        base_query = TestTask.query.filter_by(is_delete=0)
        if task_name:
            base_query = base_query.filter(TestTask.name.like(f"%{task_name}%"))
        if isinstance(run_status, int):
            base_query = base_query.filter_by(run_status=run_status)
        query = [
            item for item in base_query.order_by(db.desc(TestTask.updated_time)).all()
            if _task_belongs_to_project(item, project_set_ids)
        ]
        query = query[page_no:page_no + page_size] if page_size else query
    elif task_name:
        query = TestTask.query.filter(TestTask.name.like(f"%{task_name}%")).filter_by(is_delete=0).all()
    elif isinstance(run_status, int):
        query = TestTask.query.filter_by(run_status=run_status).filter_by(is_delete=0).all()
    else:
        query = TestTask.query.filter_by(is_delete=0).order_by(db.desc(TestTask.updated_time)).limit(page_size).offset(
            page_no)
    if not project_id:
        query = filter_task_list(list(query))
    if query:
        query = [i.to_dict() for i in query]
    for i in query:
        if i.get("updated_time"):
            i.update({"updated_time": i.get("updated_time").strftime("%Y-%m-%d %H:%M:%S")})
        if i.get("created_time"):
            i.update({"created_time": i.get("created_time").strftime("%Y-%m-%d %H:%M:%S")})
    cfg_ids = image.get_values_by_key(query, "config_ids", values=[])
    if isinstance(cfg_ids, str):
        cfg_ids = [cfg_ids]
    config_id_list = None
    ex_ids = list()
    if cfg_ids:
        for i in cfg_ids:
            if isinstance(i, str):
                i = eval(i)
                if isinstance(i, list):
                    ex_ids.extend(i)
                if isinstance(i, int):
                    ex_ids.append(i)
        config_id_list = Cfgs.query.filter(Cfgs.id.in_(ex_ids)).all()
    if config_id_list:
        config_id_list = [i.to_dict() for i in config_id_list]
        for i in range(len(query)):
            check_ids = eval(query[i].get("config_ids"))
            if isinstance(check_ids, int):
                check_ids = [check_ids]
            names = list()
            for j in check_ids:
                for z in config_id_list:
                    if j == z.get("id"):
                        names.append(z.get("cfg_name"))
            # for j in config_id_list:
            #     if j.get("id") in check_ids:
            #         names.append(j.get("cfg_name"))
            query[i].update({"cfg_name": names})

    set_ids = image.get_values_by_key(query, "test_set_ids", values=[])
    if isinstance(set_ids, str):
        set_ids = [set_ids]
    config_id_list = None
    ex_ids = list()
    if set_ids:
        for i in set_ids:
            if isinstance(i, str):
                i = eval(i)
                if isinstance(i, list):
                    ex_ids.extend(i)
                if isinstance(i, int):
                    ex_ids.append(i)
        ex_ids = list(set(ex_ids))
        config_id_list = TestSet.query.filter(TestSet.id.in_(ex_ids)).all()
    if config_id_list:
        config_id_list = [i.to_dict() for i in config_id_list]
        for i in range(len(query)):
            check_ids = eval(query[i].get("test_set_ids"))
            if isinstance(check_ids, int):
                check_ids = [check_ids]
            names = list()
            for j in check_ids:
                for z in config_id_list:
                    if j == z.get("id"):
                        names.append(z.get("title"))
            # names = list()
            # for j in config_id_list:
            #     if j.get("id") in check_ids:
            #         names.append(j.get("title"))
            query[i].update({"set_name": names})
    current_time = datetime.datetime.now()
    # 获取当前时间戳（Unix 时间戳，单位为秒）
    current_timestamp = int(current_time.timestamp())
    for i in query:
        if i.get("timed_task_time"):
            try:
                # 将字符串时间解析为 datetime 对象
                datetime_obj = datetime.datetime.strptime(i.get("timed_task_time"), "%Y-%m-%d %H:%M:%S")
                # 获取时间戳（Unix 时间戳，单位为秒）
                timestamp = datetime_obj.timestamp() - current_timestamp
                hours = int(timestamp // 3600)
                minutes = int((timestamp % 3600) // 60)
                secs = int(timestamp % 60)
                if hours >= 0 and minutes >= 0 and secs >= 0:
                    i.update({"countdown": "{}:{}:{}".format(hours, minutes, secs)})
                    i.update({"countdown_second": timestamp})
            except Exception as e:
                i.update({"countdown": None})
                i.update({"countdown_second": None})
        if i.get("start_task_time") and i.get("run_status") != 2:
            try:
                # 将字符串时间解析为 datetime 对象
                datetime_obj = datetime.datetime.strptime(i.get("start_task_time"), "%Y-%m-%d %H:%M:%S")
                # 获取时间戳（Unix 时间戳，单位为秒）
                # timestamp = datetime_obj.timestamp() - current_timestamp
                timestamp = current_timestamp - datetime_obj.timestamp()
                hours = int(timestamp // 3600)
                minutes = int((timestamp % 3600) // 60)
                secs = int(timestamp % 60)
                if hours >= 0 and minutes >= 0 and secs >= 0:
                    i.update({"run_task_time": "{}:{}:{}".format(hours, minutes, secs)})
            except Exception as e:
                i.update({"run_task_time": None})
        if i.get("progress_set_id"):
            try:

                set_query = TestSet.query.filter_by(id=i.get("progress_set_id")).filter_by(is_delete=0).first()
                if set_query:
                    i.update({"set_schedule": set_query.schedule})
            except Exception as e:
                i.update({"set_schedule": None})
    return_dict = {'code': 200, 'msg': '请求成功', 'data': query}
    return jsonify(return_dict)


@test_task.route('/add_testtask', methods=["POST"])
@swag_from('../apidocs/add_testtask.yml')
# @test_task.log_request_response(module="add_testtask")
def add_testtask():
    """新增或修改测试任务"""
    task_id = request.json.get("task_id")
    config_ids = request.json.get("config_ids")
    set_ids = request.json.get("set_ids")
    task_name = request.json.get("task_name")
    mark = request.json.get("mark", "")
    email_to = request.json.get("email_to", "")
    if task_id:
        permission_error = _require_project_ids_permission(project_ids_from_task(task_id), "edit")
        if permission_error:
            return permission_error
    permission_error = _require_project_ids_permission(_project_ids_from_set_ids(set_ids), "edit")
    if permission_error:
        return permission_error
    if not set_ids:
        return jsonify({'code': 404, 'msg': '测试集不能为空', 'data': None})
    if not task_name:
        return jsonify({'code': 404, 'msg': '测试任务名不能为空', 'data': None})
    if task_id:
        testtask_info = TestTask.query.filter_by(id=task_id).first()
    else:
        testtask_info = TestTask.query.filter_by(name=task_name).first()
    if testtask_info:
        if testtask_info.run_status not in [0, 2]:
            return jsonify({'code': 404, 'msg': '测试任务运行中，不允许修改', 'data': None})
        testset_id = testtask_info.id
        testtask_info.name = task_name
        testtask_info.test_set_ids = json.dumps(set_ids)
        testtask_info.mark = mark
        testtask_info.config_ids = json.dumps(config_ids)
        testtask_info.email_to = email_to
        return_dict = {'code': 200, 'msg': f'修改{task_name}测试任务成功', 'data': testset_id}
    else:
        new_testtask = TestTask(config_ids=json.dumps(config_ids), name=task_name, run_status=0,
                                test_set_ids=json.dumps(set_ids),
                                mark=mark, email_to=email_to)
        db.session.add(new_testtask)
        db.session.flush()
        testtask_id = new_testtask.id
        return_dict = {'code': 200, 'msg': f'新增{task_name}测试任务成功', 'data': testtask_id}
    db.session.commit()
    return jsonify(return_dict)


@test_task.route('/run_testtask', methods=["POST"])
@swag_from('../apidocs/run_testtask.yml')
def run_testtask():
    id = request.json.get("task_id")
    config_ids = request.json.get("config_ids")
    set_ids = request.json.get("set_ids")
    mark = request.json.get("mark", "")
    email_to = request.json.get("email_to", "")
    timed_task_time = request.json.get("timed_task_time")
    sent_email = request.json.get("sent_email", 0)
    start_process = request.json.get("start_process")
    rerun_type = request.json.get("rerun_type", 0)
    query = TestTask.query.filter_by(id=id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '测试任务不存在', 'data': None})
    permission_source_set_ids = set_ids or query.test_set_ids
    permission_error = _require_project_ids_permission(_project_ids_from_set_ids(permission_source_set_ids), "run")
    if permission_error:
        return permission_error
    # 这是全局配置信息写入各个测试集所属项目
    query.mark = mark
    query.email_to = email_to
    db.session.commit()
    if set_ids:
        if isinstance(set_ids, int):
            set_ids = [set_ids]
        setids = list()
        for i in set_ids:
            cfg = TestSet.query.filter_by(id=i).first()
            if cfg:
                setids.append(cfg.id)
        if setids:
            query.test_set_ids = str(setids)
    if not set_ids:
        set_ids = query.test_set_ids
        set_ids = eval(set_ids)
    db.session.commit()
    if not set_ids:
        return jsonify({'code': 404, 'msg': '测试集不能为空', 'data': None})
    for set_id in set_ids:
        set_q = TestSet.query.filter_by(id=set_id).first()
        if set_q:
            set_q.run_status = 0
            set_q.mark_info = f"[{query.name}]测试任务在使用这个测试集"
    db.session.commit()
    if config_ids:
        query.config_ids = json.dumps(config_ids)
        for i in set_ids:
            set_query = TestSet.query.filter_by(id=i).first()
            if not set_query:
                continue
            project_name = set_query.project_name
            cfg_status = update_config_file(config_ids, project=project_name)
            if not cfg_status:
                return jsonify(
                    {'code': 404, 'msg': f'{project_name}项目pytest用例配置文件更新失败！请检查配置和项目名称是否存在',
                     'data': []})
    if timed_task_time:
        # 定时任务限制时间。同一时间允许多个任务，APScheduler job id 使用任务+run_id 保证唯一。
        limit_date = (60 * 60 * 24) * 3
        time_now = int(time.time())
        time_array = time.strptime(timed_task_time, "%Y-%m-%d %H:%M:%S")
        time_array = int(time.mktime(time_array))
        if time_array <= time_now:
            query.run_status = 2
            query.timed_task_time = ""
            db.session.commit()
            return jsonify({'code': 404, 'msg': '所选定时任务时间不能低于或等于当前时间', 'data': []})
        if time_array - time_now > limit_date:
            query.run_status = 2
            query.timed_task_time = ""
            db.session.commit()
            return jsonify(
                {'code': 404, 'msg': f'所选定时任务时间不能大于{int(limit_date / (60 * 60 * 24))}天后',
                 'data': []})
    try:
        dt = datetime.datetime.fromtimestamp(time.time())
        run_id_num = int(dt.strftime('%Y%m%d%H%M%S')) + int(id)
        # run_id_num = image.get_uuid_name()
        query.run_id = run_id_num
        query.run_status = 1
        query.schedule = 0
        if timed_task_time:
            query.timed_task_time = timed_task_time
            query.run_type = "定时任务"
        db.session.commit()
        print(config_ids)
        if timed_task_time:
            def test_task():
                job_id = _timed_testtask_job_id(id, run_id_num)
                sched_task.sched.add_job(th_run_task, 'date', run_date=timed_task_time, id=job_id,
                                         kwargs={
                                             "rerun_type": rerun_type,
                                             "task_id": id,
                                             "set_ids": set_ids,
                                             "run_id_num": run_id_num,
                                             "mark": str(mark),
                                             "email_to": email_to,
                                             "sent_email": sent_email,
                                             "config_id": config_ids,
                                             "timed_task_time": timed_task_time,
                                             "start_process": start_process},
                                         jobstore='redis',
                                         replace_existing=False, misfire_grace_time=60, executor="processpool")
                scheduler_job.update({job_id: job_id})
                print(sched_task.sched.get_jobs())

            test_task()
        else:
            query.timed_task_time = ""
            db.session.commit()
            executor.submit(th_run_task, rerun_type=rerun_type, task_id=id, set_ids=set_ids,
                            run_id_num=run_id_num, mark=str(mark), email_to=email_to,
                            sent_email=sent_email, config_id=config_ids,
                            start_process=start_process)
    except Exception as e:
        db.session.rollback()
        query.timed_task_time = ""
        query.run_type = ""
        db.session.commit()
        traceback.print_exc()
        return jsonify({'code': 404, 'msg': f'执行错误:{e}', 'data': []})
    return_dict = {'code': 200, 'msg': '请求成功', 'data': []}
    return jsonify(return_dict)


@test_task.route('/stop_testtask', methods=["POST"])
@swag_from('../apidocs/stop_testtask.yml')
def stop_testtask():
    """终止测试测试任务"""
    ids = request.json.get("ids")
    if not ids:
        return jsonify({'code': 404, 'msg': '请传入需要终止的测试任务id', 'data': []})
    stop_set_title = list()
    for id in ids:
        query = TestTask.query.filter_by(id=id).first()
        if not query:
            continue
        permission_error = _require_project_ids_permission(project_ids_from_task(id), "run")
        if permission_error:
            return permission_error
        if query.run_status == 1:
            query.run_status = 2
            query.schedule = 0
            timed_task_time_value = query.timed_task_time
            job_id = _timed_testtask_job_id(id, query.run_id) if query.run_id else None
            # pid = query.pid
            query.timed_task_time = ""
            query.start_task_time = ""
            if timed_task_time_value:
                current_time = datetime.datetime.now()
                time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
                query.timed_task_time = f"已经于{time_string}手动终止定时任务"
            db.session.commit()
            try:
                _remove_scheduler_job([job_id, timed_task_time_value])
            except Exception as e:
                print(e)
            if query.test_set_ids:
                for i in eval(query.test_set_ids):
                    set_query = TestSet.query.filter_by(id=i).first()
                    if set_query.run_status == 1:
                        set_query.run_status = 2
                        set_query.schedule = 0
                        set_query.timed_task_time = ""
                        set_query.start_task_time = ""
                        set_query.run_type = ""
                        set_query.pid = 0
                db.session.commit()
            stop_set_title.append(query.name)
    return jsonify({'code': 200, 'msg': '测试任务执行已终止', 'data': stop_set_title})


@test_task.route('/delete_testtask', methods=["POST"])
@swag_from('../apidocs/delete_testtask.yml')
def delete_testtask():
    """删除测试任务"""
    ids = request.json.get("ids")
    if not ids:
        return jsonify({'code': 404, 'msg': '请传入需要删除的测试任务id', 'data': []})
    delete_task_name = list()
    for set_id in ids:
        query = TestTask.query.filter_by(id=set_id).filter_by(is_delete=0).first()
        if not query:
            continue
        permission_error = _require_project_ids_permission(project_ids_from_task(set_id), "edit")
        if permission_error:
            return permission_error
        if query.run_status in [1]:
            continue
        query.is_delete = 1
        delete_task_name.append(query.name)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '测试任务已删除', 'data': delete_task_name})


@test_task.route('/get_testtask_set', methods=["POST"])
@swag_from('../apidocs/get_testtask_set.yml')
def get_testtask_set():
    """获取测试任务测试集信息"""
    task_id = request.json.get("task_id")
    if not task_id:
        return jsonify({'code': 404, 'msg': '请传入需要的测试任务id', 'data': []})
    query = TestTask.query.filter_by(id=task_id).filter_by(is_delete=0).first()
    if not query:
        return jsonify({'code': 404, 'msg': '任务不存在', 'data': None})
    permission_error = _require_project_ids_permission(project_ids_from_task(task_id), "view")
    if permission_error:
        return permission_error
    set_ids = _safe_id_list(query.test_set_ids)
    set_query = TestSet.query.filter_by(is_delete=0).filter(TestSet.id.in_(set_ids)).all()
    set_map = {item.id: item for item in set_query}
    set_query = [set_map[set_id].to_dict() for set_id in set_ids if set_id in set_map]
    return jsonify({'code': 200, 'msg': '测试任务中测试集的详情', 'data': set_query})
@test_task.route('/get_testtask_history', methods=["POST"])
def get_testtask_history():
    """获取测试任务运行历史"""
    task_id = request.json.get("task_id")
    page_size = request.json.get("page_size", 20)
    if not task_id:
        return jsonify({'code': 404, 'msg': '请传入测试任务id', 'data': []})
    task = TestTask.query.filter_by(id=task_id).filter_by(is_delete=0).first()
    if not task:
        return jsonify({'code': 404, 'msg': '测试任务不存在', 'data': []})
    permission_error = _require_project_ids_permission(project_ids_from_task(task_id), "view")
    if permission_error:
        return permission_error
    set_ids = _safe_id_list(task.test_set_ids)
    if not set_ids:
        return jsonify({'code': 200, 'msg': '请求成功', 'data': []})
    set_query = TestSet.query.filter_by(is_delete=0).filter(TestSet.id.in_(set_ids)).all()
    set_map = {item.id: item.title for item in set_query}
    reports = Reports.query.filter(
        Reports.set_id.in_(set_ids),
        Reports.run_id.isnot(None)
    ).order_by(db.desc(Reports.updated_time)).all()
    history_map = {}
    for item in reports:
        history = history_map.setdefault(item.run_id, {
            "run_id": item.run_id,
            "report_count": 0,
            "set_names": [],
            "all_count": 0,
            "pass_count": 0,
            "fail_count": 0,
            "error_count": 0,
            "case_all_time": 0.0,
            "start_time": "",
            "end_time": "",
            "latest_report": "",
            "mark": item.mark or "",
        })
        history["report_count"] += 1
        history["set_names"].append(set_map.get(item.set_id, str(item.set_id)))
        history["all_count"] += int(item.all_count or 0)
        history["pass_count"] += int(item.pass_count or 0)
        history["fail_count"] += int(item.fail_count or 0)
        history["error_count"] += int(item.error_count or 0)
        history["case_all_time"] += float(item.case_all_time or 0)
        report_time = _format_time(item.updated_time)
        if not history["end_time"] or report_time > history["end_time"]:
            history["end_time"] = report_time
            history["latest_report"] = item.report_path
        if not history["start_time"] or report_time < history["start_time"]:
            history["start_time"] = report_time
    history_list = sorted(history_map.values(), key=lambda item: item.get("end_time") or "", reverse=True)
    for item in history_list:
        item["set_names"] = " / ".join(item["set_names"])
        item["case_all_time"] = round(item["case_all_time"], 2)
        item["pass_rate"] = round(item["pass_count"] / item["all_count"] * 100, 2) if item["all_count"] else 0
        item["status"] = "failed" if item["fail_count"] or item["error_count"] else "passed"
    if page_size:
        history_list = history_list[:int(page_size)]
    return jsonify({'code': 200, 'msg': '请求成功', 'data': history_list})


@test_task.route('/get_testtask_config_snapshot', methods=["POST"])
def get_testtask_config_snapshot():
    """获取测试任务级配置快照"""
    task_id = request.json.get("task_id")
    run_id = request.json.get("run_id")
    if not task_id:
        return jsonify({'code': 404, 'msg': '请传入测试任务id', 'data': None})
    task = TestTask.query.filter_by(id=task_id).filter_by(is_delete=0).first()
    if not task:
        return jsonify({'code': 404, 'msg': '测试任务不存在', 'data': None})
    permission_error = _require_project_ids_permission(project_ids_from_task(task_id), "view")
    if permission_error:
        return permission_error
    run_id = run_id or task.run_id
    set_ids = _safe_id_list(task.test_set_ids)
    task_config_ids = _safe_id_list(task.config_ids)
    reports = []
    if run_id and set_ids:
        reports = Reports.query.filter_by(run_id=run_id).filter(Reports.set_id.in_(set_ids)).all()
    snapshot_config_ids = set(task_config_ids)
    for report in reports:
        snapshot_config_ids.update(_safe_id_list(report.config_id))
    config_query = Cfgs.query.filter(Cfgs.id.in_(list(snapshot_config_ids))).all() if snapshot_config_ids else []
    config_map = {item.id: item for item in config_query}
    set_query = TestSet.query.filter_by(is_delete=0).filter(TestSet.id.in_(set_ids)).all() if set_ids else []
    set_map = {item.id: item for item in set_query}

    def config_payload(config_id):
        config = config_map.get(config_id)
        if not config:
            return {"id": config_id, "cfg_name": "配置不存在", "cfg": "", "mark": ""}
        return {
            "id": config.id,
            "cfg_name": config.cfg_name,
            "cfg": config.cfg,
            "mark": config.mark or "",
        }

    report_snapshots = []
    for report in reports:
        set_info = set_map.get(report.set_id)
        config_ids = _safe_id_list(report.config_id)
        report_snapshots.append({
            "set_id": report.set_id,
            "set_name": set_info.title if set_info else str(report.set_id),
            "project_name": set_info.project_name if set_info else "",
            "report_title": report.title,
            "report_path": report.report_path,
            "updated_time": _format_time(report.updated_time),
            "config_ids": config_ids,
            "config_count": len(config_ids),
            "configs": [config_payload(config_id) for config_id in config_ids],
        })
    data = {
        "task_id": task.id,
        "task_name": task.name,
        "run_id": run_id,
        "task_config_ids": task_config_ids,
        "task_configs": [config_payload(config_id) for config_id in task_config_ids],
        "set_snapshots": report_snapshots,
        "report_count": len(report_snapshots),
    }
    return jsonify({'code': 200, 'msg': '请求成功', 'data': data})


@test_task.route('/get_testtask_timeline', methods=["POST"])
def get_testtask_timeline():
    """获取测试任务执行时间线"""
    task_id = request.json.get("task_id")
    run_id = request.json.get("run_id")
    if not task_id:
        return jsonify({'code': 404, 'msg': '请传入测试任务id', 'data': None})
    task = TestTask.query.filter_by(id=task_id).filter_by(is_delete=0).first()
    if not task:
        return jsonify({'code': 404, 'msg': '测试任务不存在', 'data': None})
    permission_error = _require_project_ids_permission(project_ids_from_task(task_id), "view")
    if permission_error:
        return permission_error
    run_id = run_id or task.run_id
    set_ids = _safe_id_list(task.test_set_ids)
    set_query = TestSet.query.filter_by(is_delete=0).filter(TestSet.id.in_(set_ids)).all() if set_ids else []
    set_map = {item.id: item for item in set_query}
    ordered_sets = [set_map[set_id] for set_id in set_ids if set_id in set_map]
    reports = []
    result_counts = {}
    latest_result_time = {}
    if run_id and set_ids:
        reports = Reports.query.filter_by(run_id=run_id).filter(Reports.set_id.in_(set_ids)).all()
        count_rows = db.session.query(
            CaseResult.set_id,
            CaseResult.run_case_result,
            func.count(CaseResult.id)
        ).filter(
            CaseResult.run_id == run_id,
            CaseResult.set_id.in_(set_ids)
        ).group_by(CaseResult.set_id, CaseResult.run_case_result).all()
        for set_id, result, count in count_rows:
            result_counts.setdefault(set_id, {"passed": 0, "failed": 0, "error": 0, "total": 0})
            result_key = result or "unknown"
            result_counts[set_id][result_key] = count
            result_counts[set_id]["total"] += count
        latest_rows = db.session.query(
            CaseResult.set_id,
            func.max(CaseResult.updated_time)
        ).filter(
            CaseResult.run_id == run_id,
            CaseResult.set_id.in_(set_ids)
        ).group_by(CaseResult.set_id).all()
        latest_result_time = {set_id: updated_time for set_id, updated_time in latest_rows}
    report_map = {item.set_id: item for item in reports}
    timeline = [{
        "type": "task",
        "status": "created",
        "title": "任务创建",
        "time": _format_time(task.created_time),
        "desc": task.name,
    }]
    if task.timed_task_time:
        timeline.append({
            "type": "task",
            "status": "scheduled",
            "title": "定时等待",
            "time": task.timed_task_time,
            "desc": "到达定时时间后开始执行",
        })
    if task.start_task_time:
        timeline.append({
            "type": "task",
            "status": "running",
            "title": "任务开始执行",
            "time": task.start_task_time,
            "desc": "run_id: {}".format(run_id or ""),
        })
    for index, item in enumerate(ordered_sets, start=1):
        report = report_map.get(item.id)
        counts = result_counts.get(item.id, {"passed": 0, "failed": 0, "error": 0, "total": 0})
        status = "pending"
        if task.run_status == 1 and task.progress_set_id == item.id:
            status = "running"
        elif report or item.run_status == 2:
            status = "finished"
        elif item.run_status == 1:
            status = "running"
        time_text = _format_time(latest_result_time.get(item.id) or (report.updated_time if report else item.updated_time))
        desc_parts = [
            "进度 {}%".format(item.schedule or 0),
            "通过 {}".format(counts.get("passed", 0)),
            "失败 {}".format(counts.get("failed", 0)),
            "错误 {}".format(counts.get("error", 0)),
        ]
        timeline.append({
            "type": "testset",
            "status": status,
            "order": index,
            "set_id": item.id,
            "title": "{}. {}".format(index, item.title),
            "time": time_text,
            "desc": " / ".join(desc_parts),
            "project_name": item.project_name,
            "schedule": item.schedule or 0,
            "pass_count": counts.get("passed", 0),
            "fail_count": counts.get("failed", 0),
            "error_count": counts.get("error", 0),
            "all_count": counts.get("total", 0),
            "report_title": report.title if report else "",
            "report_path": report.report_path if report else "",
            "case_all_time": str(report.case_all_time) if report and report.case_all_time is not None else "",
        })
    if task.run_status == 2:
        timeline.append({
            "type": "task",
            "status": "finished",
            "title": "任务执行完成",
            "time": _format_time(task.updated_time),
            "desc": "已生成报告 {} 个".format(len(reports)),
        })
    data = {
        "task_id": task.id,
        "task_name": task.name,
        "run_id": run_id,
        "run_status": task.run_status,
        "schedule": task.schedule or 0,
        "set_count": len(ordered_sets),
        "report_count": len(reports),
        "timeline": timeline,
    }
    return jsonify({'code': 200, 'msg': '请求成功', 'data': data})
