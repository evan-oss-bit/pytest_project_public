#!/usr/bin/python
# -*- coding:utf-8 -*-
from functools import wraps
from flask import Flask, request, jsonify
import logging

def log_request_response(module=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 记录请求信息
            request_data = {
                'module': module,
                'method': request.method,
                'path': request.path,
                'headers': dict(request.headers),
                'body': request.get_json() or request.form.to_dict()
            }
            # print('Request:', request_data)

            # 执行路由处理函数
            response = func(*args, **kwargs)

            # 记录响应信息
            response_data = {
                'module': module,
                'status_code': response.status_code,
                'body': response.json
            }
            # print('Response:', response_data)

            return response

        return wrapper

    return decorator
