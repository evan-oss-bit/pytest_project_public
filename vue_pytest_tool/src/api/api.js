import axios from "axios";
let base = "http://127.0.0.1:5400";

export const get_url = () => {
  return base
}


export const requestLogin = (params) => {
  return axios({
    method: "POST",
    url: `${base}/login`,
    data: params,
  }).then((res) => res.data);
};

export const get_captcha = () => {
  return axios.get(`${base}/captcha`);
};

//账号权限-当前账号
export const get_auth_me = (params) => {
  return axios.post(`${base}/auth/me`, params);
};
//账号权限-修改当前账号密码
export const setpwd = (params) => {
  return axios.post(`${base}/auth/change_password`, params);
};
//账号权限-账号列表
export const get_account_info = (params) => {
  return axios.post(`${base}/auth/get_account_info`, params);
};
//账号权限-保存账号
export const save_account = (params) => {
  return axios.post(`${base}/auth/save_account`, params);
};
//账号权限-删除账号
export const delete_account = (params) => {
  return axios.post(`${base}/auth/delete_account`, params);
};
//账号权限-管理员重置账号密码
export const reset_account_password = (params) => {
  return axios.post(`${base}/auth/reset_account_password`, params);
};
//账号权限-操作日志
export const get_operation_log = (params) => {
  return axios.post(`${base}/auth/get_operation_log`, params);
};

//pytest自动化项目-获取项目信息
export const get_project_info = (params) => {
  return axios.post(`${base}/project/get_project_info`, params);
};
//pytest自动化项目-获取项目总览
export const get_project_dashboard = (params) => {
  return axios.post(`${base}/project/get_project_dashboard`, params);
};
//首页看板-顶部统计
export const get_home_stats = (params) => {
  return axios.post(`${base}/project/get_home_stats`, params);
};
//进程池占用情况
export const get_process_pool_status = (params) => {
  return axios.post(`${base}/project/get_process_pool_status`, params);
};
//接口测试-环境列表
export const get_api_environment_info = (params) => {
  return axios.post(`${base}/api_test/get_environment_info`, params);
};
//接口测试-保存环境
export const save_api_environment = (params) => {
  return axios.post(`${base}/api_test/save_environment`, params);
};
//接口测试-删除环境
export const delete_api_environment = (params) => {
  return axios.post(`${base}/api_test/delete_environment`, params);
};
//接口测试-用例列表
export const get_api_case_info = (params) => {
  return axios.post(`${base}/api_test/get_case_info`, params);
};
//接口测试-保存用例
export const save_api_case = (params) => {
  return axios.post(`${base}/api_test/save_case`, params);
};
//接口测试-删除用例
export const delete_api_case = (params) => {
  return axios.post(`${base}/api_test/delete_case`, params);
};
//接口测试-运行用例
export const run_api_case = (params) => {
  return axios.post(`${base}/api_test/run_case`, params);
};
//接口测试-运行历史
export const get_api_run_history = (params) => {
  return axios.post(`${base}/api_test/get_run_history`, params);
};
//业务部门-获取业务部门列表
export const get_business_department_info = (params) => {
  return axios.post(`${base}/business_department/get_business_department_info`, params);
};
//业务部门-保存业务部门
export const save_business_department = (params) => {
  return axios.post(`${base}/business_department/save_business_department`, params);
};
//业务部门-删除业务部门
export const delete_business_department = (params) => {
  return axios.post(`${base}/business_department/delete_business_department`, params);
};
//业务部门-业务部门总览
export const get_business_department_dashboard = (params) => {
  return axios.post(`${base}/business_department/get_business_department_dashboard`, params);
};
//pytest自动化项目-检测脚本变更
export const check_script_changes = (params) => {
  return axios.post(`${base}/project/check_script_changes`, params);
};
//pytest自动化项目-获取项目文件树
export const get_project_tree = (params) => {
  return axios.post(`${base}/project/get_project_tree`, params);
};
//pytest自动化项目-预览项目文件
export const preview_project_file = (params) => {
  return axios.post(`${base}/project/preview_project_file`, params);
};
//pytest自动化项目-同步项目脚本
export const sync_project_scripts = (params) => {
  return axios.post(`${base}/project/sync_project_scripts`, params);
};
//pytest自动化项目-Git拉取最新脚本
export const pull_project_git = (params) => {
  return axios.post(`${base}/project/pull_project_git`, params);
};
//pytest自动化项目-获取Git远端分支
export const get_project_git_branches = (params) => {
  return axios.post(`${base}/project/get_project_git_branches`, params);
};
//pytest自动化项目-获取项目列表
export const get_project_list = (params) => {
  return axios.get(`${base}/project/get_project_list`, params);
};
//pytest自动化项目-更新项目
export const update_project = (params) => {
  return axios.post(`${base}/project/update_project`, params);
};

//pytest自动化项目-新增项目
export const add_project = (params) => {
  return axios.post(`${base}/project/add_project`, params);
};
//pytest自动化项目-查看项目配置
export const check_project_ini = (params) => {
  return axios.post(`${base}/project/check_ini`, params);
};
//pytest自动化项目-清空项目配置
export const clear_ini = (params) => {
  return axios.post(`${base}/project/clear_ini`, params);
};





//pytest自动化项目-获取版本信息
export const get_version_info = (params) => {
  return axios.post(`${base}/version/get_version_info`, params);
};

//pytest自动化项目-更新版本
export const update_version = (params) => {
  return axios.post(`${base}/version/update_version`, params);
};

//pytest自动化项目-新增版本
export const add_version = (params) => {
  return axios.post(`${base}/version/add_version`, params);
};




//pytest自动化项目-获取测试集合信息
export const get_testset_info = (params) => {
  return axios.post(`${base}/testset/get_testset_info`, params);
};

//pytest自动化项目-更新测试集合信息
export const update_testset = (params) => {
  return axios.post(`${base}/testset/update_testset`, params);
};

//pytest自动化项目-新增测试集合
export const add_testset = (params) => {
  return axios.post(`${base}/testset/add_testset`, params);
};
//pytest自动化项目-新增测试任务
export const add_tesetask = (params) => {
  return axios.post(`${base}/test_task/add_testtask`, params);
};

//pytest自动化项目-运行测试集合
export const run_testset = (params) => {
  return axios.post(`${base}/testset/run_testset`, params);
};

//pytest自动化项目-终止运行测试集合
export const stop_testset = (params) => {
  return axios.post(`${base}/testset/stop_testset`, params);
};
//pytest自动化项目-删除测试集合
export const delete_testset = (params) => {
  return axios.post(`${base}/testset/delete_testset`, params);
};
//pytest自动化项目-删除测试任务
export const delete_testtask = (params) => {
  return axios.post(`${base}/test_task/delete_testtask`, params);
};
//测试任务列表
export const get_testtask_info = (params) => {
  return axios.post(`${base}/test_task/get_task_info`, params);
};
//pytest自动化项目-运行测试任务
export const run_testtask = (params) => {
  return axios.post(`${base}/test_task/run_testtask`, params);
};

//pytest自动化项目-测试集关联的测试任务
export const union_task = (params) => {
  return axios.post(`${base}/testset/union_testask`, params);
};


//pytest自动化项目-获取测试任务测试集信息
export const get_testtask_set = (params) => {
  return axios.post(`${base}/test_task/get_testtask_set`, params);
};
//pytest自动化项目-获取测试任务执行时间线
export const get_testtask_timeline = (params) => {
  return axios.post(`${base}/test_task/get_testtask_timeline`, params);
};
//pytest自动化项目-获取测试任务运行历史
export const get_testtask_history = (params) => {
  return axios.post(`${base}/test_task/get_testtask_history`, params);
};
//pytest自动化项目-获取测试任务配置快照
export const get_testtask_config_snapshot = (params) => {
  return axios.post(`${base}/test_task/get_testtask_config_snapshot`, params);
};
//pytest自动化项目-终止运行测试任务
export const stop_testtask = (params) => {
  return axios.post(`${base}/test_task/stop_testtask`, params);
};
//pytest自动化项目-获取测试报告列表
export const get_report_info = (params) => {
  return axios.post(`${base}/report/get_report_info`, params);
};
//pytest自动化项目-获取测试报告失败分析
export const get_report_failure_analysis = (params) => {
  return axios.post(`${base}/report/get_report_failure_analysis`, params);
};
// 报告备注
export const report_mark = (params) => {
  return axios.post(`${base}/report/report_mark`, params);
};
// 发送邮件
export const send_email_a = (params) => {
  return axios.post(`${base}/report/send_email`, params);
};
//pytest自动化项目-获取case执行结果信息
export const get_files = (params) => {
  return axios.get(`${base}/testset/files`, params);
};

//pytest自动化项目-获取case执行logs信息
export const get_logs = (file_name) => {
  return axios.get(`${base}/testset/files/` + file_name);
};



//pytest自动化项目-获取模块信息
export const get_module_info = (params) => {
  return axios.post(`${base}/module/get_module_info`, params);
};

//pytest自动化项目-更新模块信息
export const update_module = (params) => {
  return axios.post(`${base}/module/update_module`, params);
};

//pytest自动化项目-新增模块信息
export const add_module = (params) => {
  return axios.post(`${base}/module/add_module`, params);
};




//pytest自动化项目-获取配置信息
export const get_config_info = (params) => {
  return axios.post(`${base}/config/get_config_info`, params);
};

//pytest自动化项目-更新配置信息
export const update_config = (params) => {
  return axios.post(`${base}/config/update_config`, params);
};

//pytest自动化项目-新增配置信息
export const add_config = (params) => {
  return axios.post(`${base}/config/add_config`, params);
};
//pytest自动化项目-新增配置信息
export const union_set = (params) => {
  return axios.post(`${base}/config/union_testset`, params);
};
//pytest自动化项目-删除配置
export const deletes_config = (params) => {
  return axios.post(`${base}/config/deletes_config`, params);
};




//pytest自动化项目-获取case信息
export const get_cases_info = (params) => {
  return axios.post(`${base}/cases/get_cases_info`, params);
};

//pytest自动化项目-更新case信息
export const update_cases = (params) => {
  return axios.post(`${base}/cases/update_cases`, params);
};

//pytest自动化项目-新增case信息
export const add_case = (params) => {
  return axios.post(`${base}/cases/add_case`, params);
};

//pytest自动化项目-删除case信息
export const delete_cases = (params) => {
  return axios.post(`${base}/cases/delete_case`, params);
};

//pytest自动化项目-py文件脚本代码审查
export const case_review = (params) => {
  return axios.post(`${base}/cases/case_review`, params);
};

//pytest自动化项目-在线修改py文件脚本源码
export const update_case_source = (params) => {
  return axios.post(`${base}/cases/update_case_source`, params);
};

//pytest自动化项目-pytest脚本备注
export const case_mark = (params) => {
  return axios.post(`${base}/cases/case_mark`, params);
};

//pytest自动化项目-获取case执行结果信息
export const get_caseresult_info = (params) => {
  return axios.post(`${base}/caseresult/get_caseresult_info`, params);
};

//pytest自动化项目-py文件脚本代码审查
export const get_log_info = (params) => {
  return axios.post(`${base}/caseresult/get_log_info`, params);
};

export const case_upload = (params) => {
  let config = {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  };
  return axios.post(`${base}/cases/case_upload`, params, config);
};


























