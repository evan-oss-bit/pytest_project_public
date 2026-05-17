#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
import os
import platform

sep_token_dict = {}
file_server = os.getenv("PYTEST_TOOL_FILE_SERVER", "127.0.0.1")  # ftp/samba/nginx


class Aio_def():
    file_server_port = 'http://{}:8828'.format(file_server)
    
    script_dir = '/public/material/auto_install_script'
    server_script_dir = f'{file_server_port}/public/material/auto_install_script'
    server_wget_url = f"{server_script_dir}/sf_and_st_shell/wget-1.14-18.el7_6.1.x86_64.rpm"
    server_download_tar_url = f"{file_server_port}/public/material/shell/download_tar.sh"
    
    script_install_dir = 'wget -r -np -nH {}/'.format(script_dir)
    deploy_node_dir = '/aio'
    deploy_node_update_kernel_name = 'update_kernel.sh'
    mail_add = os.getenv("PYTEST_TOOL_NOTICE_EMAIL", "")


class Bus_def():
    # api/web
    user = os.getenv("PYTEST_TOOL_BUS_USER", "admin")
    pwd = os.getenv("PYTEST_TOOL_BUS_PASSWORD", "")
    user_vendor = os.getenv("PYTEST_TOOL_BUS_VENDOR_USER", "vendor")
    pwd_vendor = os.getenv("PYTEST_TOOL_BUS_VENDOR_PASSWORD", "")
    new_user_pwd = os.getenv("PYTEST_TOOL_BUS_NEW_USER_PASSWORD", "")
    # api/web  4.3.3 5.0 安全加固后  初始密码变更
    pwd_ssl = os.getenv("PYTEST_TOOL_BUS_SSL_PASSWORD", "")
    pwd_vendor_ssl = os.getenv("PYTEST_TOOL_BUS_VENDOR_SSL_PASSWORD", "")
    # sql
    sql_user = os.getenv("PYTEST_TOOL_BUS_SQL_USER", "root")
    sql_pwd = os.getenv("PYTEST_TOOL_BUS_SQL_PASSWORD", "")
    sql_port = int(os.getenv("PYTEST_TOOL_BUS_SQL_PORT", "10208"))
    sql_db = os.getenv("PYTEST_TOOL_BUS_SQL_DB", "senseface")
    # redis
    redis_port = int(os.getenv("PYTEST_TOOL_BUS_REDIS_PORT", "10200"))
    redis_pwd = os.getenv("PYTEST_TOOL_BUS_REDIS_PASSWORD", "")
    redis_UUMS_port = int(os.getenv("PYTEST_TOOL_BUS_REDIS_UUMS_PORT", "10299"))
    # es
    es_port = '10228'
    es_phone_index = "target_wireless_terminal_index"
    # back
    host_user = os.getenv("PYTEST_TOOL_BUS_HOST_USER", "root")
    host_pwd = os.getenv("PYTEST_TOOL_BUS_HOST_PASSWORD", "")
    # bdp
    bdp_kafka_port = 6667
    bdp_kafka_topic = ""
    # SEP
    sep_host = os.getenv("PYTEST_TOOL_SEP_HOST", "")


class materialDef():
    material_path = os.path.join(r"\\{}\public".format(file_server), 'material') if platform.system() == "Windows" else '/material'
    push_img_dir_path = os.path.join(material_path, 'images_push', 'images_relation')


class GbSimulation():
    gb_server = os.getenv("PYTEST_TOOL_GB_SERVER", "127.0.0.1")
    gb_server_user = os.getenv("PYTEST_TOOL_GB_SERVER_USER", "root")
    gb_server_password = os.getenv("PYTEST_TOOL_GB_SERVER_PASSWORD", "")


