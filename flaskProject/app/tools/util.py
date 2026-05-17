# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
import yagmail
import os
import configparser
from copy import deepcopy
import threading
import config

encoding = "utf-8"
if os.name == 'nt':
    encoding = 'GBK'


class EmailThread(threading.Thread):
    def __init__(self, email_to, subject='测试正文和附件结果', contents=[],
                 attachments=None):
        super().__init__()
        self.email_to = email_to
        self.subject = subject
        self.contents = contents
        self.attachments = attachments

    def run(self):
        email_host = config.AppConFig.email_info.get("email_host")
        token = config.AppConFig.email_info.get("token")
        smtp = config.AppConFig.email_info.get("smtp")
        if "；" in self.email_to:
            self.email_to = self.email_to.split("；")
        if ";" in self.email_to:
            self.email_to = self.email_to.split(";")
        with yagmail.SMTP(email_host, token, smtp, encoding=encoding) as mail:
            mail.send(self.email_to, self.subject, self.contents, self.attachments)


def send_email(email_to, subject='测试正文和附件结果', contents=[],
               attachments=None):
    """

    :param email_to:
    :param subject:
    :param contents:
    :param attachments:
    :return:
    """
    email_host = config.AppConFig.email_info.get("email_host")
    token = config.AppConFig.email_info.get("token")
    smtp = config.AppConFig.email_info.get("smtp")
    if "；" in email_to:
        email_to = email_to.split("；")
    if ";" in email_to:
        email_to = email_to.split(";")
    with yagmail.SMTP(email_host, token, smtp, encoding=encoding) as mail:
        mail.send(email_to, subject, contents, attachments)


def read_ini_file(file_path):
    # print(file_path)
    # 创建配置解析器对象
    config = configparser.ConfigParser()

    # 读取 INI 文件
    config.read(file_path, encoding='utf-8')

    # 将内容转换为字典
    config_dict = {section: dict(config.items(section)) for section in config.sections()}

    return config_dict


def clear_ini_file(file_path):
    # 创建 ConfigParser 对象
    config = configparser.ConfigParser()

    # 读取 ini 文件
    config.read(file_path, encoding='utf-8')

    # 清空所有内容
    for section in config.sections():
        config.remove_section(section)

    # 将清空后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as configfile:
        config.write(configfile)
    return True


def print_folder_tree(path, parent_is_last=1, depth_limit=-1, tab_width=1):
    """
    以树状打印输出文件夹下的文件, 并返回文件夹内的所有文件
    :param tab_width: 空格宽度
    :param path: 文件夹路径
    :param depth_limit: 要输出文件夹的层数, -1为输出全部文件及文件夹
    :param parent_is_last: 递归调用上级文件夹是否是最后一个文件(夹), 控制输出 │ 树干
    :return: 返回path下的所有文件的数组
    """
    files = []
    if len(str(parent_is_last)) - 1 == depth_limit:
        return files
    items = os.listdir(path)
    for index, i in enumerate(items):
        is_last = index == len(items) - 1
        i_path = path + "/" + i
        for k in str(parent_is_last)[1:]:
            if k == "0":
                if not i_path.endswith(".pyc"):
                    print("│" + "\t" * tab_width, end="")
            if k == "1":
                if not i_path.endswith(".pyc"):
                    print("\t" * tab_width, end="")
        if is_last:
            if not i_path.endswith(".pyc"):
                print("└── ", end="")
        else:
            if not i_path.endswith(".pyc"):
                print("├── ", end="")
        if os.path.isdir(i_path):
            print(i)
            files.extend(print_folder_tree(
                path=i_path, depth_limit=depth_limit,
                parent_is_last=(parent_is_last * 10 + 1) if is_last else (parent_is_last * 10)))
        else:
            if not i_path.endswith(".pyc"):
                print(i_path.split("/")[-1])
                files.append(i_path)
    return files


def get_relation_tree(path):
    finger_files_dict, people_fingers_dict, people_name_befor = {}, {}, ''
    for root, dirs, files in os.walk(path):
        if files:
            dir_list = root.split("\\")
            people_name, finger_name = dir_list[-2], dir_list[-1]
            if people_name != people_name_befor:  # 如果人名改变了，清空finger_files_dict
                finger_files_dict.clear()
            people_name_befor = deepcopy(people_name)
            finger_files_dict[finger_name] = files
            temp_dict = deepcopy(finger_files_dict)  # 深拷贝，防止已经存到people_fingers_dict的数据被覆盖

            people_fingers_dict[people_name] = temp_dict
    print(people_fingers_dict)
    return people_fingers_dict


def read(filepath, n):
    files = os.listdir(filepath)  # 获取当前路径下的文所有文件，(拿到的是一个可迭代对象)

    for el in files:  # 遍历文件
        fp = os.path.join(filepath, el)  # 拿到绝对路径
        if os.path.isdir(fp):  # 判断是否是文件夹
            print("\t" * n, el)
            read(fp, n + 1)  # 递归入口，如果还是文件夹，继续读取内部文件
        else:
            print("\t" * n, el)  # 递归出口，不是文件夹，就答应文件名
