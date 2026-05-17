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
                                placeholder="请选择关联脚本项目(也可输入项目搜索)" separator="=>" v-model="addForm.value"
                                :options="addForm.options" :props="{ expandTrigger: 'hover' }"></el-cascader>
                        </div>
                    </el-form-item>
                    <el-form-item class="len_input">
                        <div class="block" style="">
                            <span class="demonstration"></span>
                            <el-cascader :filterable="true" :clearable="true" :disabled="false"
                                placeholder="请选择关联版本号(也可输入版本号搜索)" separator="=>" v-model="addForm.value2"
                                :options="addForm.options2" :props="{ expandTrigger: 'hover' }"></el-cascader>
                        </div>
                    </el-form-item>
          <el-form-item>
            <el-input v-model="filters.cfg_name" placeholder="模块名称" clearable @change="get_config_info">
              <i slot="prefix" class="el-input__icon el-icon-search"></i>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="el-icon-search" v-on:click="getConfigList">查询</el-button>
          </el-form-item>
          <div>
            <el-form-item>
              <el-button @click="handleAddEvent" type="primary"
                style="float: right; text-align: right; margin-left: 10px">新建模块</el-button>
            </el-form-item>
          </div>
        </el-col>
      </el-form>
    </el-col>

    <!--列表-->
    <el-col :span="24" type="“flex”" style="white-space: pre">
      <el-table :data="aioLst" highlight-current-row stripe height="600" v-loading="listLoading"
        @selection-change="selsChange" style="width: 100%">
        <!-- <el-table-column type="selection" width="2">
              </el-table-column> -->
        <el-table-column type="index" width="55"> </el-table-column>
        <el-table-column v-for="item in lstForm" :key="item.prop" :prop="item.prop" :label="item.label"
          :width="item.width" style="white-space: pre" sortable>
        </el-table-column>
        <el-table-column label="操作">
          <template slot-scope="scope">
            <el-row>
              <el-button-group>

                <el-button type="primary" icon="el-icon-edit" @click="set_id(scope.$index, scope.row)">编辑</el-button>
                <!-- <el-button
                    type="danger"
                    @click="delete_id_new(scope.$index, scope.row)"
                    >删除</el-button
                  > -->
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

    <!--详情界面-->
    <!-- <el-dialog title="详情" v-model="detailFormVisible" :close-on-click-modal="false"> -->
    <el-dialog title="新建或编辑模块" :close-on-click-modal="false" :visible.sync="detailFormVisible">
      <el-form :model="addForm" label-width="150px" :rules="detailFormRules" ref="addForm">
        <el-col :span="24" style="margin-right: 100px">

          <el-row>
            <el-col :span="9">
              <el-form-item label="模块名称" required>
                <el-input ref="inputName" v-model="addForm.config_name" auto-complete="off" placeholder="模块名称"
                  autofocus="true" clearable></el-input>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row>
            <el-col :span="9">
              <el-form-item label="关联脚本项目" class="len_input" required>
                <div class="block" style="">
                  <span class="demonstration"></span>
                  <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联脚本项目(也可输入项目搜索)" separator="=>"
                    v-model="addForm.value" :options="addForm.options" :props="{ expandTrigger: 'hover' }"></el-cascader>
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="9">
            </el-col>
          </el-row>

          <el-row>
            <el-col :span="9">
              <el-form-item label="关联版本号" class="len_input" required>
                <div class="block" style="">
                  <span class="demonstration"></span>
                  <el-cascader :filterable="true" :clearable="true" placeholder="请选择关联版本号(也可输入版本号搜索)" separator="=>"
                    v-model="addForm.value2" :options="addForm.options2"
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
  </section>
</template>
  
<script>
import {
  DeleteConfig,
  get_config_info,
  update_config,
  add_config,
  get_project_info,
  get_version_info,
  get_module_info,
  add_module,
  update_module
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
      page_size: 500,
      total: 0,
      page: 0,
      addStatus: true,
      listLoading: false,
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
        add_data: true,
        anaFlag: false,
        bdaFlag: false,
        nodeFlag: false,
        cfg: "",
        node_randio: 1,
        auth: false,

        value: "",
        options: [],
        value2: "",
        options2: [],
        set_time: "",
        note: "",
        config_id: null,
        config_name: "",
        set_flag: true,
      },

      lstForm: [
        { prop: "id", label: "模块id", width: 100 },
        { prop: "module", label: "模块名称", width: 130 },
        { prop: "description", label: "备注信息", width: 600 },
        { prop: "project_name", label: "脚本项目名", width: 130 },
        { prop: "version_name", label: "版本号", width: 130 },
        { prop: "created_time", label: "创建时间", width: 185 },
        { prop: "updated_time", label: "更新时间", width: 200 },
      ],
    };
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
    //获取配置列表
    async getConfigList() {
      this.ongoing = false;
      let para = {
        project_id:this.addForm.value[0],
        version_id:this.addForm.value2[0],
        module: this.filters.cfg_name,
        page: this.page,
        page_size: this.page_size,
      };
      this.listLoading = true;
      await get_module_info(para).then((res) => {
        this.aioLst = res.data.data;
        this.listLoading = false;
        this.total = res.data.data.length
      });
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
          project_id: this.addForm.value,
          version_id: this.addForm.value2,
          id: this.addForm.config_id
        };


        await add_module(para).then((res) => {
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
      this.addForm.options = [];
      this.addForm.value = null;
      this.addForm.options2 = [];
      this.addForm.value2 = null;
      this.detailFormVisible = true;
      this.addForm.add_data = true;
      this.addForm.config_id = null
      this.addForm.cfg = null;
      this.addForm.config_name = null;
      await this.getproinfo();
      await this.getversioninfo()
    },
    async set_id(index, row) {
      this.addForm.config_id = row.id
      this.detailFormVisible = true;
      this.addForm.config_name = row.module;
      this.addForm.cfg = row.description;
      this.addForm.value = row.project_id;
      this.addForm.value2 = row.version_id;
      await this.getproinfo();
      await this.getversioninfo()

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
    async getversioninfo() {
      this.ongoing = false;
      let para = {
        page: 0,
        version: "",
        page_size: 100

      };
      await get_version_info(para).then((res) => {
        this.vipers2 = res.data.data;

      });
      await this.refreshViper_v3();
    },
  },



  mounted() {
    this.getConfigList();
    this.getproinfo();
    this.getversioninfo();
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
  
