# -*- coding: utf-8 -*-
import os
import importlib
import config

def get_cases_from_script(ori_path, py_list):
    """

    :param ori_path:
    :param py_list:
    :return:
    """
    for fi in os.listdir(ori_path):
        fi_path = os.path.join(ori_path, fi)
        if os.path.isdir(fi_path):
            get_cases_from_script(fi_path, py_list)
        else:
            if fi.endswith(".py") and fi != "__init__.py" and fi.startswith("test_"):
                py_list.append(fi_path)
    return py_list


def get_test_models(ori_path, startswith="test_"):
    """

    :param ori_path:
    :param startswith:
    :return:
    """
    models = list()
    if os.listdir(ori_path):
        for file in os.listdir(ori_path):
            if not file.endswith(".py") and file.startswith(startswith):
                models.append(ori_path + "\\" + file)
    return models


def get_test_project(ori_path):
    """

    :param ori_path:
    :return:
    """
    projects = list()
    if os.listdir(ori_path):
        for file in os.listdir(ori_path):
            if not file.endswith(".py") and file.startswith("test"):
                projects.append({"name": file})
    return projects


def add_cases(project_path="testscriptproject", project="testcenter"):
    """

    :param project_path:
    :param project:
    :return:
    """
    path = os.path.join(config.home_path, project_path, project)
    # path = os.path.abspath(os.path.join(os.getcwd(), "../..", "testscriptproject", project))
    # print(path)
    scripts = get_cases_from_script(path, [])
    cla_list = list()
    cases = list()
    # data_dict = dict()
    for script in scripts:
        # print(script)
        imp_scr = script.split(config.home_path)[-1][1:-3].replace(os.sep, ".")

        with open(script, "r", encoding="utf-8") as py_file:
            # print(script)
            for info in py_file.readlines():
                if "class Test" in info and info[0] != "#":
                    cla = info.strip()
                    cla = cla.split(" ")[1].split(":")[0]
                    cla_list.append(script + "::" + cla)
                if "def test_" in info and info[0] != "#":
                    func = info.strip()
                    func = func.split(" ")[1].split("(")[0]
                    func_file = script.split("\\")[-1]
                    relative_case_path = script.split(project_path)[-1]
                    previous_level = os.path.dirname(script)
                    previous_level = os.path.basename(previous_level)
                    imp_cla = importlib.import_module(imp_scr)
                    imp_cla = importlib.reload(imp_cla)
                    new_cla = getattr(imp_cla, cla)
                    new_funcs = eval(f"new_cla.{func}")
                    # print(new_funcs.__doc__)
                    cases.append(
                        {"case": script + "::" + cla + "::" + func, "title": func_file + "::" + cla + "::" + func,
                         "relative_case_path": project_path + relative_case_path + "::" + cla + "::" + func,
                         "relative_path": project_path + relative_case_path, "previous_level": previous_level,
                         "docs": new_funcs.__doc__, "class_name": cla,
                         "relative_cla_case_path": project_path + relative_case_path + "::" + cla })

    # print(cla_list)
    # print(cases)
    return {"cla_list": cla_list, "cases": cases}


if __name__ == "__main__":
    project = "testcenter"
    path = os.path.join(config.home_path,
                        "testscriptproject\\testcenter\\abc1\\test_file\\test_bc.py::Testprob::test_b_file")

    print(path)
    add_cases()
    # print(os.path.abspath(os.path.join(os.getcwd(), "../..")))
    # print(get_test_models(path))
