<template>
  <section class="perf-page">
    <div class="perf-side">
      <div class="panel-head">
        <div>
          <strong>{{ mode === "endpoint" ? "性能接口" : "性能场景" }}</strong>
          <span>{{ total }} 条</span>
        </div>
        <el-button size="mini" icon="el-icon-refresh" @click="loadList">刷新</el-button>
      </div>
      <div class="toolbar">
        <el-input v-model="filters.keyword" size="small" clearable placeholder="名称关键字" @keyup.enter.native="loadList"></el-input>
        <el-button size="small" type="primary" icon="el-icon-search" @click="loadList">查询</el-button>
      </div>
      <el-tabs v-model="mode" @tab-click="loadList">
        <el-tab-pane label="接口管理" name="endpoint"></el-tab-pane>
        <el-tab-pane label="场景编排" name="scenario"></el-tab-pane>
      </el-tabs>
      <el-button class="new-btn" type="success" size="small" icon="el-icon-plus" @click="mode === 'endpoint' ? newEndpoint() : newScenario()">
        {{ mode === "endpoint" ? "新增接口" : "新增场景" }}
      </el-button>
      <el-table :data="list" size="mini" height="560" border @row-click="selectRow">
        <el-table-column label="名称" min-width="220">
          <template slot-scope="scope">
            <div class="name-cell">
              <strong>{{ scope.row.name }}</strong>
              <span v-if="mode === 'endpoint'">{{ scope.row.method }} {{ scope.row.url }}</span>
              <span v-else>{{ (scope.row.endpoint_ids || []).length }} 个接口 · {{ scope.row.users }} 用户 · {{ scope.row.run_time }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column v-if="mode === 'scenario'" label="状态" width="80">
          <template slot-scope="scope">
            <el-tag size="mini" :type="statusType(scope.row.last_status)">{{ scope.row.last_status || "未运行" }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="perf-main">
      <div class="main-head">
        <div>
          <span class="kicker">{{ mode === "endpoint" ? "PERF ENDPOINT" : "PERF SCENARIO" }}</span>
          <h2>{{ mode === "endpoint" ? endpointForm.name || "新增性能接口" : scenarioForm.name || "新增性能场景" }}</h2>
          <p>性能测试模块独立于 pytest 和接口测试，使用 Locust 执行并生成单独历史与 HTML 报告。</p>
        </div>
        <div class="actions">
          <el-button v-if="mode === 'endpoint'" type="primary" icon="el-icon-check" @click="saveEndpoint">保存接口</el-button>
          <el-button v-if="mode === 'endpoint' && endpointForm.id" type="danger" icon="el-icon-delete" @click="deleteEndpoint">删除接口</el-button>
          <el-button v-if="mode === 'scenario'" type="primary" icon="el-icon-check" @click="saveScenario">保存场景</el-button>
          <el-button v-if="mode === 'scenario'" type="success" icon="el-icon-video-play" :loading="running" @click="runScenario">运行场景</el-button>
          <el-button v-if="mode === 'scenario' && currentRun && currentRun.run_status === 'running'" type="warning" icon="el-icon-video-pause" @click="stopRun">终止</el-button>
          <el-button v-if="mode === 'scenario' && scenarioForm.id" type="danger" icon="el-icon-delete" @click="deleteScenario">删除场景</el-button>
        </div>
      </div>

      <el-card v-if="mode === 'endpoint'" shadow="never">
        <el-form label-width="90px">
          <el-row :gutter="12">
            <el-col :span="12"><el-form-item label="接口名称"><el-input v-model="endpointForm.name"></el-input></el-form-item></el-col>
            <el-col :span="4"><el-form-item label="方法"><el-select v-model="endpointForm.method"><el-option v-for="m in methods" :key="m" :label="m" :value="m"></el-option></el-select></el-form-item></el-col>
            <el-col :span="4"><el-form-item label="权重"><el-input-number v-model="endpointForm.weight" :min="1" :max="100"></el-input-number></el-form-item></el-col>
          </el-row>
          <el-form-item label="URL"><el-input v-model="endpointForm.url" placeholder="/api/path 或完整 URL"></el-input></el-form-item>
          <el-tabs v-model="endpointTab">
            <el-tab-pane label="Headers" name="headers"><el-input type="textarea" :rows="8" v-model="endpointForm.headersText"></el-input></el-tab-pane>
            <el-tab-pane label="Params" name="params"><el-input type="textarea" :rows="8" v-model="endpointForm.paramsText"></el-input></el-tab-pane>
            <el-tab-pane label="Body" name="body">
              <el-select v-model="endpointForm.body_type" size="small"><el-option label="json" value="json"></el-option><el-option label="form" value="form"></el-option><el-option label="raw" value="raw"></el-option></el-select>
              <el-input class="mt8" type="textarea" :rows="8" v-model="endpointForm.body"></el-input>
            </el-tab-pane>
          </el-tabs>
          <el-form-item label="备注"><el-input v-model="endpointForm.description"></el-input></el-form-item>
        </el-form>
      </el-card>

      <template v-else>
        <el-card shadow="never">
          <el-form label-width="90px">
            <el-row :gutter="12">
              <el-col :span="8"><el-form-item label="场景名称"><el-input v-model="scenarioForm.name"></el-input></el-form-item></el-col>
              <el-col :span="4"><el-form-item label="用户数"><el-input-number v-model="scenarioForm.users" :min="1"></el-input-number></el-form-item></el-col>
              <el-col :span="4"><el-form-item label="启动速率"><el-input-number v-model="scenarioForm.spawn_rate" :min="0.1" :step="0.5"></el-input-number></el-form-item></el-col>
              <el-col :span="4"><el-form-item label="运行时长"><el-input v-model="scenarioForm.run_time" placeholder="30s/5m"></el-input></el-form-item></el-col>
            </el-row>
            <el-form-item label="Host"><el-input v-model="scenarioForm.host" placeholder="如 http://127.0.0.1:5400"></el-input></el-form-item>
            <el-form-item label="接口编排">
              <el-transfer
                v-model="scenarioForm.endpoint_ids"
                :data="endpointOptions"
                filterable
                :titles="['可选性能接口', '场景执行接口']"
                :props="{ key: 'id', label: 'label' }">
              </el-transfer>
            </el-form-item>
            <el-form-item label="备注"><el-input v-model="scenarioForm.description"></el-input></el-form-item>
          </el-form>
        </el-card>

        <el-card class="result-card" shadow="never">
          <div class="result-head">
            <div>
              <strong>实时指标与历史记录</strong>
              <span v-if="currentRun">run_id {{ currentRun.run_id }} · {{ currentRun.status_text || currentRun.run_status }}</span>
            </div>
            <el-button size="mini" icon="el-icon-refresh" @click="loadHistory">刷新历史</el-button>
          </div>
          <div class="metric-grid">
            <div><span>请求数</span><strong>{{ summaryValue('Request Count') }}</strong></div>
            <div><span>失败数</span><strong>{{ summaryValue('Failure Count') }}</strong></div>
            <div><span>平均响应</span><strong>{{ summaryValue('Average Response Time') }} ms</strong></div>
            <div><span>RPS</span><strong>{{ summaryValue('Requests/s') || summaryValue('Current RPS') }}</strong></div>
          </div>
          <el-tabs v-model="resultTab">
            <el-tab-pane label="实时明细" name="metrics">
              <el-table :data="metricRows" size="mini" border height="260">
                <el-table-column prop="method" label="方法" width="80"></el-table-column>
                <el-table-column prop="name" label="接口" min-width="240"></el-table-column>
                <el-table-column prop="num_requests" label="请求" width="80"></el-table-column>
                <el-table-column prop="num_failures" label="失败" width="80"></el-table-column>
                <el-table-column prop="avg_response_time" label="平均ms" width="100"></el-table-column>
                <el-table-column prop="rps" label="RPS" width="90"></el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane label="执行历史" name="history">
              <el-table :data="history" size="mini" border height="260" @row-click="selectHistory">
                <el-table-column prop="run_id" label="run_id" min-width="170"></el-table-column>
                <el-table-column prop="status_text" label="状态" width="90"></el-table-column>
                <el-table-column prop="elapsed_ms" label="耗时ms" width="90"></el-table-column>
                <el-table-column prop="run_by_name" label="执行人" width="100"></el-table-column>
                <el-table-column prop="created_time" label="时间" min-width="150"></el-table-column>
                <el-table-column label="报告" width="150">
                  <template slot-scope="scope">
                    <el-button type="text" size="mini" @click.stop="previewReport(scope.row)">预览</el-button>
                    <el-button type="text" size="mini" @click.stop="downloadReport(scope.row)">下载</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </template>
    </div>
  </section>
</template>

<script>
import axios from "axios";
import {
  get_url,
  get_perf_endpoint_info,
  save_perf_endpoint,
  delete_perf_endpoint,
  get_perf_scenario_info,
  save_perf_scenario,
  delete_perf_scenario,
  run_perf_scenario,
  stop_perf_run,
  get_perf_run_result,
  get_perf_run_history
} from "../../api/api";

export default {
  data() {
    return {
      mode: "endpoint",
      filters: { keyword: "" },
      list: [],
      total: 0,
      methods: ["GET", "POST", "PUT", "PATCH", "DELETE"],
      endpointTab: "headers",
      resultTab: "metrics",
      endpointForm: this.emptyEndpoint(),
      scenarioForm: this.emptyScenario(),
      endpointOptions: [],
      currentRun: null,
      history: [],
      running: false,
      pollTimer: null
    };
  },
  computed: {
    metricRows() {
      const rows = this.currentRun && this.currentRun.metrics ? (this.currentRun.metrics.stats || []) : [];
      return rows.map(item => Object.assign({}, item, {
        avg_response_time: this.formatMetric(item.avg_response_time),
        min_response_time: this.formatMetric(item.min_response_time),
        max_response_time: this.formatMetric(item.max_response_time),
        rps: this.formatMetric(item.current_rps || item.total_rps)
      }));
    }
  },
  created() {
    this.loadEndpointOptions();
    this.loadList();
  },
  beforeDestroy() {
    if (this.pollTimer) clearInterval(this.pollTimer);
  },
  methods: {
    emptyEndpoint() {
      return { id: "", name: "", method: "GET", url: "", headersText: "{}", paramsText: "{}", body_type: "json", body: "", weight: 1, description: "" };
    },
    emptyScenario() {
      return { id: "", name: "", endpoint_ids: [], users: 1, spawn_rate: 1, run_time: "1m", host: "", description: "" };
    },
    statusType(status) {
      if (status === "finished") return "success";
      if (status === "running" || status === "queued") return "warning";
      if (status === "failed" || status === "stopped") return "danger";
      return "info";
    },
    parseJson(text, fallback) {
      try { return JSON.parse(text || "{}"); } catch (e) { return fallback; }
    },
    stringifyJson(value) {
      return JSON.stringify(value || {}, null, 2);
    },
    loadList() {
      const api = this.mode === "endpoint" ? get_perf_endpoint_info : get_perf_scenario_info;
      api({ keyword: this.filters.keyword, page_size: 200 }).then(res => {
        const body = res.data || {};
        this.list = body.data || [];
        this.total = body.total || this.list.length;
      });
    },
    loadEndpointOptions() {
      get_perf_endpoint_info({ page_size: 500 }).then(res => {
        const rows = (res.data && res.data.data) || [];
        this.endpointOptions = rows.map(item => ({ id: item.id, label: `${item.name} [${item.method}] ${item.url}` }));
      });
    },
    selectRow(row) {
      if (this.mode === "endpoint") {
        this.endpointForm = Object.assign(this.emptyEndpoint(), row, {
          headersText: this.stringifyJson(row.headers),
          paramsText: this.stringifyJson(row.params)
        });
      } else {
        this.scenarioForm = Object.assign(this.emptyScenario(), row, {
          endpoint_ids: (row.endpoint_ids || []).map(item => Number(item))
        });
        this.loadHistory();
      }
    },
    newEndpoint() { this.endpointForm = this.emptyEndpoint(); },
    newScenario() { this.scenarioForm = this.emptyScenario(); this.currentRun = null; this.history = []; },
    saveEndpoint() {
      const payload = Object.assign({}, this.endpointForm, {
        headers: this.parseJson(this.endpointForm.headersText, {}),
        params: this.parseJson(this.endpointForm.paramsText, {})
      });
      save_perf_endpoint(payload).then(res => {
        this.$message.success(res.data.msg || "保存成功");
        this.loadList();
        this.loadEndpointOptions();
      });
    },
    deleteEndpoint() {
      delete_perf_endpoint({ id: this.endpointForm.id }).then(() => {
        this.$message.success("删除成功");
        this.newEndpoint();
        this.loadList();
        this.loadEndpointOptions();
      });
    },
    saveScenario() {
      save_perf_scenario(this.scenarioForm).then(res => {
        this.$message.success(res.data.msg || "保存成功");
        this.scenarioForm = Object.assign(this.emptyScenario(), res.data.data || {});
        this.loadList();
      });
    },
    deleteScenario() {
      delete_perf_scenario({ id: this.scenarioForm.id }).then(() => {
        this.$message.success("删除成功");
        this.newScenario();
        this.loadList();
      });
    },
    runScenario() {
      if (!this.scenarioForm.id) return this.$message.warning("请先保存场景");
      this.running = true;
      run_perf_scenario({ scenario_id: this.scenarioForm.id }).then(res => {
        this.currentRun = res.data.data;
        this.startPolling();
      });
    },
    stopRun() {
      if (!this.currentRun) return;
      this.$confirm(`确认终止本次性能测试吗？run_id：${this.currentRun.run_id}`, "终止确认", {
        confirmButtonText: "确认终止",
        cancelButtonText: "取消",
        type: "warning"
      }).then(() => {
        stop_perf_run({ run_id: this.currentRun.run_id }).then(res => {
          this.currentRun = res.data.data;
          this.$message.success("已发送终止请求");
        });
      }).catch(() => {});
    },
    startPolling() {
      if (this.pollTimer) clearInterval(this.pollTimer);
      this.pollTimer = setInterval(() => {
        if (!this.currentRun || !this.currentRun.run_id) return;
        get_perf_run_result({ run_id: this.currentRun.run_id }).then(res => {
          this.currentRun = res.data.data;
          if (!["queued", "running"].includes(this.currentRun.run_status)) {
            clearInterval(this.pollTimer);
            this.running = false;
            this.loadHistory();
            this.loadList();
          }
        });
      }, 2000);
    },
    loadHistory() {
      if (!this.scenarioForm.id) return;
      get_perf_run_history({ scenario_id: this.scenarioForm.id, page_size: 50 }).then(res => {
        this.history = (res.data && res.data.data) || [];
        if (!this.currentRun && this.history.length) this.currentRun = this.history[0];
      });
    },
    selectHistory(row) { this.currentRun = row; },
    formatMetric(value) {
      if (value === undefined || value === null || value === "") return 0;
      const number = Number(value);
      if (isNaN(number)) return value;
      return Math.round(number * 100) / 100;
    },
    summaryValue(name) {
      const summary = this.currentRun && this.currentRun.metrics ? (this.currentRun.metrics.summary || {}) : {};
      return this.formatMetric(summary[name]);
    },
    fetchReport(row, callback) {
      if (!row.report_path) return this.$message.warning("暂无报告文件");
      axios.post(`${get_url()}/report/report_content`, { filename: row.report_path }).then(res => callback(res.data));
    },
    previewReport(row) {
      this.fetchReport(row, html => {
        const win = window.open("", "_blank");
        if (!win) return this.$message.warning("浏览器拦截了报告窗口，请允许弹窗后重试");
        win.document.open();
        win.document.write(html);
        win.document.close();
      });
    },
    downloadReport(row) {
      this.fetchReport(row, html => {
        const blob = new Blob([html]);
        const link = document.createElement("a");
        link.download = row.report_path;
        link.href = URL.createObjectURL(blob);
        link.click();
        URL.revokeObjectURL(link.href);
      });
    }
  }
};
</script>

<style scoped>
.perf-page { display: grid; grid-template-columns: 500px 1fr; gap: 14px; padding: 14px; background: #f3f6fa; min-height: calc(100vh - 70px); }
.perf-side, .perf-main { background: #fff; border: 1px solid #dbe4ef; border-radius: 6px; padding: 12px; }
.panel-head, .main-head, .result-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; border-bottom: 1px solid #e5edf6; padding-bottom: 12px; margin-bottom: 12px; }
.panel-head span, .result-head span, .main-head p { color: #64748b; font-size: 12px; margin: 4px 0 0; }
.toolbar { display: grid; grid-template-columns: 1fr 80px; gap: 8px; margin-bottom: 10px; }
.new-btn { width: 100%; margin-bottom: 10px; }
.name-cell { display: flex; flex-direction: column; gap: 4px; }
.name-cell span { color: #64748b; font-size: 12px; overflow-wrap: anywhere; }
.kicker { color: #2563eb; font-size: 12px; font-weight: 800; }
.main-head h2 { margin: 4px 0; font-size: 22px; }
.actions { display: flex; gap: 8px; }
.mt8 { margin-top: 8px; }
.result-card { margin-top: 12px; }
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px; }
.metric-grid div { background: #f8fbff; border: 1px solid #e5edf6; border-radius: 6px; padding: 12px; }
.metric-grid span { display: block; color: #64748b; font-size: 12px; }
.metric-grid strong { font-size: 20px; }
</style>
