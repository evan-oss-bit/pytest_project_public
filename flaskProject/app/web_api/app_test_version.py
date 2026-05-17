# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
# 从app模块中即从__init__.py中导入创建的app应用
# import traceback
from flask import jsonify, request
from app.web_api import version
from app.models.test_api_models import *
from flasgger import swag_from
from app.lib import image
from app.tools.auth_permissions import filter_project_query, require_project_permission


@version.route('/get_version_info', methods=["POST"])
@swag_from('../apidocs/get_version_info.yml')
def get_version_info():
    """获取版本号列表"""

    page_no = request.json.get("page_no", 0)
    page_size = request.json.get("page_size", 10)
    pj_version = request.json.get("version", "")
    project_id = request.json.get("project_id")
    pj_version = pj_version.strip()
    if project_id:
        permission_error = require_project_permission(project_id, "view")
        if permission_error:
            return permission_error
        query = Version.query.filter_by(project_id=project_id).all()
        if pj_version:
            query = Version.query.filter(Version.version.like(f"%{pj_version}%")).filter_by(project_id=project_id).all()
    elif pj_version:
        # query = Version.query.filter_by(version=pj_version).all()
        query = Version.query.filter(Version.version.like(f"%{pj_version}%")).all()
    else:
        query = filter_project_query(Version.query, Version).order_by(db.desc(Version.updated_time)).limit(
            page_size).offset(page_no)
    if query:
        query = [i.to_dict() for i in query]
    project_ids = image.get_values_by_key(query, "project_id", values=[])
    if isinstance(project_ids, int):
        project_ids = [project_ids]
    project_list = None
    if project_ids:
        project_list = Project.query.filter(Project.id.in_(project_ids)).all()
    if project_list:
        project_list = [i.to_dict() for i in project_list]
        for i in range(len(query)):
            for j in project_list:
                if query[i].get("project_id") == j.get("id"):
                    query[i].update({"project_name": j.get("name")})
    for i in query:
        if i.get("updated_time"):
            i.update({"updated_time": i.get("updated_time").strftime("%Y-%m-%d %H:%M:%S")})
        if i.get("created_time"):
            i.update({"created_time": i.get("created_time").strftime("%Y-%m-%d %H:%M:%S")})
    return_dict = {'code': 200, 'msg': '请求成功', 'data': query}
    return jsonify(return_dict)


@version.route('/update_version', methods=["POST"])
# @swag_from('../apidocs/update_version.yml')
def update_version():
    """更新版本号"""
    id = request.json.get("id")
    pj_version = request.json.get("version")
    changelog = request.json.get("changelog")
    project_id = request.json.get("project_id")
    query = Version.query.filter_by(id=id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '版本不存在', 'data': None})
    permission_error = require_project_permission(query.project_id, "edit")
    if permission_error:
        return permission_error
    permission_error = require_project_permission(project_id, "edit")
    if permission_error:
        return permission_error
    query.version = pj_version
    query.changelog = changelog
    query.project_id = project_id

    db.session.commit()

    return_dict = {'code': 200, 'msg': '请求成功', 'data': id}
    return jsonify(return_dict)


@version.route('/add_version', methods=["POST"])
@swag_from('../apidocs/add_version.yml')
def add_version():
    """新增或者修改版本号"""
    id = request.json.get("id")
    version = request.json.get("version", "")
    changelog = request.json.get("changelog")
    project_id = request.json.get("project_id")
    version = version.strip()
    if not version or not project_id:
        return jsonify({'code': 404, 'msg': '缺少必填参数', 'data': ""})
    if project_id:
        if isinstance(project_id, list):
            project_id = project_id[0]
    if id:
        old_version = Version.query.filter_by(id=id).first()
        if old_version:
            permission_error = require_project_permission(old_version.project_id, "edit")
            if permission_error:
                return permission_error
    permission_error = require_project_permission(project_id, "edit")
    if permission_error:
        return permission_error
    if id:
        query = Version.query.filter_by(id=id).first()
        query.version = version
        query.changelog = changelog
        query.project_id = project_id
    else:
        new_project = Version(version=str(version), changelog=changelog, project_id=project_id)
        db.session.add(new_project)
        db.session.flush()
        id = new_project.id
    db.session.commit()

    return_dict = {'code': 200, 'msg': '请求成功', 'data': id}
    return jsonify(return_dict)
