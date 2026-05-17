# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
import os

token_path = {"token": "token默认值"}
headers = {"Content-Type": "application/json"}


def share_token(func):
    def wrapper(*args, **kwargs):
        token = token_path["token"]
        if "token" in kwargs.keys():
            kwargs.update({"token": token})
        global headers
        headers.update({"token": token})
        kwargs.update({"headers": headers})
        print(kwargs)
        result = func(*args, **kwargs)
        return result

    return wrapper


def set_login_token(token="abc1"):
    token_path.update({"token": token})
