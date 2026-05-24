#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
from flask import Blueprint

project = Blueprint("project", __name__, url_prefix='/project')
business_department = Blueprint("business_department", __name__, url_prefix='/business_department')
version = Blueprint("version", __name__, url_prefix='/version')
config = Blueprint("config", __name__, url_prefix='/config')
cases = Blueprint("cases", __name__, url_prefix='/cases')
module = Blueprint("module", __name__, url_prefix='/module')
testset = Blueprint("testset", __name__, url_prefix='/testset')
report = Blueprint("report", __name__, url_prefix='/report')
api_test = Blueprint("api_test", __name__, url_prefix='/api_test')
performance_test = Blueprint("performance_test", __name__, url_prefix='/performance_test')
caseresult = Blueprint("caseresult", __name__, url_prefix='/caseresult')
test_task = Blueprint("test_task", __name__, url_prefix='/test_task')
# sock_blueprint = Blueprint('sock_blueprint', __name__, url_prefix='/sock_blueprint')  # websocket
