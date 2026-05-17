#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
import os

db_config = {
    "ts": os.getenv("PYTEST_TOOL_MYSQL_URL", "mysql+pymysql://root:password@127.0.0.1:3306/database?charset=utf8mb4"),
    "host": os.getenv("PYTEST_TOOL_MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("PYTEST_TOOL_MYSQL_PORT", "3306")),
    "user": os.getenv("PYTEST_TOOL_MYSQL_USER", "root"),
    "pwd": os.getenv("PYTEST_TOOL_MYSQL_PASSWORD", "password"),
}
