<template>
  <el-row class="container">
    <el-col :span="24" class="header">
      <el-col
        :span="10"
        class="logo"
        :class="collapsed ? 'logo-collapse-width' : 'logo-width'"
      >
        {{ collapsed ? "" : sysName }}
      </el-col>
      <el-col :span="1">
        <div class="tools grid-content" @click.prevent="collapse">
          <i class="fa fa-align-justify"></i>
        </div>
      </el-col>
      <!-- <el-col :span="4" class="userinfo">
				<el-dropdown trigger="hover">
					<!-- <span class="el-dropdown-link userinfo-inner"><img src="https://s1.ax1x.com/2018/02/08/93yKtU.jpg" /> {{sysUserName}}</span> -->
      <!-- <span class="el-dropdown-link userinfo-inner"><img src="https://j.17qq.com/article/uecwhwwcx.html" /> {{sysUserName}}</span>
					<el-dropdown-menu slot="dropdown">
            <el-dropdown-item @click.native="settings">修改密码</el-dropdown-item>
						<el-dropdown-item divided @click.native="logout">退出登录</el-dropdown-item>
					</el-dropdown-menu>
				</el-dropdown>
			</el-col> -->
      <el-col :span="4" class="userinfo">
        <el-dropdown trigger="hover">
          <span class="el-dropdown-link userinfo-inner">
            <i class="fa fa-user-circle"></i>
            {{ sysUserName }}
            <i class="el-icon-arrow-down el-icon--right"></i>
          </span>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item @click.native="openUserInfo">用户信息</el-dropdown-item>
            <el-dropdown-item @click.native="settings">修改密码</el-dropdown-item>
            <el-dropdown-item divided @click.native="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </el-col>
    </el-col>
    <el-col :span="24" class="main">
      <aside :class="collapsed ? 'menu-collapsed' : 'menu-expanded'">
        <!--导航菜单-->
        <el-menu
          :default-active="$route.path"
          class="el-menu-vertical-demo el-menu-expand"
          @open="handleopen"
          @close="handleclose"
          @select="handleselect"
          unique-opened
          router
          v-if="!collapsed"
        >
          <div
            v-for="(item, index) in $router.options.routes"
            :key="index"
            v-if="canShowRoute(item)"
          >
            <el-submenu :index="index + ''" v-if="!item.leaf">
              <template slot="title"
                ><i :class="item.iconCls"></i>{{ item.name }}</template
              >
              <el-menu-item
                v-for="child in item.children"
                :index="child.path"
                :key="child.path"
                v-if="!child.hidden"
                >{{ child.name }}</el-menu-item
              >
            </el-submenu>
            <el-menu-item
              v-if="item.leaf && item.children.length > 0"
              :index="item.children[0].path"
              ><i :class="item.iconCls"></i
              >{{ item.children[0].name }}</el-menu-item
            >
          </div>
        </el-menu>
        <!--导航菜单-折叠后-->
        <ul
          class="el-menu el-menu-vertical-demo collapsed"
          v-if="collapsed"
          ref="menuCollapsed"
        >
          <li
            v-for="(item, index) in $router.options.routes"
            :key="index"
            v-if="canShowRoute(item)"
            class="el-submenu item"
          >
            <template v-if="!item.leaf">
              <div
                class="el-submenu__title"
                style="padding-left: 20px"
                @mouseover="showMenu(index, true)"
                @mouseout="showMenu(index, false)"
              >
                <i :class="item.iconCls"></i>
              </div>
              <ul
                class="el-menu submenu"
                :class="'submenu-hook-' + index"
                @mouseover="showMenu(index, true)"
                @mouseout="showMenu(index, false)"
              >
                <li
                  v-for="child in item.children"
                  v-if="!child.hidden"
                  :key="child.path"
                  class="el-menu-item"
                  style="padding-left: 40px"
                  :class="$route.path == child.path ? 'is-active' : ''"
                  @click="$router.push(child.path)"
                >
                  {{ child.name }}
                </li>
              </ul>
            </template>
            <template v-else>
              <li class="el-submenu">
                <div
                  class="el-submenu__title el-menu-item"
                  style="
                    padding-left: 20px;
                    height: 56px;
                    line-height: 56px;
                    padding: 0 20px;
                  "
                  :class="
                    $route.path == item.children[0].path ? 'is-active' : ''
                  "
                  @click="$router.push(item.children[0].path)"
                >
                  <i :class="item.iconCls"></i>
                </div>
              </li>
            </template>
          </li>
        </ul>
      </aside>
      <section class="content-container">
        <div class="grid-content bg-purple-light">
          <el-col :span="24" class="breadcrumb-container">
            <strong class="title">{{ $route.name }}</strong>
            <el-breadcrumb separator="/" class="breadcrumb-inner">
              <el-breadcrumb-item
                v-for="item in $route.matched"
                :key="item.path"
              >
                {{ item.name }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </el-col>
          <el-col :span="24" class="content-wrapper">
            <transition name="fade" mode="out-in">
              <router-view></router-view>
            </transition>
          </el-col>
        </div>
      </section>
      <!--修改密码界面-->
      <el-dialog
        title="用户信息"
        :visible.sync="userInfoVisible"
        width="620px"
        class="user-info-dialog"
      >
        <div class="user-info-panel">
          <div class="user-info-avatar">
            <i class="fa fa-user-circle"></i>
          </div>
          <div class="user-info-main">
            <div class="user-info-head">
              <div>
                <div class="user-info-name">{{ currentUser.username || sysUserName }}</div>
                <div class="user-info-sub">{{ currentUser.nickname || "未设置昵称" }}</div>
              </div>
              <el-tag size="small" :type="currentUser.role === 'admin' ? 'danger' : ''">
                {{ currentUser.role === "admin" ? "管理员" : "项目账号" }}
              </el-tag>
            </div>
            <div class="user-info-stats">
              <div class="user-info-stat">
                <span>账号ID</span>
                <strong>{{ currentUser.id || "-" }}</strong>
              </div>
              <div class="user-info-stat">
                <span>项目权限</span>
                <strong>{{ currentProjectCount() }}</strong>
              </div>
            </div>
          </div>
        </div>
        <div class="user-permission-section">
          <div class="user-permission-title">权限明细</div>
          <div v-if="currentUser.role === 'admin'" class="user-permission-admin">
            <el-tag type="success">全部项目</el-tag>
            <el-tag type="success">查看</el-tag>
            <el-tag type="success">编辑</el-tag>
            <el-tag type="success">运行</el-tag>
          </div>
          <div v-else-if="permissionList().length" class="user-permission-list">
            <div
              v-for="item in permissionList()"
              :key="item.project_id"
              class="user-permission-card"
            >
              <div class="user-permission-project">
                {{ item.project_name || ("项目 " + item.project_id) }}
              </div>
              <div class="user-permission-tags">
                <el-tag size="mini" :type="item.can_view ? 'success' : 'info'">
                  查看
                </el-tag>
                <el-tag size="mini" :type="item.can_edit ? 'warning' : 'info'">
                  编辑
                </el-tag>
                <el-tag size="mini" :type="item.can_run ? '' : 'info'">
                  运行
                </el-tag>
              </div>
            </div>
          </div>
          <div v-else class="user-permission-empty">暂无项目权限</div>
        </div>
      </el-dialog>
      <el-dialog
        title="修改密码"
        :visible.sync="setpwdFormVisible"
        :close-on-click-modal="false"
      >
        <el-form
          :model="setpwdForm"
          label-width="80px"
          :rules="setpwdFormRules"
          ref="setpwdForm"
        >
          <el-row>
            <el-form-item label="原密码" prop="oldpass">
              <el-input
                type="password"
                v-model="setpwdForm.oldpass"
                auto-complete="off"
              ></el-input>
            </el-form-item>
            <el-form-item label="新密码" prop="newpass">
              <el-input
                type="password"
                v-model="setpwdForm.newpass"
                auto-complete="off"
              ></el-input>
            </el-form-item>
            <el-form-item label="确认密码" prop="confirpass">
              <el-input
                type="password"
                v-model="setpwdForm.confirpass"
                auto-complete="off"
              ></el-input>
            </el-form-item>
          </el-row>
        </el-form>
        <div slot="footer" class="dialog-footer">
          <el-button @click.native="setpwdFormVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click.native="editSubmit"
            :loading="editLoading"
            >提交</el-button
          >
        </div>
      </el-dialog>
    </el-col>
  </el-row>
</template>

<script>
import { setpwd } from "../api/api";
export default {
  data() {
    var validatePass = (rule, value, callback) => {
      if (value === "") {
        callback(new Error("请输入新密码"));
      } else if (value.length < 8) {
        callback(new Error("密码长度请大于8"));
      } else {
        if (this.setpwdForm.confirpass !== "") {
          this.$refs.setpwdForm.validateField("confirpass");
        }
        callback();
      }
    };
    var validatePass2 = (rule, value, callback) => {
      if (value === "") {
        callback(new Error("请再次输入新密码"));
      } else if (value !== this.setpwdForm.newpass) {
        callback(new Error("两次输入密码不一致!"));
      } else {
        callback();
      }
    };
    return {
      sysName: "PYTestTool",
      collapsed: false,
      sysUserName: "HELLO",
      currentUser: {},
      userInfoVisible: false,
      form: {
        name: "",
        region: "",
        date1: "",
        date2: "",
        delivery: false,
        type: [],
        resource: "",
        desc: "",
      },

      setpwdFormVisible: false,
      editLoading: false,
      setpwdFormRules: {
        oldpass: [{ required: true, message: "请输入旧密码", trigger: "blur" }],
        newpass: [{ validator: validatePass, trigger: "blur" }],
        confirpass: [{ validator: validatePass2, trigger: "blur" }],
      },
      setpwdForm: {
        oldpass: "",
        newpass: "",
        confirpass: "",
      },
    };
  },
  methods: {
    onSubmit() {
    },
    handleopen() {
    },
    handleclose() {
    },
    handleselect: function (a, b) {},
    canShowRoute(item) {
      if (item.hidden) {
        return false;
      }
      if (item.adminOnly && (!this.currentUser || this.currentUser.role !== "admin")) {
        return false;
      }
      return true;
    },
    currentProjectCount() {
      const ids = this.currentUser && this.currentUser.project_ids;
      if (this.currentUser && this.currentUser.role === "admin") {
        return "全部项目";
      }
      return ids && ids.length ? ids.length + " 个项目" : "未分配";
    },
    permissionList() {
      const permissions = this.currentUser && this.currentUser.permissions;
      return Array.isArray(permissions) ? permissions : [];
    },
    openUserInfo() {
      this.userInfoVisible = true;
    },
    //退出登录
    logout: function () {
      var _this = this;
      this.$confirm("确认退出吗?", "提示", {
        //type: 'warning'
      })
        .then(() => {
          sessionStorage.removeItem("token");
          sessionStorage.removeItem("name");
          sessionStorage.removeItem("user");
          _this.$router.push("/login");
        })
        .catch(() => {});
    },
    //修改密码
    settings: function () {
      this.setpwdForm = {
        oldpass: "",
        newpass: "",
        confirpass: "",
      };
      this.setpwdFormVisible = true;
    },
    editSubmit: function () {
      this.$refs.setpwdForm.validate((valid) => {
        if (valid) {
          this.$confirm("确认修改吗？", "提示", {}).then(() => {
            this.editLoading = true;
            let para = Object.assign({}, this.setpwdForm);
            setpwd(para).then((res) => {
              this.editLoading = false;
              let { code, msg } = res.data;
              if (code !== 200) {
                this.$message({
                  message: msg,
                  type: "error",
                });
              } else {
                this.$message({
                  message: msg,
                  type: "success",
                });
              }
              this.$refs["setpwdForm"].resetFields();
              this.setpwdFormVisible = false;
            });
          });
        }
      });
    },
    //折叠导航栏
    collapse: function () {
      this.collapsed = !this.collapsed;
    },
    showMenu(i, status) {
      this.$refs.menuCollapsed.getElementsByClassName(
        "submenu-hook-" + i
      )[0].style.display = status ? "block" : "none";
    },
  },
  mounted() {
    try {
      this.currentUser = JSON.parse(sessionStorage.getItem("user") || "{}");
    } catch (e) {
      this.currentUser = {};
    }
    this.sysUserName = this.currentUser.username || sessionStorage.getItem("name") || "HELLO";
    // this.$router.push("/viper");
    // this.$router.push("/aio");
    //   var token = sessionStorage.getItem("token");
    //   var user = sessionStorage.getItem("name");
    //   if (token && user) {
    //     user = JSON.parse(user);
    //     this.sysUserName = user || "";
    //   } else {
    //     sessionStorage.removeItem("token");
    //     this.$router.push("/login");
    //   }
  },
};
</script>

<style scoped lang="scss">
@import "~scss_vars";

.container {
  position: absolute;
  top: 0px;
  bottom: 0px;
  width: 100%;
  .header {
    height: 60px;
    line-height: 60px;
    background: $color-primary;
    color: #fff;
    .userinfo {
      text-align: right;
      padding-right: 35px;
      float: right;
      .userinfo-inner {
        cursor: pointer;
        color: #fff;
        img {
          width: 40px;
          height: 40px;
          border-radius: 20px;
          margin: 10px 0px 10px 10px;
          float: right;
        }
      }
    }
    .user-info-panel {
      display: flex;
      gap: 16px;
      align-items: flex-start;
    }
    .user-info-avatar {
      width: 52px;
      height: 52px;
      line-height: 52px;
      text-align: center;
      border-radius: 50%;
      background: #ecf5ff;
      color: #409eff;
      font-size: 34px;
      flex: 0 0 52px;
    }
    .user-info-main {
      flex: 1;
      min-width: 0;
    }
    .user-info-name {
      margin-bottom: 12px;
      font-size: 18px;
      font-weight: 700;
      color: #303133;
      word-break: break-word;
    }
    .user-info-row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 9px 0;
      border-top: 1px solid #ebeef5;
      line-height: 20px;
      color: #606266;
    }
    .user-info-row strong {
      color: #303133;
      font-weight: 600;
      text-align: right;
      word-break: break-word;
    }
    .user-permission-section {
      margin-top: 18px;
      padding-top: 16px;
      border-top: 1px solid #ebeef5;
    }
    .user-permission-title {
      margin-bottom: 12px;
      color: #303133;
      font-size: 14px;
      font-weight: 700;
    }
    .user-permission-admin {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .user-permission-list {
      display: grid;
      grid-template-columns: 1fr;
      gap: 10px;
      max-height: 280px;
      overflow-y: auto;
    }
    .user-permission-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 12px;
      background: #f8fafc;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
    }
    .user-permission-project {
      min-width: 0;
      color: #303133;
      font-weight: 600;
      word-break: break-word;
    }
    .user-permission-tags {
      display: flex;
      flex: 0 0 auto;
      gap: 6px;
      align-items: center;
    }
    .user-permission-empty {
      padding: 14px;
      color: #909399;
      background: #f8fafc;
      border: 1px dashed #dcdfe6;
      border-radius: 6px;
      text-align: center;
    }
    .logo {
      //width:230px;
      height: 60px;
      font-size: 22px;
      padding-left: 20px;
      padding-right: 20px;
      border-color: rgba(238, 241, 146, 0.3);
      border-right-width: 1px;
      border-right-style: solid;
      img {
        width: 40px;
        float: left;
        margin: 10px 10px 10px 18px;
      }
      .txt {
        color: #fff;
      }
    }
    .logo-width {
      width: 180px;
    }
    .logo-collapse-width {
      width: 60px;
    }
    .tools {
      padding: 0px 23px;
      width: 14px;
      height: 60px;
      line-height: 60px;
      cursor: pointer;
    }
  }
  .main {
    display: flex;
    // background: #324057;
    position: absolute;
    top: 60px;
    bottom: 0px;
    overflow: hidden;
    aside {
      flex: 0 0 180px;
      width: 180px;
      // position: absolute;
      // top: 0px;
      // bottom: 0px;
      .el-menu {
        height: 100%;
      }
      .collapsed {
        width: 60px;
        .item {
          position: relative;
        }
        .submenu {
          position: absolute;
          top: 0px;
          left: 60px;
          z-index: 99999;
          height: auto;
          display: none;
        }
      }
    }
    .menu-collapsed {
      flex: 0 0 60px;
      width: 60px;
    }
    .menu-expanded {
      flex: 0 0 180px;
      width: 180px;
    }
    .el-menu-expand {
      width: 100% !important;
    }
    .el-menu-item {
      min-width: 60px;
      &.is-active {
        background-color: #cdc9c9 !important;
        border-right: 4px solid $color-primary;
        color: $color-primary;
      }
    }
    .content-container {
      // background: #f1f2f7;
      flex: 1;
      // position: absolute;
      // right: 0px;
      // top: 0px;
      // bottom: 0px;
      // left: 230px;
      overflow-y: scroll;
      padding: 20px;
      .breadcrumb-container {
        //margin-bottom: 15px;
        .title {
          width: 200px;
          float: left;
          color: #475669;
        }
        .breadcrumb-inner {
          float: right;
        }
      }
      .content-wrapper {
        background-color: #fff;
        box-sizing: border-box;
      }
    }
  }
}
.user-info-dialog /deep/ .el-dialog__header {
  padding: 16px 20px 12px;
  border-bottom: 1px solid #ebeef5;
}

.user-info-dialog /deep/ .el-dialog__body {
  padding: 18px 20px 20px;
}

.user-info-panel {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  padding: 14px;
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.user-info-avatar {
  width: 54px;
  height: 54px;
  line-height: 54px;
  text-align: center;
  border-radius: 50%;
  background: #ecf5ff;
  color: #409eff;
  font-size: 34px;
  flex: 0 0 54px;
}

.user-info-main {
  flex: 1;
  min-width: 0;
}

.user-info-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.user-info-name {
  color: #303133;
  font-size: 18px;
  font-weight: 700;
  line-height: 24px;
  word-break: break-word;
}

.user-info-sub {
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

.user-info-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.user-info-stat {
  padding: 10px 12px;
  background: #ffffff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}

.user-info-stat span {
  display: block;
  color: #909399;
  font-size: 12px;
  line-height: 18px;
}

.user-info-stat strong {
  display: block;
  margin-top: 4px;
  color: #303133;
  font-size: 14px;
  line-height: 20px;
}

.user-permission-section {
  margin-top: 16px;
}

.user-permission-title {
  margin-bottom: 10px;
  color: #303133;
  font-size: 14px;
  font-weight: 700;
}

.user-permission-admin {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
  border-radius: 6px;
}

.user-permission-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  max-height: 280px;
  overflow-y: auto;
}

.user-permission-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.user-permission-project {
  min-width: 0;
  color: #303133;
  font-weight: 600;
  word-break: break-word;
}

.user-permission-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
}

.user-permission-empty {
  padding: 16px;
  color: #909399;
  background: #f8fafc;
  border: 1px dashed #dcdfe6;
  border-radius: 6px;
  text-align: center;
}
</style>
