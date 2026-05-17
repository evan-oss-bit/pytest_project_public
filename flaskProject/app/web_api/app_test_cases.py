# !/usr/bin/python3.8
# -*- coding: utf-8 -*-


from flask import jsonify, request
from app.commom.add_test_case import *
from app.web_api import cases
from app.models.test_api_models import *
from flasgger import swag_from
# import prismjs
from flask import render_template_string
from config import home_path
from werkzeug.utils import secure_filename
from app.lib.image import get_values_by_key
from sqlalchemy import or_
from app.tools.auth_permissions import allowed_project_ids, require_project_permission, project_id_from_case


def _get_case_source_path(case):
    source_path = os.path.abspath(os.path.join(home_path, case.relative_path))
    home_dir = os.path.abspath(home_path)
    if not source_path.startswith(home_dir + os.sep):
        return None, "脚本路径不在项目目录内"
    if not source_path.endswith(".py"):
        return None, "只能查看或修改 Python 脚本"
    return source_path, None


def _save_scanned_cases(scanned_cases, project_id, project_name, description, module_id, version_id, script_type):
    unique_cases = {}
    for item in scanned_cases:
        unique_cases[item.get("case")] = item
    scanned_cases = list(unique_cases.values())
    case_paths = [item.get("case") for item in scanned_cases if item.get("case")]
    relative_case_paths = [item.get("relative_case_path") for item in scanned_cases if item.get("relative_case_path")]
    existing_cases = Cases.query.filter(
        or_(Cases.case_path.in_(case_paths), Cases.relative_case_path.in_(relative_case_paths))
    ).all()
    existing_by_case_path = {item.case_path: item for item in existing_cases if item.case_path}
    existing_by_relative_path = {item.relative_case_path: item for item in existing_cases if item.relative_case_path}

    ids = []
    created_count = 0
    updated_count = 0
    for case_path in scanned_cases:
        case = existing_by_relative_path.get(case_path.get("relative_case_path"))
        if not case:
            case = existing_by_case_path.get(case_path.get("case"))
        if case and case.is_delete:
            case.is_delete = 0
        if case:
            updated_count += 1
            case.case_name = case_path.get("docs")
            case.title = case_path.get("title")
            case.type = script_type
            if description:
                case.remark = description
            case.project_id = project_id
            case.project_name = project_name
            case.module_id = module_id
            case.version_id = version_id
            case.relative_case_path = case_path.get("relative_case_path")
            case.case_path = case_path.get("case")
            case.relative_path = case_path.get("relative_path")
            case.previous_level = case_path.get("previous_level")
            case.class_name = case_path.get("class_name")
            case.relative_cla_case_path = case_path.get("relative_cla_case_path")
        else:
            created_count += 1
            case = Cases(project_id=project_id, module_id=module_id, version_id=version_id, project_name=project_name,
                         type=script_type, remark=description, relative_case_path=case_path.get("relative_case_path"),
                         case_path=case_path.get("case"), title=case_path.get("title"), case_name=case_path.get("docs"),
                         relative_path=case_path.get("relative_path"), previous_level=case_path.get("previous_level"),
                         class_name=case_path.get("class_name"),
                         relative_cla_case_path=case_path.get("relative_cla_case_path"))
            db.session.add(case)
            existing_by_case_path[case.case_path] = case
            existing_by_relative_path[case.relative_case_path] = case
        ids.append(case.id)
    db.session.flush()
    ids = [case.id for case in existing_by_case_path.values() if case.case_path in case_paths]
    return ids, created_count, updated_count


@cases.route('/get_cases_info', methods=["POST"])
@swag_from('../apidocs/get_cases_info.yml')
def get_cases_info():
    """获取测试脚本信息列表"""
    page_no = request.json.get("page_no", 0)
    page_size = request.json.get("page_size", 10)
    case_name = request.json.get("case_name", "")
    case_name = case_name.strip()
    project_id = request.json.get("project_id")
    script_type = request.json.get("script_type")
    cases_in = request.json.get("cases_in")
    run_id = request.json.get("run_id")
    previous_level = request.json.get("previous_level")
    count = dict()
    previous_levels = None
    allowed_ids = allowed_project_ids()
    if project_id:
        permission_error = require_project_permission(project_id, "view")
        if permission_error:
            return permission_error
    if case_name:
        query = Cases.query.filter(Cases.case_name.like(f"%{case_name}%")).filter_by(is_delete=0).all()
        if not query:
            query = Cases.query.filter(Cases.title.like(f"%{case_name}%")).filter_by(is_delete=0).all()
    elif project_id:
        query = Cases.query.filter_by(project_id=project_id).filter_by(is_delete=0).order_by(
            db.desc(Cases.updated_time)).limit(
            page_size).offset(
            page_no).all()
        query_info = [i.to_dict() for i in query]
        previous_levels = get_values_by_key(query_info, "previous_level", [])
        # print(previous_levels)
        if previous_levels:
            if not isinstance(previous_levels, list):
                previous_levels = [previous_levels]
            previous_levels = list(set(previous_levels))
            previous_levels = [{"value": i, "label": i} for i in previous_levels]
        if previous_level:
            previous_level = previous_level[-1]
            query = Cases.query.filter_by(project_id=project_id).filter_by(is_delete=0).filter_by(
                previous_level=previous_level).order_by(
                db.desc(Cases.updated_time)).limit(
                page_size).offset(
                page_no).all()
            if script_type:
                query = Cases.query.filter_by(project_id=project_id).filter_by(is_delete=0).filter_by(
                    previous_level=previous_level).filter_by(
                    type=script_type).order_by(
                    db.desc(Cases.updated_time)).limit(
                    page_size).offset(
                    page_no).all()
        elif script_type:
            query = Cases.query.filter_by(project_id=project_id).filter_by(is_delete=0).filter_by(
                type=script_type).order_by(
                db.desc(Cases.updated_time)).limit(
                page_size).offset(
                page_no).all()
    elif script_type:
        query = Cases.query.filter_by(type=script_type).filter_by(is_delete=0).order_by(
            db.desc(Cases.updated_time)).limit(page_size).offset(
            page_no).all()
    elif cases_in:
        if cases_in == "no_case":
            query = list()
        else:
            cases_in = eval(cases_in)
            query = Cases.query.filter_by(is_delete=0).filter(Cases.id.in_(cases_in)).order_by(
                db.desc(Cases.updated_time)).limit(
                page_size).offset(page_no).all()
        querys = [i.to_dict() for i in query]
        pass_count = fail_count = error_count = un_executed = executed_ing = 0
        try:
            for each in querys:
                if each["run_status"] == "passed":
                    pass_count += 1
                if each["run_status"] == "failed":
                    fail_count += 1
                if each["run_status"] == "error":
                    error_count += 1
                if each["run_status"] == "未测试":
                    un_executed += 1
                if each["run_status"] == "测试中":
                    executed_ing += 1
            count.update({'pass_count': pass_count, 'fail_count': fail_count, 'error_count': error_count,
                          'un_executed': un_executed, 'executed_ing': executed_ing, 'all_count': len(query),
                          'pass_rate': round(pass_count / len(query) * 100, 2),
                          'schedule': round((pass_count + fail_count + error_count) / len(query) * 100, 2)})
        except:
            pass
        # if run_id:
        #     query = CaseResult.query.filter_by(run_id=int(run_id)).order_by(
        #         db.desc(CaseResult.run_id)).order_by(db.desc(CaseResult.updated_time)).limit(page_size).offset(
        #         page_no).all()
    else:
        query = Cases.query.filter_by(is_delete=0).order_by(db.desc(Cases.updated_time)).limit(page_size).offset(
            page_no).all()
    if query:
        if allowed_ids is not None:
            query = [item for item in query if item.project_id in allowed_ids]
        query = [i.to_dict() for i in query]
    for i in query:
        if i.get("created_time") and i.get("updated_time"):
            i.update({"created_time": i.get("created_time").strftime("%Y-%m-%d %H:%M:%S")})
            i.update({"updated_time": i.get("updated_time").strftime("%Y-%m-%d %H:%M:%S")})

    return_dict = {'code': 200, 'msg': '请求成功', 'data': query, 'count': count, "previous_levels": previous_levels}
    return jsonify(return_dict)


@cases.route('/update_cases', methods=["POST"])
@swag_from('../apidocs/update_cases.yml')
def update_cases():
    """更新测试脚本"""
    id = request.json.get("id")
    project_id = request.json.get("project_id")
    permission_error = require_project_permission(project_id, "edit")
    if permission_error:
        return permission_error
    pro_info = Project.query.filter_by(id=project_id).first()
    if not pro_info:
        return jsonify({'code': 404, 'msg': f'该项目不存在', 'data': []})
    data = add_cases(project=pro_info.name)
    query = Cases.query.filter_by(is_delete=0).filter_by(id=id).first()
    # query.cfg = cfg
    # query.cfg_name = cfg_name
    query.project_id = project_id
    db.session.commit()

    return_dict = {'code': 200, 'msg': '请求成功', 'data': id}
    return jsonify(return_dict)


@cases.route('/add_case', methods=["POST"])
@swag_from('../apidocs/add_case.yml')
def add_case():
    """新增测试脚本"""
    project_id = request.json.get("project_id")
    description = request.json.get("description")
    module_id = request.json.get("module_id")
    version_id = request.json.get("version_id")
    script_type = request.json.get("script_type")
    permission_error = require_project_permission(project_id, "edit")
    if permission_error:
        return permission_error

    pro_info = Project.query.filter_by(id=project_id).first()
    if not pro_info:
        return jsonify({'code': 404, 'msg': f'该项目不存在', 'data': []})
    data = add_cases(project=pro_info.name)
    if not data.get("cases"):
        return jsonify({'code': 404, 'msg': f'{pro_info.name}项目下没有pytest脚本', 'data': data.get("cases")})
    ids, created_count, updated_count = _save_scanned_cases(
        data.get("cases"), project_id, pro_info.name, description, module_id, version_id, script_type
    )
    db.session.commit()

    data.update({"ids": ids, "created_count": created_count, "updated_count": updated_count})
    return_dict = {'code': 200, 'msg': f'同步完成：新增{created_count}条，更新{updated_count}条', 'data': data}
    return jsonify(return_dict)


@cases.route('/case_review', methods=["POST"])
def case_review():
    """py文件脚本代码审查"""
    case_id = request.json.get("id")
    permission_error = require_project_permission(project_id_from_case(case_id), "edit")
    if permission_error:
        return permission_error
    case = Cases.query.filter_by(id=case_id).first()
    if not case:
        return jsonify({'code': 404, 'msg': '用例不存在', 'data': None})
    relative_path, error_msg = _get_case_source_path(case)
    if error_msg:
        return jsonify({'code': 400, 'msg': error_msg, 'data': None})
    with open(relative_path, "r", encoding="utf8") as f:
        code = f.read()
        return render_template_string("""
                    <!DOCTYPE html>
                    <html lang="zh-CN">
                        <head>
                          <meta charset="UTF-8">
                          <meta name="viewport" content="width=device-width, initial-scale=1.0">
                          <title>{{ title }}</title>
                          <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css">
                          <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.css">
                          <style>
                            body {
                              margin: 0;
                              background: #eef2f7;
                              color: #24292f;
                              font-family: Arial, "Microsoft YaHei", sans-serif;
                            }
                            .source-header {
                              position: sticky;
                              top: 0;
                              z-index: 1;
                              padding: 12px 18px;
                              background: #0f172a;
                              border-bottom: 1px solid #1e293b;
                              color: #e2e8f0;
                              text-align: left;
                              font-size: 14px;
                              font-weight: 700;
                            }
                            pre[class*="language-"] {
                              margin: 16px;
                              border: 1px solid #cbd5e1;
                              border-radius: 6px;
                              font-size: 14px;
                              line-height: 1.6;
                              text-align: left;
                              white-space: pre;
                              background: #ffffff;
                              box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
                            }
                            code[class*="language-"] {
                              font-family: Consolas, "Courier New", monospace;
                              color: #24292f;
                              text-shadow: none;
                            }
                            .line-numbers .line-numbers-rows {
                              border-right-color: #d0d7de;
                            }
                            .line-numbers-rows > span:before {
                              color: #8c959f;
                            }
                            .token.comment,
                            .token.prolog,
                            .token.doctype,
                            .token.cdata {
                              color: #6a737d;
                              font-style: italic;
                            }
                            .token.keyword,
                            .token.operator,
                            .token.boolean {
                              color: #d73a49;
                              font-weight: 700;
                            }
                            .token.string,
                            .token.char,
                            .token.attr-value {
                              color: #032f62;
                            }
                            .token.function,
                            .token.class-name {
                              color: #6f42c1;
                              font-weight: 700;
                            }
                            .token.number,
                            .token.constant,
                            .token.builtin {
                              color: #005cc5;
                            }
                            .token.decorator,
                            .token.annotation {
                              color: #22863a;
                              font-weight: 700;
                            }
                            .token.punctuation {
                              color: #586069;
                            }
                          </style>
                        </head>
                        <body>
                            <div class="source-header">{{ title }}</div>
                            <pre class="line-numbers"><code class="language-python">{{ code }}</code></pre>
                            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
                            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
                            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.js"></script>
                            <script>Prism.highlightAll();</script>
                        </body>
                    </html>
                    """, code=code, title=case.title or case.relative_path)


@cases.route('/update_case_source', methods=["POST"])
def update_case_source():
    """在线修改 pytest 脚本源码"""
    data = request.get_json(silent=True) or {}
    case_id = data.get("id")
    source_code = data.get("source_code")
    if source_code is None:
        source_code = data.get("code")
    if source_code is None:
        source_code = data.get("content")
    if not case_id:
        return jsonify({'code': 400, 'msg': '缺少用例 id', 'data': None})
    if source_code is None:
        return jsonify({'code': 400, 'msg': '缺少源码内容 source_code', 'data': None})

    case = Cases.query.filter_by(id=case_id).first()
    if not case:
        return jsonify({'code': 404, 'msg': '用例不存在', 'data': None})

    source_path, error_msg = _get_case_source_path(case)
    if error_msg:
        return jsonify({'code': 400, 'msg': error_msg, 'data': None})
    if not os.path.exists(source_path):
        return jsonify({'code': 404, 'msg': '脚本文件不存在', 'data': None})

    temp_path = f"{source_path}.{os.getpid()}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8", newline="") as f:
            f.write(source_code)
        os.replace(temp_path, source_path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'code': 500, 'msg': f'源码保存失败: {e}', 'data': None})

    return jsonify({
        'code': 200,
        'msg': '源码保存成功',
        'data': {
            'id': case.id,
            'relative_path': case.relative_path,
            'path': source_path
        }
    })


@cases.route('/case_upload', methods=["POST"])
def case_upload():
    """pytest脚本上传到测试项目"""
    file = request.files["file"]
    project_id = request.form.get("project_id")
    if not "." in file.filename or not file.filename.split(".")[-1] in ["py"] or not file.filename.startswith("test_"):
        return {'code': 404, 'msg': '请上传test_开头的py文件类型', 'data': None}
    pro_info = Project.query.filter_by(id=int(project_id)).first()
    if not pro_info:
        return jsonify({'code': 404, 'msg': '该项目不存在', 'data': []})
    project_path = os.path.join(config.testscriptproject, pro_info.name, "test_pub_cases")
    if not os.path.exists(project_path):
        try:
            os.makedirs(project_path)
        except:
            return jsonify({'code': 404, 'msg': f'该{pro_info.name}项目中test_pub_cases不存在', 'data': []})
    filename = secure_filename(file.filename)
    file.save(os.path.join(project_path, filename))
    return jsonify({'code': 200, 'msg': '上传成功', 'data': []})


@cases.route('/case_mark', methods=['POST'])
def case_mark():
    case_id = request.json.get("id")
    remark = request.json.get("remark")
    case = Cases.query.filter_by(is_delete=0).filter_by(id=case_id).first()
    if not case:
        return jsonify({"code": 404, "msg": "用例不存在.", 'data': None})
    case.remark = remark
    db.session.merge(case)
    db.session.commit()
    return jsonify({"code": 200, "msg": "用例备注成功", 'data': None})


@cases.route('/delete_case', methods=["POST"])
def delete_case():
    """删除用例"""
    ids = request.json.get("ids")
    if not ids:
        return jsonify({'code': 404, 'msg': '请传入需要删除的测试集id', 'data': []})
    if isinstance(ids, int):
        ids = [ids]
    delete_case_names = list()
    for case_id in ids:
        query = Cases.query.filter_by(id=case_id).filter_by(is_delete=0).first()
        if not query:
            continue
        permission_error = require_project_permission(query.project_id, "edit")
        if permission_error:
            return permission_error
        if query.run_status in [1]:
            continue
        query.is_delete = 1
        delete_case_names.append(query.case_name)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '测试用例已删除', 'data': delete_case_names})
