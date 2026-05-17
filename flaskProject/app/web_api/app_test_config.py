# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
import json

from flask import jsonify, request
from app.web_api import config
from app.models.test_api_models import *
from flasgger import swag_from
from app.lib import image
from app.tools.auth_permissions import allowed_project_ids, is_admin, require_project_permission


def _safe_config_ids(value):
    if not value:
        return []
    try:
        data = eval(value) if isinstance(value, str) else value
    except Exception:
        return []
    if isinstance(data, int):
        return [data]
    if isinstance(data, list):
        return data
    return []


def _visible_config_ids(project_id=None):
    allowed_ids = allowed_project_ids()
    query = TestSet.query.filter_by(is_delete=0)
    if project_id:
        query = query.filter_by(project_id=project_id)
    elif allowed_ids is not None:
        if not allowed_ids:
            return []
        query = query.filter(TestSet.project_id.in_(allowed_ids))
    config_ids = set()
    for item in query.all():
        config_ids.update(_safe_config_ids(item.config))
    return list(config_ids)


@config.route('/get_config_info', methods=["POST"])
@swag_from('../apidocs/get_config_info.yml')
def get_config_info():
    """获取配置信息列表"""

    page_no = request.json.get("page_no", 0)
    page_size = request.json.get("page_size", 10)
    cfg_name = request.json.get("cfg_name", "")
    project_id = request.json.get("project_id")
    cfg_name = cfg_name.strip()
    if project_id:
        permission_error = require_project_permission(project_id, "view")
        if permission_error:
            return permission_error
        visible_ids = _visible_config_ids(project_id)
        query = Cfgs.query.filter(Cfgs.id.in_(visible_ids)).filter_by(is_delete=0).all() if visible_ids else []
        if cfg_name:
            query = Cfgs.query.filter(Cfgs.id.in_(visible_ids)).filter(Cfgs.cfg_name.like(f"%{cfg_name}%")).filter_by(
                is_delete=0).all() if visible_ids else []
    elif cfg_name:
        if is_admin():
            query = Cfgs.query.filter(Cfgs.cfg_name.like(f"%{cfg_name}%")).filter_by(is_delete=0).all()
        else:
            visible_ids = _visible_config_ids()
            query = Cfgs.query.filter(Cfgs.id.in_(visible_ids)).filter(Cfgs.cfg_name.like(f"%{cfg_name}%")).filter_by(
                is_delete=0).all() if visible_ids else []
    else:
        if is_admin():
            query = Cfgs.query.filter_by(is_delete=0).order_by(db.desc(Cfgs.updated_time)).limit(page_size).offset(page_no)
        else:
            visible_ids = _visible_config_ids()
            query = Cfgs.query.filter(Cfgs.id.in_(visible_ids)).filter_by(is_delete=0).order_by(
                db.desc(Cfgs.updated_time)).limit(page_size).offset(page_no) if visible_ids else []
    if query:
        query = [i.to_dict() for i in query]
    # project_ids = image.get_values_by_key(query, "project_id", values=[])
    # if isinstance(project_ids, int):
    #     project_ids = [project_ids]
    # project_list = None
    # if project_ids:
    #     project_list = Project.query.filter(Project.id.in_(project_ids)).all()
    # if project_list:
    #     project_list = [i.to_dict() for i in project_list]
    #     for i in range(len(query)):
    #         for j in project_list:
    #             if query[i].get("project_id") == j.get("id"):
    #                 query[i].update({"project_name": j.get("name")})
    for i in query:
        if i.get("updated_time"):
            i.update({"updated_time": i.get("updated_time").strftime("%Y-%m-%d %H:%M:%S")})
        if i.get("created_time"):
            i.update({"created_time": i.get("created_time").strftime("%Y-%m-%d %H:%M:%S")})
        # if i.get("cfg"):
        #     try:
        #         i.update({"cfg": json.loads(i.get("cfg"))})
        #     except Exception as e:
        #         continue
    return_dict = {'code': 200, 'msg': '请求成功', 'data': query}
    return jsonify(return_dict)


@config.route('/update_config', methods=["POST"])
@swag_from('../apidocs/update_config.yml')
def update_config():
    """更新配置信息"""
    # print(request.json)
    id = request.json.get("id")
    cfg = request.json.get("cfg")
    cfg_name = request.json.get("cfg_name")
    project_id = request.json.get("project_id")
    query = Cfgs.query.filter_by(id=id).first()
    if not query:
        return jsonify({'code': 404, 'msg': '配置不存在', 'data': None})
    permission_error = None if is_admin() else jsonify({'code': 403, 'msg': '只有管理员可以修改全局配置', 'data': None})
    if permission_error:
        return permission_error
    permission_error = None
    if permission_error:
        return permission_error
    if False:
        return jsonify({'code': 403, 'msg': '只有管理员可以修改全局配置', 'data': None})
    query.cfg = cfg
    query.cfg_name = cfg_name

    db.session.commit()

    return_dict = {'code': 200, 'msg': '请求成功', 'data': id}
    return jsonify(return_dict)


@config.route('/add_config', methods=["POST"])
@swag_from('../apidocs/add_config.yml')
def add_config():
    """新增或修改配置信息"""
    id = request.json.get("id")
    cfg = request.json.get("cfg", "")
    mark = request.json.get("mark", "")
    cfg_name = request.json.get("cfg_name", "")
    cfg_name = cfg_name.strip()
    if not is_admin():
        return jsonify({'code': 403, 'msg': '只有管理员可以维护全局配置', 'data': None})
    # cfg = cfg.strip()
    # project_id = request.json.get("project_id")
    # extra_data = request.json.get("extra_data")
    try:
        if not isinstance(cfg, dict):
            return jsonify({'code': 404, 'msg': '配置信息格式错误,请传入dict类型', 'data': id})
        cfg_keys = list(cfg.keys())
        cfg_values = list(cfg.values())
        if not cfg or not cfg_keys or not cfg_values:
            return jsonify({'code': 404, 'msg': '缺少必填参数', 'data': ""})
        if cfg_keys:
            if not cfg_keys[0]:
                return jsonify({'code': 404, 'msg': '缺少必填参数', 'data': ""})
        if cfg_values:
            if not cfg_values[0]:
                return jsonify({'code': 404, 'msg': '缺少必填参数', 'data': ""})
        cfg = json.dumps(cfg)
        if not cfg or not cfg_name:
            return jsonify({'code': 404, 'msg': '缺少必填参数', 'data': ""})
        # if project_id:
        #     if isinstance(project_id, list):
        #         project_id = project_id[0]
        if id:
            query = Cfgs.query.filter_by(id=id).first()
            query.cfg = cfg
            query.cfg_name = cfg_name
            # query.project_id = int(project_id)
            query.mark = mark
        else:
            new_cfg = Cfgs(cfg_name=cfg_name, cfg=cfg, mark=mark)
            db.session.add(new_cfg)
            db.session.flush()
            id = new_cfg.id
        db.session.commit()
        return_dict = {'code': 200, 'msg': '请求成功', 'data': id}
    except Exception as e:
        print(e)
        return jsonify({'code': 404, 'msg': '内部错误', 'data': id})
    return jsonify(return_dict)


@config.route('/union_testset', methods=["POST"])
@swag_from('../apidocs/union_testset.yml')
def union_testset():
    """配置关联的测试集"""
    config_id = request.json.get("config_id")
    if not config_id:
        return jsonify({'code': 404, 'msg': '缺少必填参数', 'data': ""})
    # query = TestSet.query.all()
    query = TestSet.query.filter_by(is_delete=0).all()
    query = [item for item in query if require_project_permission(item.project_id, "view") is None]
    query_list = list()
    for i in query:
        if i.config:
            config_list = eval(i.config)
            if config_id in config_list:
                query_list.append(i)
    query = [i.to_dict() for i in query_list]
    return_dict = {'code': 200, 'msg': '请求成功', 'data': query}
    return jsonify(return_dict)


@config.route('/deletes_config', methods=["POST"])
@swag_from('../apidocs/deletes_config.yml')
def delete_testset():
    """删除配置项"""
    ids = request.json.get("ids")
    if not ids:
        return jsonify({'code': 404, 'msg': '请传入需要删除的配置项id', 'data': []})
    set_query = TestSet.query.filter_by(is_delete=0).all()
    # set_query = TestSet.query.all()
    delete_set_title = list()
    for cfg_id in ids:
        query = Cfgs.query.filter_by(id=cfg_id).filter_by(is_delete=0).first()
        if not query:
            continue
        if not is_admin():
            return jsonify({'code': 403, 'msg': '只有管理员可以删除全局配置', 'data': None})
        check_list = list()
        for i in set_query:
            if i.config:
                config_list = eval(i.config)
                if cfg_id in config_list:
                    check_list.append(cfg_id)
                    continue
        if not check_list:
            query.is_delete = 1
            delete_set_title.append(query.cfg_name)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '配置项已删除', 'data': delete_set_title})
