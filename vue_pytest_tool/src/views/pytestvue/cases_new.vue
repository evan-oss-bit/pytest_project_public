<template>
    <section>
        <!--工具条-->
        <el-col :span="24" class="toolbar case-toolbar" style="padding-bottom: 0px">
            <el-form :inline="true" :model="filters" class="case-filter-form">
                <div class="case-filter-line">
                    <el-form-item>
                        <el-input v-model="filters.cfg_name" placeholder="用例名" clearable @change="get_config_info">
                            <i slot="prefix" class="el-input__icon el-icon-search"></i>
                        </el-input>
                    </el-form-item>
                    <el-form-item class="case-filter-project">
                        <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联脚本项目(也可输入项目搜索)"
                            separator="=>" v-model="addForm.value" :options="addForm.options" @change="getConfigList"
                            :props="{ expandTrigger: 'hover' }"></el-cascader>
                    </el-form-item>
                    <el-form-item class="case-filter-folder">
                        <el-cascader :filterable="true" :clearable="true" placeholder="文件夹过滤(须选择关联脚本项目)"
                            separator="=>" v-model="previous_level" :options="addForm.folders" @change="getConfigList"
                            :props="{ expandTrigger: 'hover' }"></el-cascader>
                    </el-form-item>
                    <el-form-item>
                        <el-select v-model="value" placeholder="请选择" class="case-type-select">
                            <el-option v-for="item in options" :key="item.value" :label="item.label" :value="item.value">
                            </el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" icon="el-icon-search" v-on:click="getConfigList">查询</el-button>
                    </el-form-item>
                </div>

                <div class="case-action-toolbar">
                    <div class="case-action-left">
                        <el-button @click="handleAddEvent" type="primary" icon="el-icon-refresh">扫描新增用例</el-button>
                        <el-button @click="handleAddEvent2" type="success" icon="el-icon-plus">添加到测试集</el-button>
                        <el-button type="primary" icon="el-icon-download"
                            @click="handleExport('', '#exportTab', { raw: true })">导出当前页</el-button>
                    </div>
                    <div class="case-action-right">
                        <label class="case-upload-picker">
                            <input type="file" @change="getFile($event)">
                            <span>{{ filename || "选择脚本文件" }}</span>
                        </label>
                        <el-button type="primary" icon="el-icon-upload" @click="submit($event)">上传</el-button>
                        <el-button @click="is_deletes_more" type="danger" icon="el-icon-delete">删除所选</el-button>
                    </div>
                </div>
            </el-form>
        </el-col>

        <!--列表-->
        <el-col :span="24" type="“flex”" style="white-space: pre">
            <el-table :data="aioLst" highlight-current-row stripe height="600" v-loading="listLoading" id="exportTab"
                @selection-change="selsChange" style="width: 100%" :cell-style="cellStyle3">
                <!-- <el-table-column type="selection" width="2">
                </el-table-column> -->
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in lstForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column>
                <el-table-column label="用例类型" width="80"><template slot-scope="scope">{{ scope.row.type | stateFmt
                }}</template></el-table-column>
                <el-table-column label="操作" width="190" fixed="right">
                    <template slot-scope="scope">
                        <div class="case-row-actions">
                            <el-button size="mini" type="primary" icon="el-icon-document"
                                @click="get_html(scope.$index, scope.row)">源码预览</el-button>
                            <el-dropdown trigger="click" @command="handleCaseCommand($event, scope.$index, scope.row)">
                                <el-button size="mini" plain>
                                    更多<i class="el-icon-arrow-down el-icon--right"></i>
                                </el-button>
                                <el-dropdown-menu slot="dropdown">
                                    <el-dropdown-item command="history" icon="el-icon-time">测试历史</el-dropdown-item>
                                    <el-dropdown-item command="editSource" icon="el-icon-edit-outline">编辑源码</el-dropdown-item>
                                    <el-dropdown-item command="remark" icon="el-icon-edit">备注</el-dropdown-item>
                                    <el-dropdown-item command="delete" icon="el-icon-delete" class="case-dropdown-danger">删除</el-dropdown-item>
                                </el-dropdown-menu>
                            </el-dropdown>
                        </div>
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
        <el-dialog title="扫描新增用例" :close-on-click-modal="false" :visible.sync="detailFormVisible">
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





                    <el-row>
                        <el-col :span="9">
                            <el-form-item label="关联脚本项目" class="len_input" required>
                                <div class="block" style="">
                                    <span class="demonstration"></span>
                                    <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联脚本项目(也可输入项目搜索)"
                                        separator="=>" v-model="addForm.value" :options="addForm.options" 
                                        :props="{ expandTrigger: 'hover' }"></el-cascader>
                                </div>
                            </el-form-item>
                        </el-col>
                        <el-col :span="9">
                        </el-col>
                    </el-row>
                    <!-- <el-row>
                        <el-col :span="9">
                            <el-form-item label="所属文件夹" class="len_input">
                                <div class="block" style="">
                                    <span class="demonstration"></span>
                                    <el-cascader :filterable="true" :clearable="true" :disabled="true"
                                        placeholder="" separator="=>" v-model="previous_level"
                                        :options="addForm.folders" :props="{ expandTrigger: 'hover' }"></el-cascader>
                                </div>
                            </el-form-item>
                        </el-col>
                        <el-col :span="9">
                        </el-col>
                    </el-row> -->
                    <el-row>
                        <el-col :span="9">
                            <el-form-item label="关联模块" class="len_input" required>
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
                        <el-form-item label="用例脚本类型" class="len_input" required>
                            <el-select v-model="value" placeholder="请选择">
                                <el-option v-for="item in options" :key="item.value" :label="item.label"
                                    :value="item.value">
                                </el-option>
                            </el-select></el-form-item>
                    </el-row>


                    <el-row>
                        <el-col :span="9">
                            <el-form-item label="关联版本号" class="len_input" required>
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
        <el-dialog :title="addForm.case_name" :close-on-click-modal="false" :visible.sync="datailVisible">
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


        <el-dialog :title="sourceEditorTitle" :close-on-click-modal="false" :visible.sync="sourceDialogVisible" width="90%">
            <el-input
                type="textarea"
                v-model="sourceEditorCode"
                :autosize="{ minRows: 24, maxRows: 36 }"
                spellcheck="false"
                class="source-editor-textarea">
            </el-input>
            <div slot="footer" class="dialog-footer">
                <el-button type="primary" :loading="sourceEditorLoading" @click="saveCaseSource">保存源码</el-button>
                <el-button @click.native="sourceDialogVisible = false">返回</el-button>
            </div>
        </el-dialog>
        <el-dialog :title="set_title" :visible.sync="caseinfo_dialogTableVisible">
            <el-col class="toolbar" height="600">
                <el-pagination layout="total" :total="setcasetotal" style="float: right">
                </el-pagination>
            </el-col>
            <el-button type="primary" @click="getCaseTestInfoList(1, test_row)">刷新当前页</el-button>
            <template>
                <el-table :data="count_info" style="width: 100%" :cell-style="cellStyle2">
                    <el-table-column prop="all_count" label="全部测试次数"></el-table-column>
                    <el-table-column prop="pass_count" label="通过测试次数"></el-table-column>
                    <el-table-column prop="pass_rate" label="用例通过率（%）"></el-table-column>
                    <el-table-column prop="fail_count" label="失败用例次数"></el-table-column>
                    <el-table-column prop="error_count" label="错误用例次数"></el-table-column>
                </el-table>
            </template>
            <!-- <el-col :span="24" type="“flex”" style="white-space: pre"> -->
                
            <el-table :data="CaseList" highlight-current-row stripe height="600" v-loading="listLoading" id="exportTab"
                @selection-change="selsChange" style="width: 100%" :cell-style="cellStyle">
                <!-- <el-table-column type="selection" width="2">
                </el-table-column> -->
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in caseinfo_form" :key="item.prop" :prop="item.prop" :label="item.label"
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
                <el-table-column label="日志" :with="150">
                    <template slot-scope="scope"><el-button-group>
                                
                                <el-button type="primary"
                                v-if="scope.row.file_name.length>1"
                                    @click="get_logsinfo(scope.$index, scope.row)">日志</el-button>
                            </el-button-group></template>
                            
                        </el-table-column>
                <!-- <el-table-column label="日志" width="120"><template slot-scope="scope">{{ scope.row.file_name | stateFmt
                }}</template></el-table-column> -->
                <el-table-column label="操作">
                    <template slot-scope="scope">
                        <el-row>
                            <!-- <el-button-group>
  
                    <el-button
                      type="primary"
                      @click="set_id(scope.$index, scope.row)"
                      >编辑</el-button
                    > -->
                            <!-- <el-button
                      type="danger"
                      @click="delete_id_new(scope.$index, scope.row)"
                      >删除</el-button
                    > -->
                            <!-- </el-button-group> -->
                        </el-row>

                    </template>

                </el-table-column>
            </el-table>
       
            <!-- </el-col> -->
        </el-dialog>



        <el-dialog :title="addForm.set_name" :close-on-click-modal="false" :visible.sync="detailFormVisible2">
            <el-form :model="addForm" label-width="150px" :rules="detailFormRules" ref="addForm">
                <el-col :span="24" style="margin-right: 100px">
                    <el-form-item label="测试集合名称">
                        <el-input type="textarea" v-model="addForm.testset_title"></el-input>
                    </el-form-item>
                </el-col>
                <el-col :span="9">
                    <el-form-item label="所属脚本项目" class="len_input" >
                        <div class="block" style="">
                            <span class="demonstration"></span>
                            <el-cascader :filterable="true" :clearable="true" placeholder="" :disabled="true"
                                separator="=>" v-model="addForm.value" :options="addForm.options"
                                :props="{ expandTrigger: 'hover' }"></el-cascader>
                        </div>
                    </el-form-item>
                </el-col>
                <el-col :span="9">
                </el-col>
                <el-col :span="9">
                    <el-form-item label="所属文件夹" class="len_input">
                        <div class="block" style="">
                            <span class="demonstration"></span>
                            <el-cascader :filterable="true" :clearable="true" :disabled="true"
                                placeholder="" separator="=>" v-model="previous_level"
                                :options="addForm.folders" :props="{ expandTrigger: 'hover' }"></el-cascader>
                        </div>
                    </el-form-item>
                </el-col>
                <el-col :span="9">
                </el-col>
            </el-form>
            <div slot="footer" class="dialog-footer">
                <el-button type="primary" :disabled="false" @click="add_set">提交
                </el-button>
                <el-button @click.native="detailFormVisible2 = false">返回</el-button>
            </div>
        </el-dialog>
    </section>
</template>
<style>
</style>    
<script>
import FileSaver from "file-saver";
import XLSX from "xlsx";
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
    case_review,
    update_case_source,
    get_cases_info,
    add_testset,
    case_upload,
    case_mark,
    get_caseresult_info,
    get_log_info,
    delete_cases,
} from "../../api/api";
import moment from "moment";
import Vue from "vue";
Vue.prototype.$moment = moment;

export default {
    data() {
        return {
            options: [{
                value: 1,
                label: 'pytest'
            }],
            
            previous_level:null,
            file: "",
            filename: "",
            value: 1,
            clean: false,
            ongoing: false,
            filters: {
                cfg_name: "",
            },
            install_type_lst: [],
            addViperHost: "",
            aioLst: [],
            page_size: 5000,
            total: 0,
            page: 0,
            test_row: null,
            addStatus: true,
            listLoading: false,
            sels: [], //列表选中列
            caseids: [],
            caseinfo_dialogTableVisible:false,
            detailFormVisible: false, //详情界面是否显示
            detailFormVisible2:false, //添加测试集详情页
            addFormVisible: false, //添加界面是否显示
            datailVisible: false,
            sourceDialogVisible: false,
            sourceEditorLoading: false,
            sourceEditorTitle: "编辑源码",
            sourceEditorCaseId: null,
            sourceEditorCode: "",
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
                folders: [],
                set_time: "",
                note: "",
                config_id: null,
                config_name: "",
                set_flag: true,
                remark: '',
                case_id: null,
                case_name: '',
                set_name:'快捷添加或修改测试集',
            },

            lstForm: [
                { prop: "id", label: "用例id", width: 80 },
                { prop: "title", label: "用例title(py文件::pytest测试类::pytest用例)", width: 200 },
                { prop: "case_name", label: "用例名(func.__doc__)", width: 200 },
                { prop: "project_name", label: "项目名称", width: 100 },
                { prop: "relative_path", label: "用例所在路径", width: 240 },
                 { prop: "previous_level", label: "所属文件夹", width: 100 },
                // { prop: "type", label: "用例类型", width: 80 },
                // { prop: "project_id", label: "项目id", width: 100 },
                // { prop: "version_id", label: "版本id", width: 100 },
                // { prop: "module_id", label: "模块id", width: 100 },
                { prop: "case_count", label: "用例条数", width: 60 },
                // { prop: "run_status", label: "运行状态", width: 100 },
                { prop: "remark", label: "备注", width: 120 },
                { prop: "created_time", label: "创建时间", width: 120 },
                { prop: "updated_time", label: "更新时间", width: 120 },
            ],
            caseinfo_form:[
                // { prop: "id", label: "结果id", width: 100 },
                // { prop: "case_title", label: "用例title(py文件::pytest测试类::pytest用例)", width: 200 },
                // { prop: "case_name", label: "用例名(func.__doc__)", width: 200 },
                { prop: "run_case_result", label: "测试结果", width: 100 },
                // { prop: "longrepr", label: "失败日志", width: 400 },
                // { prop: "project_name", label: "脚本项目", width: 100 },
                { prop: "duration", label: "用例耗时/s", width: 100 },
                // { prop: "run_id", label: "运行唯一id", width: 180 },
                
                // { prop: "set_id", label: "测试集id", width: 100 },
                // { prop: "config_id", label: "配置id", width: 90 },
                // { prop: "version_id", label: "版本id", width: 90 },
                { prop: "set_title", label: "测试集名称", width: 100 },
                // { prop: "cfg_name", label: "配置名称", width: 100 },
                { prop: "version", label: "版本号", width: 100 },
                { prop: "updated_time", label: "更新时间", width: 200 },
                // { prop: "file_name", label: "日志", width: 150 },
                

            ],
        };
    },
    filters: {
        stateFmt(state) {
            return (
                {
                    1: "pytest",
                    2: "函数式",
                }[state] || "其他"
            );
        },
    },

    methods: {
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
        handleCaseCommand(command, index, row) {
            if (command === "history") {
                this.getCaseTestInfoList(index, row);
            } else if (command === "editSource") {
                this.openSourceEditor(index, row);
            } else if (command === "remark") {
                this.case_remark(index, row);
            } else if (command === "delete") {
                this.is_deletes(index, row);
            }
        },

        //获取配置列表
        async getConfigList() {
            this.ongoing = false;
            let para = {
                case_name: this.filters.cfg_name,
                page: this.page,
                page_size: this.page_size,
                project_id: this.addForm.value[0],
                script_type: this.value,
                previous_level:this.previous_level,
            };
            this.listLoading = true;
            // if (this.addForm.value.length === 0){
            //     this.previous_level = null;
            // };
            // this.previous_level = null;
            // this.addForm.folders = null;
            await get_cases_info(para).then((res) => {
                this.aioLst = res.data.data;
                this.listLoading = false;
                this.total = res.data.data.length
                if (this.addForm.value[0] !==null){
                    this.addForm.folders = res.data.previous_levels;
                }
            });
        },

        async add_set() {
            // this.ongoing = false;
            let para = {
                case_ids: this.caseids,
                testset_title: this.addForm.testset_title,
                project_id: this.addForm.value,
                script_type: this.value,
                previous_level:this.previous_level,
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
                        duration: 8000
                    });
                } else {
                    //   this.serial = this.result.serial;
                    this.$message({
                        message: msg,
                        type: "success",
                        duration: 8000
                    });
                }
            });
            this.detailFormVisible2 = false;
            this.getConfigList()

        },

        cellStyle({ row, column, rowIndex, columnIndex }) {
            let cell_Style
            switch (row.run_case_result) {
                case 'passed':
                    cell_Style = 'color:#00FF00'
                    break;
                case 'failed':
                    cell_Style = 'color:#FF0000'
                    break;
                case 'error':
                    cell_Style = 'color:#FF0000'
                    break;
                default:
                    cell_Style = ''
                    break;
            }
            // 返回最终处理过的样式 这样写就是让全部行被style修饰
            return cell_Style

            //返回最终处理过的样式 只让测试结果这个属性的属性被style修饰
            // if (column.label == '测试结果') {
            //     return cell_Style
            // }
        },
        cellStyle3({ row, column, rowIndex, columnIndex }) {
            let cell_Style
            if (row.case_count >1) {
                cell_Style =  'color:#00FF00'
            }
            if (row.run_status =="error") {
                cell_Style =  'color:#FF0000'
            }
            // 返回最终处理过的样式 这样写就是让全部行被style修饰
            return cell_Style

            //返回最终处理过的样式 只让测试结果这个属性的属性被style修饰
            // if (column.label == '测试结果') {
            //     return cell_Style
            // }
        },
        cellStyle2({ row, column, rowIndex, columnIndex }) {
            let cell_Style
            // switch (row.run_case_result) {
            //     case 'passed':
            //         cell_Style = 'color:#00FF00'
            //         break;
            //     case 'failed':
            //         cell_Style = 'color:#FF0000'
            //         break;
            //     case 'error':
            //         cell_Style = 'color:#FF0000'
            //         break;
            //     default:
            //         cell_Style = ''
            //         break;
            // }
            // 返回最终处理过的样式 这样写就是让全部行被style修饰
            // return cell_Style

            //返回最终处理过的样式 只让测试结果这个属性的属性被style修饰
            if (column.label == '通过测试次数') {
                return 'color:#00FF00'
            }
            if (column.label == '用例通过率（%）') {
                return 'color:blue'
            }
            if (column.label == '失败用例次数') {
                return 'color:#FF0000'
            }
            if (column.label == '错误用例次数') {
                return 'color:#FF0000'
            }
            if (column.label == '全部测试次数') {
                return 'color:blue'
            }
        },
        alertMsg(msg) {
            this.continue_flag = false;
            this.$message({
                message: msg,
                type: "warning",
            });
        },
        get_logsinfo(index, row) {
            this.htmlcontent = null
            let params = { file_name: row.file_name }
            get_log_info(params).then(res => {
                this.htmlcontent = res.data
                if (this.htmlcontent.code == 404) {
                    this.$message(this.htmlcontent.msg);
                    return false
                }
                let newwindow = window.open("", "_blank");
                newwindow.document.write(this.htmlcontent);
                newwindow.document.close();
            })

        },
        //获取用例测试结果信息
        async getCaseTestInfoList(index, row) {
            this.CaseList = null;
            this.count_info = [];
            this.setcasetotal = null;
            this.caseinfo_dialogTableVisible = true
            this.ongoing = false;
            this.test_row = row;
            this.set_title = "用例[" + row.case_name + "]的测试结果历史";
            let para = {
                page: this.page,
                page_size: 999999999,
                case_id: row.id
            };
            this.listLoading = true;
            await get_caseresult_info(para).then((res) => {
                this.CaseList = res.data.data;
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
                // if (this.addForm.value3 == null) {
                //     this.addForm.value3 = []
                // }
                // if (this.addForm.value2 == null) {
                //     this.addForm.value2 = []
                // }
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
        getExportTime() {
            return this.$moment ? this.$moment().format("YYYYMMDD_HHmmss") : this.FormatTime("yyyyMMdd_HHmmss");
        },
        normalizeExportPart(value) {
            return String(value || "")
                .trim()
                .replace(/[\\/:*?"<>|\s]+/g, "_")
                .replace(/^_+|_+$/g, "");
        },
        buildExportFileName(fileName = "") {
            let parts = [fileName || "用例脚本列表"];
            if (this.filters.cfg_name) {
                parts.push(this.filters.cfg_name);
            }
            if (this.previous_level) {
                parts.push(Array.isArray(this.previous_level) ? this.previous_level.join("_") : this.previous_level);
            }
            parts.push(this.getExportTime());
            return parts.map(this.normalizeExportPart).filter(Boolean).join("_");
        },
        //fileName 导出文件名；idName 导出table的id；xlsxParam 导出配置
        handleExport(fileName = '', idName = "#exportTab", xlsxParam = { raw: true }) {
            // let xlsxParam = { raw: true }; // 导出的内容只做解析，不进行格式转换
            let wb = XLSX.utils.table_to_book(
                document.querySelector(idName),
                xlsxParam
            );
            let wbout = XLSX.write(wb, {
                bookType: "xlsx",
                bookSST: true,
                type: "array",
            });
            try {
                FileSaver.saveAs(
                    new Blob([wbout], { type: "application/octet-stream" }),
                    `${this.buildExportFileName(fileName)}.xlsx`
                );
            } catch (e) {
                if (typeof console !== "undefined") {
                }
            }
            return wbout;
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
        get_html(index, row) {
            this.htmlcontent = null
            let params = { id: row.id }
            let newwindow = window.open("", "_blank");
            if (newwindow) {
                newwindow.document.write("<div style='padding:16px;font-family:Arial'>源码加载中...</div>");
            }
            case_review(params).then(res => {
                this.htmlcontent = res.data
                if (this.htmlcontent.code == 404) {
                    this.$message(this.htmlcontent.msg);
                    if (newwindow) {
                        newwindow.close();
                    }
                    return false
                }
                if (!newwindow) {
                    this.$message({ message: "浏览器拦截了源码预览弹窗，请允许弹窗后重试", type: "warning" });
                    return false;
                }
                newwindow.document.open();
                newwindow.document.write(this.htmlcontent);
                newwindow.document.close();
            }).catch(() => {
                if (newwindow) {
                    newwindow.close();
                }
                this.$message({ message: "源码预览加载失败", type: "error" });
            })

        },
        extractSourceCode(html) {
            let doc = new DOMParser().parseFromString(html, "text/html");
            let codeNode = doc.querySelector("code.language-python") || doc.querySelector("code");
            return codeNode ? codeNode.textContent : "";
        },
        openSourceEditor(index, row) {
            this.sourceEditorCaseId = row.id;
            this.sourceEditorTitle = "编辑源码：" + (row.title || row.relative_path || row.id);
            this.sourceEditorCode = "";
            this.sourceDialogVisible = true;
            this.sourceEditorLoading = true;
            case_review({ id: row.id }).then(res => {
                this.sourceEditorLoading = false;
                if (res.data && res.data.code && res.data.code !== 200) {
                    this.$message({ message: res.data.msg || "源码读取失败", type: "warning" });
                    this.sourceDialogVisible = false;
                    return false;
                }
                this.sourceEditorCode = this.extractSourceCode(res.data);
            }).catch(() => {
                this.sourceEditorLoading = false;
                this.$message({ message: "源码读取失败", type: "error" });
                this.sourceDialogVisible = false;
            });
        },
        saveCaseSource() {
            if (!this.sourceEditorCaseId) {
                this.$message({ message: "缺少用例 id", type: "warning" });
                return false;
            }
            this.sourceEditorLoading = true;
            update_case_source({
                id: this.sourceEditorCaseId,
                source_code: this.sourceEditorCode,
            }).then(res => {
                this.sourceEditorLoading = false;
                let { msg, code } = res.data;
                if (code !== 200) {
                    this.$message({ message: msg, type: "warning" });
                    return false;
                }
                this.$message({ message: msg, type: "success" });
                this.sourceDialogVisible = false;
                this.getConfigList();
            }).catch(() => {
                this.sourceEditorLoading = false;
                this.$message({ message: "源码保存失败", type: "error" });
            });
        },
        async case_remark(index, row) {
            this.addForm.case_name = "用例名(func.__doc__):"+row.case_name
            this.addForm.case_id = row.id
            this.addForm.remark = row.remark
            this.datailVisible = true;
            await this.getproinfo();

        },
        async mark() {
            let para = {
                id: this.addForm.case_id,
                remark: this.addForm.remark
            };
            await case_mark(para).then((res) => {
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
            this.datailVisible = false;
            this.getConfigList();
        },
        async is_deletes_more() {
            this.$confirm("此操作将删除该测试用例, 是否继续?", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            })
                .then(() => {
                    if (this.caseids.length === 0) {
                            this.$message({
                                message: "没有选择用例",
                                type: "warning",
                                duration: 3000
                            });
                        } else {    
                    let para = {
                        ids: this.caseids,
                    };
                    delete_cases(para).then((res) => {
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
                                message: "删除的测试用例:" + set_titles,
                                type: "success",
                                duration: 5000
                            });

                        }

                    });

                }})
                .catch(() => {
                    this.$message({
                        type: "info",
                        message: "已取消删除",
                    });
                });
        },
        //删除
        async is_deletes(index, row) {
            this.$confirm("此操作将删除该测试用例, 是否继续?", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            })
                .then(() => {
                    let para = {
                        ids: [row.id],
                    };

                    delete_cases(para).then((res) => {
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
                                message: "删除的测试用例:" + set_titles,
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

            this.$prompt("请输入新增或者修改的测试集名称", "提示", {
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
        async handleAddEvent2() {
            this.detailFormVisible2 = true;
            this.addForm.testset_title = null;
            // this.addForm.add_data = true;
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
                        label: this.vipers3[i3]["module"],
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
        // 手动文件上传
        getFile(event) {
            this.file = event.target.files[0];
            this.filename = this.file ? this.file.name : "";
        },
        async submit(param) {
            let upData = new FormData();
            upData.append("file", this.file); //传文件
            upData.append('project_id', this.addForm.value[0]);
            if (!this.addForm.value[0]) {
                this.$message({
                    message: "没有选择上传的测试脚本项目",
                    type: "warning",
                })
                return false;
            }
            if (!this.file) {
                this.$message({
                    message: "请上传test_开头的py文件类型",
                    type: "warning",
                })
                return false;
            }
            await case_upload(upData).then((res) => {
                let { msg, code } = res.data;
                this.listLoading = false;
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
                module: "",
                page_size: 1000

            };
            await get_module_info(para).then((res) => {
                this.vipers3 = res.data.data;

            });
            await this.refreshViper_v4();
        },
    },





    mounted() {
        this.getConfigList();
        this.getproinfo();
        this.getversioninfo();
        this.getmoduleinfo();
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

.case-toolbar {
    padding: 12px 12px 10px;
    background: #fff;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    margin-bottom: 12px;
}

.case-filter-form {
    width: 100%;
}

.case-filter-line,
.case-action-toolbar,
.case-action-left,
.case-action-right,
.case-row-actions {
    display: flex;
    align-items: center;
}

.case-filter-line,
.case-action-toolbar {
    flex-wrap: wrap;
    gap: 8px;
}

.case-action-toolbar {
    justify-content: space-between;
    padding-top: 4px;
}

.case-action-left,
.case-action-right,
.case-row-actions {
    gap: 8px;
}

.case-filter-form /deep/ .el-form-item {
    margin-bottom: 10px;
}

.case-filter-project /deep/ .el-cascader {
    width: 300px;
}

.case-filter-folder /deep/ .el-cascader {
    width: 260px;
}

.case-type-select {
    width: 110px;
}

.case-upload-picker {
    display: inline-flex;
    align-items: center;
    max-width: 220px;
    height: 32px;
    padding: 0 12px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    color: #606266;
    background: #f8fafc;
    cursor: pointer;
    overflow: hidden;
}

.case-upload-picker input {
    display: none;
}

.case-upload-picker span {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.case-row-actions {
    justify-content: center;
}

.case-dropdown-danger {
    color: #f56c6c;
}

.packInput .el-input {
    width: 680px;
}

/* .el-cascader {
      width: 280px;
    } */
.el-table div.cell {
    white-space: pre-line;
}
.source-editor-textarea /deep/ textarea {
    font-family: Consolas, "Courier New", monospace;
    font-size: 14px;
    line-height: 1.5;
    white-space: pre;
}</style>
    











