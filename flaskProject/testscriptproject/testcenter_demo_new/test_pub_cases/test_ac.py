#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
import pytest
import logging
from ..project_commom import *


class Testpro:
    @staticmethod
    def test_ac_file():
        """这是test_a_file"""
        token = token_path.get("token")
        logging.info(f"这是获取一个共享的token值>>>>>>>{token}")
        logging.info("这是测试A脚本")
        logging.debug("这是debug日志")
        logging.error("这是error日志")


if __name__ == "__main__":
    pytest.main()
