# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
import redis

import json
import decimal, datetime


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(o, bytes):
            return str(o, encoding='utf-8')
        super(DecimalEncoder, self).default(o)


def redis_obj():
    conn = redis.Redis(host='localhost', port=6379, db=0)
    return conn


new_conn = redis_obj()
print("创建redis连接对象")
