<template>
  <section class="config-page">
    <!--工具条-->
    <el-col :span="24" class="config-toolbar">
      <el-form :inline="true" :model="filters" class="config-filter-form">
        <el-col :span="24" class="config-filter-row">
          <!-- <el-form-item class="len_input">
                        <div class="block" style="">
                            <span class="demonstration"></span>
                            <el-cascader :filterable="true" :clearable="true" :disabled="false"
                                placeholder="请选择关联脚本项目(也可输入项目搜索)" separator="=>" v-model="addForm.value"
                                :options="addForm.options" :props="{ expandTrigger: 'hover' }"></el-cascader>
                        </div>
                    </el-form-item> -->
          <el-form-item>
            <el-input v-model="filters.cfg_name" placeholder="配置名称" clearable class="config-search-input">
              <i slot="prefix" class="el-input__icon el-icon-search"></i>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="el-icon-search" v-on:click="getConfigList">查询</el-button>
          </el-form-item>
          <el-form-item class="config-create-action">
            <el-button @click="handleAddEvent" type="primary" icon="el-icon-plus">新建配置</el-button>
          </el-form-item>
        </el-col>
      </el-form>
    </el-col>

    <!--列表-->
    <el-col :span="24" class="config-list-panel">
      <el-table :data="aioLst" highlight-current-row stripe height="650" v-loading="listLoading"
        @selection-change="selsChange" style="width: 100%" class="config-table">
        <!-- <el-table-column type="selection" width="2">
              </el-table-column> -->
        <el-table-column type="expand">
          <template slot-scope="scope">
            <div class="config-expand">
              <div class="config-expand-title">完整配置</div>
              <pre class="config-json-view">{{ formatCfgPretty(scope.row.cfg) }}</pre>
              <div class="config-expand-title">备注</div>
              <div class="config-mark-view">{{ scope.row.mark || "暂无备注" }}</div>
              <el-button type="text" icon="el-icon-view" @click="openJsonPreview(scope.row)">查看完整 JSON</el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column type="index" label="#" width="55"> </el-table-column>
        <el-table-column label="配置名称" width="230" sortable prop="cfg_name">
          <template slot-scope="scope">
            <div class="config-name-cell">
              <div class="config-name">{{ scope.row.cfg_name }}</div>
              <div class="config-id">ID: {{ scope.row.id }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="配置内容" min-width="520">
          <template slot-scope="scope">
            <div class="config-summary">
              <div
                v-for="section in getConfigSections(scope.row.cfg)"
                :key="section.name"
                class="config-section-card">
                <div class="config-section-title">{{ section.name }}</div>
                <div class="config-kv-list">
                  <span
                    v-for="item in section.items"
                    :key="section.name + item.key"
                    class="config-kv-chip">
                    <span class="config-kv-key">{{ item.key }}</span>
                    <span class="config-kv-value">{{ item.value }}</span>
                  </span>
                  <span v-if="section.moreCount > 0" class="config-more-chip">还有 {{ section.moreCount }} 项</span>
                </div>
              </div>
              <div v-if="getConfigSections(scope.row.cfg).length === 0" class="config-empty">暂无配置项</div>
              <div class="config-count">共 {{ getConfigPairCount(scope.row.cfg) }} 个参数，展开行可查看完整 JSON</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="180">
          <template slot-scope="scope">
            <span class="config-mark">{{ scope.row.mark || "暂无备注" }}</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="210">
          <template slot-scope="scope">
            <div class="config-time">
              <div><span>创建：</span>{{ scope.row.created_time }}</div>
              <div><span>更新：</span>{{ scope.row.updated_time }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template slot-scope="scope">
            <el-row class="config-actions">
              <el-dropdown split-button type="primary" @click="set_id(scope.$index, scope.row)" trigger="click">编辑配置
                <el-dropdown-menu slot="dropdown">
                  <el-button-group class="button-container">
                    <el-button type="primary" icon="el-icon-view" @click="openJsonPreview(scope.row)">查看完整 JSON</el-button>
                    <el-button type="primary" icon="el-icon-share" @click="union_testset(scope.$index, scope.row)">关联测试集</el-button>
                    <el-button type="danger" icon="el-icon-delete" @click="is_deletes_config(scope.$index, scope.row)">删除</el-button>
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


    <el-dialog :title="jsonPreviewTitle" :visible.sync="jsonPreviewVisible" width="78%" top="5vh">
      <div class="json-preview-dialog">
        <div class="json-preview-meta">
          <span>配置名：{{ jsonPreviewRow.cfg_name || "未知" }}</span>
          <span>ID：{{ jsonPreviewRow.id || "-" }}</span>
          <span>参数数：{{ getConfigPairCount(jsonPreviewRow.cfg) }}</span>
        </div>
        <pre class="config-json-view config-json-dialog-view">{{ formatCfgPretty(jsonPreviewRow.cfg) }}</pre>
        <div class="json-preview-mark">
          <strong>备注：</strong>{{ jsonPreviewRow.mark || "暂无备注" }}
        </div>
      </div>
      <div slot="footer" class="dialog-footer">
        <el-button type="primary" @click.native="jsonPreviewVisible = false">关闭</el-button>
      </div>
    </el-dialog>
    <el-dialog :title="config_title" :visible.sync="setdialogTableVisible">
            <el-col class="toolbar" height="600">
                <el-pagination layout="total" :total="setcasetotal" style="float: right">
                </el-pagination>
            </el-col>
            <el-table :data="UnionTestSetList" highlight-current-row stripe height="400" v-loading="listLoading" id="exportTab"
                @selection-change="selsChange" style="width: 100%">
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in UnionTestSetForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column>

                <!-- <el-table-column label="用例类型" width="120"><template slot-scope="scope">{{ scope.row.type | testFmt
                }}</template></el-table-column> -->
                <el-table-column label="操作" width="300">
                    <!-- <template slot-scope="scope">
                        <el-row>
                            <el-button-group>
                                <el-button type="primary" icon="el-icon-share"
                                    @click="get_html_list(scope.$index, scope.row)">查看在线报告</el-button>
                                <el-button type="primary" icon="el-icon-share"
                                    @click="download_list(scope.$index, scope.row)">下载报告</el-button>
                            </el-button-group>
                        </el-row>

                    </template> -->

                </el-table-column>
            </el-table>
        </el-dialog>


    <!--详情界面-->
    <!-- <el-dialog title="详情" v-model="detailFormVisible" :close-on-click-modal="false"> -->
    <el-dialog :title="configEditTitle" :close-on-click-modal="false" :visible.sync="detailFormVisible" width="1180px" top="4vh" class="config-edit-dialog">
      <el-form :model="addForm" label-width="110px" :rules="detailFormRules" ref="addForm">
        <div class="config-edit-tip">配置会写入测试项目下的 data.ini 文件，左侧维护 key/value，右侧实时预览最终 JSON。</div>
        <div class="config-edit-layout">
          <div class="config-edit-form">
          <div class="config-edit-section-title">基础信息</div>
          <el-row>
            <el-col :span="24">
              <el-form-item label="配置名称" required>
                <el-input ref="inputName" v-model="addForm.config_name" auto-complete="off" placeholder="配置名称"
                  autofocus="true" clearable></el-input>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- <el-row>
            <el-col :span="24">
              <el-form-item label="关联脚本项目" class="len_input" required>
                <div class="block" style="">
                  <span class="demonstration"></span>
                  <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联脚本项目(也可输入项目搜索)" separator="=>"
                    v-model="addForm.value" :options="addForm.options" :props="{ expandTrigger: 'hover' }"></el-cascader>
                </div>
              </el-form-item>
            </el-col>

            <el-col :span="24">

            </el-col>
          </el-row> -->

          <el-row>
            <el-col :span="24">
              <el-form-item label="配置最高层级key值:" required>
                <el-input ref="inputName" v-model="addForm.config_key" auto-complete="off" placeholder="配置最高层级key值"
                  autofocus="true" clearable></el-input>
              </el-form-item>
            </el-col>
          </el-row>

          <div class="config-edit-section-title">参数配置</div>
          <el-form-item label="扩展参数:" required>
            <div class="config-param-toolbar">
              <span>参数明细</span>
              <el-button size="mini" type="primary" plain icon="el-icon-plus" @click="addExtraInput">添加一行</el-button>
              <el-popover
                  placement="top-start"
                  title=""
                  width="500"
                  trigger="hover">
                <el-alert
                    title="key-value的json键值对,例如:{'key':'value'}"
                    type="info"
                    :closable="false">
                  <template slot='title'>
              <!--这里面是对不同场景下扩展参数的自定义说明-->
                  </template>
                </el-alert>
                <i slot="reference" style="margin-left: 5px" class="el-icon-info"></i>
              </el-popover>
            </div>
            <div v-if="extraList && extraList.length > 0" class="config-param-list">
              <div v-for="(item,index) in extraList" :key="index" class="config-param-row">
                <div class="config-param-index">{{ index + 1 }}</div>
                <el-input v-model="item.key" placeholder="key" class="config-param-input"></el-input>
                <el-input v-model="item.value" placeholder="value" class="config-param-input"></el-input>
                <el-button size="mini" type="text" icon="el-icon-delete" class="config-param-delete"
                          @click="delExtraInput(index)">删除
                </el-button>
              </div>
            </div>
            <div v-else class="config-param-empty">暂无扩展参数，点击“添加一行”开始维护。</div>
          </el-form-item>
          <el-form-item label="备注">
            <el-input type="textarea" v-model="addForm.mark" placeholder="备注信息" :disabled="false"></el-input>
          </el-form-item>
          </div>
          <div class="config-edit-preview">
            <div class="config-preview-header">
              <span>JSON 预览</span>
              <el-tag size="mini" type="info">{{ extraList.length }} 项参数</el-tag>
            </div>
            <pre class="config-json-view config-edit-json-view">{{ buildEditCfgPretty() }}</pre>
          </div>
        </div>
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
import {
  DeleteConfig,
  get_config_info,
  update_config,
  add_config,
  get_project_info,
  union_set,
  deletes_config
} from "../../api/api";
import moment from "moment";
import Vue from "vue";
Vue.prototype.$moment = moment;

export default {
  data() {
    return {
      clean: false,
      ongoing: false,
      filters: {
        cfg_name: "",
      },
      install_type_lst: [],
      addViperHost: "",
      aioLst: [],
      extraList: [],
      page_size: 500,
      total: 0,
      page: 0,
      addStatus: true,
      listLoading: false,
      jsonPreviewVisible:false,
      jsonPreviewTitle:"完整 JSON",
      jsonPreviewRow:{},
      set_title:"",
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
      config_title:"",
      UnionTestSetList:[],
      setcasetotal:null,
      setdialogTableVisible:false,
      addForm: {
        add_data: true,
        anaFlag: false,
        bdaFlag: false,
        nodeFlag: false,
        cfg: "",
        node_randio: 1,
        auth: false,
        mark:"",
        value: [],
        options: [],
        set_time: "",
        note: "",
        config_id: null,
        config_name: "",
        config_key: "",
        set_flag: true,
      },
      UnionTestSetForm:[
                // { prop: "id", label: "id", width: 60 },
                { prop: "title", label: "测试集名称", width: 400 },
                { prop: "project_name", label: "脚本项目", width: 180 },
                // { prop: "run_id", label: "最新运行id", width: 145 },
                { prop: "previous_level", label: "所属文件夹", width: 80 },
                // { prop: "version_id", label: "版本id", width: 100 },
                // { prop: "case_ids", label: "测试集内用例id", width: 160 },
                // { prop: "run_status", label: "运行状态", width: 120 },
                // { prop: "schedule", label: "测试进度（%）", width: 80 },
                // { prop: "updated_time", label: "更新时间", width: 170 },
                // { prop: "run_type", label: "运行方式", width: 80 },
                // { prop: "timed_task_time", label: "定时任务开启时间", width: 140 }
                
            ],
      lstForm: [
        // { prop: "id", label: "配置id", width: 100 },
        { prop: "cfg_name", label: "配置名称", width: 130 },
        { prop: "cfg", label: "配置信息", width: 700 },
        // { prop: "project_id", label: "脚本项目id", width: 130 },
        // { prop: "project_name", label: "脚本项目名", width: 130 },
        { prop: "mark", label: "备注", width: 185 },
        { prop: "created_time", label: "创建时间", width: 180 },
        { prop: "updated_time", label: "更新时间", width: 180 },
        
      ],
    };
  },
  computed: {
    configEditTitle() {
      return this.addForm && this.addForm.config_id ? "编辑配置项" : "新建配置项";
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
    /** 添加一行键值对 */
    addExtraInput() {
      this.extraList.push({ 'key': '', 'value': '' });
    },

    /** 根据数组索引删除一行键值对 */
    delExtraInput(index) {
      this.extraList.splice(index, 1);
    },

    /** 将参数列表提取出来 转换为对象形式 */
    extraListToData() {
      let extraList = this.extraList
      if (!extraList || extraList.length < 1) {
        return {}
      }
      let extraData = {}
      for (let item of extraList) {
        let key = item.key
        let value = item.value
        if (key && value) {
          extraData[key] = value
        }
      }
      return extraData
    },
    str_to_listdata(jsonString){
      let jsonString1 = this.parseCfg(jsonString)
      if (Object.keys(jsonString1).length === 0) {
        this.addForm.config_key = "";
        return [];
      }
      this.addForm.config_key = Object.keys(jsonString1)[0];
      const keyValueArray = [];
      let cfg_key = this.addForm.config_key
      let cfgValue = jsonString1[cfg_key] || {};
      Object.entries(cfgValue).forEach(([key, value]) => { keyValueArray.push({key: key, value: value}); });
      return keyValueArray;
    },
    parseCfg(cfg) {
      if (!cfg) {
        return {};
      }
      if (typeof cfg === "object") {
        return cfg;
      }
      try {
        return JSON.parse(cfg);
      } catch (error) {
        try {
          return JSON.parse(String(cfg).replace(/'/g, '"'));
        } catch (e) {
          return {};
        }
      }
    },
    openJsonPreview(row) {
      this.jsonPreviewRow = row || {};
      this.jsonPreviewTitle = "完整 JSON：" + (row && row.cfg_name ? row.cfg_name : "");
      this.jsonPreviewVisible = true;
    },
    getConfigTopKeys(cfg) {
      return Object.keys(this.parseCfg(cfg)).slice(0, 4);
    },
    getConfigSections(cfg) {
      const data = this.parseCfg(cfg);
      return Object.keys(data).slice(0, 3).map((sectionName) => {
        const section = data[sectionName];
        let entries = [];
        if (section && typeof section === "object" && !Array.isArray(section)) {
          entries = Object.keys(section).map((key) => ({
            key: key,
            value: this.formatConfigValue(section[key]),
          }));
        } else {
          entries = [{
            key: sectionName,
            value: this.formatConfigValue(section),
          }];
        }
        return {
          name: sectionName,
          items: entries.slice(0, 6),
          moreCount: Math.max(entries.length - 6, 0),
        };
      });
    },
    formatConfigValue(value) {
      if (value === null || value === undefined || value === "") {
        return "空";
      }
      if (typeof value === "object") {
        return JSON.stringify(value);
      }
      return String(value);
    },
    getConfigPairCount(cfg) {
      const data = this.parseCfg(cfg);
      let count = 0;
      Object.keys(data).forEach((sectionName) => {
        const section = data[sectionName];
        if (section && typeof section === "object" && !Array.isArray(section)) {
          count += Object.keys(section).length;
        } else {
          count += 1;
        }
      });
      return count;
    },
    formatCfgPreview(cfg) {
      const data = this.parseCfg(cfg);
      const fragments = [];
      Object.keys(data).some((sectionName) => {
        const section = data[sectionName];
        if (section && typeof section === "object" && !Array.isArray(section)) {
          Object.keys(section).some((key) => {
            fragments.push(sectionName + "." + key + "=" + section[key]);
            return fragments.length >= 4;
          });
        } else {
          fragments.push(sectionName + "=" + section);
        }
        return fragments.length >= 4;
      });
      return fragments.length ? fragments.join("；") : "暂无可预览的配置内容";
    },
    formatCfgPretty(cfg) {
      const data = this.parseCfg(cfg);
      if (Object.keys(data).length === 0) {
        return cfg || "暂无配置";
      }
      return JSON.stringify(data, null, 2);
    },

    buildEditCfgPretty() {
      const key = this.addForm.config_key || "section";
      const data = {};
      data[key] = this.extraListToData();
      return JSON.stringify(data, null, 2);
    },
    //获取配置列表
    async getConfigList() {
      this.ongoing = false;
      let para = {
        // project_id:this.addForm.value[0],
        cfg_name: this.filters.cfg_name,
        page: this.page,
        page_size: this.page_size,
      };
      this.listLoading = true;
      await get_config_info(para).then((res) => {
        this.aioLst = res.data.data;
        this.listLoading = false;
        this.total = res.data.data.length;
        // for (let i = 0; i < this.aioLst.length; i++) {
        //     this.aioLst[i].cfg = JSON.parse(this.aioLst[i].cfg)
            
        //   }
      });
    },
    alertMsg(msg) {
      this.continue_flag = false;
      this.$message({
        message: msg,
        type: "warning",
      });
    },
    async union_testset(index, row){
            this.UnionTestSetList = null;
            this.count_info = [];
            this.setcasetotal = null;
            this.setdialogTableVisible = true
            this.ongoing = false;
            this.test_row = row;
            this.config_title = "配置名[" + row.cfg_name + "]关联的测试集结果";
            let para = {
                config_id: row.id
            };
            this.listLoading = true;
            await union_set(para).then((res) => {
                this.UnionTestSetList = res.data.data;
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
        let cfg_new = this.extraListToData();
        let new_json = {} 
        if (this.addForm.config_key == "") {
            this.$message({
              message: "最高层级key不能为空",
              type: "warning",
            });
            return
          }
        new_json[this.addForm.config_key]=cfg_new
        let para = {
          cfg_name: this.addForm.config_name,
          // cfg: this.addForm.cfg,
          // project_id: this.addForm.value[0],
          // project_id: this.addForm.value,
          id: this.addForm.config_id,
          extra_data:this.extraList,
          cfg:new_json,
          mark:this.addForm.mark,
        };


        await add_config(para).then((res) => {
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
    async handleAddEvent() {
      this.addForm.set_time = new Date();
      this.addForm.sltFlagLst = ["os", "business", "connect", "play"];
      this.addForm.options = [];
      this.addForm.value = null;
      this.detailFormVisible = true;
      this.addForm.add_data = true;
      this.addForm.config_id = null;
      this.addForm.cfg = null;
      this.addForm.config_name = null;
      this.addForm.config_key = "";
      this.addForm.mark = "";
      this.extraList = [];
      await this.getproinfo();
    },
    async set_id(index, row) {
      this.addForm.config_id = row.id
      this.addForm.cfg = row.cfg
      this.addForm.mark = row.mark;
      this.addForm.config_name = row.cfg_name;
      this.detailFormVisible = true;
      // this.addForm.value.push(row.project_id);
      // this.addForm.value = row.project_id;
      // this.extraList = [];
      this.extraList=this.str_to_listdata(row.cfg)
      await this.getproinfo();

    },
    async is_deletes_config(index, row) {
            this.$confirm("如果已关联测试集的配置项则无法删除，此操作将删除该配置项, 是否继续?", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            })
                .then(() => {
                    let para = {
                        ids: [row.id],
                    };

                    deletes_config(para).then((res) => {
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
                                message: "删除的配置:" + set_titles,
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

    async getproinfo() {
      this.ongoing = false;
      let para = {
        page: 0,
        name: "",
        page_size: 100

      };
      await get_project_info(para).then((res) => {
        this.vipers = res.data.data;

      });
      await this.refreshViper_v2();
    },
  },
  

  mounted() {
    this.getConfigList();
    this.getproinfo();
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

.config-page {
  padding: 0 0 18px;
}

.config-toolbar {
  margin-bottom: 14px;
  padding: 14px 16px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.config-filter-form {
  width: 100%;
}

.config-filter-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.config-search-input {
  width: 260px;
}

.config-create-action {
  margin-left: auto;
  margin-right: 0;
}

.config-list-panel {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
}

.config-table /deep/ .el-table__expanded-cell {
  padding: 18px 24px;
  background: #f8fafc;
}

.config-name-cell {
  line-height: 1.5;
}

.config-name {
  color: #303133;
  font-size: 15px;
  font-weight: 700;
  word-break: break-word;
}

.config-id {
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

.config-summary {
  line-height: 1.6;
}

.config-section-card {
  margin-bottom: 8px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.config-section-title {
  margin-bottom: 8px;
  color: #303133;
  font-size: 13px;
  font-weight: 700;
}

.config-kv-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.config-kv-chip {
  display: inline-flex;
  max-width: 260px;
  overflow: hidden;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #ffffff;
  font-size: 12px;
  line-height: 24px;
}

.config-kv-key {
  max-width: 110px;
  padding: 0 8px;
  overflow: hidden;
  color: #409eff;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: #ecf5ff;
  border-right: 1px solid #dcdfe6;
  font-weight: 700;
}

.config-kv-value {
  max-width: 150px;
  padding: 0 8px;
  overflow: hidden;
  color: #606266;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.config-more-chip {
  display: inline-block;
  padding: 0 8px;
  color: #909399;
  background: #f4f4f5;
  border-radius: 4px;
  font-size: 12px;
  line-height: 24px;
}

.config-empty {
  color: #909399;
  font-size: 13px;
}

.config-count {
  margin-top: 6px;
  color: #909399;
  font-size: 12px;
}

.config-mark {
  color: #606266;
  white-space: normal;
  word-break: break-word;
}

.config-time {
  color: #606266;
  font-size: 12px;
  line-height: 1.8;
}

.config-time span {
  color: #909399;
}

.config-actions {
  white-space: normal;
}

.config-expand {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(220px, 1fr);
  gap: 12px 18px;
}

.config-expand-title {
  color: #303133;
  font-weight: 700;
}

.config-json-view {
  grid-row: span 3;
  max-height: 420px;
  margin: 0;
  padding: 14px 16px;
  overflow: auto;
  color: #d1d5db;
  background: #111827;
  border-radius: 6px;
  font-family: Consolas, "Courier New", monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre;
}

.config-json-dialog-view {
  max-height: 68vh;
  min-height: 420px;
  font-size: 14px;
}

.json-preview-dialog {
  color: #606266;
}

.json-preview-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.json-preview-meta span {
  padding: 4px 10px;
  color: #409eff;
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 4px;
  font-size: 12px;
}

.json-preview-mark {
  margin-top: 12px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  word-break: break-word;
}

.config-mark-view {
  min-height: 72px;
  padding: 12px;
  color: #606266;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  line-height: 1.6;
  word-break: break-word;
}

.config-edit-tip {
  margin-bottom: 16px;
  padding: 12px 14px;
  color: #606266;
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  font-size: 13px;
}

.config-edit-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(360px, 0.95fr);
  gap: 22px;
  align-items: start;
}

.config-edit-form,
.config-edit-preview {
  min-width: 0;
  padding: 16px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.config-edit-section-title {
  margin: 2px 0 14px;
  padding-left: 8px;
  color: #303133;
  border-left: 3px solid #409eff;
  font-size: 14px;
  font-weight: 700;
}

.config-param-toolbar,
.config-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  color: #303133;
  font-weight: 700;
}

.config-param-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-param-row {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) minmax(0, 1fr) 64px;
  gap: 10px;
  align-items: center;
  padding: 10px;
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.config-param-index {
  width: 24px;
  height: 24px;
  color: #409eff;
  background: #ecf5ff;
  border-radius: 50%;
  text-align: center;
  line-height: 24px;
  font-weight: 700;
}

.config-param-input {
  width: 100%;
}

.config-param-delete {
  color: #f56c6c;
}

.config-param-empty {
  padding: 14px;
  color: #909399;
  background: #f8fafc;
  border: 1px dashed #dcdfe6;
  border-radius: 6px;
  text-align: center;
}

.config-edit-dialog /deep/ .el-dialog__header {
  padding: 18px 24px 12px;
  border-bottom: 1px solid #ebeef5;
}

.config-edit-dialog /deep/ .el-dialog__body {
  max-height: calc(92vh - 130px);
  overflow: auto;
  padding: 18px 24px 8px;
}

.config-edit-dialog /deep/ .el-dialog__footer {
  padding: 12px 24px 18px;
  border-top: 1px solid #ebeef5;
}

.config-edit-preview {
  position: sticky;
  top: 0;
}

.config-edit-json-view {
  min-height: 480px;
  max-height: calc(92vh - 270px);
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
@media (max-width: 900px) {
  .config-filter-row {
    display: block;
  }

  .config-search-input {
    width: 100%;
  }

  .config-create-action {
    margin-left: 0;
  }

  .config-expand {
    grid-template-columns: 1fr;
  }

  .config-edit-layout {
    grid-template-columns: 1fr;
  }

  .config-param-row {
    grid-template-columns: 28px 1fr;
  }

  .config-edit-preview {
    position: static;
  }
}
</style>
  
