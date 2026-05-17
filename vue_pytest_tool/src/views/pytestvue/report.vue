<template>
    <section>
        <!--工具条-->
        <el-col :span="24" class="toolbar" style="padding-bottom: 0px">
            <el-form :inline="true" :model="filters">
                <el-row>
                    <el-col :span="9">
                        <el-form-item label="" class="len_input">
                            <div class="block" style="">
                                <span class="demonstration"></span>
                                <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联项目(也可输入项目搜索)"
                                    separator="=>" v-model="addForm.value3" :options="addForm.options3"
                                    :props="{ expandTrigger: 'hover' }"></el-cascader>
                            </div>
                        </el-form-item>
                    </el-col>
                    <el-col :span="9">
                    </el-col>
                </el-row>
                <el-col :span="20" justify="">
                    <el-row>
                        <el-col :span="9">
                            <el-form-item label="" class="len_input">
                                <div class="block" style="">
                                    <span class="demonstration"></span>
                                    <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联测试集(也可输入测试集搜索)"
                                        separator="=>" v-model="addForm.value" :options="addForm.options"
                                        :props="{ expandTrigger: 'hover' }"></el-cascader>
                                </div>
                            </el-form-item>
                        </el-col>
                        <el-col :span="9">
                        </el-col>
                    </el-row>
                    <!-- <el-form-item>
                        <el-input v-model="filters.run_id" placeholder="运行测试集所产生的唯一id" clearable @change="get_config_info">
                            <i slot="prefix" class="el-input__icon el-icon-search"></i>
                        </el-input>
                    </el-form-item>
                    <el-select v-model="value2" clearable placeholder="请选择">
                        <el-option v-for="item in options2" :key="item.value2" :label="item.label" :value="item.value2">
                        </el-option>
                    </el-select> -->
                    <el-form-item>
                        <el-input v-model="filters.cfg_name" clearable placeholder="测试报告名">
                            <i slot="prefix" class="el-input__icon el-icon-search"></i>
                        </el-input>
                    </el-form-item>



                    <el-form-item>
                        <el-button type="primary" icon="el-icon-search" v-on:click="getConfigList">查询</el-button>
                    </el-form-item>

                    <!-- <div>
                        <el-form-item>
                            <el-button @click="handleAddEvent" type="primary"
                                style="float: right; text-align: right; margin-left: 10px">扫描新增用例</el-button>
                        </el-form-item>
                        <el-button @click="handleAdd()" type="primary" style="margin-left: 100px">快捷添加修改用例到测试集</el-button>

                    </div> -->
                </el-col>
            </el-form>
        </el-col>

        <!--列表-->
        <el-col :span="24" type="“flex”" style="white-space: pre">
            <el-table :data="aioLst" highlight-current-row stripe height="600" v-loading="listLoading"
                @selection-change="selsChange" @row-click="openReportDrawer" style="width: 100%" :cell-style="cellStyle2">
                <!-- <el-table-column type="selection" width="2">
                </el-table-column> -->
                <!-- <el-table-column type="selection" width="55"> </el-table-column> -->
                <el-table-column width="55"> </el-table-column>
                <el-table-column v-for="item in lstForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column>
                <el-table-column label="配置名称">
                        <template slot-scope="scope">
                        <el-tag
                            v-for="tag in scope.row.cfg_name"
                            :key="tag"
                            type="primary"
                            style="margin-right: 4px;">
                            {{ tag }}
                        </el-tag>
                        </template>
                    </el-table-column>
                <el-table-column label="结果摘要" min-width="300">
                    <template slot-scope="scope">
                        <div class="report-summary">
                            <div class="report-summary-head">
                                <el-tag size="mini" :type="reportStatusType(scope.row)">
                                    {{ reportStatusText(scope.row) }}
                                </el-tag>
                                <span class="report-summary-run">run_id: {{ scope.row.run_id || '-' }}</span>
                            </div>
                            <el-progress
                                :percentage="passRateNumber(scope.row)"
                                :status="scope.row.fail_count > 0 || scope.row.error_count > 0 ? 'exception' : 'success'"
                                :stroke-width="12">
                            </el-progress>
                            <div class="report-summary-tags">
                                <el-tag size="mini" type="info">全部 {{ scope.row.all_count || 0 }}</el-tag>
                                <el-tag size="mini" type="success">通过 {{ scope.row.pass_count || 0 }}</el-tag>
                                <el-tag size="mini" :type="scope.row.fail_count > 0 ? 'danger' : 'info'">失败 {{ scope.row.fail_count || 0 }}</el-tag>
                                <el-tag size="mini" :type="scope.row.error_count > 0 ? 'danger' : 'info'">错误 {{ scope.row.error_count || 0 }}</el-tag>
                                <span class="report-summary-time">耗时 {{ scope.row.case_all_time || 0 }}s</span>
                            </div>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="100" fixed="right">
                    <template slot-scope="scope">
                        <el-button type="text" icon="el-icon-document" @click.stop="openReportDrawer(scope.row)">详情</el-button>
                        <el-row v-if="false">
                            <el-dropdown split-button type="primary"
                            @click="get_html(scope.$index, scope.row)" trigger="click">查看在线报告
                            <el-dropdown-menu slot="dropdown">
                            <el-button-group class="button-container">
                                <el-button type="primary" icon="el-icon-share"
                                    @click="download(scope.$index, scope.row)">下载报告</el-button>
                                    <el-button type="primary" icon="el-icon-edit"
                                    @click="send_email(scope.$index, scope.row)">发送邮件</el-button>
                                    <el-button type="primary" icon="el-icon-edit"
                                    @click="report_remark(scope.$index, scope.row)">备注</el-button>
                                    <el-button type="primary" icon="el-icon-document"
                                    @click="openReportDrawer(scope.row)">详情</el-button>
                            </el-button-group>
                        </el-dropdown-menu>
                    </el-dropdown>
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


        <!-- <el-button @click="handleAdd()" type="primary" style="margin-left: 100px">添加</el-button> -->



        <!--详情界面-->
        <!-- <el-dialog title="详情" v-model="detailFormVisible" :close-on-click-modal="false"> -->
        <el-drawer
            title="报告详情"
            :visible.sync="reportDrawerVisible"
            direction="rtl"
            size="42%"
            custom-class="report-detail-drawer">
            <div class="report-detail" v-if="selectedReport">
                <div class="report-detail-title">
                    <div>
                        <h3>{{ selectedReport.title }}</h3>
                        <p>{{ selectedReport.project_name || '-' }} / {{ selectedReport.set_title || '-' }}</p>
                    </div>
                    <el-tag :type="reportStatusType(selectedReport)">{{ reportStatusText(selectedReport) }}</el-tag>
                </div>
                <div class="report-detail-actions">
                    <el-button type="primary" icon="el-icon-view" size="mini" @click="get_html(0, selectedReport)">预览报告</el-button>
                    <el-button type="primary" icon="el-icon-download" size="mini" @click="download(0, selectedReport)">下载</el-button>
                    <el-button type="primary" icon="el-icon-message" size="mini" @click="send_email(0, selectedReport)">发送邮件</el-button>
                    <el-button icon="el-icon-edit" size="mini" @click="report_remark(0, selectedReport)">备注</el-button>
                </div>
                <div class="report-detail-section">
                    <div class="report-detail-section-title">执行结果</div>
                    <el-progress
                        :percentage="passRateNumber(selectedReport)"
                        :status="selectedReport.fail_count > 0 || selectedReport.error_count > 0 ? 'exception' : 'success'"
                        :stroke-width="14">
                    </el-progress>
                    <div class="report-detail-metrics">
                        <div><span>全部</span><strong>{{ selectedReport.all_count || 0 }}</strong></div>
                        <div><span>通过</span><strong class="metric-pass">{{ selectedReport.pass_count || 0 }}</strong></div>
                        <div><span>失败</span><strong class="metric-fail">{{ selectedReport.fail_count || 0 }}</strong></div>
                        <div><span>错误</span><strong class="metric-error">{{ selectedReport.error_count || 0 }}</strong></div>
                        <div><span>耗时/s</span><strong>{{ selectedReport.case_all_time || 0 }}</strong></div>
                    </div>
                </div>
                <div class="report-detail-section">
                    <div class="report-detail-section-title">基础信息</div>
                    <div class="report-detail-info">
                        <div><span>运行ID</span><strong>{{ selectedReport.run_id || '-' }}</strong></div>
                        <div><span>报告时间</span><strong>{{ selectedReport.updated_time || '-' }}</strong></div>
                        <div><span>报告文件</span><strong>{{ selectedReport.report_path || '-' }}</strong></div>
                        <div><span>备注</span><strong>{{ selectedReport.mark || '-' }}</strong></div>
                    </div>
                </div>
                <div class="report-detail-section">
                    <div class="report-detail-section-title">配置</div>
                    <div class="report-detail-tags">
                        <el-tag v-for="tag in selectedReport.cfg_name" :key="tag" size="mini" type="primary">{{ tag }}</el-tag>
                        <span v-if="!selectedReport.cfg_name || selectedReport.cfg_name.length === 0" class="report-detail-muted">无配置</span>
                    </div>
                    <pre class="report-detail-code">{{ reportConfigText(selectedReport) }}</pre>
                </div>
            </div>
        </el-drawer>

        <el-dialog title="新建模块" :close-on-click-modal="false" :visible.sync="detailFormVisible">
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





                    <!-- <el-row>
                        <el-col :span="9">
                            <el-form-item label="关联项目" class="len_input">
                                <div class="block" style="">
                                    <span class="demonstration"></span>
                                    <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联项目(也可输入项目搜索)"
                                        separator="=>" v-model="addForm.value" :options="addForm.options"
                                        :props="{ expandTrigger: 'hover' }"></el-cascader>
                                </div>
                            </el-form-item>
                        </el-col>
                        <el-col :span="9">
                        </el-col>
                    </el-row> -->

                    <!-- <el-row>
                        <el-col :span="9">
                            <el-form-item label="关联模块" class="len_input">
                                <div class="block" style="">
                                    <span class="demonstration"></span>
                                    <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联模块(也可输入项目搜索)"
                                        separator="=>" v-model="addForm.value3" :options="addForm.options3"
                                        :props="{ expandTrigger: 'hover' }"></el-cascader>
                                </div>
                            </el-form-item>
                        </el-col>
                        <el-col :span="9">
                        </el-col>
                    </el-row>
                    <el-row :span="9">
                        <el-form-item label="用例脚本类型" class="len_input">
                            <el-select v-model="value" placeholder="请选择">
                                <el-option v-for="item in options" :key="item.value" :label="item.label"
                                    :value="item.value">
                                </el-option>
                            </el-select></el-form-item>
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
                    </el-row> -->

                    <el-form-item label="备注信息">
                        <el-input type="textarea" v-model="addForm.cfg"></el-input>
                    </el-form-item>
                </el-col>
            </el-form>
            <div slot="footer" class="dialog-footer">
                <el-button type="primary" :disabled="false" @click="AIOOIA">提交
                </el-button>
                <el-button @click.native="detailFormVisible = false">返回</el-button>
            </div>
        </el-dialog>
        <el-dialog :title="addForm.report_name" :close-on-click-modal="false" :visible.sync="datailVisible">
            <el-form :model="addForm" label-width="150px" :rules="detailFormRules" ref="addForm">
                <el-col :span="24" style="margin-right: 100px">
                    <el-form-item label="备注信息">
                        <el-input type="textarea" v-model="addForm.remark"></el-input>
                    </el-form-item>
                </el-col>
            </el-form>
            <div slot="footer" class="dialog-footer">
                <el-button type="primary" :disabled="false" @click="mark">提交
                </el-button>
                <el-button @click.native="datailVisible = false">返回</el-button>
            </div>
        </el-dialog>

        <el-dialog :title="addForm.email_name" :close-on-click-modal="false" :visible.sync="sendemail_datailVisible">
            <el-form :model="addForm" label-width="150px" :rules="detailFormRules" ref="addForm">
                <el-col :span="24" style="margin-right: 100px">
                    <el-form-item label="邮件标题">
                        <el-input placeholder="邮件标题，不输入则使用默认标题" type="input" v-model="addForm.email_title"></el-input>
                    </el-form-item>
                    <el-form-item label="邮件地址">
                        <el-input placeholder="输入邮件地址即可发送邮件，多个邮件间请用;来区分" type="input" v-model="addForm.email_to"></el-input>
                    </el-form-item>
                </el-col>
            </el-form>
            <div slot="footer" class="dialog-footer">
                <el-button type="primary" :disabled="false" @click="email">提交
                </el-button>
                <el-button @click.native="sendemail_datailVisible = false">返回</el-button>
            </div>
        </el-dialog>
    </section>
</template>
    
<script>
import axios from "axios";
import {
    DeleteConfig,
    get_config_info,
    update_config,
    add_config,
    get_project_info,
    get_version_info,
    get_module_info,
    add_module,
    update_module,
    add_case,
    get_cases_info,
    add_testset,
    get_caseresult_info,
    get_testset_info,
    get_report_info,
    get_url,
    report_mark,
    send_email_a
} from "../../api/api";
import moment from "moment";
import Vue from "vue";
Vue.prototype.$moment = moment;

export default {
    data() {
        return {
            htmlcontent: null,
            options2: [{
                value2: 'passed',
                label: 'passed'
            }, {
                value2: 'failed',
                label: 'failed'
            }, {
                value2: 'error',
                label: 'error'
            }],
            value2: '',
            timer: "",
            options: [{
                value: 1,
                label: 'pytest'
            }],
            value: 1,
            clean: false,
            ongoing: false,
            filters: {
                cfg_name: "",
                run_id: null,
            },
            install_type_lst: [],
            addViperHost: "",
            aioLst: [],
            page_size: 1000,
            total: 0,
            page: 0,
            addStatus: true,
            listLoading: false,
            datailVisible: false,
            reportDrawerVisible: false,
            selectedReport: null,
            sels: [], //列表选中列
            caseids: [],
            sendemail_datailVisible: false,
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
                add_data: true,
                anaFlag: false,
                bdaFlag: false,
                nodeFlag: false,
                cfg: "",
                node_randio: 1,
                auth: false,
                testset_title: "",
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
                report_name:"",
                remark:"",
                report_id:"",
                report_path:"",
                email_title:"",
                email_to:"",
                project_name:"",
                set_title:""
            },

            lstForm: [
                // { prop: "id", label: "报告id", width: 100 },
                // { prop: "config_id", label: "配置id", width: 100 },
                { prop: "project_name", label: "脚本项目", width: 120 },
                //{ prop: "set_id", label: "测试集id", width: 80 },
                // { prop: "set_title", label: "测试集名称", width: 120 },
                // { prop: "cfg_name", label: "配置名称", width: 120 },
                { prop: "title", label: "测试报告名（项目名_测试集名_运行id）", width: 200 },
                { prop: "mark", label: "备注", width: 100 },
                { prop: "updated_time", label: "更新时间", width: 140 },

            ],
        };
    },
    methods: {
        openReportDrawer(row) {
            this.selectedReport = row;
            this.reportDrawerVisible = true;
        },
        reportConfigText(row) {
            if (!row) {
                return "";
            }
            const names = row.cfg_name && row.cfg_name.length ? row.cfg_name.join(" / ") : "无配置";
            return "配置ID: " + (row.config_id || "-") + "\n配置名称: " + names;
        },
        passRateNumber(row) {
            const value = Number(row.pass_rate || 0);
            if (Number.isNaN(value)) {
                return 0;
            }
            return Math.max(0, Math.min(100, Number(value.toFixed(2))));
        },
        reportStatusType(row) {
            if (row.error_count > 0 || row.fail_count > 0) {
                return "danger";
            }
            return "success";
        },
        reportStatusText(row) {
            if (row.error_count > 0) {
                return "错误";
            }
            if (row.fail_count > 0) {
                return "失败";
            }
            return "通过";
        },
        start() {
            this.timer = setInterval(this.valChange, 8000); // 注意: 第一个参数为方法名的时候不要加括号;
        },
        valChange() {
            this.getConfigList();

            // let para_1 = {
            //     page: this.page,
            //     page_size: this.page_size,
            // }
            // get_caseresult_info(para_1)
        },
        selectBlur(e) {
            Vue.set(this.addForm, "viper_version", e.target.value);
        },
        radioChangeEvt() {
            if (this.addForm.node_randio % 2 != 0) {
                this.addForm.aIp = "";
            }
        },
        handleCurrentChange(val) {
            this.page = val;
            this.getConfigList();
        },
        cellStyle2({ row, column, rowIndex, columnIndex }) {

            //返回最终处理过的样式 只让测试结果这个属性的属性被style修饰
            if (column.label == '通过用例数') {
                return 'color:#00FF00'
            }
            if (column.label == '用例通过率（%）') {
                return 'color:blue'
            }
            if (column.label == '失败用例数' && row.fail_count > 0) {
                return 'color:#FF0000'
            }
            if (column.label == '错误用例数'&& row.error_count > 0) {
                return 'color:#FF0000'
            }
            if (column.label == '全部用例数') {
                return 'color:blue'
            }
        },
        //获取配置列表
        async getConfigList() {
            this.ongoing = false;
            let para = {
                title: this.filters.cfg_name,
                page: this.page,
                page_size: this.page_size-900,
                set_id: this.addForm.value[0],
                project_id:this.addForm.value3[0]
            };
            this.listLoading = true;
            await get_report_info(para).then((res) => {
                this.aioLst = res.data.data;
                this.listLoading = false;
                this.total = res.data.data.length
            });
        },

        async add_set() {
            // this.ongoing = false;
            let para = {
                case_ids: this.caseids,
                testset_title: this.addForm.testset_title

            };
            this.listLoading = true;
            await add_testset(para).then((res) => {
                this.aioLst = res.data.data;
                let { msg, code } = res.data;
                this.listLoading = false;
                this.total = res.data.data.length;
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
            this.getConfigList()

        },
        async send_email(index, row) {
            this.addForm.email_name = "测试报告名:"+row.title
            this.addForm.report_id = row.id
            this.addForm.remark = row.mark
            this.addForm.report_path = row.report_path
            this.sendemail_datailVisible = true;
            this.addForm.email_title = "",
            this.addForm.email_to = "",
            this.addForm.project_name = row.project_name,
            this.addForm.set_title = row.set_title,
            await this.getproinfo();

        },

        async email() {
            if (this.addForm.email_to === "") {
                    this.$message({
                        message: "请输入邮箱地址！",
                        type: "warning",
                        duration: 3000
                    });
                    return
                }
            let para = {
                email_title: this.addForm.email_title,
                email_to: this.addForm.email_to,
                report_path: this.addForm.report_path,
                project_name: this.addForm.project_name,
                set_title: this.addForm.set_title
            };
            await send_email_a(para).then((res) => {
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
            });
            this.sendemail_datailVisible = false;
            this.getConfigList();
        },
        async report_remark(index, row) {
            this.addForm.report_name = "测试报告名:"+row.title
            this.addForm.report_id = row.id
            this.addForm.remark = row.mark
            this.datailVisible = true;
            await this.getproinfo();

        },
           async mark() {
            let para = {
                id: this.addForm.report_id,
                mark: this.addForm.remark
            };
            await report_mark(para).then((res) => {
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
            });
            this.datailVisible = false;
            this.getConfigList();
        },
        async mark() {
            let para = {
                id: this.addForm.report_id,
                mark: this.addForm.remark
            };
            await report_mark(para).then((res) => {
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
            });
            this.datailVisible = false;
            this.getConfigList();
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
                let para = {
                    module: this.addForm.config_name,
                    description: this.addForm.cfg,
                    project_id: this.addForm.value[0],
                    version_id: this.addForm.value2[0],
                    module_id: this.addForm.value3[0],
                    id: this.addForm.config_id,
                    script_type: this.value
                };


                await add_case(para).then((res) => {
                    this.listLoading = false;
                    let { msg, code } = res.data;
                    if (code !== 200) {
                        this.$message({
                            message: msg,
                            type: "warning",
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
                            });
                        } else {
                            this.$message({
                                message: msg,
                                type: "success",
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

            this.$prompt("请输入测试集名称", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                // inputPattern: /[\w!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?/,
                // inputPattern: /\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}?/,
                // inputErrorMessage: "IP格式不正确",
            })
                .then(({ value }) => {
                    // this.$message({
                    //     type: "info",
                    //     message: "测试集合名称是: " + value,
                    // });
                    this.addForm.testset_title = value;
                    this.add_set();
                    this.getConfigList()

                })
                .catch(() => {
                    this.$message({
                        type: "info",
                        message: "取消输入",
                    });
                });

        },
        async handleAddEvent() {
            this.addForm.set_time = new Date();
            this.addForm.sltFlagLst = ["os", "business", "connect", "play"];
            this.addForm.options = [];
            this.addForm.value = null;
            this.addForm.options2 = [];
            this.addForm.value2 = null;
            this.addForm.options3 = [];
            this.addForm.value3 = null;
            this.detailFormVisible = true;
            this.addForm.add_data = true;
            // this.addForm.testset_title = "";
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


        async delete_id_new(index, row) {
            this.$confirm("此操作将永久删除该配置, 是否继续?", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            })
                .then(() => {
                    let para = {
                        config_id: row.config_id,
                    };

                    DeleteConfig(para).then((res) => {
                        this.listLoading = false;
                        let { msg, code } = res.data;
                        this.getConfigList();

                        if (code != 200) {
                            this.$message({
                                message: msg,
                                type: "warning",
                            });
                        } else {

                            this.$message({
                                message: msg,
                                type: "success",
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

        //显示详情界面
        selsChange: function (sels) {
            this.sels = sels;
            this.caseids = [];
            for (let caseid in this.sels) {
                this.caseids.push(this.sels[caseid]["id"])
            }

        },
        download(index, row) {
            this.htmlcontent = null
            let params = { filename: row.report_path }
            axios({
                method: 'POST',
                url: get_url() + '/testset/report_content',
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
        get_html(index, row) {
            this.htmlcontent = null
            let params = { filename: row.report_path }
            axios({
                method: 'POST',
                url: get_url() + '/testset/report_content',
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
                        label: this.vipers[i]["title"],
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
                        label: this.vipers3[i3]["name"],
                    });
                }
            }
        },

        // async handleAddEvent() {
        //     this.addFormVisible = false;
        //     let para = {
        //         sc_host: this.sc_host,
        //     };
        //     this.listLoading = true;
        //     await InsertScHost(para).then((res) => { });
        //     this.getViper();
        //     this.listLoading = false;
        // },

        async getproinfo() {
            this.ongoing = false;
            let para = {
                page: 0,
                page_size: 1000

            };
            await get_testset_info(para).then((res) => {
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
        async getprojectinfo() {
            this.ongoing = false;
            let para = {
                page: 0,
                module: "",
                page_size: 1000

            };
            await get_project_info(para).then((res) => {
                this.vipers3 = res.data.data;

            });
            await this.refreshViper_v4();
        },
    },





    mounted() {
        this.getConfigList();
        this.getproinfo();
        this.getversioninfo();
        this.getprojectinfo();
        //暂时屏蔽定时任务start函数获取测试结果
        // this.start()
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

.report-summary {
    min-width: 280px;
}

.report-summary-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 8px;
}

.report-summary-run {
    color: #909399;
    font-size: 12px;
}

.report-summary-tags {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin-top: 8px;
}

.report-summary-time {
    color: #606266;
    font-size: 12px;
}

.report-detail {
    padding: 0 20px 24px;
}

.report-detail-title {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
}

.report-detail-title h3 {
    margin: 0 0 6px;
    color: #303133;
    font-size: 18px;
    line-height: 1.4;
    word-break: break-word;
}

.report-detail-title p {
    margin: 0;
    color: #909399;
    font-size: 13px;
}

.report-detail-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
}

.report-detail-section {
    margin-bottom: 18px;
    padding: 12px;
    background: #ffffff;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
}

.report-detail-section-title {
    margin-bottom: 10px;
    color: #303133;
    font-weight: 700;
}

.report-detail-metrics {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 8px;
    margin-top: 12px;
}

.report-detail-metrics div,
.report-detail-info div {
    padding: 8px;
    background: #f8fafc;
    border: 1px solid #ebeef5;
    border-radius: 4px;
}

.report-detail-metrics span,
.report-detail-info span {
    display: block;
    color: #909399;
    font-size: 12px;
}

.report-detail-metrics strong,
.report-detail-info strong {
    display: block;
    margin-top: 4px;
    color: #303133;
    word-break: break-word;
}

.metric-pass {
    color: #67c23a !important;
}

.metric-fail,
.metric-error {
    color: #f56c6c !important;
}

.report-detail-info {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
}

.report-detail-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 8px;
}

.report-detail-muted {
    color: #909399;
    font-size: 12px;
}

.report-detail-code {
    max-height: 160px;
    margin: 0;
    padding: 8px;
    overflow: auto;
    color: #303133;
    background: #f8fafc;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
}
</style>
    
