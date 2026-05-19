<template>
  <section class="dashboard-page">
    <div class="dashboard-head">
      <div>
        <h2>首页看板</h2>
        <p>平台整体执行概览</p>
      </div>
      <el-button type="primary" icon="el-icon-refresh" :loading="loading" @click="loadStats">刷新</el-button>
    </div>

    <div class="stat-grid" v-loading="loading">
      <div
        v-for="item in statCards"
        :key="item.key"
        class="stat-card"
        :class="'stat-card-' + item.tone"
      >
        <div class="stat-icon">
          <i :class="item.icon"></i>
        </div>
        <div class="stat-content">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <em>{{ item.desc }}</em>
        </div>
      </div>
    </div>

    <div class="trend-panel">
      <div class="panel-head">
        <div>
          <h3>今日执行趋势</h3>
          <p>按小时统计执行次数、通过率和失败数</p>
        </div>
      </div>
      <div ref="todayTrendChart" class="trend-chart"></div>
    </div>

    <div class="pool-panel">
      <div class="panel-head compact">
        <div>
          <h3>进程池占用情况</h3>
          <p>当前测试集和测试任务进程池的运行、排队和空闲数量</p>
        </div>
        <el-tag size="small" type="info">总容量 {{ processPool.max_workers || 0 }}</el-tag>
      </div>
      <div class="pool-grid">
        <div class="pool-total-card running">
          <span>运行中</span>
          <strong>{{ processPool.running || 0 }}</strong>
        </div>
        <div class="pool-total-card queued">
          <span>排队中</span>
          <strong>{{ processPool.queued || 0 }}</strong>
        </div>
        <div class="pool-total-card idle">
          <span>空闲数</span>
          <strong>{{ processPool.idle || 0 }}</strong>
        </div>
      </div>
      <div class="pool-detail-grid">
        <div v-for="item in processPoolDetails" :key="item.key" class="pool-detail-card">
          <div class="pool-detail-head">
            <strong>{{ item.name }}</strong>
            <span>容量 {{ item.max_workers || 0 }}</span>
          </div>
          <div class="pool-detail-values">
            <span>运行 {{ item.running || 0 }}</span>
            <span>排队 {{ item.queued || 0 }}</span>
            <span>空闲 {{ item.idle || 0 }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="running-panel">
      <div class="panel-head">
        <div>
          <h3>当前运行中任务</h3>
          <p>正在执行的测试集和测试任务</p>
        </div>
        <el-tag size="small" type="primary">运行中 {{ runningItems.length }}</el-tag>
      </div>
      <el-table :data="runningItems" stripe border>
        <el-table-column label="类型" width="90">
          <template slot-scope="scope">
            <el-tag size="mini" :type="scope.row.type === 'testtask' ? 'warning' : 'success'">
              {{ scope.row.type_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="名称" min-width="220" show-overflow-tooltip>
          <template slot-scope="scope">
            <div class="running-name">{{ scope.row.name }}</div>
            <div class="running-sub">
              <span v-if="scope.row.project_name">项目：{{ scope.row.project_name }}</span>
              <span v-if="scope.row.progress">当前：{{ scope.row.progress }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="run_id" label="run_id" width="140" show-overflow-tooltip></el-table-column>
        <el-table-column label="进度" width="190">
          <template slot-scope="scope">
            <el-progress :percentage="progressPercentage(scope.row)" :format="formatProgress"></el-progress>
          </template>
        </el-table-column>
        <el-table-column prop="run_by_name" label="执行人" width="100"></el-table-column>
        <el-table-column prop="updated_time" label="更新时间" width="170"></el-table-column>
      </el-table>
      <div v-if="!runningItems.length" class="running-empty">当前没有运行中的测试集或测试任务</div>
    </div>

    <div class="dashboard-grid">
      <div class="info-panel">
        <div class="panel-head compact">
          <div>
            <h3>最近失败 / 连续失败</h3>
            <p>优先展示最近 failed/error 报告和连续失败项目</p>
          </div>
        </div>
        <div class="split-block">
          <div class="block-title">最近失败</div>
          <el-table :data="stats.recent_failures" size="mini" stripe height="245">
            <el-table-column label="项目 / 报告" min-width="220" show-overflow-tooltip>
              <template slot-scope="scope">
                <div class="main-text">{{ scope.row.project_name || '-' }}</div>
                <div class="sub-text">{{ scope.row.title }}</div>
              </template>
            </el-table-column>
            <el-table-column label="失败" width="86">
              <template slot-scope="scope">
                <span class="danger-text">{{ scope.row.fail_count || 0 }}</span>
                <span class="muted-text"> / {{ scope.row.error_count || 0 }}</span>
              </template>
            </el-table-column>
            <el-table-column label="通过率" width="92">
              <template slot-scope="scope">{{ passRateText(scope.row.pass_rate) }}</template>
            </el-table-column>
            <el-table-column prop="updated_time" label="时间" width="145"></el-table-column>
          </el-table>
        </div>
        <div class="split-block last">
          <div class="block-title">连续失败</div>
          <div v-if="!(stats.continuous_failures || []).length" class="empty-line">暂无连续失败项目</div>
          <div v-for="item in stats.continuous_failures" :key="'cf-' + item.project_id" class="risk-row">
            <div>
              <div class="main-text">{{ item.project_name }}</div>
              <div class="sub-text">最近 run_id：{{ item.last_run_id || '-' }} · {{ item.last_run_time || '-' }}</div>
            </div>
            <div class="risk-count">连续 {{ item.consecutive_failed }} 次</div>
          </div>
        </div>
      </div>

      <div class="info-panel">
        <div class="panel-head compact">
          <div>
            <h3>项目健康状态</h3>
            <p>按用例、测试集、最近执行和连续失败综合判断</p>
          </div>
        </div>
        <div class="health-summary">
          <div class="health-card ok"><span>健康</span><strong>{{ healthSummary.ok || 0 }}</strong></div>
          <div class="health-card warning"><span>需关注</span><strong>{{ healthSummary.warning || 0 }}</strong></div>
          <div class="health-card error"><span>异常</span><strong>{{ healthSummary.error || 0 }}</strong></div>
        </div>
        <el-table :data="stats.project_health_items" size="mini" stripe height="330">
          <el-table-column label="项目" min-width="170" show-overflow-tooltip>
            <template slot-scope="scope">
              <div class="main-text">{{ scope.row.project_name }}</div>
              <div class="sub-text">{{ scope.row.business_department || '未设置部门' }}</div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="86">
            <template slot-scope="scope">
              <el-tag size="mini" :type="healthTagType(scope.row.status)">{{ scope.row.label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="最近通过率" width="105">
            <template slot-scope="scope">{{ passRateText(scope.row.last_pass_rate) }}</template>
          </el-table-column>
          <el-table-column label="摘要" min-width="180" show-overflow-tooltip>
            <template slot-scope="scope">{{ scope.row.summary }}</template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <div class="info-panel department-panel">
      <div class="panel-head compact">
        <div>
          <h3>业务部门质量概览</h3>
          <p>近 7 天按业务部门聚合报告、通过率和失败错误数</p>
        </div>
      </div>
      <el-table :data="stats.department_quality" stripe border>
        <el-table-column prop="name" label="业务部门" min-width="160" show-overflow-tooltip></el-table-column>
        <el-table-column prop="project_count" label="项目数" width="90"></el-table-column>
        <el-table-column prop="report_count" label="报告数" width="90"></el-table-column>
        <el-table-column label="通过率" width="220">
          <template slot-scope="scope">
            <div class="rate-cell">
              <el-progress :percentage="progressPercentage({ schedule: scope.row.pass_rate || 0 })" :show-text="false"></el-progress>
              <span>{{ passRateText(scope.row.pass_rate) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="all_count" label="用例总数" width="100"></el-table-column>
        <el-table-column label="失败/错误" width="110">
          <template slot-scope="scope">
            <span class="danger-text">{{ scope.row.fail_count || 0 }}</span>
            <span class="muted-text"> / {{ scope.row.error_count || 0 }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </section>
</template>

<script>
import echarts from "echarts";
import { get_home_stats } from "../../api/api";

export default {
  data() {
    return {
      loading: false,
      chart: null,
      stats: {
        project_count: 0,
        case_count: 0,
        testset_count: 0,
        task_count: 0,
        today_run_count: 0,
        today_pass_rate: 0,
        running_count: 0,
        running_testset_count: 0,
        running_task_count: 0,
        failed_pending_count: 0,
        today_trend: [],
        running_testsets: [],
        running_tasks: [],
        recent_failures: [],
        continuous_failures: [],
        project_health_summary: { ok: 0, warning: 0, error: 0 },
        project_health_items: [],
        department_quality: [],
        process_pool_status: {
          running: 0,
          queued: 0,
          idle: 0,
          max_workers: 0,
          testset: {},
          testtask: {},
        },
      },
    };
  },
  computed: {
    processPool() {
      return this.stats.process_pool_status || { running: 0, queued: 0, idle: 0, max_workers: 0, testset: {}, testtask: {} };
    },
    processPoolDetails() {
      const pool = this.processPool;
      return [
        Object.assign({ key: "testset", name: "测试集进程池", max_workers: 0, running: 0, queued: 0, idle: 0 }, pool.testset || {}),
        Object.assign({ key: "testtask", name: "测试任务进程池", max_workers: 0, running: 0, queued: 0, idle: 0 }, pool.testtask || {}),
      ];
    },
    healthSummary() {
      return this.stats.project_health_summary || { ok: 0, warning: 0, error: 0 };
    },
    statCards() {
      return [
        { key: "project", label: "脚本项目", value: this.stats.project_count || 0, desc: "当前可见项目", icon: "fa fa-folder-open", tone: "blue" },
        { key: "case", label: "用例总数", value: this.stats.case_count || 0, desc: "已入库用例", icon: "fa fa-list", tone: "green" },
        { key: "testset", label: "测试集", value: this.stats.testset_count || 0, desc: "可执行集合", icon: "fa fa-cubes", tone: "cyan" },
        { key: "task", label: "测试任务", value: this.stats.task_count || 0, desc: "编排任务数", icon: "fa fa-tasks", tone: "purple" },
        { key: "today_run", label: "今日执行", value: this.stats.today_run_count || 0, desc: "今日报告数", icon: "fa fa-play-circle", tone: "orange" },
        { key: "today_rate", label: "今日通过率", value: (this.stats.today_pass_rate || 0) + "%", desc: "按今日用例数统计", icon: "fa fa-line-chart", tone: "green" },
        { key: "running", label: "运行中", value: this.stats.running_count || 0, desc: "测试集 " + (this.stats.running_testset_count || 0) + " / 任务 " + (this.stats.running_task_count || 0), icon: "fa fa-spinner", tone: "blue" },
        { key: "pool", label: "进程池", value: (this.processPool.running || 0) + "/" + (this.processPool.max_workers || 0), desc: "排队 " + (this.processPool.queued || 0) + " / 空闲 " + (this.processPool.idle || 0), icon: "fa fa-server", tone: "purple" },
        { key: "failed", label: "失败待处理", value: this.stats.failed_pending_count || 0, desc: "今日 failed/error", icon: "fa fa-exclamation-triangle", tone: "red" },
      ];
    },
    runningItems() {
      const testsets = (this.stats.running_testsets || []).map(item => Object.assign({}, item, { type: "testset", type_name: "测试集", name: item.title || "-" }));
      const tasks = (this.stats.running_tasks || []).map(item => Object.assign({}, item, { type: "testtask", type_name: "测试任务", name: item.name || "-" }));
      return testsets.concat(tasks).slice(0, 12);
    },
  },
  methods: {
    async loadStats() {
      this.loading = true;
      await get_home_stats({}).then((res) => {
        if (res.data.code !== 200) {
          this.$message({ message: res.data.msg || "获取首页统计失败", type: "warning" });
          return;
        }
        this.stats = Object.assign({}, this.stats, res.data.data || {});
        this.$nextTick(() => { this.renderTrendChart(); });
      }).finally(() => { this.loading = false; });
    },
    renderTrendChart() {
      if (!this.$refs.todayTrendChart) return;
      if (!this.chart) this.chart = echarts.init(this.$refs.todayTrendChart);
      const trend = this.stats.today_trend || [];
      this.chart.setOption({
        tooltip: { trigger: "axis" },
        legend: { top: 0, data: ["执行次数", "通过率", "失败数"] },
        grid: { left: 40, right: 48, top: 48, bottom: 32 },
        xAxis: { type: "category", boundaryGap: true, data: trend.map(item => item.hour), axisLabel: { color: "#606266" } },
        yAxis: [
          { type: "value", name: "次数", minInterval: 1, axisLabel: { color: "#606266" } },
          { type: "value", name: "通过率", min: 0, max: 100, axisLabel: { formatter: "{value}%" } },
        ],
        series: [
          { name: "执行次数", type: "bar", barMaxWidth: 18, itemStyle: { normal: { color: "#409eff" } }, data: trend.map(item => item.run_count || 0) },
          { name: "失败数", type: "bar", barMaxWidth: 18, itemStyle: { normal: { color: "#f56c6c" } }, data: trend.map(item => item.failed_count || 0) },
          { name: "通过率", type: "line", yAxisIndex: 1, smooth: true, symbolSize: 6, itemStyle: { normal: { color: "#67c23a" } }, data: trend.map(item => item.pass_rate || 0) },
        ],
      });
    },
    progressPercentage(row) {
      const value = Number(row.schedule || row.set_schedule || 0);
      if (value < 0) return 0;
      if (value > 100) return 100;
      return value;
    },
    formatProgress(percentage) { return percentage === 100 ? "完成" : percentage + "%"; },
    passRateText(value) {
      if (value === null || value === undefined || value === "") return "-";
      return Number(value).toFixed(2).replace(/.00$/, "") + "%";
    },
    healthTagType(status) {
      if (status === "ok") return "success";
      if (status === "warning") return "warning";
      if (status === "error") return "danger";
      return "info";
    },
    resizeChart() { if (this.chart) this.chart.resize(); },
  },
  mounted() {
    this.loadStats();
    window.addEventListener("resize", this.resizeChart);
  },
  beforeDestroy() {
    window.removeEventListener("resize", this.resizeChart);
    if (this.chart) {
      this.chart.dispose();
      this.chart = null;
    }
  },
};
</script>

<style scoped>
.dashboard-page { padding: 10px; }
.dashboard-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.dashboard-head h2 { margin: 0 0 6px; color: #1f2d3d; font-size: 20px; }
.dashboard-head p { margin: 0; color: #8492a6; font-size: 13px; }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
.stat-card { display: flex; align-items: center; min-height: 104px; padding: 18px; border: 1px solid #e5e9f2; border-radius: 6px; background: #fff; box-sizing: border-box; }
.stat-icon { display: flex; align-items: center; justify-content: center; width: 46px; height: 46px; margin-right: 14px; border-radius: 6px; color: #fff; font-size: 20px; }
.stat-content { display: flex; flex-direction: column; min-width: 0; }
.stat-content span { color: #606266; font-size: 13px; }
.stat-content strong { margin-top: 5px; color: #1f2d3d; font-size: 26px; line-height: 1.1; }
.stat-content em { margin-top: 6px; color: #909399; font-size: 12px; font-style: normal; }
.stat-card-blue .stat-icon { background: #409eff; }
.stat-card-green .stat-icon { background: #67c23a; }
.stat-card-cyan .stat-icon { background: #13c2c2; }
.stat-card-purple .stat-icon { background: #7b61ff; }
.stat-card-orange .stat-icon { background: #e6a23c; }
.stat-card-red .stat-icon { background: #f56c6c; }
.trend-panel, .running-panel, .pool-panel, .info-panel { margin-top: 14px; padding: 18px; border: 1px solid #e5e9f2; border-radius: 6px; background: #fff; }
.dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(480px, 1fr)); gap: 14px; }
.pool-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px; }
.pool-total-card { padding: 14px; border-radius: 6px; border: 1px solid #e5e9f2; background: #f8fafc; }
.pool-total-card span { display: block; color: #606266; font-size: 12px; }
.pool-total-card strong { display: block; margin-top: 6px; font-size: 28px; line-height: 1; }
.pool-total-card.running strong { color: #409eff; }
.pool-total-card.queued strong { color: #e6a23c; }
.pool-total-card.idle strong { color: #67c23a; }
.pool-detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
.pool-detail-card { padding: 12px; border: 1px solid #ebeef5; border-radius: 6px; background: #fff; }
.pool-detail-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; color: #303133; }
.pool-detail-head span { color: #909399; font-size: 12px; }
.pool-detail-values { display: flex; gap: 12px; color: #606266; font-size: 13px; }
.panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.panel-head.compact { margin-bottom: 12px; }
.panel-head h3 { margin: 0 0 5px; color: #1f2d3d; font-size: 16px; }
.panel-head p { margin: 0; color: #909399; font-size: 12px; }
.trend-chart { width: 100%; height: 320px; }
.running-name, .main-text { color: #1f2d3d; font-weight: 600; line-height: 1.5; }
.running-sub, .sub-text { color: #909399; font-size: 12px; line-height: 1.5; }
.running-sub span + span { margin-left: 12px; }
.running-empty, .empty-line { padding: 16px 0 2px; color: #909399; text-align: center; font-size: 13px; }
.split-block + .split-block { margin-top: 12px; }
.block-title { margin-bottom: 8px; color: #303133; font-size: 13px; font-weight: 700; }
.risk-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border: 1px solid #fde2e2; border-radius: 6px; background: #fff7f7; }
.risk-row + .risk-row { margin-top: 8px; }
.risk-count, .danger-text { color: #f56c6c; font-weight: 700; }
.muted-text { color: #909399; }
.health-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 12px; }
.health-card { padding: 12px; border-radius: 6px; border: 1px solid #ebeef5; background: #f8fafc; }
.health-card span { display: block; color: #606266; font-size: 12px; }
.health-card strong { display: block; margin-top: 5px; font-size: 24px; line-height: 1; }
.health-card.ok strong { color: #67c23a; }
.health-card.warning strong { color: #e6a23c; }
.health-card.error strong { color: #f56c6c; }
.department-panel { margin-bottom: 18px; }
.rate-cell { display: grid; grid-template-columns: 1fr 54px; align-items: center; gap: 8px; }
</style>
