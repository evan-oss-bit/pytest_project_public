# -*- coding: utf-8 -*-
from app import db
from app.models.base import Base
from sqlalchemy import UniqueConstraint, Index
from sqlalchemy.ext.declarative import declared_attr
import datetime


class BaseMixin(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class TestTask(Base, BaseMixin):
    """测试任务表"""
    __tablename__ = 'test_task'
    test_set_ids = db.Column(db.String(1000), nullable=True)
    name = db.Column(db.String(1000), nullable=True)
    config_ids = db.Column(db.String(1000), nullable=True)
    run_id = db.Column(db.String(1000), nullable=True)
    schedule = db.Column(db.Float, nullable=True)
    run_status = db.Column(db.Integer, nullable=True)
    timed_task_time = db.Column(db.String(1000), nullable=True, default='')
    start_task_time = db.Column(db.String(1000), nullable=True, default='')
    mark = db.Column(db.String(1000), nullable=True)
    progress = db.Column(db.String(1000), nullable=True)
    progress_set_id = db.Column(db.Integer, nullable=True)
    reports = db.Column(db.String(1000), nullable=True)
    email_to = db.Column(db.String(1000), nullable=True)
    is_delete = db.Column(db.Integer, nullable=True, default=0)


class Account(Base, BaseMixin):
    """系统账号表"""
    __tablename__ = 'account'
    username = db.Column(db.String(191), nullable=False, unique=True, index=True)
    password = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(191), nullable=True)
    role = db.Column(db.String(80), nullable=False, default="project_user")
    token = db.Column(db.String(255), nullable=True, index=True)
    is_delete = db.Column(db.Integer, nullable=True, default=0)


class AccountProject(Base, BaseMixin):
    """账号项目权限表"""
    __tablename__ = 'account_project'
    account_id = db.Column(db.Integer, nullable=False, index=True)
    project_id = db.Column(db.Integer, nullable=False, index=True)
    can_view = db.Column(db.Integer, nullable=False, default=1)
    can_edit = db.Column(db.Integer, nullable=False, default=0)
    can_run = db.Column(db.Integer, nullable=False, default=0)
    __table_args__ = (
        UniqueConstraint('account_id', 'project_id', name='uix_account_project'),
    )


class OperationLog(Base, BaseMixin):
    """ç³»ç»Ÿå…³é”®æ“ä½œæ—¥å¿—è¡¨"""
    __tablename__ = 'operation_log'
    user_id = db.Column(db.Integer, nullable=True, index=True)
    username = db.Column(db.String(191), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=True, index=True)
    action_name = db.Column(db.String(191), nullable=True)
    target_type = db.Column(db.String(80), nullable=True, index=True)
    target_id = db.Column(db.String(191), nullable=True, index=True)
    target_name = db.Column(db.String(500), nullable=True)
    method = db.Column(db.String(20), nullable=True)
    path = db.Column(db.String(500), nullable=True, index=True)
    status_code = db.Column(db.Integer, nullable=True)
    result_code = db.Column(db.Integer, nullable=True)
    result_msg = db.Column(db.String(1000), nullable=True)
    before_data = db.Column(db.TEXT(65533), nullable=True)
    after_data = db.Column(db.TEXT(65533), nullable=True)
    request_data = db.Column(db.TEXT(65533), nullable=True)
    response_data = db.Column(db.TEXT(65533), nullable=True)
    ip = db.Column(db.String(80), nullable=True)


class Test_Module(Base, BaseMixin):
    """测试模块表"""
    __tablename__ = 'test_module'
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    # project_id = db.Column(db.Integer)
    version_id = db.Column(db.Integer, nullable=True)
    module = db.Column(db.String(1000), nullable=True)
    description = db.Column(db.String(1000), nullable=True)

    # def to_dict(self):
    #     return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class Cases(Base, BaseMixin):
    """测试脚本表"""
    # latest_status 0表示未运行，1表示即将运行，2表示运行中，3表示运行完成
    __tablename__ = 'cases'
    title = db.Column(db.String(191), nullable=True)
    case_name = db.Column(db.String(1000), nullable=True)
    version_id = db.Column(db.String(1000), nullable=False, index=True)
    project_id = db.Column(db.Integer, nullable=False, index=True)
    project_name = db.Column(db.String(1000), nullable=True)
    module_id = db.Column(db.String(191), nullable=True, index=True)
    case_path = db.Column(db.String(1000), nullable=False, index=True, unique=True)
    relative_case_path = db.Column(db.String(1000), nullable=True)
    relative_path = db.Column(db.String(1000), nullable=True)
    type = db.Column(db.Integer, nullable=False, index=True)
    latest_status = db.Column(db.Integer, nullable=True, default=0)
    run_status = db.Column(db.String(1000), nullable=True)
    content = db.Column(db.String(1000), nullable=True)
    previous_level = db.Column(db.String(1000), nullable=True)
    class_name = db.Column(db.String(1000), nullable=True)
    relative_cla_case_path = db.Column(db.String(1000), nullable=True)
    owner = db.Column(db.String(80), nullable=True)
    template_id = db.Column(db.Integer)
    normal = db.Column(db.Boolean, nullable=True, default=False, index=True)
    remark = db.Column(db.String(1000), nullable=True, default=None)
    testcase_id = db.Column(db.Integer, nullable=True)
    case_count = db.Column(db.Integer, nullable=True, default=1)
    is_delete = db.Column(db.Integer, nullable=True, default=0)
    __table_args__ = (
        Index('ix_cases_project_version_title_type', 'project_id', 'title', 'type'),  # 联合索引
    )

    # def to_dict(self):
    #     return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class TestSet(Base, BaseMixin):
    """测试集合表"""
    # run_status 0表示未运行，1表示即将运行，2表示运行中，3表示运行完成
    __tablename__ = 'testset'
    title = db.Column(db.String(191), nullable=False, unique=True)
    version_id = db.Column(db.Integer, db.ForeignKey('version.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project_name = db.Column(db.String(1000), nullable=True)
    # version_id = db.Column(db.Integer)
    schedule = db.Column(db.Float, nullable=True)
    run_id = db.Column(db.BigInteger, nullable=True)
    type = db.Column(db.Integer, nullable=False)
    run_status = db.Column(db.Integer, nullable=True)
    job_id = db.Column(db.String(1000), nullable=True)
    case_ids = db.Column(db.String(1000), nullable=False)
    pass_ids = db.Column(db.String(1000), nullable=True)
    fail_ids = db.Column(db.String(1000), nullable=True)
    error_ids = db.Column(db.String(1000), nullable=True)
    case_all_time = db.Column(db.Numeric(10, 4), nullable=True)
    run_time = db.Column(db.DateTime, default=None, onupdate=datetime.datetime.now)
    report = db.Column(db.String(1000), nullable=True)
    modify_count = db.Column(db.BigInteger, default=0, nullable=False)
    config = db.Column(db.String(800), nullable=True)
    config_ids = db.Column(db.String(1000), nullable=True)
    mark = db.Column(db.Integer, nullable=False, default=0)
    previous_level = db.Column(db.String(1000), nullable=True)
    fixed_cc = db.Column(db.BigInteger, nullable=False, default=0)
    rate = db.Column(db.Float, nullable=True, default=None)
    timed_task_time = db.Column(db.String(1000), nullable=True, default='')
    start_task_time = db.Column(db.String(1000), nullable=True, default='')
    class_name = db.Column(db.String(1000), nullable=True)
    pid = db.Column(db.Integer, nullable=True, default=0)
    # run_type 0运行完成，1单进程，2多进程，3定时任务
    run_type = db.Column(db.String(1000), nullable=True)
    rerun_type = db.Column(db.Integer, nullable=True, default=0)
    mark_info = db.Column(db.String(1000), nullable=True)
    email_to = db.Column(db.String(1000), nullable=True)
    is_delete = db.Column(db.Integer, nullable=True, default=0)
    priority = db.Column(db.Integer, nullable=True, default=0)
    process_number = db.Column(db.Integer, nullable=True, default=0)
    __table_args__ = (
        Index('ix_project_version_title_type', 'project_id', 'title', 'type', "config"),  # 联合索引
    )
    # def to_dict(self):
    #     return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class Cfgs(Base, BaseMixin):
    """配置表"""
    __tablename__ = 'config'
    # project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    cfg_name = db.Column(db.String(191), nullable=False)
    cfg = db.Column(db.String(1000), nullable=False)
    mark = db.Column(db.String(1000), nullable=True)
    is_delete = db.Column(db.Integer, nullable=True, default=0)
    # def to_dict(self):
    #     return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class Reports(Base, BaseMixin):
    """测试报告表"""
    __tablename__ = 'reports'
    title = db.Column(db.String(191), nullable=False)
    project_id = db.Column(db.Integer, nullable=True)
    project_name = db.Column(db.String(1000), nullable=True)
    set_id = db.Column(db.Integer, nullable=False)
    report_path = db.Column(db.String(1000), nullable=False)
    config_id = db.Column(db.String(900), nullable=True)
    all_count = db.Column(db.BigInteger, nullable=True)
    pass_count = db.Column(db.BigInteger, nullable=True)
    fail_count = db.Column(db.BigInteger, nullable=True)
    error_count = db.Column(db.BigInteger, nullable=True)
    pass_rate = db.Column(db.Numeric(10, 2), nullable=True)
    case_all_time = db.Column(db.Numeric(10, 4), nullable=True)
    serial = db.Column(db.String(1000), nullable=True, default=None)
    mark = db.Column(db.String(1000), nullable=False)
    run_id = db.Column(db.BigInteger, index=True, nullable=True)
    # def to_dict(self):
    #     return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}
    __table_args__ = (
        UniqueConstraint('set_id', "title", name='uix_set_reports_id'),  # 联合唯一索引
        Index('ix_set_reports_id', 'set_id', 'title', "id"),  # 联合索引
    )


class Version(Base, BaseMixin):
    """版本号表"""
    __tablename__ = 'version'
    version = db.Column(db.String(80))
    changelog = db.Column(db.String(191))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

    # def to_dict(self):
    #     return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class Project(Base, BaseMixin):
    """测试项目表"""
    __tablename__ = 'project'
    name = db.Column(db.String(255), unique=True)
    # title = db.Column(db.String(255))
    description = db.Column(db.String(191))
    controller = db.Column(db.String(255))
    business_department_id = db.Column(db.Integer, nullable=True, index=True)
    business_department = db.Column(db.String(255), nullable=True, default="")
    environment = db.Column(db.String(80), nullable=True, default="test")
    priority = db.Column(db.String(80), nullable=True, default="P2")
    maint_status = db.Column(db.String(80), nullable=True, default="normal")
    tags = db.Column(db.String(500), nullable=True, default="")
    git_repo_url = db.Column(db.String(1000), nullable=True, default="")
    git_branch = db.Column(db.String(191), nullable=True, default="")
    git_auto_sync = db.Column(db.Integer, nullable=True, default=1)

    # def to_dict(self):
    #     return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class BusinessDepartment(Base, BaseMixin):
    """业务部门表"""
    __tablename__ = 'business_department'
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    owner = db.Column(db.String(255), nullable=True, default="")
    description = db.Column(db.String(1000), nullable=True, default="")
    is_delete = db.Column(db.Integer, nullable=True, default=0)


class CaseResult(Base, BaseMixin):
    """用例执行结果表"""
    __tablename__ = 'caseresult'
    case_title = db.Column(db.String(191), nullable=False)
    case_name = db.Column(db.String(191), nullable=True)
    project_name = db.Column(db.String(191), nullable=True)
    set_id = db.Column(db.Integer, index=True, nullable=False)
    case_id = db.Column(db.Integer, index=True, nullable=False)
    config_id = db.Column(db.String(900), nullable=True)
    version_id = db.Column(db.Integer, index=True, nullable=True)
    project_id = db.Column(db.Integer, index=True, nullable=False)
    run_info = db.Column(db.TEXT(65533), nullable=True)
    longrepr = db.Column(db.TEXT(65533), nullable=True)
    duration = db.Column(db.Numeric(10, 4), nullable=True)
    case_created = db.Column(db.String(191), nullable=True)
    file_path_name = db.Column(db.TEXT(65533), nullable=True)
    file_name = db.Column(db.TEXT(65533), nullable=True)
    run_case_result = db.Column(db.String(80), nullable=True)
    source_type = db.Column(db.String(40), nullable=True, default="pytest", index=True)
    api_result_id = db.Column(db.Integer, nullable=True, index=True)
    api_suite_result_id = db.Column(db.Integer, nullable=True, index=True)
    mark = db.Column(db.TEXT(65533), nullable=True)
    run_id = db.Column(db.BigInteger, index=True, nullable=True, default=0)
    class_name = db.Column(db.String(1000), nullable=True)
    __table_args__ = (
        UniqueConstraint('id', 'set_id', 'case_id', "run_id", "case_title", name='uix_set_config_case_id'),  # 联合唯一索引
        Index('ix_set_config_case_id', 'set_id', 'run_id', "id", "case_title"),  # 联合索引
    )


class CaseToken(Base, BaseMixin):
    """登录验签存储表"""
    __tablename__ = 'casetoken'
    name = db.Column(db.String(191), unique=True, nullable=True)
    token = db.Column(db.String(191), nullable=True)
    user = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(255), nullable=True)
    tokeninfo = db.Column(db.String(191), nullable=True)


class ApiEnvironment(Base, BaseMixin):
    """接口测试环境变量表"""
    __tablename__ = 'api_environment'
    name = db.Column(db.String(191), nullable=False, index=True)
    project_id = db.Column(db.Integer, nullable=True, index=True)
    variables = db.Column(db.TEXT(65533), nullable=True)
    description = db.Column(db.String(1000), nullable=True, default="")
    is_delete = db.Column(db.Integer, nullable=True, default=0)


class ApiCase(Base, BaseMixin):
    """接口测试用例表"""
    __tablename__ = 'api_case'
    name = db.Column(db.String(191), nullable=False, index=True)
    project_id = db.Column(db.Integer, nullable=True, index=True)
    environment_id = db.Column(db.Integer, nullable=True, index=True)
    method = db.Column(db.String(20), nullable=False, default="GET")
    url = db.Column(db.String(2000), nullable=False)
    headers = db.Column(db.TEXT(65533), nullable=True)
    params = db.Column(db.TEXT(65533), nullable=True)
    body_type = db.Column(db.String(40), nullable=True, default="json")
    body = db.Column(db.TEXT(65533), nullable=True)
    assertions = db.Column(db.TEXT(65533), nullable=True)
    pre_case_ids = db.Column(db.TEXT(65533), nullable=True)
    extractors = db.Column(db.TEXT(65533), nullable=True)
    description = db.Column(db.String(1000), nullable=True, default="")
    last_status = db.Column(db.Integer, nullable=True)
    last_success = db.Column(db.Integer, nullable=True)
    last_elapsed_ms = db.Column(db.Integer, nullable=True)
    is_delete = db.Column(db.Integer, nullable=True, default=0)


class ApiRunResult(Base, BaseMixin):
    """接口测试执行结果表"""
    __tablename__ = 'api_run_result'
    run_id = db.Column(db.BigInteger, nullable=True, index=True, default=0)
    case_id = db.Column(db.Integer, nullable=True, index=True)
    environment_id = db.Column(db.Integer, nullable=True, index=True)
    project_id = db.Column(db.Integer, nullable=True, index=True)
    method = db.Column(db.String(20), nullable=True)
    url = db.Column(db.String(2000), nullable=True)
    request_headers = db.Column(db.TEXT(65533), nullable=True)
    request_params = db.Column(db.TEXT(65533), nullable=True)
    request_body = db.Column(db.TEXT(65533), nullable=True)
    response_status = db.Column(db.Integer, nullable=True)
    response_headers = db.Column(db.TEXT(65533), nullable=True)
    response_body = db.Column(db.TEXT(65533), nullable=True)
    elapsed_ms = db.Column(db.Integer, nullable=True)
    success = db.Column(db.Integer, nullable=True, default=0)
    run_status = db.Column(db.String(40), nullable=True, default="finished", index=True)
    status_text = db.Column(db.String(191), nullable=True, default="")
    assertion_result = db.Column(db.TEXT(65533), nullable=True)
    error_message = db.Column(db.TEXT(65533), nullable=True)


class ApiSuite(Base, BaseMixin):
    """接口测试集合/场景表"""
    __tablename__ = 'api_suite'
    name = db.Column(db.String(191), nullable=False, index=True)
    project_id = db.Column(db.Integer, nullable=True, index=True)
    environment_id = db.Column(db.Integer, nullable=True, index=True)
    case_ids = db.Column(db.TEXT(65533), nullable=True)
    stop_on_fail = db.Column(db.Integer, nullable=True, default=1)
    description = db.Column(db.String(1000), nullable=True, default="")
    last_success = db.Column(db.Integer, nullable=True)
    last_elapsed_ms = db.Column(db.Integer, nullable=True)
    last_run_time = db.Column(db.DateTime, nullable=True)
    is_delete = db.Column(db.Integer, nullable=True, default=0)


class ApiSuiteRunResult(Base, BaseMixin):
    """接口测试集合执行结果表"""
    __tablename__ = 'api_suite_run_result'
    run_id = db.Column(db.BigInteger, nullable=True, index=True, default=0)
    suite_id = db.Column(db.Integer, nullable=True, index=True)
    project_id = db.Column(db.Integer, nullable=True, index=True)
    environment_id = db.Column(db.Integer, nullable=True, index=True)
    total_count = db.Column(db.Integer, nullable=True, default=0)
    pass_count = db.Column(db.Integer, nullable=True, default=0)
    fail_count = db.Column(db.Integer, nullable=True, default=0)
    elapsed_ms = db.Column(db.Integer, nullable=True)
    success = db.Column(db.Integer, nullable=True, default=0)
    run_status = db.Column(db.String(40), nullable=True, default="finished", index=True)
    status_text = db.Column(db.String(191), nullable=True, default="")
    context = db.Column(db.TEXT(65533), nullable=True)
    step_results = db.Column(db.TEXT(65533), nullable=True)
    error_message = db.Column(db.TEXT(65533), nullable=True)


class ApiReport(Base, BaseMixin):
    """接口测试报告表，独立于 pytest HTML 报告"""
    __tablename__ = 'api_report'
    title = db.Column(db.String(255), nullable=False, index=True)
    report_type = db.Column(db.String(40), nullable=False, default="api", index=True)
    target_type = db.Column(db.String(40), nullable=False, index=True)  # case / suite
    target_id = db.Column(db.Integer, nullable=True, index=True)
    target_name = db.Column(db.String(255), nullable=True)
    run_id = db.Column(db.BigInteger, nullable=True, index=True, default=0)
    report_path = db.Column(db.String(1000), nullable=True)
    run_result_id = db.Column(db.Integer, nullable=True, index=True)
    suite_result_id = db.Column(db.Integer, nullable=True, index=True)
    project_id = db.Column(db.Integer, nullable=True, index=True)
    environment_id = db.Column(db.Integer, nullable=True, index=True)
    total_count = db.Column(db.Integer, nullable=True, default=0)
    pass_count = db.Column(db.Integer, nullable=True, default=0)
    fail_count = db.Column(db.Integer, nullable=True, default=0)
    success = db.Column(db.Integer, nullable=True, default=0, index=True)
    elapsed_ms = db.Column(db.Integer, nullable=True)
    summary = db.Column(db.TEXT(65533), nullable=True)
    detail = db.Column(db.TEXT(65533), nullable=True)
    is_delete = db.Column(db.Integer, nullable=True, default=0)
