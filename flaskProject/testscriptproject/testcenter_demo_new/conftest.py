#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
import pytest
import logging
import os


@pytest.fixture(autouse=True)
def login():
    logging.info("》》》用例前置操作开始执行《《《")


# 示例：清理函数，收集测试数据进行清理 autouse建议为False，需要调用才生效，每个模块的用例建议写一个前置后置，以免混乱
@pytest.fixture(autouse=False)
def del_case_data(data="aaaa"):
    logging.info("yield前置开始-生成调用的方法，用于测试执行，例如，测试用例接口公共方法生成，并返回相应需要清理的数据")

    def _del_case(data):
        for i in data:
            logging.info(i)
        return "yield生成器的返回值"

    yield _del_case
    logging.info("后置开始-拿到前置和用例执行过程的返回的数据，进行清理")


# def pytest_sessionstart(session):
#     session.log_files = []
# 
#
# def pytest_runtest_call(item):
#     try:
#         # 获取当前测试用例名称
#         test_name = item.nodeid.split('::')[-1]
#         # 创建日志文件路径
#         log_file = os.path.join("./testscriptproject/logs", f"{test_name}.log")
#         # 记录日志文件路径
#         item.session.log_files.append(log_file)
#         # 在测试用例执行前创建空日志文件
#         with open(log_file, "w") as f:
#             f.write("")
#     except:
#         pass
#
#
# def pytest_runtest_logreport(report):
#     # 在测试用例执行结束后写入日志
#     try:
#         nodeid_name = report.nodeid.split("::")[-1]
#         log_file = os.path.join("./testscriptproject/logs", f"{nodeid_name}.log")
#         with open(log_file, "a", encoding="utf-8") as f:
#             f.write(f"{report.longreprtext}\n")
#     except:
#         pass
def pytest_collection_modifyitems(items):
    """
    测试用例收集完成时，将收集到的item的name和nodeid的中文显示
    :return:
    """
    for item in items:
        item.name = item.name.encode("utf-8").decode("unicode_escape")
        item._nodeid = item.nodeid.encode("utf-8").decode("unicode_escape")
