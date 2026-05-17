#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
import os
from flask_sqlalchemy import SQLAlchemy
# from flask.ext.cache import Cache
from app.lib.image import get_redis_ch

red_client = get_redis_ch(
    host=os.getenv("PYTEST_TOOL_IMAGE_REDIS_HOST", "127.0.0.1"),
    pwd=os.getenv("PYTEST_TOOL_IMAGE_REDIS_PASSWORD", ""),
    port=int(os.getenv("PYTEST_TOOL_IMAGE_REDIS_PORT", "6379")),
)
db = SQLAlchemy()
# cache = Cache()


import sqlalchemy
from conf.config import db_config
from sqlalchemy.orm import sessionmaker
engine = sqlalchemy.create_engine(db_config['ts'])
# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)
db_worker = DBSession()
