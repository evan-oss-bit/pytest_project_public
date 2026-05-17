# -*- coding: utf-8 -*-
import subprocess
import gevent.monkey
from waitress import serve
gevent.monkey.patch_all()
from app import create_app

if __name__ == '__main__':
    app = create_app()
    serve(app, host='0.0.0.0', port=5400)
