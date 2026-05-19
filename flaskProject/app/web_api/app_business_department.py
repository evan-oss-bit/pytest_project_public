#!/usr/bin/python3.8
# -*- coding: utf-8 -*-

from flask import jsonify, request
from flasgger import swag_from

from app.lib.lib_define import db
from app.models.test_api_models import BusinessDepartment, Project
from app.tools.business_department_service import (
    clean_project_value,
    department_payload,
    department_project_query,
    ensure_business_department_schema,
)
from app.tools.auth_permissions import is_admin
from app.web_api import business_department


@business_department.route('/get_business_department_info', methods=["POST"])
@swag_from('../apidocs/get_business_department_info.yml')
def get_business_department_info():
    """获取业务部门列表"""
    ensure_business_department_schema()
    data = request.get_json(silent=True) or {}
    name = clean_project_value(data.get("name"))
    query = BusinessDepartment.query.filter_by(is_delete=0)
    if name:
        query = query.filter(BusinessDepartment.name.like(f"%{name}%"))
    departments = query.order_by(db.desc(BusinessDepartment.updated_time)).all()
    return jsonify({
        'code': 200,
        'msg': '请求成功',
        'data': [department_payload(item) for item in departments],
        'total': len(departments),
    })


@business_department.route('/save_business_department', methods=["POST"])
@swag_from('../apidocs/save_business_department.yml')
def save_business_department():
    """新增或编辑业务部门"""
    ensure_business_department_schema()
    if not is_admin():
        return jsonify({'code': 403, 'msg': '只有管理员可以维护业务部门', 'data': None})
    data = request.get_json(silent=True) or {}
    dept_id = data.get("id")
    name = clean_project_value(data.get("name"))
    owner = clean_project_value(data.get("owner"))
    description = clean_project_value(data.get("description"))
    if not name:
        return jsonify({'code': 404, 'msg': '业务部门名称不能为空', 'data': None})
    duplicate_query = BusinessDepartment.query.filter_by(name=name, is_delete=0)
    if dept_id:
        duplicate_query = duplicate_query.filter(BusinessDepartment.id != dept_id)
    if duplicate_query.first():
        return jsonify({'code': 404, 'msg': '业务部门名称已存在', 'data': None})
    if dept_id:
        dept = BusinessDepartment.query.filter_by(id=dept_id, is_delete=0).first()
        if not dept:
            return jsonify({'code': 404, 'msg': '业务部门不存在', 'data': None})
    else:
        dept = BusinessDepartment()
        db.session.add(dept)
    old_name = dept.name
    dept.name = name
    dept.owner = owner
    dept.description = description
    db.session.flush()
    project_query = Project.query.filter(Project.business_department_id == dept.id)
    if old_name:
        project_query = project_query.union(Project.query.filter(Project.business_department == old_name))
    for project_item in project_query.all():
        project_item.business_department_id = dept.id
        project_item.business_department = dept.name
    db.session.commit()
    return jsonify({'code': 200, 'msg': '请求成功', 'data': department_payload(dept)})


@business_department.route('/delete_business_department', methods=["POST"])
@swag_from('../apidocs/delete_business_department.yml')
def delete_business_department():
    """删除业务部门"""
    ensure_business_department_schema()
    if not is_admin():
        return jsonify({'code': 403, 'msg': '只有管理员可以删除业务部门', 'data': None})
    dept_id = request.json.get("id")
    dept = BusinessDepartment.query.filter_by(id=dept_id, is_delete=0).first()
    if not dept:
        return jsonify({'code': 404, 'msg': '业务部门不存在', 'data': None})
    if department_project_query(dept).count() > 0:
        return jsonify({'code': 404, 'msg': '该业务部门下还有脚本项目，不能删除', 'data': None})
    dept.is_delete = 1
    db.session.commit()
    return jsonify({'code': 200, 'msg': '请求成功', 'data': dept_id})


@business_department.route('/get_business_department_dashboard', methods=["POST"])
@swag_from('../apidocs/get_business_department_dashboard.yml')
def get_business_department_dashboard():
    """获取业务部门总览"""
    ensure_business_department_schema()
    dept_id = request.json.get("id")
    dept = BusinessDepartment.query.filter_by(id=dept_id, is_delete=0).first()
    if not dept:
        return jsonify({'code': 404, 'msg': '业务部门不存在', 'data': None})
    return jsonify({'code': 200, 'msg': '请求成功', 'data': department_payload(dept, include_projects=True)})
