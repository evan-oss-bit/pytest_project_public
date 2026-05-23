<template>
    <section>
        <!--工具条-->
        <el-col :span="24" class="toolbar" style="padding-bottom: 0px">
            <el-form :inline="true" :model="filters">
                <el-col :span="20" justify="">
                    <el-form-item class="len_input">
                        <div class="block" style="">
                            <span class="demonstration"></span>
                            <el-cascader :filterable="true" :clearable="true" :disabled="false"
                                placeholder="请选择关联脚本项目(也可输入项目搜索)" separator="=>" v-model="filterProjectValue"
                                :options="addForm.options" :props="{ expandTrigger: 'hover' }"></el-cascader>
                        </div>
                    </el-form-item>
                    <el-form-item>
                        <el-input v-model="filters.cfg_name" placeholder="测试集名称" clearable>
                            <i slot="prefix" class="el-input__icon el-icon-search"></i>
                        </el-input>
                    </el-form-item>
                    <el-select v-model="value2" clearable placeholder="请选择">
                        <el-option v-for="item in options2" :key="item.value2" :label="item.label" :value="item.value2">
                        </el-option>
                    </el-select>
                    <el-form-item>
                        <el-button type="primary" icon="el-icon-search" v-on:click="getConfigList">查询</el-button>
                    </el-form-item>
                    <div>
                        <el-form-item>
                            <el-button @click="handleCreateTestset" type="success" icon="el-icon-plus"
                                style="float: right; text-align: right; margin-left: 10px">新建测试集</el-button>
                        </el-form-item>
                        <el-form-item>
                            <el-button @click="stop_set" type="danger"
                                style="float: right; text-align: right; margin-left: 10px">批量终止测试集</el-button>
                        </el-form-item>
                    </div>
                </el-col>
            </el-form>
        </el-col>
        <el-col :span="24">
            <div class="pool-usage-bar">
                <div class="pool-usage-main">
                    <span class="pool-title">进程池占用</span>
                    <el-tag size="mini" type="primary">运行中 {{ poolDetail.running || 0 }}</el-tag>
                    <el-tag size="mini" type="warning">排队中 {{ poolDetail.queued || 0 }}</el-tag>
                    <el-tag size="mini" type="success">空闲 {{ poolDetail.idle || 0 }}</el-tag>
                    <span class="pool-capacity">容量 {{ poolDetail.max_workers || 0 }}</span>
                </div>
                <div class="pool-usage-detail">
                    <el-button type="text" icon="el-icon-refresh" @click="loadProcessPoolStatus">刷新</el-button>
                </div>
            </div>
        </el-col>
        <!-- <template>
            <div v-html="htmlContent"></div>
        </template> -->
        <!--列表-->
        <el-col :span="24" type="“flex”" style="white-space: pre">
            <el-table :data="aioLst" highlight-current-row stripe height="600" v-loading="listLoading"
                @selection-change="selsChange" style="width: 100%" :cell-style="cellStyle">

                <!-- <el-table-column type="selection" width="2">
                </el-table-column> -->
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column label="测试集信息" min-width="260" sortable prop="title">
                    <template slot-scope="scope">
                        <div class="testset-main-cell">
                            <div class="testset-title">{{ scope.row.title }}</div>
                            <div class="testset-sub">项目：{{ scope.row.project_name || "-" }}</div>
                            <div class="testset-sub">run_id：{{ scope.row.run_id || "-" }}　用例：{{ scope.row.case_count_total || 0 }}</div>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column label="执行状态" width="190">
                    <template slot-scope="scope">
                        <div class="testset-status-cell">
                            <el-tag size="mini" :type="testsetStatusTag(scope.row.run_status)">{{ scope.row.run_status | stateFmt }}</el-tag>
                            <span class="testset-sub">进程 {{ scope.row.process_number || 0 }}</span>
                            <el-progress class="compact-progress" :percentage="percentagenum(scope.row)" :format="format"></el-progress>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column label="时间" width="190">
                    <template slot-scope="scope">
                        <div class="testset-sub">更新：{{ scope.row.updated_time || "-" }}</div>
                        <div class="testset-sub">已测：{{ scope.row.run_task_time || "-" }}</div>
                        <div class="testset-sub" v-if="scope.row.countdown">倒计时：{{ scope.row.countdown }}</div>
                        <div class="testset-sub" v-if="scope.row.timed_task_time">定时：{{ scope.row.timed_task_time }}</div>
                    </template>
                </el-table-column>
                <el-table-column prop="audit_info" label="操作人" width="170" show-overflow-tooltip></el-table-column>
                <el-table-column prop="mark_info" label="备注" min-width="110" show-overflow-tooltip></el-table-column>
                <!-- <el-table-column label="任务优先级" width="65"><template slot-scope="scope">{{ scope.row.priority | PriorityFmt}}</template></el-table-column> -->
                <!-- <el-table-column
          prop="num"
          label="里程数"
          sortable=""
          width="250"
        >
          <template slot-scope="scope">
            <el-progress type="line" :percentage="(scope.row.num)/percent*100" :format="format_info(scope.row,scope.column)" color="#57DCDD" :text-inside="false" :stroke-width="12" />
          </template>
        </el-table-column> -->
                <el-table-column label="操作" width="160" fixed="right">
                    <template slot-scope="scope">
                        <el-row>
                            <el-dropdown split-button type="primary" @click="handleAddEvent(scope.$index, scope.row)"
                                trigger="click">
                                运行
                                <el-dropdown-menu slot="dropdown">
                                    <el-button-group class="button-container">
                                        <el-button type="primary" icon="el-icon-edit"
                                            @click="handleEditEvent(scope.$index, scope.row)">编辑</el-button>
                                        <el-button @click="handleAddEvent_rerun(scope.$index, scope.row, 1)"
                                            type="primary">失败用例重试</el-button>
                                        <el-button
                                        type="primary"
                                        @click="union_testtask(scope.$index, scope.row)"
                                        >关联测试任务</el-button>
                                        <el-button type="primary" icon="el-icon-search"
                                            @click="getCaseListNow(scope.$index, scope.row)">实时测试用例详情</el-button>
                                        <el-button type="primary" icon="el-icon-search"
                                            @click="getCaseList(scope.$index, scope.row)">查看用例</el-button>
                                        <el-button type="primary" icon="el-icon-share"
                                            @click="getSetReportList(scope.$index, scope.row)">报告列表</el-button>
                                        <el-button type="primary" icon="el-icon-share"
                                            @click="get_html(scope.$index, scope.row)">查看最新报告</el-button>
                                        <el-button type="primary" icon="el-icon-share"
                                            @click="download(scope.$index, scope.row)">下载最新报告</el-button>
                                        
                                        <el-button type="warning" @click="delete_id_new(scope.$index, scope.row)">终止</el-button>
                                        <el-button type="danger" @click="is_deletes(scope.$index, scope.row)">删除</el-button>
                                    </el-button-group>
                                </el-dropdown-menu>
                            </el-dropdown>
                            <el-button-group>
                                <!-- <el-button type="primary" icon="el-icon-edit"
                                    @click="handleEditEvent(scope.$index, scope.row)">编辑</el-button>
                                <el-button type="danger" @click="delete_id_new(scope.$index, scope.row)"
                                    style="float: right; text-align: right; margin-left: 10px">终止</el-button> -->
                                <!-- <el-button @click="handleAddEvent(scope.$index, scope.row)" type="primary">运行测试集</el-button>
                                <el-button @click="handleAddEvent_rerun(scope.$index, scope.row, true)"
                                    type="primary">失败用例重试</el-button>
                                <el-button type="primary" icon="el-icon-search"
                                    @click="getCaseList(scope.$index, scope.row)">查看用例</el-button>
                                <el-button type="primary" icon="el-icon-share"
                                    @click="get_html(scope.$index, scope.row)">查看最新报告</el-button>
                                <el-button type="primary" icon="el-icon-share"
                                    @click="download(scope.$index, scope.row)">下载最新报告</el-button> -->
                            </el-button-group>

                        </el-row>

                    </template>

                </el-table-column>
            </el-table>
        </el-col>

        <!--工具条-->
        <el-col :span="24" class="toolbar" v-if="!this.ongoing">

            <el-pagination layout="total, prev, pager, next" @current-change="handleCurrentChange" :page-size="page_size"
                :total="total" style="float: right">
            </el-pagination>
        </el-col>
        <!-- <el-dialog title="用例列表" :visible.sync="dialogTableVisible">
            <el-table :data="gridData">
                <el-table-column property="date" label="日期" width="150"></el-table-column>
                <el-table-column property="name" label="姓名" width="200"></el-table-column>
                <el-table-column property="address" label="地址"></el-table-column>
            </el-table>
        </el-dialog> -->
        <el-dialog :title="set_title" :visible.sync="dialogTableVisible">
            <el-col class="toolbar" height="600">
                <el-pagination layout="total" :total="setcasetotal" style="float: right">
                </el-pagination>
            </el-col>
            <el-button type="primary" @click="getCaseList(1, testset_row)">刷新当前页</el-button>
            <template>
                <el-table :data="count_info" style="width: 100%">
                    <el-table-column prop="schedule" label="测试进度（%）"></el-table-column>
                    <el-table-column prop="all_count" label="全部用例数"></el-table-column>
                    <el-table-column prop="pass_count" label="通过用例数"></el-table-column>
                    <el-table-column prop="pass_rate" label="用例通过率（%）"></el-table-column>
                    <el-table-column prop="fail_count" label="失败用例数"></el-table-column>
                    <el-table-column prop="error_count" label="错误用例数"></el-table-column>
                    <el-table-column prop="executed_ing" label="测试中用例数"></el-table-column>
                    <el-table-column prop="un_executed" label="未测试用例数"></el-table-column>
                </el-table>
            </template>
            <!-- <el-col :span="24" type="“flex”" style="white-space: pre"> -->
            <el-table :data="CaseList" highlight-current-row stripe height="400" v-loading="listLoading" id="exportTab"
                @selection-change="selsChange" style="width: 100%" :cell-style="CasecellStyle">
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in CaseForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column>
                <el-table-column label="用例类型" width="120"><template slot-scope="scope">{{ scope.row.type | testFmt
                }}</template></el-table-column>
                <!-- <el-table-column label="操作">
                    <template scope="scope">
                        <el-row>
                        </el-row>
                    </template>
                </el-table-column> -->
            </el-table>
            <!-- </el-col> -->
        </el-dialog>

        <el-dialog :title="set_title" :visible.sync="casenow_dialogTableVisible">
            <el-col class="toolbar" height="600">
                <el-pagination layout="total" :total="setcasetotal" style="float: right">
                </el-pagination>
            </el-col>
            <el-button type="primary" @click="getCaseListNow(1, testset_row)">刷新当前页</el-button>
            <template>
                <el-table :data="count_info" style="width: 100%">
                    <el-table-column prop="schedule" label="测试进度（%）"></el-table-column>
                    <el-table-column prop="all_count" label="全部用例数"></el-table-column>
                    <el-table-column prop="pass_count" label="通过用例数"></el-table-column>
                    <el-table-column prop="pass_rate" label="用例通过率（%）"></el-table-column>
                    <el-table-column prop="fail_count" label="失败用例数"></el-table-column>
                    <el-table-column prop="error_count" label="错误用例数"></el-table-column>
                    <el-table-column prop="executed_ing" label="测试中用例数"></el-table-column>
                    <el-table-column prop="un_executed" label="未测试用例数"></el-table-column>
                </el-table>
            </template>
            <!-- <el-col :span="24" type="“flex”" style="white-space: pre"> -->
            <el-table :data="CaseList" highlight-current-row stripe height="400" v-loading="listLoading" id="exportTab"
                @selection-change="selsChange" style="width: 100%" :cell-style="CasecellStyle">
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in CaseForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column>
                <el-table-column label="用例类型" width="120"><template slot-scope="scope">{{ scope.row.type | testFmt
                }}</template></el-table-column>
                <!-- <el-table-column label="操作">
                    <template scope="scope">
                        <el-row>
                        </el-row>
                    </template>
                </el-table-column> -->
            </el-table>
            <!-- </el-col> -->
        </el-dialog>
        <el-dialog :title="set_title" :visible.sync="setdialogTableVisible">
            <el-col class="toolbar" height="600">
                <el-pagination layout="total" :total="setcasetotal" style="float: right">
                </el-pagination>
            </el-col>
            <el-table :data="ReportList" highlight-current-row stripe height="400" v-loading="listLoading" id="exportTab"
                @selection-change="selsChange" style="width: 100%" :cell-style="CasecellStyle">
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in ReportForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column>

                <!-- <el-table-column label="用例类型" width="120"><template slot-scope="scope">{{ scope.row.type | testFmt
                }}</template></el-table-column> -->
                <el-table-column label="操作" width="300">
                    <template slot-scope="scope">
                        <el-row>
                            <el-button-group>
                                <el-button type="primary" icon="el-icon-share"
                                    @click="get_html_list(scope.$index, scope.row)">查看在线报告</el-button>
                                <el-button type="primary" icon="el-icon-share"
                                    @click="download_list(scope.$index, scope.row)">下载报告</el-button>
                            </el-button-group>
                        </el-row>

                    </template>

                </el-table-column>
            </el-table>
        </el-dialog>
        <el-dialog :title="set_title" :visible.sync="taskdialogTableVisible">
            <el-col class="toolbar" height="600">
                <el-pagination layout="total" :total="setcasetotal" style="float: right">
                </el-pagination>
            </el-col>
            <el-table :data="UnionTestTaskList" highlight-current-row stripe height="400" v-loading="listLoading" id="exportTab"
                @selection-change="selsChange" style="width: 100%" :cell-style="CasecellStyle">
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in TaskForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column>

                <!-- <el-table-column label="用例类型" width="120"><template slot-scope="scope">{{ scope.row.type | testFmt
                }}</template></el-table-column> -->
                <!-- <el-table-column label="操作" width="300">
                    <template slot-scope="scope">
                        <el-row>
                            <el-button-group>
                                <el-button type="primary" icon="el-icon-share"
                                    @click="get_html_list(scope.$index, scope.row)">查看在线报告</el-button>
                                <el-button type="primary" icon="el-icon-share"
                                    @click="download_list(scope.$index, scope.row)">下载报告</el-button>
                            </el-button-group>
                        </el-row>

                    </template>

                </el-table-column> -->
            </el-table>
        </el-dialog>

        <!--详情界面-->
        <!-- <el-dialog title="详情" v-model="detailFormVisible" :close-on-click-modal="false"> -->
        <el-dialog :title="runset_title" :close-on-click-modal="false" :visible.sync="detailFormVisible">
            <el-form :model="addForm" label-width="150px" :rules="detailFormRules" ref="addForm">
                <el-col :span="24" style="margin-right: 100px">

                    <!-- <el-row>
                <el-col :span="9">
                  <el-form-item label="模块名称" prop="ip">
                    <el-input
                      ref="inputName"
                      v-model="addForm.config_name"
                      auto-complete="off"
                      placeholder="模块名称"
                      autofocus="true"
                      clearable
                    ></el-input>
                  </el-form-item>
                </el-col>
              </el-row> -->


                    <!-- <el-form-item label="项目名称" class="len_input">
                        <div class="block" style=""><el-input v-model="addForm.cfg" placeholder="请输入项目名称"></el-input></div>

                    </el-form-item> -->
                    <el-row><el-form-item>
                            <pre>1.每个用例都需要独立不依赖其他用例参数,需要依赖前置用例的请在conftest.py修改成前置方法,用例调用即可<br>2.定时任务为线程执行用例,<br>两个以上同时运行pytest有概率会引发ValueError: I/O operation on closed file导致测试中断的问题<br>3.UI自动化对服务器性能要求较高!<br></pre>
                        </el-form-item></el-row>

                    <el-row>
                        <el-col :span="9">
                            <el-form-item label="关联脚本项目" class="len_input" required>
                                <div class="block" style="">
                                    <span class="demonstration"></span>
                                    <el-cascader :filterable="true" :clearable="true" :disabled="true"
                                        placeholder="请选择关联脚本项目(也可输入项目搜索)" separator="=>" v-model="addForm.value"
                                        :options="addForm.options" :props="{ expandTrigger: 'hover' }"></el-cascader>
                                </div>
                            </el-form-item>
                        </el-col>
                        <el-col :span="9">
                        </el-col>
                    </el-row>

                    <!-- <el-row>
                        <el-col :span="9">
                            <el-form-item label="关联配置" class="len_input" required>
                                <div class="block" style="">
                                    <span class="demonstration"></span>
                                    <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联配置(也可输入配置搜索)"
                                        separator="=>" v-model="addForm.value3" :options="addForm.options3"
                                        :props="{ expandTrigger: 'hover' }"></el-cascader>
                                </div>
                            </el-form-item>
                        </el-col>
                        <el-col :span="9">
                        </el-col>
                    </el-row> -->


                    <el-row>
                        <el-col :span="9">
                            <el-form-item label="关联配置" class="len_input" required>
                                <div class="block" style="">
                                    <span class="demonstration">
                                    </span>
                                    <el-select v-model="addForm.value3" filterable multiple clearable default-first-option placeholder="请选择关联配置(也可输入配置搜索)">
                                        <el-option
                                        v-for="item in addForm.options3"
                                        :key="item.value"
                                        :label="item.label"
                                        :value="item.value">
                                        </el-option>   
                                    </el-select>
                                </div>
                            </el-form-item>
                        </el-col>
                        <!-- <el-col :span="9">
                            <p>当前所选项序号:</p>
                            <ul>
                                <li v-for="(selectedItem, index) in addForm.value3" :key="selectedItem">
                                {{ index + 1 }}
                                </li>
                            </ul>
                            </el-col> -->
                        <!-- <el-col :span="9">
                        </el-col> -->
                    </el-row>

                    <el-row>
                        <el-col :span="9">
                            <el-form-item label="用例脚本类型" class="len_input">
                                <el-select v-model="value" placeholder="请选择">
                                    <el-option v-for="item in options" :key="item.value" :label="item.label"
                                        :value="item.value">
                                    </el-option>
                                </el-select>
                            </el-form-item>
                        </el-col>
                    </el-row>
                    <el-row>
                        <el-col :span="9">
                            <el-form-item label="任务优先级" class="len_input">
                                <el-select v-model="priority_value" placeholder="请选择" :disabled="true">
                                    <el-option v-for="item in priority_options" :key="item.value" :label="item.label"
                                        :value="item.value">
                                    </el-option>
                                </el-select>
                            </el-form-item>
                        </el-col>
                    </el-row>
                    <el-row>
                        <el-col :span="9">
                            <el-form-item label="关联版本号" class="len_input">
                                <div class="block" style="">
                                    <span class="demonstration"></span>
                                    <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联版本号(也可输入项目搜索)"
                                        separator="=>" v-model="addForm.value2" :options="addForm.options2"
                                        :props="{ expandTrigger: 'hover' }"></el-cascader>
                                </div>
                            </el-form-item>
                        </el-col>
                        <el-col :span="9">
                        </el-col>
                    </el-row>
                    <el-form-item label="是否发送邮件">
                        <el-tooltip  :content="'绿色则为发送,红色则为不发送'" placement="top">
                            <el-switch v-model="sent_email" active-color="#13ce66" inactive-color="#ff4949" active-value=1
                                inactive-value=0>
                            </el-switch>
                        </el-tooltip>
                    </el-form-item>
                    <el-form-item label="邮件地址">
                        <el-input placeholder="输入邮件地址即可发送邮件，多个邮件间请用;来区分" type="input" v-model="addForm.email_to"></el-input>
                    </el-form-item>

                    <el-form-item label="备注信息">
                        <el-input type="textarea" v-model="addForm.mark" placeholder="填写测试集合备注信息"></el-input>
                    </el-form-item>
                    <!-- <el-form-item label="多进程执行脚本">
                        <el-tooltip :content="'开启的进程数: ' + pros_value" placement="top">
                            <el-switch v-model="pros_value" active-color="#13ce66" inactive-color="#ff4949" active-value=3
                                inactive-value=0>
                            </el-switch>
                        </el-tooltip>
                    </el-form-item> -->
                    <el-form-item label="多进程执行脚本">
                        <el-select v-model="pros_value" clearable placeholder="请选择,不选默认单进程执行用例">
                            <el-option v-for="item in pros_options" :key="item.value" :label="item.label"
                                :value="item.value">
                            </el-option>
                        </el-select></el-form-item>
                    <el-form-item label="定时任务开启时间">
                        <!-- <span class="demonstration">带快捷选项</span> -->
                        <el-date-picker v-model="datevalue2" type="datetime" value-format="yyyy-MM-dd HH:mm:ss"
                            placeholder="选择时间则开启定时任务">
                        </el-date-picker>
                    </el-form-item>

                </el-col>
            </el-form>
            <div slot="footer" class="dialog-footer">
                <el-button type="primary" :disabled="false" @click="AIOOIA">提交
                </el-button>
                <el-button @click.native="detailFormVisible = false">返回</el-button>
            </div>
        </el-dialog>
        <el-dialog :title="runset_title" :close-on-click-modal="false" :visible.sync="EditSetVisible">
            <el-form :model="addForm" label-width="150px" :rules="detailFormRules" ref="addForm">
            <el-form-item label="提示信息:">
                <span>
                    <pre>先选择脚本项目，再从左侧用例列表中选择需要加入测试集的用例</pre>
                </span>
            </el-form-item>
            <el-form-item label="测试集名称:">
            <el-input v-model="set_title" placeholder="测试集名称" clearable>
                <i slot="prefix" class="el-input__icon el-icon-search"></i>
            </el-input>
           </el-form-item>
            <el-row>
                <el-col :span="9">
                    <el-form-item label="关联脚本项目" class="len_input" required>
                        <div class="block" style="">
                            <span class="demonstration"></span>
                            <el-select v-if="isCreateSet" v-model="createProjectId" filterable clearable
                                placeholder="请选择关联脚本项目(也可输入项目搜索)" @change="handleCreateProjectChange">
                                <el-option
                                    v-for="item in addForm.options"
                                    :key="item.value"
                                    :label="item.label"
                                    :value="item.value">
                                </el-option>
                            </el-select>
                            <el-cascader v-else :filterable="true" :clearable="true" :disabled="true"
                                placeholder="请选择关联脚本项目(也可输入项目搜索)" separator="=>" v-model="addForm.value"
                                :options="addForm.options" :props="{ expandTrigger: 'hover' }"></el-cascader>
                        </div>
                    </el-form-item>
                </el-col>
                <el-col :span="9">
                </el-col>
            </el-row>
           <!-- <el-row>
                <el-col :span="9">
                    <el-form-item label="关联配置:" class="len_input">
                        <div class="block" style="">
                            <span class="demonstration"></span>
                            <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联配置(也可输入配置搜索)"
                                separator="=>" v-model="addForm.value3" :options="addForm.options3"
                                :props="{ expandTrigger: 'hover' }"></el-cascader>
                        </div>
                    </el-form-item>
                </el-col>
                <el-col :span="9">
                </el-col>
            </el-row> -->
            <el-row>
                <el-col :span="9">
                    <el-form-item label="关联配置" class="len_input" required>
                        <div class="block" style="">
                            <span class="demonstration">
                            </span>
                            <el-select v-model="addForm.value3" filterable multiple clearable default-first-option placeholder="请选择关联配置(也可输入配置搜索)">
                                <el-option
                                v-for="item in addForm.options3"
                                :key="item.value"
                                :label="item.label"
                                :value="item.value">
                                </el-option>   
                            </el-select>
                        </div>
                    </el-form-item>
                </el-col>
                <!-- <el-col :span="9">
                    <p>当前所选项序号:</p>
                    <ul>
                        <li v-for="(selectedItem, index) in addForm.value3" :key="selectedItem">
                        {{ index + 1 }}
                        </li>
                    </ul>
                    </el-col> -->
                <!-- <el-col :span="9">
                </el-col> -->
            </el-row>
            <el-row>
                <el-col :span="9">
                    <el-form-item label="任务优先级" class="len_input">
                        <el-select v-model="priority_value" placeholder="请选择">
                            <el-option v-for="item in priority_options" :key="item.value" :label="item.label"
                                :value="item.value">
                            </el-option>
                        </el-select>
                    </el-form-item>
                </el-col>
            </el-row>
            <el-row>
                <el-col :span="9">
                    <el-form-item label="关联版本号" class="len_input">
                        <div class="block" style="">
                            <span class="demonstration"></span>
                            <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联版本号(也可输入项目搜索)"
                                separator="=>" v-model="addForm.value2" :options="addForm.options2"
                                :props="{ expandTrigger: 'hover' }"></el-cascader>
                        </div>
                    </el-form-item>
                </el-col>
                <el-col :span="9">
                </el-col>
            </el-row>
            <!-- <el-input v-model="addForm.mark" placeholder="备注" clearable>
                <i slot="prefix" class="el-input__icon el-icon-search"></i>
            </el-input> -->
            <el-form-item label="邮件地址:">
                <el-input placeholder="输入邮件地址即可发送邮件，多个邮件间请用;来区分" type="input" v-model="addForm.email_to"></el-input>
            </el-form-item>
            <el-form-item label="备注信息:">
                <el-input type="textarea" v-model="addForm.mark" placeholder="填写测试集合备注信息"></el-input>
            </el-form-item>
        </el-form>
            <!-- <div class="block" style="">
                <span class="demonstration"></span>
                <el-cascader :filterable="true" :clearable="true" :disabled="false" placeholder="请选择关联脚本项目(也可输入项目搜索)"
                    separator="=>" v-model="addForm.value" :options="addForm.options"
                    :props="{ expandTrigger: 'hover' }"></el-cascader>
                <el-button type="primary" icon="el-icon-search" v-on:click="getConfigList">查询</el-button>
            </div> -->
            <div style="text-align: center">
                <el-transfer style="text-align: left; display: inline-block" v-model="value4" filterable
                    @mouseover.native="addTitle" :left-default-checked="[2, 3]" :right-default-checked="[1]"
                    :titles="['未添加用例列表', '已添加用例列表']" :button-texts="['到左边', '到右边']" :format="{
                        noChecked: '${total}',
                        hasChecked: '${checked}/${total}'
                    }" @change="handleChange" :data="case_data">
                    <!-- <span slot-scope="{ option }">{{ option.key }} - {{ option.label }}</span> -->
                    <!-- <span slot-scope="{ option }">{{ option.label }}</span> -->
                    <span slot-scope="{ option }" v-if="option.case_count > 1" style="color: #00FF00;">{{ option.label }}</span>
                    <span slot-scope="{ option }" v-else-if="option.run_status == 'error'" style="color: #FF0000;">{{ option.label }}</span>
                    <span slot-scope="{ option }" v-else>{{ option.label }}</span>
                    <!-- <el-button class="transfer-footer" slot="left-footer" size="small">操作</el-button>
                    <el-button class="transfer-footer" slot="right-footer" size="small">操作</el-button> -->
                </el-transfer>
            </div>
            <div slot="footer" class="dialog-footer">
                <el-button type="primary" :disabled="false" @click="add_set">保存
                </el-button>
                <el-button @click.native="EditSetVisible = false">返回</el-button>
            </div>
        </el-dialog>
    </section>
</template>
<style>  .button-container {
      display: flex;
      flex-direction: column;
  }
</style>    
<script>
import axios from "axios";
import draggable from 'vuedraggable';
import {
    // DeleteConfig,
    get_config_info,
    get_project_info,
    get_version_info,
    get_testset_info,
    run_testset,
    stop_testset,
    delete_testset,
    get_files,
    union_task,
    get_url,
    get_cases_info,
    add_testset,
    get_report_info,
    get_process_pool_status,
} from "../../api/api";
import moment from "moment";
import Vue from "vue";
Vue.prototype.$moment = moment;

export default {
    data() {
        return {
            datevalue2: "",
            deadline2: '11111111111111',
            runset_title: "运行测试集",
            isCreateSet: false,
            createProjectId: null,
            set_title: '',
            pros_value: '',
            sent_email:0,
            dialogTableVisible: false,
            setdialogTableVisible: false,
            casenow_dialogTableVisible: false,
            EditSetVisible: false, //编辑测试集页面是否显示
            taskdialogTableVisible: false,
            setcasetotal: 0,
            setids: [],
            value4: [],
            CaseList: [],
            ReportList: [],
            case_data: [],
            count_info: [],
            UnionTestTaskList: [],
            pros_options: [{
                value: 2,
                label: '进程数2'
            }, {
                value: 3,
                label: '进程数3'
            }, {
                value: 4,
                label: '进程数4'
            }, {
                value: 5,
                label: '进程数5'
            }],
            options2: [{
                value2: 0,
                label: '未运行'
            }, {
                value2: 1,
                label: '运行中'
            }, {
                value2: 2,
                label: '运行完成'
            }],
            value2: null,
            timer: "",
            htmlcontent: null,
            priority_options: [{
                value: 0,
                label: 'P0'
            },
            {
                value: 1,
                label: 'P1'
            },
            {
                value: 2,
                label: 'P2'
            },
            {
                value: 3,
                label: 'P3'
            },
            {
                value: 4,
                label: 'P4'
            },
            {
                value: 5,
                label: 'P5'
            },
            {
                value: 6,
                label: 'P6'
            },
            {
                value: 7,
                label: 'P7'
            },
            {
                value: 8,
                label: 'P8'
            },
            {
                value: 9,
                label: 'P9'
            },
            {
                value: 10,
                label: 'P10'
            }],
            options: [{
                value: 1,
                label: 'pytest'
            }],
            value: 1,
            priority_value: 0,
            clean: false,
            ongoing: false,
            filters: {
                cfg_name: "",
            },
            filterProjectValue: [],
            install_type_lst: [],
            addViperHost: "",
            aioLst: [],
            testset_row: "",
            run_id: "",
            page_size: 1000,
            total: 0,
            page: 0,
            rerun_type: 0,
            addStatus: true,
            listLoading: false,
            processPool: {
                running: 0,
                queued: 0,
                idle: 0,
                max_workers: 0,
                testset: {},
                testtask: {},
            },
            sels: [], //列表选中列

            detailFormVisible: false, //详情界面是否显示
            addFormVisible: false, //添加界面是否显示
            editLoading: false,
            detailFormRules: {
                name: [{ required: true, message: "请输入姓名", trigger: "blur" }],
            },
            //详情界面数据
            continue_flag: true,
            dialogVisible: false,
            addForm: {
                email_to: "",
                add_data: true,
                anaFlag: false,
                bdaFlag: false,
                nodeFlag: false,
                cfg: "",
                node_randio: 1,
                auth: false,
                mark: "",
                value: "",
                options: [],
                value2: "",
                options2: [],
                value3: "",
                options3: [],
                set_time: "",
                note: "",
                config_id: null,
                config_name: "",
                set_flag: true,
            },

            lstForm: [
                // { prop: "id", label: "id", width: 60 },
                { prop: "title", label: "测试集名称", width: 145 },
                { prop: "project_name", label: "脚本项目", width: 140 },
                { prop: "run_id", label: "最新运行id", width: 120 },
                // { prop: "previous_level", label: "所属文件夹", width: 80 },
                // { prop: "version_id", label: "版本id", width: 100 },
                // { prop: "case_ids", label: "测试集内用例id", width: 160 },
                // { prop: "run_status", label: "运行状态", width: 120 },
                // { prop: "schedule", label: "测试进度（%）", width: 80 },
                { prop: "updated_time", label: "更新时间", width: 175 },
                { prop: "case_count_total", label: "用例数量（条）", width: 80 },
                { prop: "audit_info", label: "操作人", width: 190 },
                { prop: "mark_info", label: "备注", width: 100 },
                { prop: "run_type", label: "运行方式", width: 80 },
                { prop: "timed_task_time", label: "定时任务开启时间", width: 140 }
            ],
            CaseForm: [
                // { prop: "id", label: "用例id", width: 100 },
                { prop: "title", label: "用例title(py文件::pytest测试类::pytest用例)", width: 200 },
                { prop: "case_name", label: "用例名(func.__doc__)", width: 200 },
                { prop: "project_name", label: "项目名称", width: 100 },
                // { prop: "type", label: "用例类型", width: 100 },
                { prop: "run_status", label: "测试结果", width: 100 },
                { prop: "case_count", label: "用例条数", width: 60 },
                { prop: "relative_case_path", label: "用例所在路径", width: 200 },
                // { prop: "project_id", label: "项目id", width: 100 },
                // { prop: "version_id", label: "版本id", width: 100 },
                // { prop: "module_id", label: "模块id", width: 100 },
                { prop: "remark", label: "备注", width: 160 },
                // { prop: "updated_time", label: "更新时间", width: 200 },
            ],
            ReportForm: [
                // { prop: "id", label: "报告id", width: 100 },
                // { prop: "config_id", label: "配置id", width: 100 },
                // { prop: "project_name", label: "脚本项目", width: 120 },
                // { prop: "set_id", label: "测试集id", width: 80 },
                { prop: "title", label: "测试报告名（项目名_测试集名_运行id）", width: 300 },
                { prop: "mark", label: "备注", width: 200 },
                { prop: "case_all_time", label: "用例总耗时/s", width: 100 },
                { prop: "run_by_name", label: "执行人", width: 100 },
                { prop: "all_count", label: "全部用例数", width: 100 },
                { prop: "pass_count", label: "通过用例数", width: 100 },
                { prop: "pass_rate", label: "用例通过率（%）", width: 100 },
                { prop: "fail_count", label: "失败用例数", width: 100 },
                { prop: "error_count", label: "错误用例数", width: 100 },
                { prop: "updated_time", label: "更新时间", width: 200 },

            ],
            TaskForm: [
                // { prop: "id", label: "报告id", width: 100 },
                // { prop: "config_id", label: "配置id", width: 100 },
                // { prop: "project_name", label: "脚本项目", width: 120 },
                // { prop: "set_id", label: "测试集id", width: 80 },
                { prop: "name", label: "测试任务名", width: 120 },
                { prop: "mark", label: "备注", width: 200 },
                { prop: "run_id", label: "运行id", width: 100 },
                { prop: "run_status", label: "运行状态", width: 100 },
                { prop: "schedule", label: "进度", width: 100 },
                { prop: "start_task_time", label: "定时任务开启时间", width: 100 },
                { prop: "timed_task_time", label: "定时任务时间", width: 100 },
                // { prop: "error_count", label: "错误用例数", width: 100 },ff
                // { prop: "updated_time", label: "更新时间", width: 200 },

            ],
        };
    },

    filters: {
        stateFmt(state) {
            return (
                {
                    0: "未运行",
                    1: "运行中",
                    2: "运行完成",
                }[state] || "其他"
            );
        },
        testFmt(state) {
            return (
                {
                    1: "pytest",
                    2: "函数式",
                }[state] || "其他"
            );
        },
        PriorityFmt(state) {
            return (
                {
                    0: "P0",
                    1: "P1",
                    2: "P2",
                    3: "P3",
                    4: "P4",
                    5: "P5",
                    6: "P6",
                    7: "P7",
                    8: "P8",
                    9: "P9",
                    10: "P10",
                }[state] || "其他"
            );
        },
    },
//     computed: {
//     computedOptions() {
//       return this.addForm.options3.map((item) => {
//         const index = this.addForm.value3.indexOf(item.value);
//         const label = index > -1 ? `${index + 1}. ${item.label}` : item.label;
//         return {item, label};
//       });
//     }
//   },
    computed: {
        poolDetail() {
            return this.processPool.testset || { name: '测试集进程池', max_workers: 0, running: 0, queued: 0, idle: 0 };
        },
    },
    methods: {

        async loadProcessPoolStatus() {
            await get_process_pool_status({}).then((res) => {
                if (res.data.code === 200) {
                    this.processPool = Object.assign({}, this.processPool, res.data.data || {});
                }
            });
        },

        start() {
            this.timer = setInterval(this.valChange, 10000); // 注意: 第一个参数为方法名的时候不要加括号;
        },
        valChange() {
            this.getConfigList();
        },
        format(percentage) {
        return percentage === 100 ? '完成' : `${percentage}%`;
            },
        testsetStatusTag(status) {
            if (status === 0 || status === "测试中") {
                return "";
            }
            if (status === 2 || status === "通过" || status === "passed") {
                return "success";
            }
            if (status === 1 || status === "失败" || status === "failed" || status === "error") {
                return "danger";
            }
            return "info";
        },
        percentagenum(row){
                if (!row.schedule){
                    return 0
                }
                else{return row.schedule}
            },
        progress_status(row){
            if (!row.schedule)
                {return ""}
            if(row.schedule === 100){
                return 'success'
            }

        },
        mounted() { },
        beforeDestroy() {
            clearInterval(this.timer);
        },
        // selectBlur(e) {
        //     Vue.set(this.addForm, "viper_version", e.target.value);
        // },
        radioChangeEvt() {
            if (this.addForm.node_randio % 2 != 0) {
                this.addForm.aIp = "";
            }
        },
        handleCurrentChange(val) {
            this.page = val;
            this.getConfigList();
        },
        handleChange(value, direction, movedKeys) {
        },
        projectIdFromValue(value) {
            if (Array.isArray(value)) {
                return value.length ? value[0] : null;
            }
            return value || null;
        },
        auditInfoText(row) {
            const created = row.created_by_name || "-";
            const updated = row.updated_by_name || "-";
            const run = row.run_by_name || "-";
            return "创 " + created + " / 更 " + updated + " / 执 " + run;
        },
        parseIdList(value) {
            if (Array.isArray(value)) {
                return value;
            }
            if (value === null || value === undefined || value === "" || value === "None") {
                return [];
            }
            try {
                const parsed = JSON.parse(value);
                return Array.isArray(parsed) ? parsed : [];
            } catch (e) {
                return [];
            }
        },
        cellStyle({ row, column, rowIndex, columnIndex }) {
            let cell_Style
            switch (row.run_status) {
                case 0:
                    cell_Style = 'color:#0000FF'
                    break;
                case 1:
                    cell_Style = 'color:#FF0000'
                    break;
                case 2:
                    cell_Style = 'color:#00FF00'
                    break;
                default:
                    cell_Style = ''
                    break;
            }
            // 返回最终处理过的样式 这样写就是让全部行被style修饰
            // return cell_Style

            //返回最终处理过的样式 只让测试结果这个属性的属性被style修饰
            if (column.label == '运行状态') {
                return cell_Style
            }
        },
        CasecellStyle({ row, column, rowIndex, columnIndex }) {
            let cell_Style
            switch (row.run_status) {
                case 'passed':
                    cell_Style = 'color:#00FF00'
                    break;
                case 'failed':
                    cell_Style = 'color:#FF0000'
                    break;
                case 'error':
                    cell_Style = 'color:#FF0000'
                    break;
                case '测试中':
                    cell_Style = 'color:#0000FF'
                    break;
                default:
                    cell_Style = ''
                    break;
            }
            // 返回最终处理过的样式 这样写就是让全部行被style修饰
            // return cell_Style

            //返回最终处理过的样式 只让测试结果这个属性的属性被style修饰
            if (column.label == '测试结果') {
                return cell_Style
            }
        },

        format_info(row, column) {
      return () => {
        if (column.label === '里程数') {
          return row.num + 'km'
        }
      }
    },
        //获取测试集列表
        async getConfigList() {
            this.ongoing = false;
            let para = {
                run_status: this.value2,
                project_id: this.projectIdFromValue(this.filterProjectValue),
                title: this.filters.cfg_name,
                page: this.page,
                page_size: this.page_size,
            };
            this.listLoading = true;
            await get_testset_info(para).then((res) => {
                const rows = res.data.data || [];
                this.aioLst = rows.map((item) => Object.assign({}, item, {
                    audit_info: this.auditInfoText(item)
                }));
                this.listLoading = false;
                this.total = rows.length;
            });
            this.loadProcessPoolStatus();
        },
        async handleCreateTestset() {
            this.isCreateSet = true;
            this.EditSetVisible = true;
            this.runset_title = "新建测试集";
            this.set_title = "";
            this.addForm.config_id = null;
            this.addForm.mark = "";
            this.createProjectId = this.projectIdFromValue(this.filterProjectValue);
            this.addForm.value = this.createProjectId ? [this.createProjectId] : [];
            this.addForm.value2 = [];
            this.addForm.value3 = [];
            this.addForm.email_to = "";
            this.priority_value = 0;
            this.value4 = [];
            this.case_data = [];
            this.CaseList = [];
            this.setcasetotal = 0;
            await this.getproinfo();
            await this.getversioninfo();
            await this.getmoduleinfo();
            if (this.createProjectId) {
                await this.loadTransferCases(this.createProjectId);
            }
        },
        async handleCreateProjectChange(value) {
            if (!this.isCreateSet) {
                return;
            }
            const projectId = this.projectIdFromValue(value);
            this.createProjectId = projectId;
            this.addForm.value = projectId ? [projectId] : [];
            this.value4 = [];
            this.case_data = [];
            this.CaseList = [];
            this.setcasetotal = 0;
            if (projectId) {
                await this.loadTransferCases(projectId);
            }
        },
        async loadTransferCases(projectId, selectedCaseIds) {
            let para = {
                page: 0,
                page_size: 10000,
                project_id: projectId,
                script_type: this.value
            };
            this.listLoading = true;
            await get_cases_info(para).then((res) => {
                this.CaseList = res.data.data || [];
                this.setcasetotal = this.CaseList.length;
                this.case_data = [];
                for (let i = 0; i < this.CaseList.length; i++) {
                    this.case_data.push({
                        key: this.CaseList[i].id,
                        label: this.CaseList[i].case_count + "-" + this.CaseList[i].case_name + "-" + this.CaseList[i].project_name,
                        disabled: false,
                        subscript: i,
                        case_count: this.CaseList[i].case_count,
                        run_status: this.CaseList[i].run_status
                    });
                }
                this.listLoading = false;
                if (this.isCreateSet && this.CaseList.length === 0) {
                    this.$message({
                        message: "当前脚本项目暂无可选用例，请先扫描/同步脚本",
                        type: "warning",
                        duration: 5000
                    });
                }
            }).catch(() => {
                this.listLoading = false;
            });
            if (selectedCaseIds) {
                this.value4 = selectedCaseIds;
            }
        },
        //获取用例列表
        async getCaseList(index, row) {
            this.dialogTableVisible = true
            this.ongoing = false;
            this.testset_row = row;
            this.set_title = "测试集[" + row.title + "]的用例列表";
            this.run_id = row.run_id;
            let para = {
                page: this.page,
                page_size: this.page_size,
                cases_in: row.case_ids,
                run_id: this.run_id
            };
            this.listLoading = true;
            await get_cases_info(para).then((res) => {
                this.CaseList = res.data.data;
                this.listLoading = false;
                this.setcasetotal = res.data.data.length;
                this.count_info = [];
                if (res.data.count !== null) {
                    this.count_info = [res.data.count];
                }
            });
        },
        //获取用例列表
        async getCaseListNow(index, row) {
            this.casenow_dialogTableVisible = true
            this.ongoing = false;
            this.testset_row = row;
            this.set_title = "测试集[" + row.title + "]的实时测试用例列表";
            this.run_id = row.run_id;
            let check_case = row.case_ids
            if (row.rerun_type == 1){
                check_case = row.fail_ids
                this.set_title = "测试集[" + row.title + "]的实时失败用例重试测试用例列表";
            }
            if (row.run_status == 0 || row.run_status == 2){
                check_case = 'no_case'
            }
            let para = {
                page: this.page,
                page_size: this.page_size,
                cases_in: check_case,
                run_id: this.run_id
            };
            this.listLoading = true;
            await get_cases_info(para).then((res) => {
                this.CaseList = res.data.data;
                this.listLoading = false;
                this.setcasetotal = res.data.data.length;
                this.count_info = [];
                if (res.data.count !== null) {
                    this.count_info = [res.data.count];
                }
            });
        },
        async union_testtask(index, row){
            this.UnionTestTaskList = null;
            this.count_info = [];
            this.setcasetotal = null;
            this.taskdialogTableVisible = true
            this.ongoing = false;
            this.test_row = row;
            this.set_title = "测试集[" + row.title + "]的关联任务列表";
            let para = {
                set_id: row.id
            };
            this.listLoading = true;
            await union_task(para).then((res) => {
                this.UnionTestTaskList = res.data.data;
                this.listLoading = false;
                this.setcasetotal = res.data.data.length;
                if (res.data.count !== null) {
                    this.count_info = [res.data.count];
                }
                if (this.setcasetotal > 1000 ){
                    this.set_title=this.set_title + ">>>测试数据量大于100条的不宜展示！"; 
                    this.CaseList=this.CaseList.slice(0,100)
                }
            });
        },
        //获取该测试集的报告列表
        async getSetReportList(index, row) {
            this.setdialogTableVisible = true
            this.set_title = "测试集[" + row.title + "]的测试报告列表";
            let para = {
                page: this.page,
                page_size: this.page_size,
                set_id: row.id
            };
            this.listLoading = true;
            await get_report_info(para).then((res) => {
                this.ReportList = res.data.data;
                this.listLoading = false;
                this.setcasetotal = res.data.data.length;
                this.count_info = [];
                if (res.data.count !== null) {
                    this.count_info = [res.data.count];
                }
            });
        },

        //选择列
        selsChange: function (sels) {
            this.sels = sels;
            this.caseids = [];
            for (let caseid in this.sels) {
                this.caseids.push(this.sels[caseid]["id"])
            }

        },

        alertMsg(msg) {
            this.continue_flag = false;
            this.$message({
                message: msg,
                type: "warning",
            });
        },
        async AIOOIA() {
            this.continue_flag = true;
            if (this.continue_flag) {
                let delayTime = new Date(this.addForm.set_time).toJSON();
                var set_time = new Date(+new Date(delayTime) + 8 * 3600 * 1000)
                    .toISOString()
                    .replace(/T/g, " ")
                    .replace(/\.[\d]{3}Z/, "");
                if (this.addForm.add_data) {
                    var Config_id = null;

                } else {
                    var Config_id = this.addForm.config_id;
                }
                //version_id可传可不传
                if (this.addForm.value2 == null) {
                    this.addForm.value2 = []
                }


                let para = {
                    module: this.addForm.config_name,
                    project_name: this.addForm.cfg,
                    project_id: this.projectIdFromValue(this.addForm.value),
                    version_id: this.addForm.value2[0],
                    cfg_id: this.addForm.value3,
                    id: this.addForm.config_id,
                    script_type: this.value,
                    priority_value: this.priority_value,
                    rerun_type: this.rerun_type,
                    mark: this.addForm.mark,
                    email_to: this.addForm.email_to,
                    timed_task_time: this.datevalue2,
                    start_process: this.pros_value,
                    sent_email:this.sent_email,
                };


                await run_testset(para).then((res) => {
                    this.listLoading = false;
                    let { msg, code } = res.data;
                    if (code !== 200) {
                        this.$message({
                            message: msg,
                            type: "warning",
                            duration: 5000
                        });
                    } else {
                        this.$message({
                            message: msg,
                            type: "success",
                        });
                    }
                });
                this.detailFormVisible = false;
            }
            this.getConfigList();
        },

        FormatTime(fmt) {
            var dateTime = new Date();
            var o = {
                "M+": dateTime.getMonth() + 1, //月份
                "d+": dateTime.getDate(), //日
                "H+": dateTime.getHours(), //小时
                "m+": dateTime.getMinutes(), //分
                "s+": dateTime.getSeconds(), //秒
                "q+": Math.floor((dateTime.getMonth() + 3) / 3), //季度
                S: dateTime.getMilliseconds(), //毫秒
            };
            if (/(y+)/.test(fmt)) {
                fmt = fmt.replace(
                    RegExp.$1,
                    (dateTime.getFullYear() + "").substr(4 - RegExp.$1.length)
                );
            }
            for (var k in o) {
                if (new RegExp("(" + k + ")").test(fmt)) {
                    fmt = fmt.replace(
                        RegExp.$1,
                        RegExp.$1.length == 1
                            ? o[k]
                            : ("00" + o[k]).substr(("" + o[k]).length)
                    );
                }
            }
            return fmt;
        },


        //更新
        // async handleUpdate(index, row) {

        //   this.listLoading = true;

        //   let para = { viper: row.viper };
        //   await updateViper(para).then((res) => {
        //     this.listLoading = false;
        //     let { msg, code } = res.data;
        //     if (code !== 200) {
        //       this.$message({
        //         message: msg,
        //         type: "warning",
        //       });
        //     } else {
        //       this.$message({
        //         message: msg,
        //         type: "success",
        //       });
        //     }
        //   });
        //   this.getproinfo();
        //   // })
        //   // .catch(() => {});
        // },
        //删除
        handleDel: function (index, row) {
            this.$confirm("确认删除该用户吗?", "提示", {
                type: "warning",
            })
                .then(() => {
                    this.listLoading = true;
                    let para = { id: row.id };
                    removeUser(para).then((res) => {
                        this.listLoading = false;
                        let { msg, code } = res.data;
                        if (code !== 200) {
                            this.$message({
                                message: msg,
                                type: "warning",
                                duration: 5000
                            });
                        } else {
                            this.$message({
                                message: msg,
                                type: "success",
                                duration: 5000
                            });
                        }
                        this.getproinfo();
                        this.getversioninfo()
                        this.getmoduleinfo()
                    });
                })
                .catch(() => { });
        },
        //添加界面
        handleAdd: function (index, row) {
            // this.addFormVisible = true;

            this.$prompt("请Viper IP", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                // inputPattern: /[\w!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?/,
                inputPattern: /\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}?/,
                inputErrorMessage: "IP格式不正确",
            })
                .then(({ value }) => {
                    this.$message({
                        type: "success",
                        message: "IP是: " + value,
                    });
                    this.addViperHost = value;
                    this.handleAddEvent();
                })
                .catch(() => {
                    this.$message({
                        type: "info",
                        message: "取消输入",
                    });
                });
        },
        async handleAddEvent(index, row) {
            this.addForm.set_time = new Date();
            // this.addForm.sltFlagLst = ["os", "business", "connect", "play"];
            this.addForm.options = [];
            this.priority_value = row.priority;
            this.addForm.value = [row.project_id];
            this.addForm.options2 = [];
            this.addForm.value2 = [row.version_id];
            this.addForm.options3 = [];
            this.addForm.value3 = this.parseIdList(row.config);
            // this.addForm.value3 = [row.config];
            this.addForm.mark = row.mark_info;
            this.detailFormVisible = true;
            this.addForm.add_data = true;
            this.datevalue2 = "";
            this.runset_title = "运行测试集:" + row.title;
            this.pros_value = '';
            this.sent_email = 0;
            this.addForm.email_to = row.email_to;
            // this.addForm.email_to = "";
            this.addForm.config_id = row.id;
            this.rerun_type = 0

            await this.getproinfo();
            await this.getversioninfo()
            await this.getmoduleinfo()
        },

        async handleAddEvent_rerun(index, row, rerun_type) {
            this.addForm.set_time = new Date();
            // this.addForm.sltFlagLst = ["os", "business", "connect", "play"];
            this.addForm.options = [];
            this.priority_value = row.priority;
            this.addForm.value = [row.project_id];
            this.addForm.options2 = [];
            this.addForm.value2 = [row.version_id];
            this.addForm.options3 = [];
            this.addForm.value3 = this.parseIdList(row.config);
            // this.addForm.value3 = [row.config];
            this.addForm.mark = row.mark_info;
            this.detailFormVisible = true;
            this.addForm.add_data = true;
            this.datevalue2 = "";
            this.runset_title = "失败用例重试测试集:" + row.title;
            this.pros_value = '';
            this.sent_email = 0;
            this.addForm.email_to = row.email_to;
            // this.addForm.email_to = "";
            this.addForm.config_id = row.id;
            this.rerun_type = rerun_type
            await this.getproinfo();
            await this.getversioninfo()
            await this.getmoduleinfo()
        },
        async set_id(index, row) {
            this.addForm.config_id = row.id
            this.addForm.cfg = row.cfg
            this.addForm.config_name = row.cfg_name;
            this.detailFormVisible = true;
            await this.getproinfo();
            await this.getversioninfo()
            await this.getmoduleinfo()

        },
        //修改测试集用例
        async handleEditEvent(index, row) {
            this.isCreateSet = false;
            this.addForm.set_time = new Date();
            this.EditSetVisible = true;
            this.runset_title = "修改所属项目[" + row.project_name + "]测试集[" + row.title + "]";
            this.addForm.config_id = row.id;
            this.set_title = row.title;
            this.addForm.mark = row.mark_info;
            this.addForm.value = [row.project_id];
            this.priority_value = row.priority;
            // this.addForm.value3 = [row.config];
            this.addForm.value3 = this.parseIdList(row.config);
            this.addForm.value2 = [row.version_id];
            this.addForm.email_to = row.email_to;
            this.case_data = [];
            this.value4 = [];
            await this.getproinfo();
            await this.getConfigList();
            await this.getversioninfo()
            await this.getmoduleinfo()
            await this.loadTransferCases(row.project_id);
            let para2 = {
                page: this.page,
                page_size: this.page_size,
                cases_in: row.case_ids,
            };
            await get_cases_info(para2).then((res) => {
                this.CaseList = res.data.data;
                this.setcasetotal = res.data.data.length
                for (let i = 0; i < this.CaseList.length; i++) {
                    this.value4.push(
                        this.CaseList[i].id
                    )
                }


            });


        },
        //获取用例列表
        async GetCasesInfo() {
            this.ongoing = false;
            let para = {
                case_name: this.filters.cfg_name,
                page: this.page,
                page_size: this.page_size,
                project_id: this.projectIdFromValue(this.addForm.value),
                script_type: this.value
            };
            this.listLoading = true;
            await get_cases_info(para).then((res) => {
                this.aioLst = res.data.data;
                this.listLoading = false;
                this.total = res.data.data.length
            });
        },
        async add_set() {
            // this.ongoing = false;
            const projectId = this.isCreateSet ? this.createProjectId : this.projectIdFromValue(this.addForm.value);
            if (!projectId) {
                this.$message({
                    message: "请先选择关联脚本项目",
                    type: "warning",
                    duration: 5000
                });
                return;
            }
            let para = {
                case_ids: this.value4,
                testset_title: this.set_title,
                project_id: projectId,
                set_id: this.addForm.config_id,
                mark:this.addForm.mark,
                config_id: this.addForm.value3,
                version_id: this.addForm.value2[0],
                email_to: this.addForm.email_to,
                priority_value: this.priority_value,

            };
            this.listLoading = true;
            await add_testset(para).then((res) => {
                this.aioLst = res.data.data;
                let { msg, code } = res.data;
                this.listLoading = false;
                // this.total = res.data.length;
                if (code != 200) {
                    this.$message({
                        message: msg,
                        type: "warning",
                        duration: 5000
                    });
                } else {
                    //   this.serial = this.result.serial;
                    this.$message({
                        message: msg,
                        type: "success",
                        duration: 5000
                    });
                }
            });
            this.EditSetVisible = false;
            this.getConfigList()

        },
        addTitle(e) {
            // 手动给鼠标滑过的元素加一个title
            let target_el = e.target;
            if (target_el.title) return;
            target_el.title = target_el.innerText;
        },

        download(index, row) {
            this.htmlcontent = null
            let params = { filename: row.report, set_id: row.id }
            axios({
                method: 'POST',
                url: get_url() + '/report/report_content',
                // responseType: 'blob',
                data: params
            }).then(res => {
                const content = res.data
                this.htmlcontent = res.data
                const blob = new Blob([content])
                const fileName = row.report
                if (content.code == 404) {
                    this.$message(content.msg);
                    return false
                }
                if ('download' in document.createElement('a')) {
                    const elink = document.createElement('a')
                    elink.download = fileName
                    elink.style.display = 'none'
                    elink.href = URL.createObjectURL(blob)

                    // let url = 'data:text/html;charset=utf-8,' + encodeURIComponent(elink.href);
                    // window.open(url, '_blank');

                    document.body.appendChild(elink)
                    elink.click()
                    URL.revokeObjectURL(elink.href)
                    document.body.removeChild(elink)
                } else {
                    navigator.msSaveBlob(blob, fileName)
                }

                // window.open('data:text/html,' + encodeURIComponent(content), '_blank');

                // window.open(document.write(content));
                // let url = 'data:text/html;charset=utf-8,' + encodeURIComponent(this.htmlcontent);
                // window.open(url, '_blank');

            })

        },
        download_list(index, row) {
            this.htmlcontent = null
            let params = { filename: row.report_path }
            axios({
                method: 'POST',
                url: get_url() + '/report/report_content',
                // responseType: 'blob',
                data: params
            }).then(res => {
                const content = res.data
                this.htmlcontent = res.data
                const blob = new Blob([content])
                const fileName = row.report_path
                if (content.code == 404) {
                    this.$message(content.msg);
                    return false
                }
                if ('download' in document.createElement('a')) {
                    const elink = document.createElement('a')
                    elink.download = fileName
                    elink.style.display = 'none'
                    elink.href = URL.createObjectURL(blob)

                    // let url = 'data:text/html;charset=utf-8,' + encodeURIComponent(elink.href);
                    // window.open(url, '_blank');

                    document.body.appendChild(elink)
                    elink.click()
                    URL.revokeObjectURL(elink.href)
                    document.body.removeChild(elink)
                } else {
                    navigator.msSaveBlob(blob, fileName)
                }

                // window.open('data:text/html,' + encodeURIComponent(content), '_blank');

                // window.open(document.write(content));
                // let url = 'data:text/html;charset=utf-8,' + encodeURIComponent(this.htmlcontent);
                // window.open(url, '_blank');

            })

        },
        // openNewWindow() {
        //     // 调用后端接口获取HTML内容
        //     window.open('data:text/html,' + encodeURIComponent(this.htmlcontent), '_blank');
        // },

        get_html(index, row) {
            this.htmlcontent = null;
            let params = { filename: row.report, set_id: row.id }
            axios({
                method: 'POST',
                url: get_url() + '/report/report_content',
                // responseType: 'blob',
                data: params
            }).then(res => {
                this.htmlcontent = res.data
                if (this.htmlcontent.code == 404) {
                    this.$message(this.htmlcontent.msg);
                    return false
                }
                let newwindow = window.open("", "_blank");
                newwindow.document.write(this.htmlcontent);
            })

        },

        get_html_list(index, row) {
            this.htmlcontent = null
            let params = { filename: row.report_path }
            axios({
                method: 'POST',
                url: get_url() + '/report/report_content',
                // responseType: 'blob',
                data: params
            }).then(res => {
                this.htmlcontent = res.data
                if (this.htmlcontent.code == 404) {
                    this.$message(this.htmlcontent.msg);
                    return false
                }
                let newwindow = window.open("", "_blank");
                newwindow.document.write(this.htmlcontent);
            })

        },
        async delete_id_new(index, row) {
            this.$confirm("此操作将终止该测试集, 是否继续?", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            })
                .then(() => {
                    let para = {
                        ids: [row.id],
                    };

                    stop_testset(para).then((res) => {
                        this.listLoading = false;
                        let { msg, code } = res.data;
                        let set_titles = res.data.data;
                        this.getConfigList();

                        if (code != 200) {
                            this.$message({
                                message: msg,
                                type: "warning",
                                duration: 5000
                            });
                        } else {

                            this.$message({
                                message: "终止的测试集:" + set_titles,
                                type: "success",
                                duration: 5000
                            });

                        }

                    });

                })
                .catch(() => {
                    this.$message({
                        type: "info",
                        message: "已取消终止",
                    });
                });
        },

        async is_deletes(index, row) {
            this.$confirm("此操作将删除该测试集, 是否继续?", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            })
                .then(() => {
                    let para = {
                        ids: [row.id],
                    };

                    delete_testset(para).then((res) => {
                        this.listLoading = false;
                        let { msg, code } = res.data;
                        let set_titles = res.data.data;
                        this.getConfigList();

                        if (code != 200) {
                            this.$message({
                                message: msg,
                                type: "warning",
                                duration: 5000
                            });
                        } else {

                            this.$message({
                                message: "删除的测试集:" + set_titles,
                                type: "success",
                                duration: 5000
                            });

                        }

                    });

                })
                .catch(() => {
                    this.$message({
                        type: "info",
                        message: "已取消删除",
                    });
                });
        },

        async stop_set() {
            this.$confirm("此操作将终止所选测试集, 是否继续?", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            })
                .then(() => {
                    let para = {
                        ids: this.setids
                    };
                    stop_testset(para).then((res) => {
                        this.listLoading = false;
                        let { msg, code } = res.data;
                        let set_titles = res.data.data;

                        this.getConfigList();
                        if (code != 200) {
                            this.$message({
                                message: msg,
                                type: "warning",
                                duration: 5000
                            });
                        }
                        else {
                            this.$message({
                                message: "终止的测试集:" + set_titles,
                                type: "success",
                                duration: 5000
                            });

                        }

                    });

                })
                .catch(() => {
                    this.$message({
                        type: "info",
                        message: "已取消终止",
                    });
                });
        },

        //显示详情界面
        selsChange: function (sels) {
            this.sels = sels;
            this.setids = [];
            this.caseids = [];
            for (let item in this.sels) {
                this.setids.push(this.sels[item]["id"])
                this.caseids.push(this.sels[item]["id"])
            }

        },


        refreshViper_v2() {
            // var install_type = this.addForm.install_type;
            this.addForm.options = [];
            if (this.vipers) {
                var server_len = this.vipers.length;

                var cnt = 0;
                for (var i in this.vipers) {
                    cnt++;
                    this.addForm.options.push({
                        value: this.vipers[i]["id"],
                        label: this.vipers[i]["name"],
                    });
                }
            }
        },
        refreshViper_v3() {
            // var install_type = this.addForm.install_type;
            this.addForm.options2 = [];
            if (this.vipers2) {
                var server_len2 = this.vipers2.length;

                var cnt2 = 0;
                for (var i2 in this.vipers2) {
                    cnt2++;
                    this.addForm.options2.push({
                        value: this.vipers2[i2]["id"],
                        label: this.vipers2[i2]["version"],
                    });
                }
            }
        },

        refreshViper_v4() {
            // var install_type = this.addForm.install_type;
            this.addForm.options3 = [];
            if (this.vipers3) {
                var server_len3 = this.vipers3.length;

                var cnt3 = 0;
                for (var i3 in this.vipers3) {
                    cnt3++;
                    this.addForm.options3.push({
                        value: this.vipers3[i3]["id"],
                        label: this.vipers3[i3]["cfg_name"],
                    });
                }
            }
        },



        async getproinfo() {
            this.ongoing = false;
            let para = {
                page: 0,
                name: "",
                page_size: 1000

            };
            await get_project_info(para).then((res) => {
                this.vipers = res.data.data;
            });
            await this.refreshViper_v2();

        },
        async getversioninfo() {
            this.ongoing = false;
            let para = {
                page: 0,
                version: "",
                page_size: 1000

            };
            await get_version_info(para).then((res) => {
                this.vipers2 = res.data.data;

            });
            await this.refreshViper_v3();
        },
        async getmoduleinfo() {
            this.ongoing = false;
            let para = {
                page: 0,
                cfg_name: "",
                page_size: 1000

            };
            await get_config_info(para).then((res) => {
                this.vipers3 = res.data.data;

            });
            await this.refreshViper_v4();
        },
    },

    // startCountdown(futureTime) {
    //     const timerInterval = setInterval(() => {
    //         const now = new Date().getTime();
    //         const distance = futureTime - now;
    //         const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    //         const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    //         const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    //         const seconds = Math.floor((distance % (1000 * 60)) / 100);
    //         // 将计算结果更新到el-countdown组件的timer属性中  
    //         this.timer = { days, hours, minutes, seconds };
    //     }, 1000);
    // },




    mounted() {
        this.getConfigList();
        this.getproinfo();
        this.getversioninfo();
        this.getmoduleinfo();
        //定时任务开启
        this.start()
    },
    destroyed() {
        clearInterval(this.timer);
    },
};
</script>
    
<style scoped>
/* .len_input .el-cascader {
      width: 280px;
    } */

.packInput .el-input {
    width: 680px;
}

/* .el-cascader {
      width: 280px;
    } */
.el-table div.cell {
    white-space: pre-line;
}

.testset-main-cell {
    line-height: 1.6;
}

.testset-title {
    color: #2f86ff;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.testset-sub {
    color: #606266;
    font-size: 12px;
    line-height: 1.6;
}

.testset-status-cell {
    line-height: 1.8;
}

.testset-status-cell .el-progress {
    margin-top: 4px;
}

.pool-usage-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin: 8px 0 10px;
    padding: 10px 12px;
    border: 1px solid #e5e9f2;
    border-radius: 6px;
    background: #fff;
}

.pool-usage-main,
.pool-usage-detail {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #606266;
    font-size: 13px;
}

.pool-title {
    color: #1f2d3d;
    font-weight: 600;
}

.pool-capacity {
    color: #909399;
}

@media (max-width: 1200px) {
    .pool-usage-bar {
        align-items: flex-start;
        flex-direction: column;
    }
}

.compact-progress {
    width: 150px;
}
</style>
    
