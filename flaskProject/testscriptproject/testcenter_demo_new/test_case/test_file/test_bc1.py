#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
import logging
from ...project_commom import *
import pytest


class Testprob:

    def test_bc_file(self):
        """这是test_b1111_file"""
        logging.info("这是测试B脚本token》》》》")
        set_login_token(token="这是test_b_file用例更新的token值:test_b_file")
        token = token_path.get("token")
        logging.info(f"这是获取一个共享的token值>>>>>>>{token}")
        logging.info("这是测试B脚本")
        logging.debug("这是debug日志")
        self.a = "addddddddddddddddddd"
        assert 3 == 1

    def test_bc_1_file(self, del_case_data):
        """这是test_b1111_1_file"""
        logging.info(del_case_data(["111", "222", "333", "444", "555", "666", "777"]))
        logging.info("这是测试B-1脚本tonen》》》》")
        token = token_path.get("token")
        logging.info(f"这是获取一个共享的token值>>>>>>>{token}")
        logging.info("这是测试B-1脚本")
        logging.debug("这是debug日志")
        self.a = "addddddddddddddddddd"
        assert 3 == 3

    @pytest.mark.parametrize("a, b, expected",
                             [(1, 1, 2), (2, 3, 5), (0, 0, 0), (-2, 1, 0), (-1, 1, 0), (-1, 1, 0), (-1, 1, 0),
                              (-1, 1, 0)])
    def test_add(self, a, b, expected):
        """这是test_add,测试参数化用例"""
        logging.info("这是测试test_add脚本1111111111111")
        assert a + b == expected

    def login_token(self):
        pass


if __name__ == "__main__":
    pytest.main()
