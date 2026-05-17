from gevent import pywsgi
import subprocess
import gevent.monkey

gevent.monkey.patch_all()
from app import create_app

app = create_app()

server = pywsgi.WSGIServer(('0.0.0.0', 5400), app)
server.serve_forever()
