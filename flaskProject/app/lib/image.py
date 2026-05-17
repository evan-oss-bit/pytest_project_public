# coding=UTF-8

import os
import random
import re

import uuid

import redis

related_path = "material" + os.sep + "SenseFace" + os.sep + "API"
home_path = os.environ.get("HOME_PATH") if "HOME_PATH" in os.environ.keys() else \
    os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + os.path.sep + "..")
full_path = os.path.join(home_path, related_path)


def random_int(min, max, return_str=False):
    return str(random.randint(min, max)) if return_str else random.randint(min, max)


def random_choice(boundary, return_str=False):
    return str(random.choice(boundary)) if return_str else random.choice(boundary)


def get_uuid1():
    temp = str(uuid.uuid1()).replace('-', '')
    return temp


def convert_to_json(search_dict, field):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []

    for key, value in search_dict.items():

        if key == field:
            fields_found.append(value)

        elif isinstance(value, dict):
            results = convert_to_json(value, field)
            for result in results:
                fields_found.append(result)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results = convert_to_json(item, field)
                    for another_result in more_results:
                        fields_found.append(another_result)
    return fields_found


def get_uuid_name(name_prefix="", name_suffix="", cut_length=10, ):
    """
    获取一个随机uuid字符串
    :param name_prefix:字符串拼接前缀
    :param name_suffix: 字符串拼接后缀,同上使用
    :param cut_length: 随机截取uuid字符串长度
    :return: 大于30位自动截取,默认截取10uuid+2位数字字符串
    """
    uuid_cut = ""
    name_suffix = name_suffix or random_int(10, 99, True)
    while len(uuid_cut) < cut_length:
        uuid_cut += random_choice(list(get_uuid1()))
    name_str = name_prefix + uuid_cut + name_suffix
    return name_str if len(name_str) <= 30 else name_str[:30]


def get_ip_in_str(message, index=0, is_all=False):
    """
    获取字符串里面的IP
    :param message:
    :param index:
    :param is_all:
    :return:
    """
    try:
        ip_reg = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        ip_reg = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        ip_list = re.findall(ip_reg, message)
        if ip_list:
            return ip_list[0] if len(ip_list) == 1 else ip_list
        # if is_all:
        #     return ip_list
        # if index is not None and len(ip_list) <= index:
        #     return message
        # elif index is not None:
        #     return ip_list[int(index)]
    except Exception:
        return None


def get_values_by_key(input_json, key, values, dict_in=None):
    """
    递归获取key对应的value
    :param input_json:
    :param key:
    :param values:
    :param dict_in:
    :return:
    """
    optional = False
    if input_json is None:
        return None
    if "?" in key:
        key = key.split("?")[0]
        optional = True
    else:
        pass
    if isinstance(input_json, dict):
        for json_result in input_json.values():
            if key in input_json.keys():
                key_value = input_json.get(key)
                if type(key_value) is int and not key_value:
                    key_value = 0
                elif type(key_value) is list and not key_value:
                    key_value = []
                elif type(key_value) is dict and not key_value:
                    key_value = {}
                elif type(key_value) is float and not key_value:
                    key_value = 0.0
                elif type(key_value) is str and not key_value:
                    key_value = ""
                elif type(key_value) is bool and not key_value:
                    key_value = False
                elif not key_value:
                    if dict_in and type(dict_in) == "dict" and "key" in dict_in.keys() and \
                            "senseface_host" in dict_in["key"].keys():
                        if optional:
                            return "Optional"
                        else:
                            return None
                    else:
                        # key_value = "None"
                        key_value = None
                if key_value not in values:
                    values.append(key_value)
            else:
                get_values_by_key(json_result, key, values, dict_in)
    elif isinstance(input_json, list):
        for json_array in input_json:
            get_values_by_key(json_array, key, values, dict_in)
    if values:
        if len(values) > 1:
            return values
        elif len(values) == 1:
            return values[0]
    else:
        if optional:
            return "Optional"
        else:
            return None


def get_item_by_key(obj, key, result=None):
    if isinstance(obj, dict):
        for k in obj:
            if key == k:
                if isinstance(result, list):
                    if isinstance(obj[k], list):
                        result.extend(obj[k])
                    else:
                        result.append(obj[k])
                elif result is None:
                    result = obj[k]
                else:
                    result = [result, obj[k]]
            else:
                if isinstance(obj[k], dict) or isinstance(obj[k], list):
                    result = get_item_by_key(obj[k], key, result)
    elif isinstance(obj, list):
        for i in obj:
            if isinstance(i, dict) or isinstance(i, list):
                result = get_item_by_key(i, key, result)
    return result[0] if isinstance(result, list) and len(result) == 1 else result


def get_redis_ch(host='127.0.0.1', pwd='', port=6379):
    """
     redis 连接
    :param host:
    :param pwd:
    :param port:
    :return:
    """
    sf_ip = get_ip_in_str(host)
    pool = redis.ConnectionPool(host=sf_ip, port=port, db=0, password=pwd, decode_responses=True)
    red_con = redis.StrictRedis(connection_pool=pool)
    return red_con
