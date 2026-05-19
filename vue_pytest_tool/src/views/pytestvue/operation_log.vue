<template>
  <section class="operation-log-page">
    <el-col :span="24" class="toolbar operation-toolbar">
      <el-form :inline="true" :model="filters">
        <el-form-item>
          <el-input v-model="filters.username" placeholder="操作账号" clearable>
            <i slot="prefix" class="el-input__icon el-icon-user"></i>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.action" clearable placeholder="操作类型" style="width: 140px">
            <el-option label="新增" value="create"></el-option>
            <el-option label="保存" value="save"></el-option>
            <el-option label="编辑" value="update"></el-option>
            <el-option label="删除" value="delete"></el-option>
            <el-option label="运行" value="run"></el-option>
            <el-option label="终止" value="stop"></el-option>
            <el-option label="Git拉取" value="pull"></el-option>
            <el-option label="同步" value="sync"></el-option>
            <el-option label="重置" value="reset"></el-option>
            <el-option label="修改密码" value="change_password"></el-option>
            <el-option label="报告备注" value="remark"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.target_type" clearable placeholder="对象类型" style="width: 140px">
            <el-option label="脚本项目" value="project"></el-option>
            <el-option label="版本" value="version"></el-option>
            <el-option label="模块" value="module"></el-option>
            <el-option label="配置" value="config"></el-option>
            <el-option label="用例" value="case"></el-option>
            <el-option label="测试集" value="testset"></el-option>
            <el-option label="测试任务" value="testtask"></el-option>
            <el-option label="业务部门" value="business_department"></el-option>
            <el-option label="账号" value="account"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-input v-model="filters.keyword" placeholder="对象/接口/结果关键字" clearable style="width: 220px">
            <i slot="prefix" class="el-input__icon el-icon-search"></i>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="search">查询</el-button>
          <el-button icon="el-icon-refresh" @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-col>

    <el-col :span="24" class="operation-list-panel">
      <el-table :data="logs" stripe border height="650" v-loading="loading" @row-click="openDetail">
        <el-table-column prop="created_time" label="操作时间" width="170"></el-table-column>
        <el-table-column prop="username" label="操作账号" width="120"></el-table-column>
        <el-table-column label="操作" width="110">
          <template slot-scope="scope">
            <el-tag size="mini" :type="actionTagType(scope.row.action)">
              {{ scope.row.action_name || actionText(scope.row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="对象" min-width="220">
          <template slot-scope="scope">
            <div class="target-cell">
              <strong>{{ targetText(scope.row.target_type) }}</strong>
              <span>{{ scope.row.target_name || "-" }}</span>
              <em v-if="scope.row.target_id">ID: {{ scope.row.target_id }}</em>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="接口" min-width="260" show-overflow-tooltip></el-table-column>
        <el-table-column label="结果" width="170">
          <template slot-scope="scope">
            <el-tag size="mini" :type="scope.row.result_code === 200 ? 'success' : 'danger'">
              {{ scope.row.result_code || scope.row.status_code }}
            </el-tag>
            <span class="result-msg">{{ scope.row.result_msg || "-" }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="130"></el-table-column>
        <el-table-column label="详情" width="80" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" size="mini" @click.stop="openDetail(scope.row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-col>

    <el-col :span="24" class="toolbar">
      <el-pagination
        layout="total, prev, pager, next"
        :page-size="pageSize"
        :total="total"
        @current-change="handleCurrentChange"
        style="float: right">
      </el-pagination>
    </el-col>

    <el-drawer title="操作日志详情" :visible.sync="detailVisible" direction="rtl" size="48%">
      <div class="log-detail" v-if="currentLog">
        <div class="detail-title">
          <h3>{{ currentLog.action_name || actionText(currentLog.action) }}</h3>
          <el-tag :type="currentLog.result_code === 200 ? 'success' : 'danger'">
            {{ currentLog.result_msg || currentLog.status_code }}
          </el-tag>
        </div>
        <div class="detail-grid">
          <div><span>操作账号</span><strong>{{ currentLog.username || "-" }}</strong></div>
          <div><span>操作时间</span><strong>{{ currentLog.created_time || "-" }}</strong></div>
          <div><span>对象类型</span><strong>{{ targetText(currentLog.target_type) }}</strong></div>
          <div><span>对象ID</span><strong>{{ currentLog.target_id || "-" }}</strong></div>
          <div><span>对象名称</span><strong>{{ currentLog.target_name || "-" }}</strong></div>
          <div><span>IP</span><strong>{{ currentLog.ip || "-" }}</strong></div>
        </div>
        <div class="detail-section">
          <div class="detail-section-title">接口</div>
          <pre>{{ currentLog.method }} {{ currentLog.path }}</pre>
        </div>
        <div class="detail-section">
          <div class="detail-section-title">请求数据</div>
          <pre>{{ prettyJson(currentLog.request_data) }}</pre>
        </div>
        <div class="detail-section">
          <div class="detail-section-title">响应数据</div>
          <pre>{{ prettyJson(currentLog.response_data) }}</pre>
        </div>
      </div>
    </el-drawer>
  </section>
</template>

<script>
import { get_operation_log } from "../../api/api";

export default {
  data() {
    return {
      loading: false,
      detailVisible: false,
      currentLog: null,
      logs: [],
      total: 0,
      page: 0,
      pageSize: 50,
      filters: {
        username: "",
        action: "",
        target_type: "",
        keyword: "",
      },
    };
  },
  methods: {
    async loadLogs() {
      this.loading = true;
      const params = Object.assign({}, this.filters, {
        page: this.page,
        page_size: this.pageSize,
      });
      await get_operation_log(params).then((res) => {
        if (res.data.code !== 200) {
          this.$message({ message: res.data.msg, type: "warning" });
          this.logs = [];
          this.total = 0;
          return;
        }
        this.logs = res.data.data || [];
        this.total = res.data.total || 0;
      }).finally(() => {
        this.loading = false;
      });
    },
    search() {
      this.page = 0;
      this.loadLogs();
    },
    resetFilters() {
      this.filters = {
        username: "",
        action: "",
        target_type: "",
        keyword: "",
      };
      this.search();
    },
    handleCurrentChange(val) {
      this.page = val - 1;
      this.loadLogs();
    },
    openDetail(row) {
      this.currentLog = row;
      this.detailVisible = true;
    },
    prettyJson(value) {
      if (!value) {
        return "-";
      }
      try {
        return JSON.stringify(JSON.parse(value), null, 2);
      } catch (e) {
        return value;
      }
    },
    actionText(action) {
      return {
        create: "新增",
        save: "保存",
        update: "编辑",
        delete: "删除",
        run: "运行",
        stop: "终止",
        pull: "Git拉取",
        sync: "同步",
        reset: "重置",
        change_password: "修改密码",
        remark: "报告备注",
        clear: "清空",
      }[action] || action || "-";
    },
    actionTagType(action) {
      return {
        create: "success",
        save: "success",
        update: "warning",
        delete: "danger",
        run: "primary",
        stop: "danger",
        pull: "success",
        sync: "success",
        reset: "warning",
      }[action] || "info";
    },
    targetText(type) {
      return {
        project: "脚本项目",
        version: "版本",
        module: "模块",
        config: "配置",
        case: "用例",
        testset: "测试集",
        testtask: "测试任务",
        business_department: "业务部门",
        account: "账号",
      }[type] || type || "-";
    },
  },
  mounted() {
    this.loadLogs();
  },
};
</script>

<style scoped>
.operation-toolbar,
.operation-list-panel {
  padding: 10px;
  background: #fff;
}

.target-cell {
  display: flex;
  flex-direction: column;
  line-height: 1.6;
}

.target-cell span,
.target-cell em,
.result-msg {
  color: #606266;
  font-style: normal;
  font-size: 12px;
}

.log-detail {
  padding: 0 18px 24px;
}

.detail-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.detail-title h3 {
  margin: 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.detail-grid div,
.detail-section {
  padding: 10px;
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.detail-grid span,
.detail-section-title {
  display: block;
  margin-bottom: 6px;
  color: #909399;
  font-size: 12px;
}

.detail-grid strong {
  color: #303133;
}

.detail-section {
  margin-bottom: 12px;
}

pre {
  max-height: 260px;
  margin: 0;
  overflow: auto;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
