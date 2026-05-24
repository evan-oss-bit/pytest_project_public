#!/usr/bin/python3.8
# -*- coding: utf-8 -*-

from app.web_api.app_test_project import project
from app.web_api.app_business_department import business_department
from app.web_api.app_test_version import version
from app.web_api.app_test_config import config
from app.web_api.app_test_cases import cases
from app.web_api.app_test_module import module
from app.web_api.app_test_testset import testset
from app.web_api.app_test_report import report
from app.web_api.app_api_test import api_test
from app.web_api.app_performance_test import performance_test
from app.web_api.app_test_caseresult import caseresult
from app.web_api.app_test_testtask import test_task
from app.web_api.app_auth import auth

# from app.ws_api.ws_server import sock_blueprint


#
def init_app(app):
    app.register_blueprint(auth)
    app.register_blueprint(project)
    app.register_blueprint(business_department)
    app.register_blueprint(version)
    app.register_blueprint(config)
    app.register_blueprint(cases)
    app.register_blueprint(module)
    app.register_blueprint(testset)
    app.register_blueprint(report)
    app.register_blueprint(api_test)
    app.register_blueprint(performance_test)
    app.register_blueprint(caseresult)
    app.register_blueprint(test_task)


def init_sock_app(sock):
    @sock.route('/echo')
    def echo(ws):
        while 1:
            data = ws.receive()
            print("服务端接收客户端的数据", data)
            ws.send("这是服务端发送的数据" + data)
            # sock.broadcast(data, channel='chat')
