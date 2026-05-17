#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
import logging
from ...project_commom import *


class Testprob:

    def test_bc_file(self):
        """这是test_b_file"""
        logging.info("这是测试B脚本token》》》》")
        set_login_token(token="这是test_b_file用例更新的token值:test_b_file")
        token = token_path.get("token")
        logging.info(f"这是获取一个共享的token值>>>>>>>{token}")
        logging.info("这是测试B脚本")
        logging.debug("这是debug日志111111111111111111111111111111111111111111111111111111")
        self.a = "adddkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"
        assert 3 == 2

    def test_bc_1_file(self, del_case_data):
        """这是test_b_1_file"""
        logging.info(del_case_data(["111", "222", "333", "444", "555", "666", "777"]))
        logging.info("这是测试B-1脚本tonen》》》》")
        token = token_path.get("token")
        logging.info(f"这是获取一个共享的token值>>>>>>>{token}")
        logging.info("这是测试B-1脚本")
        self.a = "addddddddddddddddddd11111111111111111111111111111"
        assert 3 == 3

    def login_token(self):
        pass
