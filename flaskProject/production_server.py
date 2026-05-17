# -*- coding: utf-8 -*-
"""
Production entrypoint for PyTestTool.

Default server:
    gevent.pywsgi + gevent-websocket

Environment variables:
    PYTEST_TOOL_HOST       default: config.run_info["ip"]
    PYTEST_TOOL_PORT       default: config.run_info["port"]
    PYTEST_TOOL_LOG_LEVEL  default: INFO
    PYTEST_TOOL_SSL_CERT   optional TLS certificate file
    PYTEST_TOOL_SSL_KEY    optional TLS private key file
"""
from __future__ import print_function

import logging
import os
import signal
import sys
from logging.handlers import RotatingFileHandler

from gevent import monkey

monkey.patch_all()

from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

import config
from app import create_app


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "production_server.log")


def _env_int(name, default):
    value = os.environ.get(name)
    if value in (None, ""):
        return int(default)
    try:
        return int(value)
    except ValueError:
        raise RuntimeError("{} must be an integer, got {!r}".format(name, value))


def _setup_logging():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    level_name = os.environ.get("PYTEST_TOOL_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = []

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=20 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    root.addHandler(stream_handler)
    root.addHandler(file_handler)

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("geventwebsocket").setLevel(logging.WARNING)


def _server_options():
    options = {
        "handler_class": WebSocketHandler,
        "log": logging.getLogger("gevent.pywsgi"),
        "error_log": logging.getLogger("gevent.pywsgi.error"),
    }

    certfile = os.environ.get("PYTEST_TOOL_SSL_CERT")
    keyfile = os.environ.get("PYTEST_TOOL_SSL_KEY")
    if certfile and keyfile:
        options["certfile"] = certfile
        options["keyfile"] = keyfile
    elif certfile or keyfile:
        raise RuntimeError(
            "PYTEST_TOOL_SSL_CERT and PYTEST_TOOL_SSL_KEY must be set together"
        )

    return options


def main():
    _setup_logging()

    host = os.environ.get("PYTEST_TOOL_HOST", config.run_info.get("ip", "0.0.0.0"))
    port = _env_int("PYTEST_TOOL_PORT", config.run_info.get("port", 5400))
    app = create_app()
    server = WSGIServer((host, port), app, **_server_options())

    def shutdown(signum, frame):
        logging.info("received signal %s, stopping server", signum)
        server.stop(timeout=10)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    scheme = "https" if os.environ.get("PYTEST_TOOL_SSL_CERT") else "http"
    logging.info("production server started at %s://%s:%s", scheme, host, port)
    logging.info("websocket endpoint: %s://%s:%s/execution_notify", "wss" if scheme == "https" else "ws", host, port)
    server.serve_forever()


if __name__ == "__main__":
    main()
