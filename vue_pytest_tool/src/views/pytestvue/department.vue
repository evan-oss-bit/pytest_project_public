<template>
  <section class="department-page">
    <el-col :span="24" class="toolbar department-toolbar-panel">
      <el-form :inline="true" :model="filters">
        <el-form-item>
          <el-input v-model="filters.name" placeholder="业务部门名称" clearable>
            <i slot="prefix" class="el-input__icon el-icon-search"></i>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="loadDepartments">查询</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-plus" @click="openEdit()">新建业务部门</el-button>
        </el-form-item>
      </el-form>
    </el-col>

    <el-col :span="24" class="department-list-panel">
      <el-table :data="departments" stripe border height="650" v-loading="loading">
        <el-table-column type="index" label="#" width="55"></el-table-column>
        <el-table-column label="业务部门" min-width="220">
          <template slot-scope="scope">
            <div class="department-name">{{ scope.row.name }}</div>
            <div class="muted-text">负责人：{{ scope.row.owner || "未设置" }}</div>
          </template>
        </el-table-column>
        <el-table-column label="总览" min-width="360">
          <template slot-scope="scope">
            <span class="metric-chip">项目 {{ scope.row.project_count || 0 }}</span>
            <span class="metric-chip">用例 {{ scope.row.case_count || 0 }}</span>
            <span class="metric-chip">测试集 {{ scope.row.testset_count || 0 }}</span>
            <span class="metric-chip">任务 {{ scope.row.task_count || 0 }}</span>
            <span class="metric-chip">报告 {{ scope.row.report_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="备注" min-width="260" show-overflow-tooltip></el-table-column>
        <el-table-column prop="created_by_name" label="创建人" width="100"></el-table-column>
        <el-table-column prop="updated_by_name" label="更新人" width="100"></el-table-column>
        <el-table-column prop="updated_time" label="更新时间" width="180"></el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template slot-scope="scope">
            <el-button size="mini" @click="openDashboard(scope.row)">总览</el-button>
            <el-button size="mini" type="primary" @click="openEdit(scope.row)">编辑</el-button>
            <el-button size="mini" type="danger" @click="removeDepartment(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-col>

    <el-dialog :title="form.id ? '编辑业务部门' : '新建业务部门'" :visible.sync="editVisible" width="540px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="部门名称" required>
          <el-input v-model="form.name" clearable placeholder="如：支付业务部"></el-input>
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="form.owner" clearable placeholder="部门负责人"></el-input>
        </el-form-item>
        <el-form-item label="备注">
          <el-input type="textarea" :rows="4" v-model="form.description" placeholder="部门说明"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveDepartment">保存</el-button>
      </span>
    </el-dialog>

    <el-dialog :title="dashboardTitle" :visible.sync="dashboardVisible" width="920px">
      <div v-if="dashboard" class="department-dashboard">
        <div class="department-stat-row">
          <div class="stat-card"><span>脚本项目</span><strong>{{ dashboard.project_count || 0 }}</strong></div>
          <div class="stat-card"><span>用例</span><strong>{{ dashboard.case_count || 0 }}</strong></div>
          <div class="stat-card"><span>测试集</span><strong>{{ dashboard.testset_count || 0 }}</strong></div>
          <div class="stat-card"><span>任务</span><strong>{{ dashboard.task_count || 0 }}</strong></div>
          <div class="stat-card"><span>报告</span><strong>{{ dashboard.report_count || 0 }}</strong></div>
        </div>
        <el-table :data="dashboard.projects || []" stripe height="380">
          <el-table-column prop="name" label="脚本项目" min-width="160"></el-table-column>
          <el-table-column prop="controller" label="负责人" width="130"></el-table-column>
          <el-table-column label="规模" min-width="260">
            <template slot-scope="scope">
              <span class="metric-chip">用例 {{ scope.row.case_count || 0 }}</span>
              <span class="metric-chip">测试集 {{ scope.row.testset_count || 0 }}</span>
              <span class="metric-chip">报告 {{ scope.row.report_count || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_by_name" label="创建人" width="100"></el-table-column>
          <el-table-column prop="updated_by_name" label="更新人" width="100"></el-table-column>
          <el-table-column prop="updated_time" label="更新时间" width="180"></el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </section>
</template>

<script>
import {
  delete_business_department,
  get_business_department_dashboard,
  get_business_department_info,
  save_business_department,
} from "../../api/api";

export default {
  data() {
    return {
      loading: false,
      editVisible: false,
      dashboardVisible: false,
      dashboardTitle: "业务部门总览",
      dashboard: null,
      departments: [],
      filters: {
        name: "",
      },
      form: {
        id: null,
        name: "",
        owner: "",
        description: "",
      },
    };
  },
  methods: {
    async loadDepartments() {
      this.loading = true;
      await get_business_department_info({ name: this.filters.name }).then((res) => {
        this.departments = res.data.data || [];
      }).finally(() => {
        this.loading = false;
      });
    },
    openEdit(row) {
      this.form = {
        id: row ? row.id : null,
        name: row ? row.name : "",
        owner: row ? (row.owner || "") : "",
        description: row ? (row.description || "") : "",
      };
      this.editVisible = true;
    },
    async saveDepartment() {
      await save_business_department(this.form).then((res) => {
        const { code, msg } = res.data;
        this.$message({ message: msg, type: code === 200 ? "success" : "warning" });
        if (code === 200) {
          this.editVisible = false;
          this.loadDepartments();
        }
      });
    },
    async removeDepartment(row) {
      this.$confirm("确认删除该业务部门吗？", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(async () => {
        await delete_business_department({ id: row.id }).then((res) => {
          const { code, msg } = res.data;
          this.$message({ message: msg, type: code === 200 ? "success" : "warning" });
          if (code === 200) {
            this.loadDepartments();
          }
        });
      }).catch(() => {});
    },
    async openDashboard(row) {
      this.dashboardTitle = "业务部门总览：" + row.name;
      this.dashboardVisible = true;
      this.dashboard = null;
      await get_business_department_dashboard({ id: row.id }).then((res) => {
        if (res.data.code !== 200) {
          this.$message({ message: res.data.msg, type: "warning" });
          this.dashboardVisible = false;
          return false;
        }
        this.dashboard = res.data.data;
      });
    },
  },
  mounted() {
    this.loadDepartments();
  },
};
</script>

<style scoped>
.department-page {
  padding-bottom: 18px;
}

.department-toolbar-panel {
  background: #f5f7fa;
  padding: 12px 10px 0;
  margin-bottom: 10px;
}

.department-list-panel {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
}

.department-name {
  color: #1f8efb;
  font-weight: 700;
  line-height: 1.7;
}

.muted-text {
  color: #909399;
  font-size: 12px;
}

.metric-chip {
  display: inline-block;
  padding: 3px 8px;
  margin: 2px 4px 2px 0;
  color: #409eff;
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 4px;
  font-size: 12px;
  line-height: 20px;
}

.department-stat-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.stat-card {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #fafafa;
}

.stat-card span {
  display: block;
  color: #909399;
  font-size: 12px;
}

.stat-card strong {
  display: block;
  margin-top: 6px;
  color: #303133;
  font-size: 22px;
}
</style>
