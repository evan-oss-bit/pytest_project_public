#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
import logging
from ...project_commom import *

class Testprob:
    # def setup(self):
    #     print("setup_function：整个.py模块只执行一次")
    #     print("例如：数据准备")

    def test_bc_file(self, login):
        """这是test_b_1_file"""
        logging.info("这是测试B脚本token》》》》")
        logging.info("这是测试B脚本")
        set_login_token(token="这是首次插入共享token的用例test_b_file")
        # token = token_path.get("token")
        # logging.info(f"这是获取一个共享的token值>>>>>>>{token}")
        self.a = "addddddddddddddddddd"
        assert 3 == 2

    #
    # def teardown(self):
    #     print(self.a)
    #     print("teardown_function：每个用例结束后都会执行一次")

    def test_bc_1_file(self, del_case_data):
        """这是test_b_1_file"""
        logging.info("这是测试B-1脚本tonen》》》》")
        logging.info("这是测试B-1脚本")
        token = token_path.get("token")
        logging.info(f"这是获取一个共享的token值>>>>>>>{token}")
        self.a = "addddddddddddddddddd11111111111111111111111asdddddddddddddddddddddddddddddddddddddddddasd"
        assert 3 == 3
        del_case_data(["111", "222", "333", "444", "555", "666", "777"])
# class Testprocccasd:
#     @staticmethod
#     def test_a_file():
#         print("这是测试A脚本")
#
#     @staticmethod
#     def test_c_file():
#         print("这是测试A脚本")
