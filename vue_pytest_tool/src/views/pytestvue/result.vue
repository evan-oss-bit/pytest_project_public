<template>
    <section>
        <!--工具条-->
        <el-col :span="24" class="toolbar" style="padding-bottom: 0px">
            <el-form :inline="true" :model="filters">
                <el-col :span="20" justify="">
                    <el-row>
                        <el-col :span="9">
                            <el-form-item label="" class="len_input">
                                <div class="block" style="">
                                    <span class="demonstration"></span>
                                    <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联测试集(也可输入测试集搜索)"
                                        separator="=>" v-model="addForm.value" :options="addForm.options" @change="getConfigList"
                                        :props="{ expandTrigger: 'hover' }"></el-cascader>
                                </div>
                            </el-form-item>
                        </el-col>
                        <el-col :span="9">
                        </el-col>
                    </el-row>
                    <el-form-item>
                        <el-input v-model="filters.run_id" placeholder="运行测试集或任务的id" clearable @change="getConfigList">
                            <i slot="prefix" class="el-input__icon el-icon-search"></i>
                        </el-input>
                    </el-form-item>
                    <el-select v-model="value2" clearable placeholder="请选择"  @change="getConfigList">
                        <el-option v-for="item in options2" :key="item.value2" :label="item.label" :value="item.value2">
                        </el-option>
                    </el-select>
                    <el-form-item class="block">
    <!-- <span class="demonstration">带快捷选项</span> -->
    <el-date-picker
      v-model="time_value1"
      type="datetimerange"
      :picker-options="pickerOptions"
      range-separator="至"
      start-placeholder="开始日期"
      end-placeholder="结束日期"
      value-format = "yyyy-MM-dd HH:mm:ss"
       @change="getConfigList"> 
    </el-date-picker>
  </el-form-item>
                    <el-form-item>
                        <el-input v-model="filters.cfg_name" placeholder="用例名" clearable @change="getConfigList">
                            <i slot="prefix" class="el-input__icon el-icon-search"></i>
                        </el-input>
                    </el-form-item>



                    <el-form-item>
                        <el-button type="primary" icon="el-icon-search" v-on:click="getConfigList">查询</el-button>
                    </el-form-item>

                    <el-button type="primary" @click="handleExport('导出', '#exportTab', { raw: true })">导出当前页面数据</el-button>

                    <template>
                        <el-table :data="count_info" style="width: 100%" :cell-style="cellStyle2">
                            <el-table-column prop="all_count" label="全部用例数"></el-table-column>
                            <el-table-column prop="pass_count" label="通过用例数"></el-table-column>
                            <el-table-column prop="pass_rate" label="用例通过率（%）"></el-table-column>
                            <el-table-column prop="fail_count" label="失败用例数"></el-table-column>
                            <el-table-column prop="error_count" label="错误用例数"></el-table-column>
                        </el-table>
                    </template>

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
            <el-table :data="aioLst" highlight-current-row stripe height="600" v-loading="listLoading" id="exportTab"
                @selection-change="selsChange" style="width: 100%" :cell-style="cellStyle">
                <!-- <el-table-column type="selection" width="2">
                </el-table-column> -->
                <el-table-column type="selection" width="55"> </el-table-column>
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
                    <el-table-column label="操作">
                    <template slot-scope="scope">
                        <el-row>
                            <el-dropdown split-button type="primary" @click="get_html(scope.$index, scope.row)"
                                trigger="click">
                                日志
                                <el-dropdown-menu slot="dropdown">
                                    <el-button-group class="button-container">
                                        <el-button type="primary" icon="el-icon-search"
                                    @click="get_html2(scope.$index, scope.row)">用例源码</el-button>
                                    </el-button-group>
                                </el-dropdown-menu>
                            </el-dropdown>
                        </el-row>
                    </template>

                </el-table-column>
                <!-- <el-table-column label="日志" width="120"><template slot-scope="scope">{{ scope.row.file_name | stateFmt
                }}</template></el-table-column> -->
                <!-- <el-table-column label="操作">
                    <template slot-scope="scope">
                        <el-row> -->
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
                        <!-- </el-row>

                    </template>

                </el-table-column> -->
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
    </section>
</template>
    
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
    get_cases_info,
    add_testset,
    get_caseresult_info,
    get_testset_info,
    get_log_info,
    case_review,
} from "../../api/api";
import moment from "moment";
import Vue from "vue";
Vue.prototype.$moment = moment;

export default {
    data() {
        return {
            time_value1:"",
            pickerOptions: {
          shortcuts: [{
            text: '最近一天',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 1);
              picker.$emit('pick', [start, end]);
            }
          },{
            text: '最近三天',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 3);
              picker.$emit('pick', [start, end]);
            }
          },{
            text: '最近一周',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
              picker.$emit('pick', [start, end]);
            }
          }, {
            text: '最近一个月',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
              picker.$emit('pick', [start, end]);
            }
          }, {
            text: '最近三个月',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
              picker.$emit('pick', [start, end]);
            }
          },{
            text: '最近六个月',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 180);
              picker.$emit('pick', [start, end]);
            }
          }, {
            text: '最近一年',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 365);
              picker.$emit('pick', [start, end]);
            }
          }]
        },
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
            count_info: [],
            page_size: 1000,
            total: 0,
            page: 0,
            addStatus: true,
            listLoading: false,
            sels: [], //列表选中列
            caseids: [],
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
            },

            lstForm: [
                { prop: "id", label: "结果id", width: 100 },
                { prop: "case_title", label: "用例title(py文件::pytest测试类::pytest用例)", width: 200 },
                { prop: "case_name", label: "用例名(func.__doc__)", width: 200 },
                { prop: "run_case_result", label: "测试结果", width: 100 },
                // { prop: "longrepr", label: "失败日志", width: 400 },
                { prop: "project_name", label: "脚本项目", width: 100 },
                { prop: "duration", label: "用例耗时/s", width: 100 },
                { prop: "run_id", label: "运行唯一id", width: 180 },
                { prop: "updated_time", label: "更新时间", width: 180 },
                // { prop: "set_id", label: "测试集id", width: 100 },
                // { prop: "config_id", label: "配置id", width: 90 },
                // { prop: "version_id", label: "版本id", width: 90 },
                { prop: "set_title", label: "测试集名称", width: 100 },
                // { prop: "cfg_name", label: "配置名称", width: 100 },
                { prop: "version", label: "版本号", width: 100 },
                // { prop: "file_name", label: "日志", width: 150 },
                

            ],
        };
    },
    methods: {
        start() {
            this.timer = setInterval(this.valChange, 10000); // 注意: 第一个参数为方法名的时候不要加括号;
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
        get_html(index, row) {
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
        get_html2(index, row) {
            this.htmlcontent = null
            let params = { id: row.case_id }
            case_review(params).then(res => {
                this.htmlcontent = res.data
                if (this.htmlcontent.code == 404) {
                    this.$message(this.htmlcontent.msg);
                    return false
                }
                let newwindow = window.open("", "_blank");
                newwindow.document.write(this.htmlcontent);
            })

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
            // return cell_Style

            //返回最终处理过的样式 只让测试结果这个属性的属性被style修饰
            if (column.label == '测试结果') {
                return cell_Style
            }
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
            if (column.label == '通过用例数') {
                return 'color:#00FF00'
            }
            if (column.label == '用例通过率（%）') {
                return 'color:blue'
            }
            if (column.label == '失败用例数') {
                return 'color:#FF0000'
            }
            if (column.label == '错误用例数') {
                return 'color:#FF0000'
            }
            if (column.label == '全部用例数') {
                return 'color:blue'
            }
        },
        //获取配置列表
        async getConfigList() {
            this.ongoing = false;
            let page_siz = this.page_size;
            if(this.filters.cfg_name == false && this.value2 == false && this.filters.run_id == null && this.addForm.value == false && this.time_value1 == false){
                page_siz = 100
            };
            let para = {
                case_name: this.filters.cfg_name,
                run_case_result: this.value2,
                run_id: this.filters.run_id,
                page: this.page,
                page_size: page_siz,
                set_id: this.addForm.value[0],
                time_value: this.time_value1,

            };
            this.listLoading = true;
            await get_caseresult_info(para).then((res) => {
                this.aioLst = res.data.data;
                this.count_info = [];
                if (res.data.count !== null) {
                    this.count_info = [res.data.count];
                }
                this.listLoading = false;
                this.total = res.data.data.length
            });
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
                    `${fileName}用例执行结果.xlsx`
                );
            } catch (e) {
                if (typeof console !== "undefined") {
                }
            }
            return wbout;
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
</style>
    
