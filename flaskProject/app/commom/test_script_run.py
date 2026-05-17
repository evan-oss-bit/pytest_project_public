#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
import pytest
from .pytest_json_report.plugin import JSONReport
# from pytest_jsonreport.plugin import JSONReport
from config import logs
import configparser
import time
import config
from app.models.test_api_models import *
from app.lib.image import *
from app.commom.create_report import *
import yagmail
import os
import traceback
import asyncio
# from aiofiles import open as async_open
import aiofiles
from app.tools.util import EmailThread
import copy


async def write_to_logfile(file_path_name, log_info, longrepr):
    async with aiofiles.open(file_path_name, mode='w', encoding='utf-8') as f:
        if log_info:
            for i in log_info:
                if isinstance(i, dict):
                    await f.write(
                        f"{i.get('asctime')} {i.get('filename')}:{i.get('lineno')} [{i.get('levelname')}]: {i.get('msg')}\n")
                else:
                    for j in i:
                        await f.write(
                            f"{j.get('asctime')} {j.get('filename')}:{j.get('lineno')} [{j.get('levelname')}]: {j.get('msg')}\n")
        await f.write(f"{longrepr}\n")


def update_config_file(config_id, project="testcenter", file_name="data.ini"):
    """

    :param config_id:
    :param project:
    :param file_name:
    :return:
    """
    # 连接sql
    session = config.db_work(db_path=config.AppConFig.sql_url)
    try:
        path = os.path.join(config.testscriptproject, project, file_name)
        conf = configparser.ConfigParser()
        conf.read(path, encoding="utf-8")
        # print(type(config_id))
        if isinstance(config_id, list) and config_id:
            # config_ids = eval(config_id)
            query = session.query(Cfgs).filter(Cfgs.id.in_(config_id)).all()
            if not query:
                return False
            if len(config_id) != len(query):
                return False
            for data in query:
                cfg = data.cfg
                # cfg_name = data.cfg_name
                cfg = eval(cfg)
                # print(cfg)
                if not cfg:
                    return False
                for k, v in cfg.items():
                    conf[k] = v
                with open(path, "w", encoding='utf-8') as f:
                    conf.write(f)
            return True
        else:
            return False
    except Exception as e:
        traceback.print_exc()
        print(e)
        return False
    finally:
        if session:
            session.close()


def script_run(*args, **kwargs):
    session = kwargs.get("db_session")
    case_title = kwargs.get("case_title")
    set_id = kwargs.get("set_id")
    case_id = kwargs.get("case_id")
    config_id = kwargs.get("config_id")
    version_id = kwargs.get("version_id")
    run_id = kwargs.get("run_id")
    project_id = kwargs.get("project_id")
    project_name = kwargs.get("project_name")
    case_ids_len = kwargs.get("case_ids_len")
    case_id_coor = kwargs.get("case_id_coor")
    mark = kwargs.get("mark")
    case_name = kwargs.get("case_name")

    try:
        plugin = JSONReport()
        pytest.main(args[0], plugins=[plugin])
        tests = plugin.report.get("tests")
        created = plugin.report.get("created")
        ten_time = time.localtime(created)
        case_created = time.strftime("%Y-%m-%d %H:%M:%S", ten_time)
        duration = plugin.report.get("duration")
        run_case_result = tests[0]["outcome"]
        longrepr = get_values_by_key(tests[0], "longrepr", [])
        log_info = get_values_by_key(plugin.report, "log", [])
        print(plugin.report)
        if not longrepr:
            longrepr = ""
        if isinstance(longrepr, list):
            longrepr = longrepr[0]
        file_path_name = ""
        file_name = ""

        try:
            log_names = case_title.split("::")
            log_name = "_".join(log_names)
            file_name = f"{log_name}_{str(run_id)}_{get_uuid_name()}.log"
            if not os.path.exists(logs):
                os.makedirs(logs)
            file_path_name = os.path.join(logs, file_name)
            asyncio.run(write_to_logfile(file_path_name, log_info, longrepr))
        except Exception as e:
            print(traceback.print_exc())

        try:
            set_info = session.query(TestSet).filter_by(id=kwargs.get("set_id")).first()
            set_info.schedule = round((case_id_coor + 1) / case_ids_len * 100, 2)
            res = CaseResult(case_title=case_title, set_id=set_id, case_id=case_id, config_id=config_id,
                             version_id=version_id, mark=mark, longrepr=str(longrepr), file_path_name=file_path_name,
                             file_name=file_name, run_info=str(tests), run_id=run_id, project_id=project_id,
                             case_name=case_name, project_name=project_name, duration=duration,
                             case_created=case_created,
                             run_case_result=run_case_result)
            session.add(res)
            session.commit()
        except Exception as e:
            print(e)
            session.rollback()
        return tests
    except Exception as e:
        print("这是脚本执行错误信息：", traceback.print_exc())
        return [{"case_id": case_id, "outcome": "error", "error_info": str(e)}]


# async def write_to_logfile(file_path_name, log_info, longrepr):
#     try:
#         async with aiofiles.open(file_path_name, "w", encoding="utf-8") as f:
#             if log_info:
#                 for i in log_info:
#                     if isinstance(i, dict):
#                         await f.write(
#                             f"{i.get('asctime')} {i.get('filename')}:{i.get('lineno')} [{i.get('levelname')}]: {i.get('msg')}\n")
#                     else:
#                         for j in i:
#                             await f.write(
#                                 f"{j.get('asctime')} {j.get('filename')}:{j.get('lineno')} [{j.get('levelname')}]: {j.get('msg')}\n")
#             await f.write(f"{longrepr}\n")
#     except Exception as e:
#         print(traceback.print_exc())
#
# async def write_main(file_path_name, log_info, longrepr):
#     await write_to_logfile(file_path_name, log_info, longrepr)

# def script_run(*args, **kwargs):
#     """
#
#     :param args:
#     :param kwargs:
#     :return:
#     """
#     session = kwargs.get("db_session")
#     case_title = kwargs.get("case_title")
#     set_id = kwargs.get("set_id")
#     case_id = kwargs.get("case_id")
#     config_id = kwargs.get("config_id")
#     version_id = kwargs.get("version_id")
#     run_id = kwargs.get("run_id")
#     project_id = kwargs.get("project_id")
#     project_name = kwargs.get("project_name")
#     case_ids_len = kwargs.get("case_ids_len")
#     case_id_coor = kwargs.get("case_id_coor")
#     mark = kwargs.get("mark")
#     case_name = kwargs.get("case_name")
#     try:
#         plugin = JSONReport()
#         pytest.main(args[0], plugins=[plugin])
#         tests = plugin.report.get("tests")
#         # print(f"tests:{tests}")
#         # 用例开始时间
#         created = plugin.report.get("created")
#         ten_time = time.localtime(created)
#         case_created = time.strftime("%Y-%m-%d %H:%M:%S", ten_time)
#         # 该用例耗时
#         duration = plugin.report.get("duration")
#         run_case_result = tests[0]["outcome"]
#         longrepr = get_values_by_key(tests[0], "longrepr", [])
#         log_info = get_values_by_key(plugin.report, "log", [])
#         if not longrepr:
#             longrepr = ""
#         if isinstance(longrepr, list):
#             longrepr = longrepr[0]
#         file_path_name = ""
#         file_name = ""
#         try:
#             log_names = case_title.split("::")
#             log_name = "_".join(log_names)
#             file_name = f"{log_name}_{str(run_id)}.log"
#             if not os.path.exists(logs):
#                 os.makedirs(logs)
#             file_path_name = os.path.join(logs, file_name)
#             # 运行主协程
#             # asyncio.run(write_main(file_path_name, log_info, longrepr))
#             # 协程启动
#             # loop = asyncio.get_event_loop()
#             # loop.run_until_complete(write_to_logfile(file_path_name, log_info, longrepr))
#             with open(file_path_name, "w", encoding="utf-8") as f:
#                 if log_info:
#                     for i in log_info:
#                         if isinstance(i, dict):
#                             f.write(
#                                 f"{i.get('asctime')} {i.get('filename')}:{i.get('lineno')} [{i.get('levelname')}]: {i.get('msg')}\n")
#                         else:
#                             for j in i:
#                                 f.write(
#                                     f"{j.get('asctime')} {j.get('filename')}:{j.get('lineno')} [{j.get('levelname')}]: {j.get('msg')}\n")
#                 f.write(f"{longrepr}\n")
#         except Exception as e:
#             print(traceback.print_exc())
#         try:
#             set_info = session.query(TestSet).filter_by(id=kwargs.get("set_id")).first()
#             set_info.schedule = round((case_id_coor + 1) / case_ids_len * 100, 2)
#             res = CaseResult(case_title=case_title, set_id=set_id, case_id=case_id, config_id=config_id,
#                              version_id=version_id, mark=mark, longrepr=str(longrepr), file_path_name=file_path_name,
#                              file_name=file_name,
#                              run_info=str(tests), run_id=run_id, project_id=project_id, case_name=case_name,
#                              project_name=project_name, duration=duration, case_created=case_created,
#                              run_case_result=run_case_result)
#             session.add(res)
#             session.commit()
#         except Exception as e:
#             print(e)
#             session.rollback()
#             # time.sleep(1)
#         return tests
#     except Exception as e:
#         print("这是脚本执行错误信息：", traceback.print_exc())
#         return [{"case_id": case_id, "outcome": "error", "error_info": str(e)}]
#
#     # return tests
def single_script_run(*args, **kwargs):
    session = kwargs.get("db_session")
    case_title = kwargs.get("case_title")
    set_id = kwargs.get("set_id")
    case_id = kwargs.get("case_id")
    config_id = kwargs.get("config_id")
    version_id = kwargs.get("version_id")
    run_id = kwargs.get("run_id")
    project_id = kwargs.get("project_id")
    project_name = kwargs.get("project_name")
    # case_ids_len = kwargs.get("case_ids_len")
    # case_id_coor = kwargs.get("case_id_coor")
    mark = kwargs.get("mark")
    case_name = kwargs.get("case_name")

    try:
        plugin = JSONReport()
        pytest.main(args[0], plugins=[plugin])
        tests = plugin.report.get("tests")
        # print(plugin.report)
        created = plugin.report.get("created")
        ten_time = time.localtime(created)
        case_created = time.strftime("%Y-%m-%d %H:%M:%S", ten_time)
        duration = plugin.report.get("duration")
        if not tests:
            return [{"case_id": case_id, "outcome": "error", "error_info": plugin.report.get("exitcode")}]
        for test in tests:
            run_case_result = test["outcome"]
            longrepr = get_values_by_key(test, "longrepr", [])
            log_info = get_values_by_key(test, "log", [])
            # print(plugin.report)
            if not longrepr:
                longrepr = ""
            if isinstance(longrepr, list):
                longrepr = longrepr[0]
            file_path_name = ""
            file_name = ""

            try:
                log_names = case_title.split("::")
                log_name = "_".join(log_names)
                file_name = f"{log_name}_{str(run_id)}_{get_uuid_name()}.log"
                if not os.path.exists(logs):
                    os.makedirs(logs)
                file_path_name = os.path.join(logs, file_name)
                asyncio.run(write_to_logfile(file_path_name, log_info, longrepr))
            except Exception as e:
                print(traceback.print_exc())
            try:
                # set_info = session.query(TestSet).filter_by(id=kwargs.get("set_id")).first()
                # set_info.schedule = round((case_id_coor + 1) / case_ids_len * 100, 2)
                res = CaseResult(case_title=case_title, set_id=set_id, case_id=case_id, config_id=str(config_id),
                                 version_id=version_id, mark=mark, longrepr=str(longrepr),
                                 file_path_name=file_path_name,
                                 file_name=file_name, run_info=str(tests), run_id=run_id, project_id=project_id,
                                 case_name=case_name, project_name=project_name, duration=duration,
                                 case_created=case_created,
                                 run_case_result=run_case_result)
                session.add(res)
                session.commit()
            except Exception as e:
                print(e)
                session.rollback()
        return tests
    except Exception as e:
        print("这是脚本执行错误信息：", traceback.print_exc())
        return [{"case_id": case_id, "outcome": "error", "error_info": str(e)}]


def process_run(kwargs, session, case_ids):
    """

    :param kwargs:
    :param session:
    :param case_ids:
    :return:
    """
    pass_ids = list()
    fail_ids = list()
    error_ids = list()
    set_query = session.query(TestSet).filter_by(id=kwargs.get("set_id")).first()
    set_query.run_type = f"多进程,进程数:{kwargs.get('start_process')}"
    set_query.process_number = int(kwargs.get('start_process'))
    session.commit()
    if set_query.run_status == 2:
        return False
    relative_case_paths = list()
    querys = session.query(Cases).filter(Cases.id.in_(case_ids)).all()
    for query in querys:
        relative_case_paths.append(query.relative_case_path)
    run_info = ["-n", str(kwargs.get("start_process"))] + relative_case_paths
    if kwargs.get("run_parameter") and isinstance(kwargs.get("run_parameter"), list):
        run_info = kwargs.get("run_parameter") + run_info
    try:
        plugin = JSONReport()
        pytest.main(run_info, plugins=[plugin])
        tests = plugin.report.get("tests")
        created = plugin.report.get("created")
        ten_time = time.localtime(created)
        case_created = time.strftime("%Y-%m-%d %H:%M:%S", ten_time)
        # print(plugin.report)
        # 该用例耗时
        duration = plugin.report.get("duration")
        # 写入CaseResult表
        for test in tests:
            # print(test)
            node_id = test["nodeid"].split("[")[0]
            longrepr = get_values_by_key(test, "longrepr", [])
            if not longrepr:
                longrepr = ""
            if isinstance(longrepr, list):
                longrepr = longrepr[1]
            # print(node_id, len(longrepr), longrepr)
            # print(len(longrepr), longrepr)
            for query in querys:
                normalized_path = os.path.normpath(query.relative_case_path)
                normalized_path = normalized_path.replace("\\", "/")
                normalized_path = normalized_path.replace(f"testscriptproject/{query.project_name}/", "")
                file_path_name = ""
                file_name = ""
                if normalized_path == node_id:
                    try:
                        log_names = query.title.split("::")
                        log_name = "_".join(log_names)
                        file_name = f"{log_name}_{str(kwargs.get('run_id_num'))}_{get_uuid_name()}.log"
                        if not os.path.exists(logs):
                            os.makedirs(logs)
                        file_path_name = os.path.join(logs, file_name)
                        with open(file_path_name, "w", encoding="utf-8") as f:
                            # f.write(f"{longrepr}\n")
                            f.write(f"setup>>>>>>>>>{test['setup']['longrepr']}\n")
                            f.write(f"call>>>>>>>>>>{test['call']['longrepr']}\n")
                            f.write(f"teardown>>>>>>{test['teardown']['longrepr']}\n")
                    except:
                        pass
                    if test["outcome"] == "passed":
                        pass_ids.append(query.id)
                    if test["outcome"] == "failed":
                        fail_ids.append(query.id)
                    if test["outcome"] == "error":
                        error_ids.append(query.id)
                    res = CaseResult(case_title=query.title, set_id=set_query.id, case_id=query.id,
                                     config_id=str(kwargs.get("config_id")),
                                     version_id=query.version_id, mark=kwargs.get("mark"), longrepr=str(longrepr),
                                     file_path_name=file_path_name,
                                     file_name=file_name,
                                     run_info=str(test), run_id=kwargs.get("run_id_num"),
                                     project_id=kwargs.get("project_id"),
                                     case_name=query.case_name,
                                     project_name=kwargs.get("project_name"), duration=duration,
                                     case_created=case_created,
                                     run_case_result=test["outcome"])
                    session.add(res)
                    query.run_status = test["outcome"]
        set_query.schedule = 100
        session.commit()
        return pass_ids, fail_ids, error_ids
    except Exception as e:
        session.rollback()
        print(e)
    finally:
        return pass_ids, fail_ids, error_ids


def th_run_set(**kwargs):
    """

    :param kwargs:
    :return:
    """
    # script_type 1 为pytest执行用例 ,2 为直接加载py文件运行脚本执行用例
    # TestSet.run_status 0为未运行，1为运行中，2为已完成
    print(kwargs)
    set_query = None
    rerun_set_title = ""
    process_run_title = ""
    pid = None
    # 连接sql
    session = config.db_work(db_path=config.AppConFig.sql_url)
    try:
        if kwargs.get("script_type") == 1:
            set_info = session.query(TestSet).filter_by(id=kwargs.get("set_id")).first()
            project_query = session.query(Project).filter_by(id=kwargs.get("project_id")).first()
            current_time = datetime.now()
            time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
            set_info.start_task_time = time_string
            set_info.rerun_type = kwargs.get("rerun_type")
            if not set_info:
                return False
            if not kwargs.get("timed_task_time"):
                pid = os.getpid()
                set_info.pid = pid
                session.commit()
                # print(f"pid是>>>>>>>>>>>>>>>>>>{pid}")
            if set_info.run_status == 2:
                set_info.timed_task_time = "定时任务已被手动终止"
                session.commit()
                return False
            pass_ids = list()
            fail_ids = list()
            error_ids = list()
            case_ids = eval(set_info.case_ids)
            querys = session.query(Cases).filter(Cases.id.in_(case_ids)).all()
            for query in querys:
                query.run_status = "未测试"
            session.commit()
            if kwargs.get("rerun_type"):
                case_ids = eval(set_info.fail_ids)
                # rerun_set_title = '测试集用例失败重跑_'
                rerun_set_title = 'test_set_failed_case_rerun_'
            start_time = time.time()
            # 多进程执行用例
            if kwargs.get("start_process") and kwargs.get("start_process") > 1:
                kwargs.update({"project_name": project_query.name})
                pass_ids, fail_ids, error_ids = process_run(kwargs, session, case_ids)
                case_ids = pass_ids + fail_ids + error_ids
                process_run_title = "process_run_"
            else:
                set_info.run_type = "单进程"
                set_info.process_number = 1
                session.commit()
                case_id_progress = 0
                for case_id_coor in range(len(case_ids)):
                    case_id_progress = case_id_progress + 1
                    set_query = session.query(TestSet).filter_by(id=kwargs.get("set_id")).first()
                    if set_query.run_status == 2:
                        break
                    query = session.query(Cases).filter_by(id=case_ids[case_id_coor]).first()
                    case_title = query.title
                    case_name = query.case_name
                    case_id = query.id
                    run_info = [query.relative_case_path]
                    query.run_status = "测试中"
                    session.commit()
                    # run_info = ["--browser", "webkit", "--headed"] + [query.relative_case_path]
                    if kwargs.get("run_parameter") and isinstance(kwargs.get("run_parameter"), list):
                        run_info = kwargs.get("run_parameter") + run_info
                    tests = single_script_run(run_info,
                                              case_title=case_title, case_name=case_name, mark=kwargs.get("mark"),
                                              case_id=case_id, run_id=kwargs.get("run_id_num"),
                                              version_id=kwargs.get("version_id"),
                                              set_id=kwargs.get("set_id"), case_ids_len=len(case_ids),
                                              config_id=kwargs.get("config_id"), case_id_coor=case_id_progress,
                                              project_id=kwargs.get("project_id"), project_name=project_query.name,
                                              db_session=session)
                    # print(case_id_coor, len(case_ids))
                    if tests:
                        failed_count = error_count = 0
                        for test in tests:
                            if test["outcome"] == "passed":
                                pass_ids.append(case_id)
                            if test["outcome"] == "failed":
                                fail_ids.append(case_id)
                                failed_count += 1
                            if test["outcome"] == "error":
                                error_ids.append(case_id)
                                error_count += 1
                                # print(test["error_info"])
                                if test.get("error_info"):
                                    if "ExitCode.USAGE_ERROR" in str(test.get("error_info")):
                                        query.remark = "自动化测试过程中发现此case不存在，请检查路径和名称或者删除此用例"
                        if failed_count == 0 and error_count == 0:
                            query.run_status = "passed"
                        if failed_count > 0:
                            query.run_status = "failed"
                        if error_count > 0:
                            query.run_status = "error"
                        if len(tests) > 1:
                            case_ids.extend([case_ids[case_id_coor]] * (len(tests) - 1))
                            case_id_progress = case_id_progress + (len(tests) - 1)
                            query.case_count = len(tests)
                        set_info.schedule = round(case_id_progress / len(case_ids) * 100, 2)
                        session.commit()
                    time.sleep(0.01)
            case_all_time = time.time() - start_time
            set_query = session.query(TestSet).filter_by(id=kwargs.get("set_id")).first()
            set_query.run_status = 2
            set_query.pass_ids = str(list(set(pass_ids)))
            set_query.fail_ids = str(list(set(fail_ids)))
            set_query.error_ids = str(list(set(error_ids)))
            set_query.project_name = project_query.name
            set_query.case_all_time = case_all_time
            set_query.pid = 0
            session.commit()
            result_query = session.query(CaseResult).filter_by(set_id=int(kwargs.get("set_id"))).filter_by(
                run_id=int(kwargs.get("run_id_num"))).order_by(
                db.desc(CaseResult.run_id)).order_by(db.desc(CaseResult.updated_time)).all()
            result_query = [i.to_dict() for i in result_query]
            if not result_query:
                return False
            file_name = process_run_title + rerun_set_title + project_query.name + "_" + set_query.title + "_" + str(
                result_query[-1]["run_id"])
            info = [project_query.name, set_query.title, result_query[-1]["run_id"]]
            try:
                run_type = set_query.run_type
                html = case_report(result_query, file_name, case_all_time, info, run_type)
                name = report_file(file_name, html)
                set_query.report = name
                set_query.timed_task_time = ""
                pass_rate = len(pass_ids) / len(case_ids) * 100
                res = Reports(title=file_name, set_id=kwargs.get("set_id"), config_id=str(kwargs.get("config_id")),
                              report_path=name, all_count=len(case_ids), pass_count=len(pass_ids),
                              error_count=len(error_ids), fail_count=len(fail_ids), mark=kwargs.get("mark"),
                              run_id=kwargs.get("run_id_num"), pass_rate=pass_rate, case_all_time=case_all_time,
                              project_id=kwargs.get("project_id"), project_name=project_query.name
                              )
                session.add(res)
                session.commit()
                if kwargs.get("email_to") and kwargs.get("sent_email") == "1":
                    try:
                        dir_path = os.path.join(report_path, name)
                        t = EmailThread(kwargs.get("email_to"),
                                        subject="自动化测试报告",
                                        contents=['您好：',
                                                  f'请查收{project_query.name}项目的{set_query.title}测试集的自动化测试报告:',
                                                  yagmail.inline(r"{dir_path}".format(dir_path=dir_path))],
                                        attachments=None)
                        t.start()
                    except Exception as e:
                        print(e)
            except Exception as e:
                session.rollback()
                print(e)

        elif kwargs.get("script_type") == 2:
            pass
        else:
            pass
    except Exception as e:
        print("th_run_set函数执行异常", e)
        session.rollback()
        traceback.print_exc()
        if set_query:
            set_query.timed_task_time = ""
        return False
    finally:
        set_query = session.query(TestSet).filter_by(id=kwargs.get("set_id")).first()
        set_query.run_status = 2
        set_query.pid = 0
        set_query.run_type = ""
        set_query.process_number = 0
        set_query.start_task_time = ""
        # set_query.timed_task_time = ""
        session.commit()
        if session:
            session.close()


def th_run_task(**kwargs):
    """测试任务执行"""
    # print(kwargs)
    session = config.db_work(db_path=config.AppConFig.sql_url)
    task_info = session.query(TestTask).filter_by(id=kwargs.get("task_id")).first()
    config_id = kwargs.get("config_id")
    current_time = datetime.now()
    time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
    task_info.start_task_time = time_string
    try:
        if kwargs.get("set_ids"):
            for index, set_id in enumerate(kwargs.get("set_ids")):
                set_info = session.query(TestSet).filter_by(id=set_id).first()
                set_info.run_status = 1
                if set_info.config:
                    new_config_id = config_id + eval(set_info.config)
                else:
                    new_config_id = config_id
                project_name = set_info.project_name
                new_config_id = list(set(new_config_id))
                cfg_status = update_config_file(new_config_id, project=project_name)
                if not cfg_status:
                    return False
                if not kwargs.get("config_id") and not set_info.config:
                    set_info.run_status = 2
                    task_info.run_status = 2
                    session.commit()
                    return False
                kwargs.update(
                    {"project_id": set_info.project_id, "script_type": set_info.type, "config_id": new_config_id,
                     "set_id": set_id, "version_id": set_info.version_id})
                task_info.progress = set_info.title
                task_info.progress_set_id = set_info.id
                set_info.run_id = kwargs.get("run_id_num")
                session.commit()
                time.sleep(0.1)
                th_run_set(**kwargs)
                task_info.schedule = round((index + 1) / len(kwargs.get("set_ids")) * 100, 2)
                set_info.mark_info = ""
                session.commit()
    except Exception as e:
        pass
    finally:
        task_info.run_status = 2
        task_info.progress = ""
        task_info.start_task_time = ""
        task_info.progress_set_id = None
        task_info.timed_task_time = ""
        session.commit()
        time.sleep(0.01)
        if session:
            session.close()
