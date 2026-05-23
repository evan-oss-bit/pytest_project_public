# -*- coding: utf-8 -*-
from playwright.sync_api import Page, expect
import logging
from ...common.platform_ui import PytestToolUI


class TestPytestToolPlatformSmoke:
    """基于测试平台自身页面的 Playwright UI 自动化用例。"""

    def test_login_and_dashboard(self, page: Page):
        """登录平台并进入首页看板"""
        app = PytestToolUI(page)
        app.login()
        expect(page.get_by_text("首页看板").first).to_be_visible(timeout=10000)
        expect(page.get_by_text("admin").first).to_be_visible(timeout=10000)
        logging.info("这是测试B脚本")
    def test_core_menu_pages_can_open(self, page: Page):
        """核心菜单页面可以正常打开"""
        app = PytestToolUI(page)
        pages = [
            ("/dashboard", "首页看板"),
            ("/business_department", "业务部门管理"),
            ("/pytest_project", "脚本项目列表"),
            ("/pytest_testset", "测试集合列表"),
            ("/pytest_testtask", "测试任务列表"),
            ("/api_test", "接口测试"),
            ("/pytest_report", "测试报告列表"),
            ("/pytest_result", "用例执行结果"),
        ]
        for route, title in pages:
            app.goto_page(route, title)
        logging.info("这是测试B脚本")
    def test_script_project_list_search(self, page: Page):
        """脚本项目列表支持按项目名称查询"""
        app = PytestToolUI(page)
        app.goto_page("/pytest_project", "脚本项目列表")
        page.get_by_placeholder("脚本项目名称").fill("test")
        app.click_query()
        expect(page.locator(".el-table").first).to_be_visible(timeout=10000)
        expect(page.get_by_text("脚本项目").first).to_be_visible(timeout=10000)
        logging.info("这是测试脚本项目列表支持按项目名称查询脚本1")
        logging.info("这是测试脚本项目列表支持按项目名称查询脚本2")
        logging.info("这是测试脚本项目列表支持按项目名称查询脚本3")
        logging.info("这是测试脚本项目列表支持按项目名称查询脚本4")
    def test_api_test_workspace_visible(self, page: Page):
        """接口测试页面展示接口用例和接口集合工作区"""
        app = PytestToolUI(page)
        app.goto_page("/api_test", "接口测试")
        expect(page.get_by_text("接口用例").first).to_be_visible(timeout=10000)
        expect(page.get_by_text("接口集合").first).to_be_visible(timeout=10000)
        expect(page.get_by_role("button", name="新增接口")).to_be_visible(timeout=10000)

    def test_report_and_result_filters_visible(self, page: Page):
        """测试报告和用例执行结果页面展示核心筛选条件"""
        app = PytestToolUI(page)
        app.goto_page("/pytest_report", "测试报告列表")
        expect(page.get_by_placeholder("测试报告名")).to_be_visible(timeout=10000)
        expect(page.get_by_role("button", name="查询")).to_be_visible(timeout=10000)

        app.goto_page("/pytest_result", "用例执行结果")
        expect(page.get_by_placeholder("运行测试集或任务的id")).to_be_visible(timeout=10000)
        expect(page.get_by_role("button", name="查询")).to_be_visible(timeout=10000)
        logging.info("这是测试B脚本")
