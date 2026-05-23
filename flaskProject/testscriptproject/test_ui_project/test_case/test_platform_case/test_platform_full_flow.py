# -*- coding: utf-8 -*-
from playwright.sync_api import Page, expect

from ...page_common.page_platform_flow import PlatformFlowPage


class TestPytestToolFullFlow:
    """按测试平台业务模块组织的 UI 全流程用例。"""

    def test_dashboard_overview_flow(self, page: Page):
        """首页看板展示平台核心统计入口"""
        platform = PlatformFlowPage(page)
        platform.login_platform()
        platform.assert_dashboard_cards()

    def test_department_project_flow(self, page: Page):
        """业务部门和脚本项目管理流程"""
        platform = PlatformFlowPage(page)
        platform.goto_business_department()
        platform.assert_page_has_table_and_query()
        platform.open_button_dialog("新建业务部门", "新建业务部门")

        platform.goto_project()
        platform.search_by_placeholder("脚本项目名称", "test")
        platform.open_button_dialog("新建脚本项目", "新建或编辑脚本项目")
        platform.assert_project_dashboard_if_available()

    def test_version_module_config_flow(self, page: Page):
        """版本、模块、配置基础维护流程"""
        platform = PlatformFlowPage(page)
        platform.goto_version()
        platform.search_by_placeholder("版本号", "v")
        platform.open_button_dialog("新建脚本项目版本信息", "新建或编辑项目版本信息")

        platform.goto_module()
        platform.search_by_placeholder("模块名称", "test")
        platform.open_button_dialog("新建模块", "新建或编辑模块")

        platform.goto_config()
        platform.assert_page_has_table_and_query()
        platform.open_button_dialog("新建配置", "新建配置项")

    def test_case_and_testset_flow(self, page: Page):
        """用例列表、源码预览入口、测试集管理流程"""
        platform = PlatformFlowPage(page)
        platform.goto_cases()
        platform.search_by_placeholder("用例名", "test")
        expect(page.get_by_role("button", name="扫描新增用例")).to_be_visible(timeout=10000)
        expect(page.get_by_role("button", name="添加到测试集")).to_be_visible(timeout=10000)

        platform.goto_testset()
        platform.assert_page_has_table_and_query()
        expect(page.get_by_role("button", name="新建测试集")).to_be_visible(timeout=10000)
        expect(page.get_by_text("进程池占用").first).to_be_visible(timeout=10000)

    def test_testtask_flow(self, page: Page):
        """测试任务列表和资源占用展示流程"""
        platform = PlatformFlowPage(page)
        platform.goto_testtask()
        platform.search_by_placeholder("任务名称", "test")
        expect(page.get_by_role("button", name="新增测试任务")).to_be_visible(timeout=10000)
        expect(page.get_by_text("进程池占用").first).to_be_visible(timeout=10000)

    def test_api_test_flow(self, page: Page):
        """接口用例、接口集合、执行结果工作区流程"""
        platform = PlatformFlowPage(page)
        platform.assert_api_workspace()
        expect(page.get_by_role("button", name="新增接口")).to_be_visible(timeout=10000)
        page.get_by_text("接口集合").first.click()
        expect(page.get_by_role("button", name="新增集合")).to_be_visible(timeout=10000)
        for text in ("接口编排", "集合结果", "执行历史"):
            expect(page.get_by_text(text).first).to_be_visible(timeout=10000)

    def test_report_and_result_flow(self, page: Page):
        """测试报告和用例执行结果追踪流程"""
        platform = PlatformFlowPage(page)
        platform.goto_report()
        expect(page.get_by_placeholder("测试报告名")).to_be_visible(timeout=10000)
        expect(page.get_by_placeholder("报告来源")).to_be_visible(timeout=10000)
        platform.query()

        platform.goto_result()
        expect(page.get_by_placeholder("运行测试集或任务的id")).to_be_visible(timeout=10000)
        expect(page.get_by_placeholder("全部来源")).to_be_visible(timeout=10000)
        platform.query()

    def test_account_and_operation_log_flow(self, page: Page):
        """管理员账号权限和操作日志流程"""
        platform = PlatformFlowPage(page)
        platform.goto_account()
        platform.wait_table()
        expect(page.get_by_role("button", name="新增账号")).to_be_visible(timeout=10000)

        platform.goto_operation_log()
        platform.assert_page_has_table_and_query()
        expect(page.get_by_placeholder("操作账号")).to_be_visible(timeout=10000)
