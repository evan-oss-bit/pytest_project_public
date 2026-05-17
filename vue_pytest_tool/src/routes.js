import Login from './views/Login.vue'
import NotFound from './views/404.vue'
import Home from './views/Home.vue'



import CONFIG from './views/pytestvue/config.vue'
import PROJECT from './views/pytestvue/project.vue'
import DEPARTMENT from './views/pytestvue/department.vue'
import VERSION from './views/pytestvue/version.vue'
import MODULE from './views/pytestvue/module.vue'
import CASE_NEW from './views/pytestvue/cases_new.vue'
import TESTSET from './views/pytestvue/testset.vue'
import RESULT from './views/pytestvue/result.vue'
import REPORT from './views/pytestvue/report.vue'
import TESTTASK from './views/pytestvue/testtask.vue'
import ACCOUNT from './views/pytestvue/account.vue'

let routes = [
    {
        path: '/login',
        component: Login,
        name: '',
        hidden: true
    },
    {
        path: '/404',
        component: NotFound,
        name: '',
        hidden: true
    },

    {
        path: '/',
        component: Home,
        name: '业务部门管理',
        leaf: true,
        iconCls: 'fa fa-sitemap',
        children: [
            { path: '/business_department', component: DEPARTMENT, name: '业务部门管理' }
        ]
    },
    {
        path: '/',
        component: Home,
        name: '脚本项目列表',
        leaf: true,//只有一个节点
        iconCls: 'fa fa-link',//图标样式class
        children: [
            { path: '/pytest_project', component: PROJECT, name: '脚本项目列表' }
        ]
    },

    {
        path: '/',
        component: Home,
        name: '项目版本列表',
        leaf: true,//只有一个节点
        iconCls: 'fa fa-link',//图标样式class
        children: [
            { path: '/pytest_version', component: VERSION, name: '项目版本列表' }
        ]
    },
    {
        path: '/',
        component: Home,
        name: '项目模块列表',
        leaf: true,//只有一个节点
        iconCls: 'fa fa-link',//图标样式class
        children: [
            { path: '/pytest_module', component: MODULE, name: '项目模块列表' }
        ]
    },

    {
        path: '/',
        component: Home,
        name: '配置列表',
        leaf: true,//只有一个节点
        iconCls: 'fa fa-link',//图标样式class
        children: [
            { path: '/pytest_config', component: CONFIG, name: '配置列表' }
        ]
    },
    {
        path: '/',
        component: Home,
        name: '用例列表',
        leaf: true,//只有一个节点
        iconCls: 'fa fa-link',//图标样式class
        children: [
            { path: '/pytest_cases', component: CASE_NEW, name: '用例列表' }
        ]
    },
    {
        path: '/',
        component: Home,
        name: '测试集合列表',
        leaf: true,//只有一个节点
        iconCls: 'fa fa-link',//图标样式class
        children: [
            { path: '/pytest_testset', component: TESTSET, name: '测试集合列表' }
        ]
    },
    {
        path: '/',
        component: Home,
        name: '测试任务列表',
        leaf: true,//只有一个节点
        iconCls: 'fa fa-link',//图标样式class
        children: [
            { path: '/pytest_testtask', component: TESTTASK, name: '测试任务列表' }
        ]
    },
    {
        path: '/',
        component: Home,
        name: '测试报告列表',
        leaf: true,//只有一个节点
        iconCls: 'fa fa-link',//图标样式class
        children: [
            { path: '/pytest_report', component: REPORT, name: '测试报告列表' }
        ]
    },
    {
        path: '/',
        component: Home,
        name: '用例执行结果',
        leaf: true,//只有一个节点
        iconCls: 'fa fa-link',//图标样式class
        children: [
            { path: '/pytest_result', component: RESULT, name: '用例执行结果' }
        ]
    },
    {
        path: '/',
        component: Home,
        name: '账号权限',
        leaf: true,
        adminOnly: true,
        iconCls: 'fa fa-user',
        children: [
            { path: '/account_permission', component: ACCOUNT, name: '账号权限' }
        ]
    },


    // {
    //     path: '/',
    //     component: Home,
    //     name: 'pytest测试集合列表',
    //     leaf: true,//只有一个节点
    //     iconCls: 'fa fa-link',//图标样式class
    //     children: [
    //         { path: '/pytest_testset', component: TESTSET, name: 'pytest测试集合列表' }
    //     ]
    // },





];

export default routes;
