# -*- coding: utf-8 -*-
import os
import platform

from app.tools.console_encoding import configure_console_streams

configure_console_streams()
from app import create_app
from config import run_info


def main():
    host = os.getenv("PYTEST_TOOL_HOST", run_info.get("ip", "0.0.0.0"))
    port = int(os.getenv("PYTEST_TOOL_PORT", run_info.get("port", 5400)))
    debug = os.getenv("PYTEST_TOOL_DEBUG", "0").lower() in ("1", "true", "yes", "on")

    print("Python {}".format(platform.python_version()))
    swagger_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    print("Swagger: http://{}:{}/traffic/apidocs/".format(swagger_host, port))

    app = create_app()
    app.run(debug=debug, host=host, port=port, use_reloader=debug)


if __name__ == "__main__":
    main()
