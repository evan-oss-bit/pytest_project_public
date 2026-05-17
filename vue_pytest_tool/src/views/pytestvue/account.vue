<template>
  <section class="account-page">
    <el-row class="toolbar" type="flex" justify="space-between" align="middle">
      <div>
        <h3>账号权限</h3>
        <span>按脚本项目分配查看、编辑、运行权限</span>
      </div>
      <el-button type="primary" size="small" icon="el-icon-plus" @click="openEdit()">新增账号</el-button>
    </el-row>

    <el-table :data="accounts" border stripe v-loading="loading">
      <el-table-column prop="username" label="账号" width="150"></el-table-column>
      <el-table-column prop="nickname" label="名称" width="150"></el-table-column>
      <el-table-column label="角色" width="120">
        <template slot-scope="scope">
          <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'success'">
            {{ scope.row.role === 'admin' ? '管理员' : '项目账号' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="项目权限">
        <template slot-scope="scope">
          <span v-if="scope.row.role === 'admin'">全部项目</span>
          <el-tag
            v-for="item in scope.row.permissions"
            :key="item.project_id"
            size="mini"
            class="project-tag"
          >
            <span v-if="item.business_department">[{{ item.business_department }}]</span>
            {{ projectName(item.project_id) }}
            <span v-if="item.can_edit"> / 编辑</span>
            <span v-if="item.can_run"> / 运行</span>
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template slot-scope="scope">
          <el-button size="mini" @click="openEdit(scope.row)">编辑</el-button>
          <el-button
            size="mini"
            type="danger"
            :disabled="scope.row.role === 'admin'"
            @click="deleteAccount(scope.row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog :title="form.id ? '编辑账号' : '新增账号'" :visible.sync="dialogVisible" width="760px">
      <el-form :model="form" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="账号">
              <el-input v-model="form.username"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="名称">
              <el-input v-model="form.nickname"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="密码">
              <el-input v-model="form.password" type="password" placeholder="不填则保持原密码"></el-input>
              <el-button
                v-if="form.id"
                class="reset-password-btn"
                type="warning"
                size="mini"
                plain
                @click="resetPassword"
              >重置为初始密码</el-button>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色">
              <el-select v-model="form.role" style="width: 100%">
                <el-option label="项目账号" value="project_user"></el-option>
                <el-option label="管理员" value="admin"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <div v-if="form.role !== 'admin'" class="permission-toolbar">
          <el-select v-model="permissionDepartmentFilter" clearable filterable placeholder="按业务部门筛选">
            <el-option
              v-for="item in departmentOptions"
              :key="item"
              :label="item"
              :value="item"
            ></el-option>
          </el-select>
          <span>选择业务部门下的脚本项目，并分配查看、编辑、运行权限</span>
        </div>

        <el-table v-if="form.role !== 'admin'" :data="filteredPermissionRows" border height="320">
          <el-table-column prop="business_department" label="业务部门" width="150">
            <template slot-scope="scope">
              <el-tag size="mini" type="info" effect="plain">{{ scope.row.business_department || "未设置" }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="脚本项目"></el-table-column>
          <el-table-column label="允许查看" width="100">
            <template slot-scope="scope">
              <el-checkbox v-model="scope.row.can_view"></el-checkbox>
            </template>
          </el-table-column>
          <el-table-column label="允许编辑" width="100">
            <template slot-scope="scope">
              <el-checkbox v-model="scope.row.can_edit" :disabled="!scope.row.can_view"></el-checkbox>
            </template>
          </el-table-column>
          <el-table-column label="允许运行" width="100">
            <template slot-scope="scope">
              <el-checkbox v-model="scope.row.can_run" :disabled="!scope.row.can_view"></el-checkbox>
            </template>
          </el-table-column>
        </el-table>
      </el-form>
      <div slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveAccount">保存</el-button>
      </div>
    </el-dialog>
  </section>
</template>

<script>
import { delete_account, get_account_info, get_project_info, reset_account_password, save_account } from "../../api/api";

export default {
  data() {
    return {
      loading: false,
      saving: false,
      accounts: [],
      projects: [],
      dialogVisible: false,
      form: {
        id: null,
        username: "",
        nickname: "",
        password: "",
        role: "project_user",
      },
      permissionDepartmentFilter: "",
      permissionRows: [],
    };
  },
  computed: {
    departmentOptions() {
      const names = (this.projects || [])
        .map(item => item.business_department)
        .filter(item => item);
      return Array.from(new Set(names));
    },
    filteredPermissionRows() {
      if (!this.permissionDepartmentFilter) {
        return this.permissionRows;
      }
      return this.permissionRows.filter(item => item.business_department === this.permissionDepartmentFilter);
    },
  },
  methods: {
    loadData() {
      this.loading = true;
      Promise.all([
        get_account_info({}),
        get_project_info({ page_no: 0, page_size: 1000 }),
      ]).then(([accountRes, projectRes]) => {
        this.loading = false;
        this.accounts = accountRes.data.data || [];
        this.projects = projectRes.data.data || [];
      }).catch(() => {
        this.loading = false;
      });
    },
    projectName(projectId) {
      const project = this.projects.find(item => item.id === projectId);
      return project ? project.name : projectId;
    },
    openEdit(row) {
      this.form = {
        id: row ? row.id : null,
        username: row ? row.username : "",
        nickname: row ? row.nickname : "",
        password: "",
        role: row ? row.role : "project_user",
      };
      this.permissionDepartmentFilter = "";
      const permissionMap = {};
      (row && row.permissions ? row.permissions : []).forEach(item => {
        permissionMap[item.project_id] = item;
      });
      this.permissionRows = this.projects.map(project => {
        const permission = permissionMap[project.id] || {};
        return {
          project_id: project.id,
          name: project.name,
          business_department: project.business_department || "未设置",
          can_view: !!permission.can_view,
          can_edit: !!permission.can_edit,
          can_run: !!permission.can_run,
        };
      });
      this.dialogVisible = true;
    },
    saveAccount() {
      const permissions = this.permissionRows
        .filter(item => item.can_view)
        .map(item => ({
          project_id: item.project_id,
          can_edit: item.can_edit ? 1 : 0,
          can_run: item.can_run ? 1 : 0,
        }));
      const payload = Object.assign({}, this.form, { permissions });
      if (!payload.password) {
        delete payload.password;
      }
      this.saving = true;
      save_account(payload).then(res => {
        this.saving = false;
        if (res.data.code !== 200) {
          this.$message.error(res.data.msg);
          return;
        }
        this.$message.success(res.data.msg);
        this.dialogVisible = false;
        this.loadData();
      }).catch(() => {
        this.saving = false;
      });
    },
    resetPassword() {
      if (!this.form.id) {
        return false;
      }
      this.$confirm("确认将该账号密码重置为初始密码 123456789？", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        reset_account_password({ id: this.form.id }).then(res => {
          if (res.data.code !== 200) {
            this.$message.error(res.data.msg);
            return;
          }
          this.$message.success(res.data.msg);
          this.form.password = "";
        });
      }).catch(() => {});
    },
    deleteAccount(row) {
      this.$confirm("确认删除该账号？", "提示").then(() => {
        delete_account({ id: row.id }).then(res => {
          if (res.data.code !== 200) {
            this.$message.error(res.data.msg);
            return;
          }
          this.$message.success(res.data.msg);
          this.loadData();
        });
      }).catch(() => {});
    },
  },
  mounted() {
    this.loadData();
  },
};
</script>

<style scoped>
.account-page {
  padding: 8px 0;
}
.toolbar {
  margin-bottom: 14px;
}
.toolbar h3 {
  margin: 0 0 4px;
}
.toolbar span {
  color: #888;
  font-size: 12px;
}
.project-tag {
  margin: 3px 6px 3px 0;
}
.permission-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 6px 0 10px;
}
.permission-toolbar .el-select {
  width: 220px;
}
.permission-toolbar span {
  color: #909399;
  font-size: 12px;
}
.reset-password-btn {
  margin-top: 8px;
}
</style>
