# -*- coding: utf-8 -*-
import os
import time

import requests
# 任务
from locust import task, FastHttpUser
import json


class WebsiteTasks(FastHttpUser):
    @task
    def make_api_request(self):
        payload = {"run_status": None, "title": "", "page": 0, "page_size": 1000}
        res = self.client.post("/testset/get_testset_info", json=payload)
        print(res.text)
        # with self.rest("POST", "/testset/get_testset_info", json=payload) as resp:
        #     print(resp.js)
        #     if resp.js is None:
        #         # 响应无效，已标记为失败
        #         pass
        #     elif "msg" not in resp.js:
        #         # 响应中缺少 "msg" 字段
        #         resp.failure(f"'bar' missing from response: {resp.text}")
        #     # elif resp.js["bar"] != 42:
        #     #     # "bar" 字段的值不符合预期
        #     #     resp.failure(f"'bar' had an unexpected value: {resp.js['bar']}")


class WebsiteUser(FastHttpUser):
    task_set = WebsiteTasks
    host = "http://127.0.0.1:5400"
    min_wait = 0
    max_wait = 1000


# if __name__ == "__main__":
#     os.system('locust -f file_test.py --web-port 8090')


from flask import Flask, Blueprint
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)


# 创建一个蓝图
# my_blueprint = Blueprint('my_blueprint', __name__)

# 添加 WebSocket 路由到蓝图
@sock.route('/echo')
def echo(ws):
    while True:
        data = ws.receive()
        print(data)
        ws.send(data)


# 注册蓝图
# app.register_blueprint(my_blueprint)

def reqs():
    while True:

        for set_id in [1, 2]:
            reps = requests.post("http://127.0.0.1:5400/testset/run_testset",
                                 json={"id": set_id, "script_type": 1})
            time.sleep(0.1)
            print(f"set_id:{set_id}请求中----{reps.json()}")

def test_uri():
    reps = requests.post("http://127.0.0.1:5400/testset/sys_info")
    print(reps.json())

if __name__ == '__main__':
    test_uri()
