# -*- coding: utf-8 -*-
import os

import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect

from ..component_commom.page_navigation import BaseNaviationPage


class PlatformFlowPage(BaseNaviationPage):
    """测试平台全流程页面对象封装。"""

    def __init__(self, page: Page):
        super().__init__(page, "")
        self.url = os.getenv("PYTEST_TOOL_UI_BASE_URL", "http://127.0.0.1:8888/#/")
        self.username = os.getenv("PYTEST_TOOL_UI_USERNAME", "test_admin")
        self.password = os.getenv("PYTEST_TOOL_UI_PASSWORD", "123456789")

    def route_url(self, route):
        return "{}{}".format(self.url.rstrip("/"), route if route.startswith("/") else "/{}".format(route))

    def open_route(self, route, title):
        try:
            self.page.goto(self.route_url(route), wait_until="commit", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        expect(self.page.get_by_text(title).first).to_be_visible(timeout=10000)

    def login_platform(self):
        try:
            self.page.goto(self.route_url("/login"), wait_until="commit", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        if self.page.get_by_text("首页看板").count() > 0:
            return
        self.page.get_by_placeholder("账号").fill(self.username)
        self.page.get_by_placeholder("密码").fill(self.password)
        self.page.get_by_role("button", name="登录").click()
        try:
            self.page.wait_for_url("**/dashboard", timeout=10000)
        except PlaywrightTimeoutError:
            expect(self.page.get_by_text("首页看板").first).to_be_visible(timeout=5000)

    def goto_business_department(self):
        self.login_platform()
        self.open_route("/business_department", "业务部门管理")

    def goto_project(self):
        self.login_platform()
        self.open_route("/pytest_project", "脚本项目列表")

    def goto_version(self):
        self.login_platform()
        self.open_route("/pytest_version", "项目版本列表")

    def goto_module(self):
        self.login_platform()
        self.open_route("/pytest_module", "项目模块列表")

    def goto_config(self):
        self.login_platform()
        self.open_route("/pytest_config", "配置列表")

    def goto_cases(self):
        self.login_platform()
        self.open_route("/pytest_cases", "用例列表")

    def goto_testset(self):
        self.login_platform()
        self.open_route("/pytest_testset", "测试集合列表")

    def goto_testtask(self):
        self.login_platform()
        self.open_route("/pytest_testtask", "测试任务列表")

    def goto_api_test(self):
        self.login_platform()
        self.open_route("/api_test", "接口测试")

    def goto_report(self):
        self.login_platform()
        self.open_route("/pytest_report", "测试报告列表")

    def goto_result(self):
        self.login_platform()
        self.open_route("/pytest_result", "用例执行结果")

    def goto_account(self):
        self.login_platform()
        self.open_route("/account_permission", "账号权限")

    def goto_operation_log(self):
        self.login_platform()
        self.open_route("/operation_log", "操作日志")

    def query(self):
        self.page.get_by_role("button", name="查询").first.click()
        self.wait_table()

    def wait_table(self):
        expect(self.page.locator(".el-table").first).to_be_visible(timeout=10000)

    def open_button_dialog(self, button_name, dialog_title):
        self.page.get_by_role("button", name=button_name).first.click()
        dialog = self.page.locator(".el-dialog__wrapper:visible").first
        expect(dialog).to_be_visible(timeout=10000)
        expect(dialog.get_by_text(dialog_title).first).to_be_visible(timeout=10000)
        self.close_visible_dialog()

    def close_visible_dialog(self):
        close_buttons = self.page.locator(".el-dialog__wrapper:visible .el-dialog__headerbtn")
        if close_buttons.count() > 0:
            close_buttons.last.click()

    def search_by_placeholder(self, placeholder, keyword):
        self.page.get_by_placeholder(placeholder).first.fill(keyword)
        self.query()

    def assert_page_has_table_and_query(self):
        expect(self.page.get_by_role("button", name="查询").first).to_be_visible(timeout=10000)
        self.wait_table()

    def assert_dashboard_cards(self):
        self.open_route("/dashboard", "首页看板")
        for text in ("脚本项目", "测试集", "测试任务", "报告"):
            expect(self.page.get_by_text(text).first).to_be_visible(timeout=10000)

    def assert_project_dashboard_if_available(self):
        self.goto_project()
        self.wait_table()
        project_links = self.page.locator(".project-name-button")
        if project_links.count() == 0:
            return
        project_links.first.click()
        dialog = self.page.locator(".el-dialog__wrapper:visible").first
        expect(dialog).to_be_visible(timeout=10000)
        for text in ("总览", "用例", "测试集", "测试任务", "报告"):
            expect(dialog.get_by_text(text).first).to_be_visible(timeout=10000)
        self.close_visible_dialog()

    def assert_api_workspace(self):
        self.goto_api_test()
        for text in ("接口用例", "接口集合", "响应Body", "执行历史"):
            expect(self.page.get_by_text(text).first).to_be_visible(timeout=10000)
