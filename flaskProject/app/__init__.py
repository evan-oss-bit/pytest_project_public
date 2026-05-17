# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
from celery import Celery
from flask import Flask, request
import logging
import os
from app.lib.lib_define import db
from app.models.test_api_models import *
# from flasgger import Swagger
# from flask_cors import CORS
import route
import config
from flask_cors import CORS
from flasgger import Swagger
from conf.swag_conf import swagger_config
from flask_sock import Sock
from app.tools.auth_permissions import require_login, seed_admin


class Config(object):
    LOG_FILE = 'app.log'
    LOG_LEVEL = logging.DEBUG
    # 连接sql
    SQLALCHEMY_DATABASE_URI = config.AppConFig.sql_url
    SQLALCHEMY_ENGINE_OPTIONS = config.AppConFig.sqlalchemy_engine_options()
    SQLALCHEMY_ECHO = False
    # SQLALCHEMY_POOL_SIZE = 20  # 设置连接池大小
    # SQLALCHEMY_MAX_OVERFLOW = 5  # 设置最大溢出连接数
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    JSON_AS_ASCII = False
    SECRET_KEY = os.getenv("PYTEST_TOOL_SECRET_KEY", "change-me-in-production")


def create_app(register_blueprint=True):
    app = Flask(__name__, static_folder="../logs")
    sock = Sock(app)
    CORS(app)
    Swagger(app, config={"specs_route": "/traffic/apidocs/"}, merge=True)

    # f = open('output.log', 'w+')  # 可以使用 .log 或 .txt
    # sys.stdout = f  # 保存 print 输出
    # sys.stderr = f  # 保存异常或错误信息
    # logging.basicConfig(filename='api.log', level=logging.DEBUG)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.DEBUG)
    # app.config['LOG_FILE'] = 'app.log'  # 日志文件路径
    # app.config['LOG_LEVEL'] = logging.DEBUG
    # app.config['SQLALCHEMY_DATABASE_URI'] = config.AppConFig.sqlite_url
    # app.config['SQLALCHEMY_POOL_SIZE'] = 20  # 设置连接池大小
    # app.config['SQLALCHEMY_MAX_OVERFLOW'] = 5  # 设置最大溢出连接数
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    # app.config['JSON_AS_ASCII'] = False
    app.config.from_object(Config)
    config.ensure_runtime_dirs()
    # f.flush()
    if register_blueprint:
        db.app = app
        db.init_app(app)
        with app.app_context():
            config.configure_sqlite_engine(db.engine)
            # 删表
            # db.drop_all()
            db.create_all()
            seed_admin(db)

        # app.config.from_object(cache_config)
        # cache.init_app(app)
        # app.config.from_object(config)
        # CORS(app, supports_credentials=True)

        route.init_app(app)
        route.init_sock_app(sock)

        @app.before_request
        def auth_guard():
            if request.method == "OPTIONS":
                return None
            public_prefixes = (
                "/login",
                "/traffic/apidocs",
                "/apispec",
                "/flasgger_static",
                "/echo",
            )
            if request.path.startswith(public_prefixes):
                return None
            return require_login()
    return app
