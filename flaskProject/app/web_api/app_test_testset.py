# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
# 从app模块中即从__init__.py中导入创建的app应用
import random
import traceback
from flask import jsonify, request, Response
from app.commom.add_test_case import *
from app.commom.test_script_run import th_run_set, update_config_file
from app.web_api import testset

from app.models.test_api_models import *

from concurrent.futures import ProcessPoolExecutor
from flasgger import swag_from
import time
import datetime
from config import report_path
from config import logs
from app.lib import image
from app.tools import request_details
from app.tools import sched_task
import os
import psutil
from time import strftime as strf_time
from time import gmtime
import signal
import yagmail
from app.tools.util import EmailThread
from app.tools.auth_permissions import (
    allowed_project_ids,
    filter_project_query,
    project_id_from_report_path,
    project_id_from_testset,
    require_project_permission,
)
from sqlalchemy import func

# workers = multiprocessing.cpu_count() * 2
workers = 5
executor = ProcessPoolExecutor(workers)
scheduler_job = {}


def _timed_testset_job_id(testset_id, run_id):
    return f"testset:{testset_id}:{run_id}"


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


def _safe_report_file_path(filename):
    if not filename:
        return None
    report_root = os.path.realpath(report_path)
    target_path = os.path.realpath(os.path.join(report_root, filename))
    try:
        if os.path.commonpath([report_root, target_path]) != report_root:
            return None
    except ValueError:
        return None
    return target_path


@testset.route('/ws')
def websocket():
    return """
    <!doctype html>
    <html>
      <head>
        <title>Flask-Sock Demo</title>
      </head>
      <body>
        <h1>Flask-Sock Demo</h1>
        <div id="log"></div>
        <br>
        <form id="form">
          <label for="text">Input: </label>
          <input type="text" id="text" autofocus>
        </form>
        <script>
          const log = (text, color) => {
            document.getElementById('log').innerHTML += `<span style="color: ${color}">${text}</span><br>`;
          };

          const socket = new WebSocket('ws://' + location.host + '/echo');
          socket.addEventListener('message', ev => {
            log('<<< ' + ev.data, 'blue');
          });
          document.getElementById('form').onsubmit = ev => {
            ev.preventDefault();
            const textField = document.getElementById('text');
            log('>>> ' + textField.value, 'red');
            socket.send(textField.value);
            textField.value = '';
          };
        </script>
      </body>
    </html>
    """


@testset.route('/get_testset_info', methods=["POST"])
@swag_from('../apidocs/get_testset_info.yml')
@request_details.log_request_response(module="get_testset_info")
def get_testset_info():
    """获取测试集合列表"""

    page_no = request.json.get("page_no", 0)
    page_size = request.json.get("page_size", 10)
    title = request.json.get("title", "")
    run_status = request.json.get("run_status")
    project_id = request.json.get("project_id")
    title = title.strip()
    allowed_ids = allowed_project_ids()
    if project_id:
        permission_error = require_project_permission(project_id, "view")
        if permission_error:
            return permission_error
    if project_id:
        query = TestSet.query.filter_by(project_id=project_id).filter_by(is_delete=0).all()
        if isinstance(run_status, int):
            query = TestSet.query.filter_by(project_id=project_id).filter_by(run_status=run_status).filter_by(
                is_delete=0).all()
        if title:
            query = TestSet.query.filter(TestSet.title.like(f"%{title}%")).filter_by(project_id=project_id).filter_by(
                is_delete=0).all()
            if isinstance(run_status, int):
                query = TestSet.query.filter(TestSet.title.like(f"%{title}%")).filter_by(
                    run_status=run_status).filter_by(
                    project_id=project_id).filter_by(is_delete=0).all()
    elif title:
        query = TestSet.query.filter(TestSet.title.like(f"%{title}%")).filter_by(is_delete=0).all()
        if isinstance(run_status, int):
            query = TestSet.query.filter(TestSet.title.like(f"%{title}%")).filter_by(run_status=run_status).filter_by(
                is_delete=0).all()
    else:
        query = TestSet.query.filter_by(is_delete=0).order_by(db.desc(TestSet.updated_time)).limit(page_size).offset(
            page_no)
        if isinstance(run_status, int):
            query = TestSet.query.filter_by(run_status=run_status).filter_by(is_delete=0).all()

    # 优化的代码
    # page_no = request.json.get("page_no", 0)
    # page_size = request.json.get("page_size", 10)
    # title = request.json.get("title", "").strip()
    # run_status = request.json.get("run_status")
    # project_id = request.json.get("project_id")
    #
    # query = TestSet.query
    #
    # if project_id:
    #     query = query.filter_by(project_id=project_id)
    #     if title:
    #         query = query.filter(TestSet.title.like(f"%{title}%"))
    #         if isinstance(run_status, int):
    #             query = query.filter_by(run_status=run_status)
    # elif title:
    #     query = query.filter(TestSet.title.like(f"%{title}%"))
    #     if isinstance(run_status, int):
    #         query = query.filter_by(run_status=run_status)
    # else:
    #     query = query.order_by(db.desc(TestSet.updated_time)).limit(page_size).offset(page_no)
    #     if isinstance(run_status, int):
    #         query = query.filter_by(run_status=run_status)
    #
    # results = query.all()

    # query = [i.to_dict() for i in query.all()]
    if allowed_ids is not None:
        query = [item for item in query if item.project_id in allowed_ids]
    query = [i.to_dict() for i in query]
    current_time = datetime.datetime.now()
    # 获取当前时间戳（Unix 时间戳，单位为秒）
    current_timestamp = int(current_time.timestamp())
    for i in query:
        case_count_total = db.session.query(func.sum(Cases.case_count)).filter(
            Cases.id.in_(eval(i.get("case_ids")))).scalar()
        i.update({"case_count_total": case_count_total})
        if i.get("updated_time"):
            i.update({"updated_time": i.get("updated_time").strftime("%Y-%m-%d %H:%M:%S")})
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
    return_dict = {'code': 200, 'msg': '请求成功', 'data': query}
    return jsonify(return_dict)


@testset.route('/update_testset', methods=["POST"])
# @swag_from('../apidocs/update_testset.yml')
@request_details.log_request_response(module="update_testset")
def update_testset():
    """更新测试集合"""
    # print(request.json)
    id = request.json.get("id")
    config_id = request.json.get("config_id")
    project_id = request.json.get("project_id")
    testset_title = request.json.get("testset_title")
    case_ids = request.json.get("case_ids")
    version_id = request.json.get("version_id")
    script_type = request.json.get("script_type")

    if not version_id or not config_id or not script_type or not testset_title or not project_id:
        return jsonify({"code": 404, "msg": "缺少必填参数", 'data': None})
    if not case_ids:
        return jsonify({'code': 404, 'msg': '测试用例列表不能为空', 'data': None})
    query = TestSet.query.filter_by(id=id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '测试集不存在', 'data': None})
    permission_error = require_project_permission(query.project_id, "edit")
    if permission_error:
        return permission_error
    permission_error = require_project_permission(project_id, "edit")
    if permission_error:
        return permission_error
    query.config = config_id
    query.project_id = project_id
    query.title = testset_title
    query.case_ids = str(case_ids)
    query.version_id = version_id
    query.type = script_type
    db.session.commit()
    return_dict = {'code': 200, 'msg': '请求成功', 'data': id}
    return jsonify(return_dict)


@testset.route('/add_testset', methods=["POST"])
@swag_from('../apidocs/add_testset.yml')
@request_details.log_request_response(module="add_testset")
def add_testset():
    """新增或修改测试集合"""
    config_id = request.json.get("config_id")
    project_id = request.json.get("project_id")
    testset_title = request.json.get("testset_title")
    mark = request.json.get("mark", "")
    case_ids = request.json.get("case_ids")
    version_id = request.json.get("version_id")
    script_type = request.json.get("script_type", 1)
    set_id = request.json.get("set_id")
    # version = Version.query.filter_by(id=version_id).first()
    previous_level = request.json.get("previous_level")
    email_to = request.json.get("email_to", "")
    priority_value = request.json.get("priority_value", 0)
    if previous_level and isinstance(previous_level, list):
        previous_level = previous_level[0]
    else:
        previous_level = None
    if project_id:
        if isinstance(project_id, list):
            project_id = project_id[0]
    permission_error = require_project_permission(project_id, "edit")
    if permission_error:
        return permission_error
    if not testset_title or not project_id:
        return jsonify({"code": 404, "msg": "缺少必填参数测试集名称或关联项目", 'data': None})
    testset_title = testset_title.strip()
    project_info = Project.query.filter_by(id=project_id).first()
    if set_id:
        testset_info = TestSet.query.filter_by(id=set_id).first()
    else:
        testset_info = TestSet.query.filter_by(title=testset_title).first()
    if not case_ids:
        return jsonify({'code': 404, 'msg': '测试用例列表不能为空', 'data': None})
    # case_group = Cases.query.filter(Cases.id.in_(case_ids)).group_by(Cases.project_id).all()
    case_group = Cases.query.filter(Cases.id.in_(case_ids)).all()
    project_id_list = [i.project_id for i in case_group]
    case_group = list(set(project_id_list))
    if len(case_group) > 1:
        return jsonify({'code': 404, 'msg': '测试集不能同时添加多个项目用例', 'data': None})
    # print(project_id, case_group[0].project_id)
    # if project_id != case_group[0].project_id:
    if project_id != case_group[0]:
        return jsonify({'code': 404, 'msg': '测试用例所属项目与测试集关联脚本项目不符', 'data': None})
    if testset_info:
        if testset_info.run_status not in [0, 2]:
            return jsonify({'code': 404, 'msg': '测试集合运行中，不允许修改用例', 'data': None})
        testset_info.case_ids = str(case_ids)
        testset_id = testset_info.id
        testset_info.title = testset_title
        testset_info.project_id = project_info.id
        testset_info.project_name = project_info.name
        testset_info.previous_level = previous_level
        testset_info.mark_info = mark
        testset_info.config = str(config_id)
        testset_info.email_to = email_to
        testset_info.version_id = version_id
        testset_info.priority = priority_value
        return_dict = {'code': 200, 'msg': f'修改{testset_title}测试集成功', 'data': testset_id}
    else:
        new_testset = TestSet(config=str(config_id), title=testset_title, case_ids=str(case_ids), project_id=project_id,
                              version_id=version_id, modify_count=0, mark=0, fixed_cc=0, run_status=0,
                              project_name=project_info.name, previous_level=previous_level, mark_info=mark,
                              priority=priority_value, email_to=email_to,
                              type=script_type)
        db.session.add(new_testset)
        db.session.flush()
        testset_id = new_testset.id
        return_dict = {'code': 200, 'msg': f'新增{testset_title}测试集成功', 'data': testset_id}
    db.session.commit()
    return jsonify(return_dict)


@testset.route('/run_testset', methods=["POST"])
@swag_from('../apidocs/run_testset.yml')
@request_details.log_request_response(module="run_testset")
def run_testset():
    """运行测试集合"""
    id = request.json.get("id")
    permission_error = require_project_permission(project_id_from_testset(id), "run")
    if permission_error:
        return permission_error
    cfg_id = request.json.get("cfg_id")
    # project_name = request.json.get("project_name")
    # project_id = request.json.get("project_id")
    version_id = request.json.get("version_id")
    script_type = request.json.get("script_type")
    priority_value = request.json.get("priority_value", 0)
    rerun_type = request.json.get("rerun_type")
    mark = request.json.get("mark", "")
    email_to = request.json.get("email_to", "")
    sent_email = request.json.get("sent_email", "")
    timed_task_time = request.json.get("timed_task_time")
    start_process = request.json.get("start_process")
    query = TestSet.query.filter_by(id=id).first()
    project_name = query.project_name
    project_id = query.project_id
    if cfg_id:
        if isinstance(cfg_id, int):
            cfg_id = [cfg_id]
        cfgids = list()
        for i in cfg_id:
            cfg = Cfgs.query.filter_by(id=i).first()
            if cfg:
                cfgids.append(cfg.id)
        if cfgids:
            query.config = str(cfgids)
    if not cfg_id:
        cfg_id = query.config
    if version_id:
        version = Version.query.filter_by(id=version_id).first()
        version_id = version.id
        query.version_id = version_id
    if not script_type:
        script_type = query.type
        # cfg_id=eval(cfg_id)
    if not mark:
        mark = ""
    query.mark_info = mark
    query.priority = priority_value
    query.email_to = email_to
    if not version_id:
        version_id = None
    if start_process:
        start_process = int(start_process)
        if int(start_process) >= 5:
            start_process = 5
    if not project_name or not project_id:
        return jsonify({'code': 404, 'msg': '没有输入需要执行的项目名', 'data': []})
    cfg_status = update_config_file(cfg_id, project=project_name)
    if not cfg_status:
        return jsonify({'code': 404, 'msg': 'pytest用例配置文件更新失败！请检查配置和项目名称是否存在', 'data': []})
    if query.run_status in [1]:
        return jsonify({'code': 404, 'msg': '测试集合运行中，请勿重复运行！', 'data': []})
    if timed_task_time:
        # 禁止设置1个以上的定时任务
        # timed_task_set_info = TestSet.query.filter(TestSet.timed_task_time.isnot('')).first()
        # if timed_task_set_info:
        #     return jsonify({'code': 404, 'msg': '已有定时任务，请等待定时任务完成后再设置定时任务', 'data': []})

        # 定时任务限制时间。同一时间允许多个任务，APScheduler job id 使用测试集+run_id 保证唯一。
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
        if timed_task_time:
            def test_task():
                # scheduler = BackgroundScheduler(daemon=True)
                job_id = _timed_testset_job_id(id, run_id_num)
                sched_task.sched.add_job(th_run_set, 'date', run_date=timed_task_time, id=job_id,
                                         kwargs={"version_id": version_id,
                                                 "rerun_type": rerun_type,
                                                 "set_id": id,
                                                 "config_id": cfg_id,
                                                 "script_type": script_type,
                                                 "run_id_num": run_id_num,
                                                 "mark": str(mark),
                                                 "email_to": email_to,
                                                 "sent_email": sent_email,
                                                 "project_id": project_id, "timed_task_time": timed_task_time,
                                                 "start_process": start_process},
                                         jobstore='redis',
                                         replace_existing=False, misfire_grace_time=60, executor="processpool")
                scheduler_job.update({job_id: job_id})
                # scheduler.start()
                # executor.submit(scheduler.running)
                print(sched_task.sched.get_jobs())

            test_task()
        else:
            query.timed_task_time = ""
            db.session.commit()
            executor.submit(th_run_set, version_id=version_id, rerun_type=rerun_type, set_id=id, config_id=cfg_id,
                            script_type=script_type, run_id_num=run_id_num, mark=str(mark), email_to=email_to,
                            sent_email=sent_email,
                            project_id=project_id, start_process=start_process)
    except Exception as e:
        db.session.rollback()
        query.timed_task_time = ""
        query.run_type = ""
        db.session.commit()
        traceback.print_exc()
        return jsonify({'code': 404, 'msg': f'执行错误:{e}', 'data': []})
    return_dict = {'code': 200, 'msg': '请求成功', 'data': []}
    return jsonify(return_dict)


@testset.route('/get_job_list', methods=["POST"])
@swag_from('../apidocs/get_job_list.yml')
def get_job_list():
    """获取定时任务列表"""
    jobs = sched_task.sched.get_jobs()
    print(jobs)
    job_list = []
    for job in jobs:
        job_info = {'id': job.id,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    "name": str(job.name)}
        job_list.append(job_info)
    return_dict = {'code': 200, 'msg': '请求成功', 'data': job_list}
    return return_dict


@testset.route('/stop_testset', methods=["POST"])
@swag_from('../apidocs/stop_testset.yml')
@request_details.log_request_response(module="stop_testset")
def stop_testset():
    """终止测试集合"""
    ids = request.json.get("ids")
    if not ids:
        return jsonify({'code': 404, 'msg': '请传入需要终止的测试集id', 'data': []})
    stop_set_title = list()
    for id in ids:
        query = TestSet.query.filter_by(id=id).first()
        if not query:
            continue
        permission_error = require_project_permission(query.project_id, "run")
        if permission_error:
            return permission_error
        if query.run_status == 1:
            query.run_status = 2
            query.schedule = 0
            timed_task_time_value = query.timed_task_time
            job_id = _timed_testset_job_id(id, query.run_id) if query.run_id else None
            # pid = query.pid
            query.timed_task_time = ""
            query.start_task_time = ""
            query.run_type = ""
            query.pid = 0
            if timed_task_time_value:
                current_time = datetime.datetime.now()
                time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
                query.timed_task_time = f"已经于{time_string}手动终止定时任务"
            db.session.commit()
            stop_set_title.append(query.title)
            try:
                _remove_scheduler_job([job_id, timed_task_time_value])
            except Exception as e:
                print(e)
    return jsonify({'code': 200, 'msg': '测试集合执行已终止', 'data': stop_set_title})


@testset.route('/delete_testset', methods=["POST"])
@swag_from('../apidocs/delete_testset.yml')
@request_details.log_request_response(module="delete_testset")
def delete_testset():
    """删除测试集合"""
    ids = request.json.get("ids")
    if not ids:
        return jsonify({'code': 404, 'msg': '请传入需要删除的测试集id', 'data': []})
    delete_set_title = list()
    for set_id in ids:
        query = TestSet.query.filter_by(id=set_id).filter_by(is_delete=0).first()
        if not query:
            continue
        permission_error = require_project_permission(query.project_id, "edit")
        if permission_error:
            return permission_error
        if query.run_status in [1]:
            continue
        query.is_delete = 1
        delete_set_title.append(query.title)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '测试集已删除', 'data': delete_set_title})


@testset.route('/report_content', methods=["POST"])
@swag_from('../apidocs/report_content.yml')
@request_details.log_request_response(module="report_content")
def report_content():
    """获取测试报告内容"""
    filename = request.json.get("filename")
    set_id = request.json.get("set_id")
    if not filename:
        return jsonify({"code": 404, "msg": "没有测试报告", "data": None})
    query = Reports.query.filter_by(report_path=filename).order_by(
        db.desc(Reports.updated_time)).first()
    if not query:
        return jsonify({"code": 404, "msg": "没有测试报告", "data": None})
    if set_id:
        query = Reports.query.filter_by(report_path=filename).filter_by(set_id=set_id).order_by(
            db.desc(Reports.updated_time)).first()
    if not query:
        return jsonify({"code": 404, "msg": "没有测试报告", "data": None})
    permission_error = require_project_permission(query.project_id, "view")
    if permission_error:
        return permission_error

    ext = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "cr2": "image/x-canon-cr2",
        "tiff": "image/tiff",
        "bmp": "image/bmp",
        "jxr": "image/vnd.ms-photo",
        "psd": "image/vnd.adobe.photoshop",
        "ico": "image/x-icon",
        "epub": "application/epub+zip",
        "zip": "application/zip",
        "tar": "application/x-tar",
        "rar": "application/x-rar-compressed",
        "pdf": "application/pdf",
        "doc": "application/msword",
        "rtf": "application/rtf",
        "html": "text/html",
        "htm": "text/html",
        "stm": "text/html",
        "xlsx": "application/vnd.ms-excel",
        "xls": "application/vnd.ms-excel",
        "css": "text/css"
    }
    mine = query.report_path.split(".")[-1]
    if mine in ext.keys():
        minetype = ext[mine]
    else:
        minetype = "text/html"
    report_allpath = _safe_report_file_path(query.report_path)
    if not report_allpath:
        return jsonify({"code": 404, "msg": "测试报告路径不合法！", "data": None})
    if not os.path.exists(report_allpath):
        return jsonify({"code": 404, "msg": "测试报告不存在！", "data": None})
    with open(report_allpath, "rb") as f:
        response = Response(f.read(), mimetype=minetype)

    # with open(report_allpath, "r", encoding="utf8") as f:
    #     response = f.read()
    return response


@testset.route('/get_report_info', methods=["POST"])
@swag_from('../apidocs/get_report_info.yml')
# @request_details.log_request_response(module="get_report_info")
def get_report_info():
    """获取报告列表"""
    set_id = request.json.get("set_id")
    title = request.json.get("title", "")
    run_id = request.json.get("run_id")
    title = title.strip()
    page_no = request.json.get("page", 0)
    page_size = request.json.get("page_size", 10)
    project_id = request.json.get("project_id")
    allowed_ids = allowed_project_ids()
    if project_id:
        permission_error = require_project_permission(project_id, "view")
        if permission_error:
            return permission_error
    try:
        if set_id:
            if title:
                query = Reports.query.filter_by(set_id=set_id).filter(Reports.title.like(f"%{title}%")).order_by(
                    db.desc(Reports.updated_time)).limit(page_size).offset(
                    page_no).all()
            else:
                query = Reports.query.filter_by(set_id=set_id).order_by(db.desc(Reports.updated_time)).limit(
                    page_size).offset(
                    page_no).all()
        elif project_id:
            if set_id:
                if title:
                    query = Reports.query.filter_by(project_id=project_id).filter_by(set_id=set_id).filter(
                        Reports.title.like(f"%{title}%")).order_by(
                        db.desc(Reports.updated_time)).limit(page_size).offset(
                        page_no).all()
                else:
                    query = Reports.query.filter_by(project_id=project_id).filter_by(set_id=set_id).order_by(
                        db.desc(Reports.updated_time)).limit(
                        page_size).offset(
                        page_no).all()
            else:
                query = Reports.query.filter_by(project_id=project_id).order_by(
                    db.desc(Reports.updated_time)).limit(page_size).offset(
                    page_no).all()
        elif title:
            query = Reports.query.filter(Reports.title.like(f"%{title}%")).order_by(
                db.desc(Reports.updated_time)).limit(page_size).offset(
                page_no).all()
        elif run_id:
            query = Reports.query.filter_by(run_id=run_id).order_by(
                Reports.updated_time).limit(page_size).offset(
                page_no).all()
        else:
            query = Reports.query.order_by(db.desc(Reports.updated_time)).limit(page_size).offset(page_no).all()
        if allowed_ids is not None:
            query = [item for item in query if item.project_id in allowed_ids]
        query = [i.to_dict() for i in query]
        set_ids = image.get_values_by_key(query, "set_id", values=[])
        if isinstance(set_ids, int):
            set_ids = [set_ids]
        set_id_list = None
        if set_ids:
            set_id_list = TestSet.query.filter(TestSet.id.in_(set_ids)).all()
        if set_id_list:
            set_id_list = [i.to_dict() for i in set_id_list]
            for i in range(len(query)):
                for j in set_id_list:
                    if query[i].get("set_id") == j.get("id"):
                        query[i].update({"set_title": j.get("title")})
        cfg_ids = image.get_values_by_key(query, "config_id", values=[])
        # print(type(cfg_ids))
        # print(cfg_ids)
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
                check_ids = eval(query[i].get("config_id"))
                if isinstance(check_ids, int):
                    check_ids = [check_ids]
                names = list()
                for j in config_id_list:
                    if j.get("id") in check_ids:
                        names.append(j.get("cfg_name"))
                query[i].update({"cfg_name": names})
        for i in query:
            if i.get("updated_time"):
                i.update({"updated_time": i.get("updated_time").strftime("%Y-%m-%d %H:%M:%S")})
        return_dict = {'code': 200, 'msg': '请求成功', 'data': query}
        return jsonify(return_dict)
    except Exception as e:
        print(traceback.print_exc())
        return_dict = {'code': 404, 'msg': '内部错误', 'data': None}
        return jsonify(return_dict)


@testset.route('/report_mark', methods=["POST"])
@swag_from('../apidocs/report_mark.yml')
def report_mark():
    mark = request.json.get("mark", "")
    report_id = request.json.get("id")
    if not report_id:
        return {'code': 404, 'msg': '没有report_id', 'data': None}
    query = Reports.query.filter_by(id=report_id).first()
    if not query:
        return {'code': 404, 'msg': '报告不存在', 'data': None}
    permission_error = require_project_permission(query.project_id, "edit")
    if permission_error:
        return permission_error
    query.mark = mark
    db.session.commit()
    return {'code': 200, 'msg': '请求成功！', 'data': None}


@testset.route('/send_email', methods=["POST"])
@swag_from('../apidocs/send_email.yml')
def send_email_a():
    email_title = request.json.get("email_title", "")
    email_to = request.json.get("email_to")
    report_name = request.json.get("report_path")
    project_name = request.json.get("project_name", "")
    set_title = request.json.get("set_title", "")
    try:
        permission_error = require_project_permission(project_id_from_report_path(report_name), "view")
        if permission_error:
            return permission_error
        dir_path = _safe_report_file_path(report_name)
        if not dir_path or not os.path.exists(dir_path):
            return {'code': 404, 'msg': '报告文件不存在或路径不合法', 'data': None}
        if email_title:
            contents = ['您好：', email_title,
                        yagmail.inline(r"{dir_path}".format(dir_path=dir_path))]
        else:
            contents = ['您好：',
                        f'请查收{project_name}项目的{set_title}测试集的自动化测试报告:',
                        yagmail.inline(r"{dir_path}".format(dir_path=dir_path))]
        t = EmailThread(email_to,
                        subject="自动化测试报告",
                        contents=contents,
                        attachments=None)
        t.start()
        return {'code': 200, 'msg': '请求成功！', 'data': None}
    except Exception as e:
        print(e)
        return {'code': 404, 'msg': f'发送失败>>>>{e}', 'data': None}


@testset.route('/files/<path:path>')
def serve_files(path):
    ext = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "cr2": "image/x-canon-cr2",
        "tiff": "image/tiff",
        "bmp": "image/bmp",
        "jxr": "image/vnd.ms-photo",
        "psd": "image/vnd.adobe.photoshop",
        "ico": "image/x-icon",
        "epub": "application/epub+zip",
        "zip": "application/zip",
        "tar": "application/x-tar",
        "rar": "application/x-rar-compressed",
        "pdf": "application/pdf",
        "doc": "application/msword",
        "rtf": "application/rtf",
        "html": "text/html",
        "htm": "text/html",
        "stm": "text/html",
        "xlsx": "application/vnd.ms-excel",
        "xls": "application/vnd.ms-excel",
        "css": "text/css"
    }
    mine = path.split(".")[-1]
    if mine in ext.keys():
        minetype = ext[mine]
    else:
        minetype = "text/html"
    log_allpath = os.path.join(logs, path)
    if not os.path.exists(log_allpath):
        return jsonify({"code": 404, "msg": "日志文件不存在！", "data": None})
    with open(log_allpath, "rb") as f:
        response = Response(f.read(), mimetype=minetype)
    return response


@testset.route('/union_testask', methods=["POST"])
@swag_from('../apidocs/union_testask.yml')
def union_testset():
    """测试集关联的测试任务"""
    set_id = request.json.get("set_id")
    if not set_id:
        return jsonify({'code': 404, 'msg': '缺少必填参数', 'data': ""})
    # query = TestSet.query.all()
    query = TestTask.query.filter_by(is_delete=0).all()
    query_list = list()
    for i in query:
        if i.test_set_ids:
            test_set_ids = eval(i.test_set_ids)
            if set_id in test_set_ids:
                query_list.append(i)
    query = [i.to_dict() for i in query_list]
    return_dict = {'code': 200, 'msg': '请求成功', 'data': query}
    return jsonify(return_dict)


@testset.route('/sys_info', methods=["POST"])
@swag_from('../apidocs/sys_info.yml')
def sys_info():
    """获取当前cpu和内存信息"""
    memory_info = psutil.virtual_memory().percent
    cpu_percent = psutil.cpu_percent(interval=1)
    # query = TestSet.query.filter_by(is_delete=0).filter_by(run_status=1).all()
    data = {"memory_info": memory_info, "cpu_percent": cpu_percent}
    return_dict = {'code': 200, 'msg': '请求成功', 'data': data}
    return jsonify(return_dict)
