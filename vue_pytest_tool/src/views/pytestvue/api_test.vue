<template>
  <section class="api-test-page">
    <el-row :gutter="12">
      <el-col :span="7">
        <div class="api-side">
          <div class="api-side-toolbar">
            <el-input v-model="filters.keyword" size="small" clearable placeholder="接口名称" @keyup.enter.native="loadCases">
              <i slot="prefix" class="el-input__icon el-icon-search"></i>
            </el-input>
            <el-button type="primary" size="small" icon="el-icon-search" @click="loadCases">查询</el-button>
          </div>
          <div class="api-side-toolbar">
            <el-select v-model="filters.project_id" size="small" clearable placeholder="脚本项目" @change="handleProjectChange">
              <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id"></el-option>
            </el-select>
            <el-button type="success" size="small" icon="el-icon-plus" @click="newCase">新增接口</el-button>
          </div>
          <el-table :data="cases" stripe height="620" v-loading="caseLoading" @row-click="selectCase">
            <el-table-column label="接口用例" min-width="220">
              <template slot-scope="scope">
                <div class="case-row" :class="{ active: currentCase.id === scope.row.id }">
                  <el-tag size="mini" :type="methodType(scope.row.method)">{{ scope.row.method }}</el-tag>
                  <strong>{{ scope.row.name }}</strong>
                  <span>{{ scope.row.url }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="结果" width="72">
              <template slot-scope="scope">
                <el-tag v-if="scope.row.last_success !== null && scope.row.last_success !== undefined" size="mini" :type="scope.row.last_success ? 'success' : 'danger'">
                  {{ scope.row.last_status || "-" }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>

      <el-col :span="17">
        <div class="api-main">
          <div class="request-line">
            <el-select v-model="currentCase.method" class="method-select">
              <el-option v-for="item in methods" :key="item" :label="item" :value="item"></el-option>
            </el-select>
            <el-input v-model="currentCase.url" :placeholder="urlPlaceholder"></el-input>
            <el-select v-model="currentCase.environment_id" clearable class="env-select" placeholder="环境">
              <el-option v-for="item in environments" :key="item.id" :label="item.name" :value="item.id"></el-option>
            </el-select>
            <el-button type="primary" icon="el-icon-video-play" :loading="running" @click="runCase">发送</el-button>
            <el-dropdown split-button type="success" @click="saveCase" @command="handleCaseCommand">
              保存
              <el-dropdown-menu slot="dropdown">
                <el-dropdown-item command="copy">复制为新用例</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
              </el-dropdown-menu>
            </el-dropdown>
          </div>

          <el-form label-width="80px" size="small" class="case-form">
            <el-form-item label="接口名称">
              <el-input v-model="currentCase.name" placeholder="例如：登录接口"></el-input>
            </el-form-item>
            <el-form-item label="所属项目">
              <el-select v-model="currentCase.project_id" clearable placeholder="可选，选择后走项目权限">
                <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id"></el-option>
              </el-select>
            </el-form-item>
          </el-form>

          <el-tabs v-model="activeTab" class="request-tabs">
            <el-tab-pane label="Params" name="params">
              <json-editor v-model="currentCase.paramsText" placeholder='{"page": 1, "size": 20}'></json-editor>
            </el-tab-pane>
            <el-tab-pane label="Headers" name="headers">
              <json-editor v-model="currentCase.headersText" :placeholder="headersPlaceholder"></json-editor>
            </el-tab-pane>
            <el-tab-pane label="Body" name="body">
              <div class="body-tools">
                <el-radio-group v-model="currentCase.body_type" size="small">
                  <el-radio-button label="json">JSON</el-radio-button>
                  <el-radio-button label="form">Form</el-radio-button>
                  <el-radio-button label="raw">Raw</el-radio-button>
                  <el-radio-button label="none">None</el-radio-button>
                </el-radio-group>
              </div>
              <json-editor v-if="currentCase.body_type !== 'none'" v-model="currentCase.body" :placeholder="bodyPlaceholder"></json-editor>
            </el-tab-pane>
            <el-tab-pane label="断言" name="assertions">
              <div class="assertion-tools">
                <el-button size="mini" icon="el-icon-plus" @click="addAssertion('status_code')">状态码</el-button>
                <el-button size="mini" icon="el-icon-plus" @click="addAssertion('body_contains')">包含文本</el-button>
                <el-button size="mini" icon="el-icon-plus" @click="addAssertion('json_equals')">JSON等于</el-button>
              </div>
              <el-table :data="currentCase.assertions" border size="mini">
                <el-table-column label="类型" width="150">
                  <template slot-scope="scope">
                    <el-select v-model="scope.row.type" size="mini">
                      <el-option label="状态码" value="status_code"></el-option>
                      <el-option label="Body包含" value="body_contains"></el-option>
                      <el-option label="JSON字段等于" value="json_equals"></el-option>
                      <el-option label="Header存在" value="header_exists"></el-option>
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="JSON Path/Header" min-width="160">
                  <template slot-scope="scope">
                    <el-input v-model="scope.row.path" size="mini" placeholder="data.id / Content-Type"></el-input>
                  </template>
                </el-table-column>
                <el-table-column label="期望值" min-width="180">
                  <template slot-scope="scope">
                    <el-input v-model="scope.row.expected" size="mini" placeholder="200 / success"></el-input>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="70">
                  <template slot-scope="scope">
                    <el-button type="text" size="mini" @click="currentCase.assertions.splice(scope.$index, 1)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane label="环境变量" name="env">
              <div class="env-toolbar">
                <el-button type="primary" size="small" icon="el-icon-plus" @click="newEnvironment">新增环境</el-button>
                <el-button size="small" icon="el-icon-edit" :disabled="!currentEnvironment.id" @click="editEnvironment">编辑环境</el-button>
              </div>
              <el-table :data="environments" border size="mini" height="220" @row-click="chooseEnvironment">
                <el-table-column prop="name" label="环境名" width="180"></el-table-column>
                <el-table-column label="变量" min-width="260">
                  <template slot-scope="scope">
                    <code>{{ scope.row.variables }}</code>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template slot-scope="scope">
                    <el-button type="text" size="mini" @click.stop="removeEnvironment(scope.row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>

          <div class="response-panel" v-if="lastResult">
            <div class="response-head">
              <div>
                <el-tag :type="lastResult.success ? 'success' : 'danger'">{{ lastResult.success ? "通过" : "失败" }}</el-tag>
                <strong>Status {{ lastResult.response_status || "-" }}</strong>
                <span>{{ lastResult.elapsed_ms || 0 }} ms</span>
              </div>
              <el-button size="mini" icon="el-icon-refresh" @click="loadHistory">刷新历史</el-button>
            </div>
            <el-tabs v-model="responseTab">
              <el-tab-pane label="响应Body" name="body">
                <pre class="response-body">{{ prettyBody(lastResult.response_body) }}</pre>
              </el-tab-pane>
              <el-tab-pane label="响应Headers" name="headers">
                <pre class="response-body">{{ prettyJson(lastResult.response_headers) }}</pre>
              </el-tab-pane>
              <el-tab-pane label="断言结果" name="assertions">
                <el-table :data="lastResult.assertion_result || []" size="mini" border>
                  <el-table-column label="结果" width="90">
                    <template slot-scope="scope">
                      <el-tag size="mini" :type="scope.row.success ? 'success' : 'danger'">{{ scope.row.success ? "通过" : "失败" }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="name" label="名称" min-width="160"></el-table-column>
                  <el-table-column prop="expected" label="期望" min-width="160"></el-table-column>
                  <el-table-column prop="actual" label="实际" min-width="160"></el-table-column>
                  <el-table-column prop="error" label="错误" min-width="180"></el-table-column>
                </el-table>
              </el-tab-pane>
              <el-tab-pane label="执行历史" name="history">
                <el-table :data="history" size="mini" border height="260">
                  <el-table-column prop="created_time" label="时间" width="160"></el-table-column>
                  <el-table-column prop="method" label="方法" width="80"></el-table-column>
                  <el-table-column prop="response_status" label="状态" width="80"></el-table-column>
                  <el-table-column prop="elapsed_ms" label="耗时ms" width="90"></el-table-column>
                  <el-table-column label="结果" width="80">
                    <template slot-scope="scope">
                      <el-tag size="mini" :type="scope.row.success ? 'success' : 'danger'">{{ scope.row.success ? "通过" : "失败" }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="url" label="URL" min-width="260" show-overflow-tooltip></el-table-column>
                </el-table>
              </el-tab-pane>
            </el-tabs>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-dialog title="接口测试环境" :visible.sync="envDialogVisible" width="620px">
      <el-form label-width="80px">
        <el-form-item label="环境名">
          <el-input v-model="envForm.name"></el-input>
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select v-model="envForm.project_id" clearable placeholder="可选">
            <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="变量JSON">
          <json-editor v-model="envForm.variablesText" :placeholder="envPlaceholder"></json-editor>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="envForm.description" type="textarea"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="envDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEnvironment">保存</el-button>
      </div>
    </el-dialog>
  </section>
</template>

<script>
import {
  delete_api_case,
  delete_api_environment,
  get_api_case_info,
  get_api_environment_info,
  get_api_run_history,
  get_project_info,
  run_api_case,
  save_api_case,
  save_api_environment,
} from "../../api/api";

const JsonEditor = {
  props: ["value", "placeholder"],
  template: '<el-input class="json-editor" type="textarea" :rows="8" :value="value" :placeholder="placeholder" @input="$emit(\'input\', $event)"></el-input>',
};

function emptyCase() {
  return {
    id: "",
    name: "",
    project_id: "",
    environment_id: "",
    method: "GET",
    url: "",
    headersText: "{}",
    paramsText: "{}",
    body_type: "json",
    body: "{\n  \n}",
    assertions: [{ type: "status_code", expected: "200", path: "" }],
  };
}

export default {
  components: { JsonEditor },
  data() {
    return {
      methods: ["GET", "POST", "PUT", "PATCH", "DELETE"],
      activeTab: "params",
      responseTab: "body",
      urlPlaceholder: "https://api.example.com/users/{{id}}",
      headersPlaceholder: '{"Authorization": "Bearer {{token}}"}',
      envPlaceholder: '{"host": "http://127.0.0.1:5400", "token": "xxx"}',
      caseLoading: false,
      running: false,
      envDialogVisible: false,
      filters: { keyword: "", project_id: "" },
      cases: [],
      projects: [],
      environments: [],
      currentCase: emptyCase(),
      currentEnvironment: {},
      envForm: { id: "", name: "", project_id: "", variablesText: "{\n  \n}", description: "" },
      lastResult: null,
      history: [],
    };
  },
  computed: {
    bodyPlaceholder() {
      return this.currentCase.body_type === "form" ? '{"username": "admin"}' : '{\n  "name": "demo"\n}';
    },
  },
  methods: {
    parseJson(text, fallback) {
      if (!text || !String(text).trim()) {
        return fallback;
      }
      try {
        return JSON.parse(text);
      } catch (e) {
        this.$message.warning("JSON格式不正确：" + e.message);
        throw e;
      }
    },
    prettyJson(value) {
      try {
        return JSON.stringify(typeof value === "string" ? JSON.parse(value) : value, null, 2);
      } catch (e) {
        return value || "";
      }
    },
    prettyBody(value) {
      return this.prettyJson(value);
    },
    normalizeCase(row) {
      return {
        id: row.id || "",
        name: row.name || "",
        project_id: row.project_id || "",
        environment_id: row.environment_id || "",
        method: row.method || "GET",
        url: row.url || "",
        headersText: this.prettyJson(row.headers || {}),
        paramsText: this.prettyJson(row.params || {}),
        body_type: row.body_type || "json",
        body: row.body || "",
        assertions: row.assertions && row.assertions.length ? row.assertions : [],
      };
    },
    methodType(method) {
      return { GET: "success", POST: "primary", PUT: "warning", PATCH: "warning", DELETE: "danger" }[method] || "info";
    },
    async loadProjects() {
      await get_project_info({ page_no: 0, page_size: 1000, name: "" }).then((res) => {
        if (res.data && res.data.code === 200) {
          this.projects = res.data.data || [];
        } else {
          this.projects = [];
        }
      }).catch(() => {
        this.projects = [];
      });
    },
    async loadCases() {
      this.caseLoading = true;
      const params = { page_no: 0, page_size: 1000, keyword: this.filters.keyword, project_id: this.filters.project_id };
      await get_api_case_info(params).then((res) => {
        if (!res.data || res.data.code !== 200) {
          this.$message.warning((res.data && res.data.msg) || "接口测试用例加载失败");
          this.cases = [];
          return;
        }
        this.cases = res.data.data || [];
      }).catch((err) => {
        this.cases = [];
        this.$message.warning((err.response && err.response.data && err.response.data.msg) || "接口测试用例加载失败，请确认后端已重启");
      }).finally(() => {
        this.caseLoading = false;
      });
    },
    async loadEnvironments() {
      await get_api_environment_info({ project_id: this.filters.project_id }).then((res) => {
        if (res.data && res.data.code === 200) {
          this.environments = res.data.data || [];
        } else {
          this.environments = [];
        }
      }).catch(() => {
        this.environments = [];
      });
    },
    handleProjectChange() {
      this.loadCases();
      this.loadEnvironments();
    },
    selectCase(row) {
      this.currentCase = this.normalizeCase(row);
      this.lastResult = null;
      this.loadHistory();
    },
    newCase() {
      this.currentCase = emptyCase();
      this.currentCase.project_id = this.filters.project_id || "";
      this.lastResult = null;
      this.history = [];
    },
    payloadFromCase() {
      return {
        id: this.currentCase.id,
        name: this.currentCase.name,
        project_id: this.currentCase.project_id,
        environment_id: this.currentCase.environment_id,
        method: this.currentCase.method,
        url: this.currentCase.url,
        headers: this.parseJson(this.currentCase.headersText, {}),
        params: this.parseJson(this.currentCase.paramsText, {}),
        body_type: this.currentCase.body_type,
        body: this.currentCase.body_type === "none" ? "" : this.currentCase.body,
        assertions: this.currentCase.assertions || [],
      };
    },
    async saveCase() {
      const payload = this.payloadFromCase();
      const res = await save_api_case(payload);
      if (!res.data || res.data.code !== 200) {
        this.$message.warning((res.data && res.data.msg) || "保存失败");
        return;
      }
      this.$message.success(res.data.msg);
      this.currentCase = this.normalizeCase(res.data.data);
      this.loadCases();
    },
    async runCase() {
      const payload = this.payloadFromCase();
      this.running = true;
      await run_api_case(payload).then((res) => {
        if (!res.data || res.data.code !== 200) {
          this.$message.warning((res.data && res.data.msg) || "执行失败");
          return;
        }
        this.lastResult = res.data.data;
        this.responseTab = "body";
        this.loadCases();
        this.loadHistory();
      }).finally(() => {
        this.running = false;
      });
    },
    handleCaseCommand(command) {
      if (command === "copy") {
        this.currentCase.id = "";
        this.currentCase.name = this.currentCase.name + "_copy";
      }
      if (command === "delete") {
        this.removeCase();
      }
    },
    async removeCase() {
      if (!this.currentCase.id) {
        return;
      }
      await this.$confirm("确认删除这个接口用例？", "提示", { type: "warning" });
      const res = await delete_api_case({ id: this.currentCase.id });
      if (res.data && res.data.code === 200) {
        this.$message.success(res.data.msg);
        this.newCase();
        this.loadCases();
      } else {
        this.$message.warning((res.data && res.data.msg) || "删除失败");
      }
    },
    addAssertion(type) {
      this.currentCase.assertions.push({ type, path: "", expected: type === "status_code" ? "200" : "" });
    },
    chooseEnvironment(row) {
      this.currentEnvironment = row;
      this.currentCase.environment_id = row.id;
    },
    newEnvironment() {
      this.envForm = { id: "", name: "", project_id: this.filters.project_id || "", variablesText: "{\n  \n}", description: "" };
      this.envDialogVisible = true;
    },
    editEnvironment() {
      this.envForm = {
        id: this.currentEnvironment.id,
        name: this.currentEnvironment.name,
        project_id: this.currentEnvironment.project_id || "",
        variablesText: this.prettyJson(this.currentEnvironment.variables || {}),
        description: this.currentEnvironment.description || "",
      };
      this.envDialogVisible = true;
    },
    async saveEnvironment() {
      const payload = {
        id: this.envForm.id,
        name: this.envForm.name,
        project_id: this.envForm.project_id,
        variables: this.parseJson(this.envForm.variablesText, {}),
        description: this.envForm.description,
      };
      const res = await save_api_environment(payload);
      if (!res.data || res.data.code !== 200) {
        this.$message.warning((res.data && res.data.msg) || "保存失败");
        return;
      }
      this.$message.success(res.data.msg);
      this.envDialogVisible = false;
      this.loadEnvironments();
    },
    async removeEnvironment(row) {
      await this.$confirm("确认删除这个环境？", "提示", { type: "warning" });
      const res = await delete_api_environment({ id: row.id });
      if (res.data && res.data.code === 200) {
        this.$message.success(res.data.msg);
        this.loadEnvironments();
      } else {
        this.$message.warning((res.data && res.data.msg) || "删除失败");
      }
    },
    async loadHistory() {
      if (!this.currentCase.id) {
        return;
      }
      const res = await get_api_run_history({ case_id: this.currentCase.id, limit: 20 });
      if (res.data && res.data.code === 200) {
        this.history = res.data.data || [];
      }
    },
  },
  mounted() {
    this.loadProjects();
    this.loadCases();
    this.loadEnvironments();
  },
};
</script>

<style scoped>
.api-test-page {
  padding: 10px;
}
.api-side,
.api-main {
  background: #fff;
  border: 1px solid #e5eaf3;
  padding: 12px;
}
.api-side-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}
.api-side-toolbar .el-input,
.api-side-toolbar .el-select {
  flex: 1;
}
.case-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  line-height: 1.35;
}
.case-row strong {
  color: #1f4f99;
}
.case-row span {
  color: #6b778c;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.request-line {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
}
.method-select {
  width: 110px;
}
.env-select {
  width: 150px;
}
.case-form {
  max-width: 720px;
}
.request-tabs {
  margin-top: 6px;
}
.body-tools,
.assertion-tools,
.env-toolbar {
  margin-bottom: 10px;
}
.json-editor /deep/ textarea {
  font-family: Consolas, "Courier New", monospace;
  font-size: 13px;
  line-height: 1.55;
}
.response-panel {
  margin-top: 14px;
  border-top: 1px solid #e5eaf3;
  padding-top: 12px;
}
.response-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.response-head div {
  display: flex;
  align-items: center;
  gap: 10px;
}
.response-body {
  min-height: 260px;
  max-height: 420px;
  overflow: auto;
  margin: 0;
  padding: 12px;
  color: #24364b;
  background: #f7f9fc;
  border: 1px solid #e1e7ef;
  font-family: Consolas, "Courier New", monospace;
  line-height: 1.55;
}
code {
  color: #4b6078;
}
</style>
