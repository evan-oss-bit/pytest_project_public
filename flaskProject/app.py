# -*- coding: utf-8 -*-
import platform
import subprocess
import gevent.monkey

# from gevent.pywsgi import WSGIServer
gevent.monkey.patch_all()
from app import create_app

# app = create_app()
from config import run_info

if __name__ == '__main__':

    # 该项目Swagger本地地址：http://host:port/traffic/apidocs/

    # http_server = WSGIServer(("0.0.0.0", 5400), app)
    # http_server.serve_forever()

    # app = create_app()
    # app.run(debug=True, host='0.0.0.0', port=5400)
    print(platform.python_version())
    # 使用多进程启动服务，防止执行pytest用例时控制台输出冲突导致flask服务假死，期待大佬改一下
    app = create_app()
    subprocess.run(['flask', 'run', '-p', run_info.get("port"), '-h', run_info.get("ip")])
