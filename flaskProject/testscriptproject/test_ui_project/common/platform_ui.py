# -*- coding: utf-8 -*-
import os

import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect


class PytestToolUI:
    """Playwright helper for the pytest test platform frontend."""

    def __init__(self, page: Page):
        self.page = page
        self.base_url = os.getenv("PYTEST_TOOL_UI_BASE_URL", "http://127.0.0.1:8888/#")
        self.username = os.getenv("PYTEST_TOOL_UI_USERNAME", "test_admin")
        self.password = os.getenv("PYTEST_TOOL_UI_PASSWORD", "123456789")

    def url(self, route: str) -> str:
        route = route if route.startswith("/") else "/{}".format(route)
        return "{}{}".format(self.base_url.rstrip("/"), route)

    def open(self, route: str = "/login"):
        try:
            self.page.goto(self.url(route), wait_until="commit", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        except Exception as exc:
            pytest.skip("前端页面无法访问，请先启动 vue_pytest_tool 前端服务: {}".format(exc))

    def login(self):
        self.open("/login")
        if self.page.locator(".el-menu").count() > 0:
            return
        self.page.get_by_placeholder("账号").fill(self.username)
        self.page.get_by_placeholder("密码").fill(self.password)
        self.page.get_by_role("button", name="登录").click()
        try:
            self.page.wait_for_url("**/dashboard", timeout=10000)
        except PlaywrightTimeoutError:
            expect(self.page.get_by_text("首页看板").first).to_be_visible(timeout=5000)
        expect(self.page.get_by_text("PYTestTool")).to_be_visible(timeout=8000)

    def goto_page(self, route: str, title: str):
        self.login()
        self.page.goto(self.url(route), wait_until="domcontentloaded", timeout=10000)
        expect(self.page.get_by_text(title).first).to_be_visible(timeout=10000)

    def click_query(self):
        self.page.get_by_role("button", name="查询").click()
