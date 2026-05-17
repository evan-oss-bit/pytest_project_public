# !/usr/bin/python3.8
# -*- coding: utf-8 -*-

from flask import jsonify, request
from app.web_api import module
from app.models.test_api_models import *
from flasgger import swag_from
from app.lib import image
from app.tools.auth_permissions import filter_project_query, require_project_permission

@module.route('/get_module_info', methods=["POST"])
@swag_from('../apidocs/get_module_info.yml')
def get_module_info():
    """获取模块信息列表"""

    page_no = request.json.get("page_no", 0)
    page_size = request.json.get("page_size", 100)
    module = request.json.get("module", "").strip()
    project_id = request.json.get("project_id")
    version_id = request.json.get("version_id")

    query = Test_Module.query

    if project_id:
        permission_error = require_project_permission(project_id, "view")
        if permission_error:
            return permission_error
        query = query.filter_by(project_id=project_id)
    else:
        query = filter_project_query(query, Test_Module)
    if version_id:
        query = query.filter_by(version_id=version_id)
    if module:
        query = query.filter(Test_Module.module.like(f"%{module}%"))

    query = query.order_by(db.desc(Test_Module.updated_time)).limit(page_size).offset(page_no * page_size).all()

    if query:
        query = [i.to_dict() for i in query]

    version_ids = image.get_values_by_key(query, "version_id", values=[])
    project_ids = image.get_values_by_key(query, "project_id", values=[])

    if isinstance(project_ids, int):
        project_ids = [project_ids]
    if isinstance(version_ids, int):
        version_ids = [version_ids]

    version_list = project_list = None
    if version_ids:
        version_list = Version.query.filter(Version.id.in_(version_ids)).all()
    if project_ids:
        project_list = Project.query.filter(Project.id.in_(project_ids)).all()

    if project_list:
        project_list = {i.id: i.to_dict() for i in project_list}
        for item in query:
            project = project_list.get(item.get("project_id"))
            if project:
                item.update({"project_name": project.get("name")})

    if version_list:
        version_list = {i.id: i.to_dict() for i in version_list}
        for item in query:
            version = version_list.get(item.get("version_id"))
            if version:
                item.update({"version_name": version.get("version")})
    for i in query:
        if i.get("updated_time"):
            i.update({"updated_time": i.get("updated_time").strftime("%Y-%m-%d %H:%M:%S")})
        if i.get("created_time"):
            i.update({"created_time": i.get("created_time").strftime("%Y-%m-%d %H:%M:%S")})
    return_dict = {'code': 200, 'msg': '请求成功', 'data': query}
    return jsonify(return_dict)

# @module.route('/get_module_info', methods=["POST"])
# @swag_from('../apidocs/get_module_info.yml')
# def get_module_info():
#     """获取模块信息列表"""
#
#     page_no = request.json.get("page_no", 0)
#     page_size = request.json.get("page_size", 100)
#     module = request.json.get("module")
#     project_id = request.json.get("project_id")
#     version_id = request.json.get("version_id")
#     module = module.strip()
#     # query = None
#     if project_id:
#         if version_id:
#             if module:
#                 query = Test_Module.query.filter_by(project_id=project_id).filter_by(version_id=version_id).filter(
#                     Test_Module.module.like(f"%{module}%")).order_by(
#                     db.desc(Test_Module.updated_time)).limit(page_size).offset(
#                     page_no).all()
#             else:
#                 query = Test_Module.query.filter_by(project_id=project_id).filter_by(version_id=version_id).order_by(
#                     db.desc(Test_Module.updated_time)).limit(page_size).offset(
#                     page_no).all()
#         else:
#             query = Test_Module.query.filter_by(project_id=project_id).order_by(
#                 db.desc(Test_Module.updated_time)).limit(page_size).offset(
#                 page_no).all()
#     elif module:
#         # query = Test_Module.query.filter_by(module=module).all()
#         query = Test_Module.query.filter(Test_Module.module.like(f"%{module}%")).all()
#     else:
#         query = Test_Module.query.order_by(db.desc(Test_Module.updated_time)).limit(page_size).offset(page_no)
#     if query:
#         query = [i.to_dict() for i in query]
#     version_ids = image.get_values_by_key(query, "version_id", values=[])
#     project_ids = image.get_values_by_key(query, "project_id", values=[])
#     if isinstance(project_ids, int):
#         project_ids = [project_ids]
#     if isinstance(version_ids, int):
#         version_ids = [version_ids]
#     # print(version_ids)
#     version_list = project_list = None
#     if version_ids:
#         version_list = Version.query.filter(Version.id.in_(version_ids)).all()
#     if project_ids:
#         project_list = Project.query.filter(Project.id.in_(project_ids)).all()
#     if project_list:
#         project_list = [i.to_dict() for i in project_list]
#         for i in range(len(query)):
#             for j in project_list:
#                 if query[i].get("project_id") == j.get("id"):
#                     query[i].update({"project_name": j.get("name")})
#     if version_list:
#         version_list = [i.to_dict() for i in version_list]
#         for i in range(len(query)):
#             for j in version_list:
#                 if query[i].get("version_id") == j.get("id"):
#                     query[i].update({"version_name": j.get("version")})
#     return_dict = {'code': 200, 'msg': '请求成功', 'data': query}
#     return jsonify(return_dict)


@module.route('/update_module', methods=["POST"])
# @swag_from('../apidocs/update_module.yml')
def update_module():
    """更新模块信息"""

    id = request.json.get("id")
    description = request.json.get("description")
    module = request.json.get("module")
    version_id = request.json.get("version_id")
    project_id = request.json.get("project_id")
    query = Test_Module.query.filter_by(id=id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '模块不存在', 'data': None})
    permission_error = require_project_permission(query.project_id, "edit")
    if permission_error:
        return permission_error
    permission_error = require_project_permission(project_id, "edit")
    if permission_error:
        return permission_error
    query.version_id = version_id
    query.module = module
    query.project_id = project_id
    query.description = description

    db.session.commit()

    return_dict = {'code': 200, 'msg': '请求成功', 'data': id}
    return jsonify(return_dict)


@module.route('/add_module', methods=["POST"])
@swag_from('../apidocs/add_module.yml')
def add_module():
    """新增或修改模块信息"""
    id = request.json.get("id")
    description = request.json.get("description")
    module = request.json.get("module", "")
    version_id = request.json.get("version_id")
    project_id = request.json.get("project_id")
    module = module.strip()
    if not module or not version_id or not project_id:
        return jsonify({'code': 404, 'msg': '缺少必填参数', 'data': ""})
    if project_id:
        if isinstance(project_id, list):
            project_id = project_id[0]
    if version_id:
        if isinstance(version_id, list):
            version_id = version_id[0]
    if id:
        old_module = Test_Module.query.filter_by(id=id).first()
        if old_module:
            permission_error = require_project_permission(old_module.project_id, "edit")
            if permission_error:
                return permission_error
    permission_error = require_project_permission(project_id, "edit")
    if permission_error:
        return permission_error
    if id:
        query = Test_Module.query.filter_by(id=id).first()
        query.version_id = version_id
        query.module = module
        query.project_id = project_id
        query.description = description
    else:
        new_mod = Test_Module(project_id=int(project_id), module=module, version_id=int(version_id),
                              description=description)
        db.session.add(new_mod)
        db.session.flush()
        id = new_mod.id
    db.session.commit()

    return_dict = {'code': 200, 'msg': '请求成功', 'data': id}
    return jsonify(return_dict)
