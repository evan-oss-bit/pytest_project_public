<template>
  <section class="project-page">
    <!--工具条-->
    <el-col :span="24" class="toolbar" style="padding-bottom: 0px">
      <el-form :inline="true" :model="filters">
        <el-col :span="20" justify="">
          <div><el-form-item>
            <el-button type="primary" icon="el-icon-search" v-on:click="getProtList">全部项目列表</el-button>
          </el-form-item></div>
          
          <el-form-item>
            <el-input v-model="filters.cfg_name" placeholder="脚本项目名称" clearable>
              <i slot="prefix" class="el-input__icon el-icon-search"></i>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-select
              v-model="filters.business_department_id"
              clearable
              filterable
              placeholder="业务部门"
              style="width: 180px"
              @change="getConfigList"
            >
              <el-option
                v-for="item in departmentOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              ></el-option>
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="el-icon-search" v-on:click="getConfigList">查询</el-button>
          </el-form-item>
         
          <div>
            <el-form-item>
              <el-button @click="handleAddEvent" type="primary"
                style="float: right; text-align: right; margin-left: 10px">新建脚本项目</el-button>
            </el-form-item>
          </div>
        </el-col>
      </el-form>
    </el-col>

    <!--列表-->
    <el-col :span="24" class="project-list-panel">
      <el-table :data="aioLst" highlight-current-row stripe height="650" v-loading="listLoading"
        @selection-change="selsChange" style="width: 100%" class="project-table">
        <!-- <el-table-column type="selection" width="2">
              </el-table-column> -->
        <el-table-column type="index" label="#" width="55"> </el-table-column>
        <el-table-column label="脚本项目" min-width="260" sortable prop="name">
          <template slot-scope="scope">
            <div class="project-name-cell">
              <el-button type="text" class="project-name-button" @click="openProjectDashboard(scope.row)">
                {{ scope.row.name }}
              </el-button>
              <div class="project-desc">{{ scope.row.description || "暂无描述" }}</div>
              <div class="project-owner">负责人：{{ scope.row.controller || "未设置" }}</div>
              <div class="project-owner" v-if="scope.row.git_status">
                Git：{{ scope.row.git_status.is_git_repo ? (scope.row.git_status.branch || "已接入") : (scope.row.git_status.message || "未接入") }}
                <span v-if="scope.row.git_status.commit"> @ {{ scope.row.git_status.commit }}</span>
              </div>
              <div class="project-tag-row" v-if="scope.row.tags">
                <el-tag
                  v-for="tag in splitTags(scope.row.tags)"
                  :key="scope.row.id + '-' + tag"
                  size="mini"
                  type="info"
                  effect="plain"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="业务部门" width="160" prop="business_department" sortable>
          <template slot-scope="scope">
            <el-tag size="mini" type="info" effect="plain">
              {{ scope.row.business_department || "未设置" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="项目标识" min-width="230">
          <template slot-scope="scope">
            <div class="project-meta-cell">
              <div class="meta-tag-line">
                <el-tag size="mini" :type="environmentTagType(scope.row.environment)">
                  {{ scope.row.environment || "test" }}
                </el-tag>
                <el-tag size="mini" type="warning">
                  {{ scope.row.priority || "P2" }}
                </el-tag>
                <el-tag size="mini" :type="maintStatusTagType(scope.row.maint_status)">
                  {{ maintStatusText(scope.row.maint_status) }}
                </el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="项目规模" width="260">
          <template slot-scope="scope">
            <div class="metric-row">
              <span class="metric-chip">用例 {{ scope.row.case_count || 0 }}</span>
              <span class="metric-chip">测试集 {{ scope.row.testset_count || 0 }}</span>
              <span class="metric-chip">任务 {{ scope.row.task_count || 0 }}</span>
              <span class="metric-chip">报告 {{ scope.row.report_count || 0 }}</span>
            </div>
            <div class="metric-row change-row">
              <span :class="changeChipClass(scope.row.script_added_count)">新增 {{ scope.row.script_added_count || 0 }}</span>
              <span :class="changeChipClass(scope.row.script_deleted_count, 'danger')">删除 {{ scope.row.script_deleted_count || 0 }}</span>
              <span :class="changeChipClass(scope.row.script_modified_count, 'warning')">修改 {{ scope.row.script_modified_count || 0 }}</span>
              <span :class="changeChipClass(scope.row.script_parse_error_count, 'danger')">解析错误 {{ scope.row.script_parse_error_count || 0 }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="最近执行" min-width="240">
          <template slot-scope="scope">
            <div v-if="scope.row.last_run_id" class="last-run-cell">
              <div class="last-run-title">
                <span>run_id：{{ scope.row.last_run_id }}</span>
                <span :class="passRateClass(scope.row.last_pass_rate)">{{ formatPassRate(scope.row.last_pass_rate) }}</span>
              </div>
              <div class="last-run-counts">
                <span>总 {{ scope.row.last_all_count || 0 }}</span>
                <span class="rate-good">过 {{ scope.row.last_pass_count || 0 }}</span>
                <span class="rate-bad">败 {{ scope.row.last_fail_count || 0 }}</span>
                <span class="rate-warn">错 {{ scope.row.last_error_count || 0 }}</span>
                <span>耗时 {{ formatDuration(scope.row.last_case_all_time) }}</span>
              </div>
              <div class="muted-text">{{ scope.row.last_run_time }}</div>
            </div>
            <span v-else class="muted-text">暂无执行记录</span>
          </template>
        </el-table-column>
        <el-table-column label="失败趋势" min-width="220">
          <template slot-scope="scope">
            <div v-if="scope.row.failure_trend && scope.row.failure_trend.sample_count" class="trend-cell">
              <div class="trend-bars">
                <span
                  v-for="(rate, index) in scope.row.failure_trend.pass_rates"
                  :key="'rate-' + index"
                  :title="'通过率 ' + formatPassRate(rate)"
                  :style="{ height: trendBarHeight(rate) }"
                  :class="['trend-bar', trendRateClass(rate)]"
                ></span>
              </div>
              <div class="trend-line">失败：{{ formatTrendList(scope.row.failure_trend.fail_counts) }}</div>
              <el-tag size="mini" :type="scope.row.failure_trend.is_continuous_failed ? 'danger' : 'success'">
                连续失败 {{ scope.row.failure_trend.consecutive_failed || 0 }} 次
              </el-tag>
            </div>
            <span v-else class="muted-text">暂无趋势</span>
          </template>
        </el-table-column>
        <el-table-column label="运行中" width="150">
          <template slot-scope="scope">
            <el-tag :type="(scope.row.running_count || scope.row.running_task_count) ? 'warning' : 'success'">
              测试集 {{ scope.row.running_count || 0 }} / 任务 {{ scope.row.running_task_count || 0 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="健康状态" width="150">
          <template slot-scope="scope">
            <el-tag :type="healthTagType(scope.row.health_status)">
              {{ scope.row.health_label || "未知" }} {{ scope.row.health_score || 0 }}
            </el-tag>
            <div class="muted-text">{{ scope.row.health_summary || "" }}</div>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="180" prop="updated_time" sortable>
          <template slot-scope="scope">
            <div class="time-cell">
              <div>{{ scope.row.updated_time }}</div>
              <div class="muted-text">创建：{{ scope.row.created_time }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="快捷操作" width="150" fixed="right">
          <template slot-scope="scope">
            <el-dropdown split-button type="primary" size="mini" trigger="click" @click="openProjectDashboard(scope.row)">
              总览
              <el-dropdown-menu slot="dropdown">
                <el-button-group class="button-container project-action-menu">
                  <el-button type="primary" icon="el-icon-document" @click="openProjectDashboard(scope.row, 'cases')">查看用例</el-button>
                  <el-button type="primary" icon="el-icon-collection" @click="openProjectDashboard(scope.row, 'testsets')">查看测试集</el-button>
                  <el-button type="primary" icon="el-icon-s-operation" @click="openProjectDashboard(scope.row, 'tasks')">查看任务</el-button>
                  <el-button type="primary" icon="el-icon-data-analysis" @click="openProjectDashboard(scope.row, 'reports')">查看报告</el-button>
                  <el-button type="success" icon="el-icon-download" @click="pullProjectGit(scope.row)">Git 拉取最新</el-button>
                  <el-button type="success" icon="el-icon-refresh" @click="syncProjectScripts(scope.row)">扫描/同步脚本</el-button>
                  <el-button type="warning" icon="el-icon-setting" @click="check_config(scope.$index, scope.row)">检查配置</el-button>
                  <el-button type="danger" icon="el-icon-video-play" @click="runDefaultTestset(scope.row)">运行默认测试集</el-button>
                  <el-button type="info" icon="el-icon-folder-opened" @click="previewProject(scope.row)">预览项目</el-button>
                  <el-button type="primary" icon="el-icon-edit" @click="set_id(scope.$index, scope.row)">编辑</el-button>
                </el-button-group>
              </el-dropdown-menu>
            </el-dropdown>

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
    <el-dialog title="业务部门管理" :visible.sync="departmentDialogVisible" width="860px">
      <div class="department-toolbar">
        <el-button type="primary" icon="el-icon-plus" @click="openDepartmentEdit()">新建业务部门</el-button>
      </div>
      <el-table :data="departments" stripe border height="360" v-loading="departmentLoading">
        <el-table-column prop="name" label="业务部门" min-width="160"></el-table-column>
        <el-table-column prop="owner" label="负责人" width="130">
          <template slot-scope="scope">{{ scope.row.owner || "未设置" }}</template>
        </el-table-column>
        <el-table-column label="总览" min-width="260">
          <template slot-scope="scope">
            <span class="metric-chip">项目 {{ scope.row.project_count || 0 }}</span>
            <span class="metric-chip">用例 {{ scope.row.case_count || 0 }}</span>
            <span class="metric-chip">测试集 {{ scope.row.testset_count || 0 }}</span>
            <span class="metric-chip">报告 {{ scope.row.report_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="备注" min-width="180" show-overflow-tooltip></el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template slot-scope="scope">
            <el-button size="mini" @click="openDepartmentDashboard(scope.row)">总览</el-button>
            <el-button size="mini" type="primary" @click="openDepartmentEdit(scope.row)">编辑</el-button>
            <el-button size="mini" type="danger" @click="removeDepartment(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
    <el-dialog :title="departmentForm.id ? '编辑业务部门' : '新建业务部门'" :visible.sync="departmentFormVisible" width="520px">
      <el-form :model="departmentForm" label-width="90px">
        <el-form-item label="部门名称" required>
          <el-input v-model="departmentForm.name" clearable placeholder="如：支付业务部"></el-input>
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="departmentForm.owner" clearable placeholder="部门负责人"></el-input>
        </el-form-item>
        <el-form-item label="备注">
          <el-input type="textarea" :rows="4" v-model="departmentForm.description" placeholder="部门说明"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="departmentFormVisible = false">取消</el-button>
        <el-button type="primary" @click="saveDepartment">保存</el-button>
      </span>
    </el-dialog>
    <el-dialog :title="departmentDashboardTitle" :visible.sync="departmentDashboardVisible" width="920px">
      <div v-if="departmentDashboard" class="department-dashboard">
        <div class="department-stat-row">
          <div class="dashboard-stat-card"><span>脚本项目</span><strong>{{ departmentDashboard.project_count || 0 }}</strong></div>
          <div class="dashboard-stat-card"><span>用例</span><strong>{{ departmentDashboard.case_count || 0 }}</strong></div>
          <div class="dashboard-stat-card"><span>测试集</span><strong>{{ departmentDashboard.testset_count || 0 }}</strong></div>
          <div class="dashboard-stat-card"><span>任务</span><strong>{{ departmentDashboard.task_count || 0 }}</strong></div>
          <div class="dashboard-stat-card"><span>报告</span><strong>{{ departmentDashboard.report_count || 0 }}</strong></div>
        </div>
        <el-table :data="departmentDashboard.projects || []" stripe height="360">
          <el-table-column prop="name" label="脚本项目" min-width="160"></el-table-column>
          <el-table-column prop="controller" label="负责人" width="120"></el-table-column>
          <el-table-column label="规模" min-width="240">
            <template slot-scope="scope">
              <span class="metric-chip">用例 {{ scope.row.case_count || 0 }}</span>
              <span class="metric-chip">测试集 {{ scope.row.testset_count || 0 }}</span>
              <span class="metric-chip">报告 {{ scope.row.report_count || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="updated_time" label="更新时间" width="170"></el-table-column>
          <el-table-column label="操作" width="100">
            <template slot-scope="scope">
              <el-button size="mini" type="text" @click="openProjectDashboard(scope.row)">项目总览</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
    <el-dialog :title="set_title" :visible.sync="setdialogTableVisible">
            <el-col class="toolbar" height="600">
                <el-pagination layout="total" :total="setcasetotal" style="float: right">
                </el-pagination>
            </el-col>
            <el-table :data="ReportList" highlight-current-row stripe height="430" v-loading="listLoading" id="exportTab"
                @selection-change="selsChange" style="width: 100%" :cell-style="cellStyle">
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in ReportForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column>
                <el-table-column label="配置状态" width="210">
                    <template slot-scope="scope">
                        <el-tag :type="scope.row.has_data_ini ? 'success' : 'danger'" size="mini">
                            data.ini {{ scope.row.has_data_ini ? "存在" : "缺失" }}
                        </el-tag>
                        <el-tag :type="scope.row.has_pytest_ini ? 'success' : 'info'" size="mini" style="margin-left: 6px">
                            pytest.ini {{ scope.row.has_pytest_ini ? "存在" : "无" }}
                        </el-tag>
                    </template>
                </el-table-column>

                <!-- <el-table-column label="用例类型" width="120"><template slot-scope="scope">{{ scope.row.type | testFmt
                }}</template></el-table-column> -->
                <el-table-column label="操作" width="300">
                    <template slot-scope="scope">
                        <el-row>
                            <el-button-group>
                                
                                <el-button type="primary" :disabled="scope.row.status === '已新建'"
                                v-if="scope.row.status !== '已新建'"
                                    @click="set_id(scope.$index, scope.row)">快捷新建脚本项目</el-button>
                            </el-button-group>
                        </el-row>

                    </template>

                </el-table-column>
            </el-table>
    </el-dialog>
    <el-dialog :title="set_title" :visible.sync="configinfodialogTableVisible">
      <template>
        <div class="data-display">
          <el-card>
            <el-row :gutter="20" v-for="(sectionData, sectionName) in jsonData" :key="sectionName">
              <el-col :span="24">
                <h3 :class="'section-name'">{{ sectionName }}</h3>
                <ul>
                  <li v-for="(value, key) in sectionData" :key="key">
                    <strong :class="'key-name'">{{ key }}:</strong> <span :class="'value-name'">{{ value }}</span>
                  </li>
                </ul>
              </el-col>
            </el-row>
          </el-card>
        </div>
        <div slot="footer" class="dialog-footer">
                <el-button type="danger" :disabled="false" @click="clear_ini_info">清空配置项
                </el-button>
                <el-button type="primary" @click.native="configinfodialogTableVisible = false">返回</el-button>
            </div>
      </template>
    </el-dialog>
    <el-dialog :title="projectPreviewTitle" :visible.sync="projectPreviewVisible" width="70%">
      <div class="project-preview" v-loading="projectPreviewLoading">
        <div class="project-preview-header">
          <div>
            <div class="preview-project-name">{{ projectPreviewData.name }}</div>
            <div class="muted-text">{{ projectPreviewData.path }}</div>
          </div>
          <el-tag type="info">IDEA Project View</el-tag>
        </div>
        <div class="project-preview-body">
          <el-tree
            class="project-tree"
            :data="projectPreviewData.tree"
            node-key="path"
            default-expand-all
            :expand-on-click-node="false"
            @node-click="handleProjectFileClick"
          >
            <span class="project-tree-node" slot-scope="{ node, data }">
              <span>
                <i :class="projectTreeIcon(data)"></i>
                <span :class="['project-tree-label', data.type === 'file' ? 'is-file' : 'is-dir']">
                  {{ node.label }}
                </span>
              </span>
              <span class="project-tree-meta" v-if="data.type === 'file'">
                {{ formatFileSize(data.size) }}
              </span>
            </span>
          </el-tree>
          <div class="file-preview-panel" v-loading="filePreviewLoading">
            <div v-if="filePreviewData" class="file-preview-content">
              <div class="file-preview-header">
                <div>
                  <div class="file-preview-name">
                    <i :class="projectTreeIcon({ type: 'file', ext: filePreviewData.ext })"></i>
                    {{ filePreviewData.name }}
                  </div>
                  <div class="muted-text">{{ filePreviewData.path }}</div>
                </div>
                <div class="file-preview-meta">
                  {{ formatFileSize(filePreviewData.size) }} · {{ filePreviewData.mtime }}
                </div>
              </div>
              <pre :class="['file-preview-code', filePreviewData.ext === 'py' ? 'is-python' : '']"><code>{{ filePreviewData.content }}</code></pre>
            </div>
            <div v-else class="file-preview-empty">
              点击左侧文件预览内容
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
    <el-dialog :title="dashboardTitle" :visible.sync="dashboardVisible" width="78%">
      <div v-if="projectDashboard" class="dashboard-panel">
        <div class="dashboard-grid">
          <div class="dashboard-card">
            <div class="dashboard-label">用例数</div>
            <strong>{{ projectDashboard.stats.case_count || 0 }}</strong>
          </div>
          <div class="dashboard-card">
            <div class="dashboard-label">测试集</div>
            <strong>{{ projectDashboard.stats.testset_count || 0 }}</strong>
          </div>
          <div class="dashboard-card">
            <div class="dashboard-label">任务</div>
            <strong>{{ projectDashboard.stats.task_count || 0 }}</strong>
          </div>
          <div class="dashboard-card">
            <div class="dashboard-label">报告</div>
            <strong>{{ projectDashboard.stats.report_count || 0 }}</strong>
          </div>
          <div class="dashboard-card">
            <div class="dashboard-label">最近通过率</div>
            <strong :class="passRateClass(projectDashboard.stats.last_pass_rate)">
              {{ formatPassRate(projectDashboard.stats.last_pass_rate) }}
            </strong>
          </div>
        </div>
        <el-row :gutter="16" class="dashboard-row">
          <el-col :span="24">
            <el-card>
              <div slot="header">项目标识</div>
              <div class="dashboard-meta-grid">
                <div>
                  <span class="meta-label">业务部门</span>
                  <strong>{{ projectDashboard.project.business_department || "未设置" }}</strong>
                </div>
                <div>
                  <span class="meta-label">环境</span>
                  <el-tag size="mini" :type="environmentTagType(projectDashboard.project.environment)">
                    {{ projectDashboard.project.environment || "test" }}
                  </el-tag>
                </div>
                <div>
                  <span class="meta-label">优先级</span>
                  <el-tag size="mini" type="warning">{{ projectDashboard.project.priority || "P2" }}</el-tag>
                </div>
                <div>
                  <span class="meta-label">负责人</span>
                  <strong>{{ projectDashboard.project.controller || "未设置" }}</strong>
                </div>
                <div>
                  <span class="meta-label">维护状态</span>
                  <el-tag size="mini" :type="maintStatusTagType(projectDashboard.project.maint_status)">
                    {{ maintStatusText(projectDashboard.project.maint_status) }}
                  </el-tag>
                </div>
                <div>
                  <span class="meta-label">标签</span>
                  <span v-if="projectDashboard.project.tags" class="project-tag-row">
                    <el-tag
                      v-for="tag in splitTags(projectDashboard.project.tags)"
                      :key="'dashboard-tag-' + tag"
                      size="mini"
                      type="info"
                      effect="plain"
                    >
                      {{ tag }}
                    </el-tag>
                  </span>
                  <span v-else>无</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="16" class="dashboard-row">
          <el-col :span="12">
            <el-card>
              <div slot="header">项目文件状态</div>
              <div class="dashboard-info-line">路径：{{ projectDashboard.file_status.path }}</div>
              <div class="dashboard-info-line" v-if="projectDashboard.git_status">
                Git：{{ projectDashboard.git_status.is_git_repo ? "已接入" : projectDashboard.git_status.message }}
                <span v-if="projectDashboard.git_status.branch">（{{ projectDashboard.git_status.branch }} @ {{ projectDashboard.git_status.commit || "-" }}）</span>
              </div>
              <div class="dashboard-info-line">Python 文件数：{{ projectDashboard.file_status.py_file_count }}</div>
              <div class="dashboard-info-line">目录更新时间：{{ projectDashboard.file_status.mtime }}</div>
              <div class="dashboard-info-line">
                <el-tag :type="projectDashboard.file_status.has_data_ini ? 'success' : 'danger'">
                  data.ini {{ projectDashboard.file_status.has_data_ini ? "存在" : "缺失" }}
                </el-tag>
                <el-tag :type="projectDashboard.file_status.has_pytest_ini ? 'success' : 'info'" style="margin-left: 8px">
                  pytest.ini {{ projectDashboard.file_status.has_pytest_ini ? "存在" : "无" }}
                </el-tag>
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <div slot="header">运行中</div>
              <div class="dashboard-info-line">测试集：{{ projectDashboard.stats.running_count || 0 }}</div>
              <div class="dashboard-info-line">任务：{{ projectDashboard.stats.running_task_count || 0 }}</div>
              <div class="dashboard-info-line">最近 run_id：{{ projectDashboard.stats.last_run_id || "暂无" }}</div>
              <div class="dashboard-info-line">最近执行时间：{{ projectDashboard.stats.last_run_time || "暂无" }}</div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="16" class="dashboard-row">
          <el-col :span="12">
            <el-card>
              <div slot="header">最近报告</div>
              <el-table :data="projectDashboard.recent_reports" height="260" size="mini">
                <el-table-column prop="title" label="报告" min-width="180"></el-table-column>
                <el-table-column prop="run_id" label="run_id" width="130"></el-table-column>
                <el-table-column label="通过率" width="90">
                  <template slot-scope="scope">{{ formatPassRate(scope.row.pass_rate) }}</template>
                </el-table-column>
                <el-table-column label="操作" width="90">
                  <template slot-scope="scope">
                    <el-button type="text" size="mini" @click="previewReport(scope.row)">预览</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <div slot="header">运行中的测试集</div>
              <el-table :data="projectDashboard.running_testsets" height="260" size="mini">
                <el-table-column prop="title" label="测试集" min-width="160"></el-table-column>
                <el-table-column prop="schedule" label="进度" width="80"></el-table-column>
                <el-table-column prop="run_id" label="run_id" width="130"></el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="16" class="dashboard-row">
          <el-col :span="24">
            <el-card>
              <div slot="header" class="card-header-line">
                <span>最近一次执行摘要</span>
                <el-button
                  v-if="projectDashboard.stats.last_report_path"
                  type="primary"
                  size="mini"
                  plain
                  @click="previewReport(projectDashboard.stats.last_execution_summary)"
                >预览报告</el-button>
              </div>
              <div v-if="projectDashboard.stats.last_run_id" class="execution-summary">
                <div class="execution-main">
                  <div class="execution-run">run_id：{{ projectDashboard.stats.last_run_id }}</div>
                  <div :class="['execution-rate', passRateClass(projectDashboard.stats.last_pass_rate)]">
                    {{ formatPassRate(projectDashboard.stats.last_pass_rate) }}
                  </div>
                  <div class="muted-text">{{ projectDashboard.stats.last_report_name }}</div>
                  <div class="muted-text">{{ projectDashboard.stats.last_run_time }}</div>
                </div>
                <div class="execution-metrics">
                  <div class="execution-metric">
                    <span>总用例</span>
                    <strong>{{ projectDashboard.stats.last_all_count || 0 }}</strong>
                  </div>
                  <div class="execution-metric is-pass">
                    <span>通过</span>
                    <strong>{{ projectDashboard.stats.last_pass_count || 0 }}</strong>
                  </div>
                  <div class="execution-metric is-fail">
                    <span>失败</span>
                    <strong>{{ projectDashboard.stats.last_fail_count || 0 }}</strong>
                  </div>
                  <div class="execution-metric is-error">
                    <span>错误</span>
                    <strong>{{ projectDashboard.stats.last_error_count || 0 }}</strong>
                  </div>
                  <div class="execution-metric">
                    <span>耗时/s</span>
                    <strong>{{ formatDuration(projectDashboard.stats.last_case_all_time) }}</strong>
                  </div>
                </div>
              </div>
              <div v-else class="muted-text">暂无执行记录</div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="16" class="dashboard-row">
          <el-col :span="24">
            <el-card>
              <div slot="header" class="card-header-line">
                <span>失败趋势</span>
                <el-tag
                  v-if="projectDashboard.stats.failure_trend"
                  :type="projectDashboard.stats.failure_trend.is_continuous_failed ? 'danger' : 'success'"
                >
                  连续失败 {{ projectDashboard.stats.failure_trend.consecutive_failed || 0 }} 次
                </el-tag>
              </div>
              <div v-if="projectDashboard.stats.failure_trend && projectDashboard.stats.failure_trend.sample_count" class="trend-detail">
                <div class="trend-chart">
                  <div
                    v-for="(rate, index) in projectDashboard.stats.failure_trend.pass_rates"
                    :key="'detail-rate-' + index"
                    class="trend-column"
                  >
                    <div class="trend-column-bar-wrap">
                      <span :style="{ height: trendBarHeight(rate) }" :class="['trend-column-bar', trendRateClass(rate)]"></span>
                    </div>
                    <div :class="['trend-column-rate', passRateClass(rate)]">{{ formatPassRate(rate) }}</div>
                    <div class="muted-text">失败 {{ projectDashboard.stats.failure_trend.fail_counts[index] || 0 }}</div>
                    <div class="muted-text">错误 {{ projectDashboard.stats.failure_trend.error_counts[index] || 0 }}</div>
                  </div>
                </div>
              </div>
              <div v-else class="muted-text">暂无趋势数据</div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="16" class="dashboard-row">
          <el-col :span="24">
            <el-card>
              <div slot="header" class="card-header-line">
                <span>项目健康状态</span>
                <el-tag v-if="projectDashboard.health" :type="healthTagType(projectDashboard.health.status)">
                  {{ projectDashboard.health.label }} {{ projectDashboard.health.score }}
                </el-tag>
              </div>
              <div v-if="projectDashboard.health">
                <div class="health-summary">{{ projectDashboard.health.summary }}</div>
                <div class="health-check-grid">
                  <div
                    v-for="item in projectDashboard.health.checks"
                    :key="item.key"
                    :class="['health-check-item', 'is-' + item.status]"
                  >
                    <div class="health-check-title">
                      <span>{{ item.name }}</span>
                      <el-tag size="mini" :type="healthTagType(item.status)">{{ healthStatusText(item.status) }}</el-tag>
                    </div>
                    <div class="health-check-message">{{ item.message }}</div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="16" class="dashboard-row">
          <el-col :span="24">
            <el-card>
              <div slot="header" class="card-header-line">
                <span>脚本变更检测</span>
                <el-button type="primary" size="mini" plain @click="refreshScriptChanges">重新检测</el-button>
              </div>
              <div v-if="projectDashboard.script_changes" class="change-summary">
                <span class="change-summary-item">扫描用例 {{ projectDashboard.script_changes.scanned_case_count || 0 }}</span>
                <span class="change-summary-item">平台用例 {{ projectDashboard.script_changes.db_case_count || 0 }}</span>
                <span class="change-summary-item is-success">新增 {{ projectDashboard.script_changes.added_case_count || 0 }}</span>
                <span class="change-summary-item is-danger">删除 {{ projectDashboard.script_changes.deleted_case_count || 0 }}</span>
                <span class="change-summary-item is-warning">修改 {{ projectDashboard.script_changes.modified_script_count || 0 }}</span>
                <span class="change-summary-item is-danger">解析错误 {{ projectDashboard.script_changes.parse_error_count || 0 }}</span>
                <span class="muted-text">检测时间：{{ projectDashboard.script_changes.checked_time || "暂无" }}</span>
              </div>
              <el-tabs class="change-detail-tabs">
                <el-tab-pane label="新增用例">
                  <el-table :data="projectDashboard.script_changes.added_cases" height="220" size="mini" stripe>
                    <el-table-column prop="title" label="用例" min-width="220"></el-table-column>
                    <el-table-column prop="relative_path" label="脚本路径" min-width="260"></el-table-column>
                    <el-table-column prop="mtime_text" label="文件更新时间" width="160"></el-table-column>
                  </el-table>
                </el-tab-pane>
                <el-tab-pane label="删除用例">
                  <el-table :data="projectDashboard.script_changes.deleted_cases" height="220" size="mini" stripe>
                    <el-table-column prop="title" label="用例" min-width="220"></el-table-column>
                    <el-table-column prop="relative_path" label="原脚本路径" min-width="260"></el-table-column>
                    <el-table-column prop="updated_time" label="平台更新时间" width="160"></el-table-column>
                  </el-table>
                </el-tab-pane>
                <el-tab-pane label="修改脚本">
                  <el-table :data="projectDashboard.script_changes.modified_scripts" height="220" size="mini" stripe>
                    <el-table-column prop="relative_path" label="脚本路径" min-width="320"></el-table-column>
                    <el-table-column prop="mtime" label="文件更新时间" width="170"></el-table-column>
                    <el-table-column prop="case_updated_time" label="平台更新时间" width="170"></el-table-column>
                  </el-table>
                </el-tab-pane>
                <el-tab-pane label="解析错误">
                  <el-table :data="projectDashboard.script_changes.parse_errors" height="220" size="mini" stripe>
                    <el-table-column prop="path" label="脚本路径" min-width="300"></el-table-column>
                    <el-table-column prop="error" label="错误" min-width="320"></el-table-column>
                  </el-table>
                </el-tab-pane>
              </el-tabs>
            </el-card>
          </el-col>
        </el-row>
        <el-tabs v-model="dashboardActiveTab" class="project-detail-tabs" @tab-click="loadProjectDetailTab">
          <el-tab-pane label="用例" name="cases">
            <el-table :data="projectCaseList" height="360" size="mini" stripe v-loading="projectDetailLoading">
              <el-table-column prop="case_name" label="用例名称" min-width="180"></el-table-column>
              <el-table-column prop="title" label="脚本标题" min-width="180"></el-table-column>
              <el-table-column prop="relative_path" label="路径" min-width="260"></el-table-column>
              <el-table-column prop="run_status" label="状态" width="100"></el-table-column>
              <el-table-column prop="updated_time" label="更新时间" width="160"></el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="测试集" name="testsets">
            <el-table :data="projectTestsetList" height="360" size="mini" stripe v-loading="projectDetailLoading">
              <el-table-column prop="title" label="测试集" min-width="180"></el-table-column>
              <el-table-column prop="schedule" label="进度" width="90"></el-table-column>
              <el-table-column prop="run_status" label="状态" width="90"></el-table-column>
              <el-table-column prop="run_id" label="run_id" width="140"></el-table-column>
              <el-table-column prop="updated_time" label="更新时间" width="160"></el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="测试任务" name="tasks">
            <el-table :data="projectTaskList" height="360" size="mini" stripe v-loading="projectDetailLoading">
              <el-table-column prop="name" label="任务名称" min-width="180"></el-table-column>
              <el-table-column prop="set_name" label="测试集" min-width="220"></el-table-column>
              <el-table-column prop="schedule" label="进度" width="90"></el-table-column>
              <el-table-column prop="run_status" label="状态" width="90"></el-table-column>
              <el-table-column prop="run_id" label="run_id" width="140"></el-table-column>
              <el-table-column prop="updated_time" label="更新时间" width="160"></el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="报告" name="reports">
            <el-table :data="projectReportList" height="360" size="mini" stripe v-loading="projectDetailLoading">
              <el-table-column prop="title" label="报告" min-width="180"></el-table-column>
              <el-table-column prop="set_title" label="测试集" min-width="160"></el-table-column>
              <el-table-column prop="run_id" label="run_id" width="140"></el-table-column>
              <el-table-column label="通过率" width="90">
                <template slot-scope="scope">{{ formatPassRate(scope.row.pass_rate) }}</template>
              </el-table-column>
              <el-table-column prop="updated_time" label="更新时间" width="160"></el-table-column>
              <el-table-column label="操作" width="90">
                <template slot-scope="scope">
                  <el-button type="text" size="mini" @click="previewReport(scope.row)">预览</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
    <!--详情界面-->
    <!-- <el-dialog title="详情" v-model="detailFormVisible" :close-on-click-modal="false"> -->
    <el-dialog title="新建或编辑脚本项目" :close-on-click-modal="false" :visible.sync="detailFormVisible">
      <el-form :model="addForm" label-width="150px" :rules="detailFormRules" ref="addForm">
        <el-col :span="24" style="margin-right: 100px">
          <el-row><el-form-item>
              <pre>1.脚本工程在该平台后端项目文件夹为testscriptproject的目录下,编写用例时请使用相对路径导入模块<br></pre>
            </el-form-item>
          </el-row>
          <el-row>
            <el-col :span="9">
              <el-form-item label="测试脚本项目名称" required>
                <el-input ref="inputName" v-model="addForm.config_name" auto-complete="off" placeholder="真实的脚本项目名称"
                  autofocus="true" clearable></el-input>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row>
            <el-col :span="9">
              <el-form-item label="项目管理者" required>
                <el-input ref="inputName" v-model="addForm.controller" auto-complete="off" placeholder="项目管理者"
                  autofocus="true" clearable></el-input>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="12">
            <el-col :span="8">
              <el-form-item label="业务部门">
                <el-select
                  v-model="addForm.business_department_id"
                  filterable
                  clearable
                  placeholder="请选择业务部门"
                  style="width: 100%"
                  @change="handleDepartmentChange"
                >
                  <el-option
                    v-for="item in departmentOptions"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  ></el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="环境">
                <el-select v-model="addForm.environment" placeholder="请选择环境" clearable>
                  <el-option
                    v-for="item in environmentOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  ></el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="7">
              <el-form-item label="优先级">
                <el-select v-model="addForm.priority" placeholder="请选择优先级" clearable>
                  <el-option
                    v-for="item in priorityOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  ></el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="12">
            <el-col :span="9">
              <el-form-item label="维护状态">
                <el-select v-model="addForm.maint_status" placeholder="请选择维护状态">
                  <el-option
                    v-for="item in maintStatusOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  ></el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="14">
              <el-form-item label="项目标签">
                <el-input v-model="addForm.tags" auto-complete="off" placeholder="多个标签用逗号分隔，如 smoke,核心链路" clearable></el-input>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="12" class="project-git-row">
            <el-col :span="23">
              <el-form-item label="Git 仓库地址">
                <el-input v-model="addForm.git_repo_url" auto-complete="off" placeholder="如：https://github.com/org/project.git" clearable></el-input>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="12" class="project-git-row">
            <el-col :span="12">
              <el-form-item label="Git 分支">
                <div class="git-branch-field">
                  <el-select
                    v-model="addForm.git_branch"
                    filterable
                    allow-create
                    clearable
                    :loading="gitBranchLoading"
                    placeholder="请选择或输入分支"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="branch in gitBranchOptions"
                      :key="branch"
                      :label="branch"
                      :value="branch"
                    ></el-option>
                  </el-select>
                  <el-button
                    type="primary"
                    plain
                    icon="el-icon-refresh"
                    :loading="gitBranchLoading"
                    @click="loadGitBranches"
                  >加载分支</el-button>
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item label="自动同步">
                <el-switch v-model="addForm.git_auto_sync" active-text="是" inactive-text="否"></el-switch>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- <el-row >
              <el-col :span="9">
                <el-form-item label="关联项目" class="len_input">
                  <div class="block" style="">
                    <span class="demonstration"></span>
                    <el-cascader
                      :filterable="true"
                      :clearable="true"
                      placeholder="请选择关联项目(也可输入项目搜索)"
                      separator="=>"
                      v-model="addForm.value"
                      :options="addForm.options"
                      :props="{ expandTrigger: 'hover' }"
                    ></el-cascader>
                  </div>
                </el-form-item>
              </el-col>
  
              <el-col :span="9">
                
              </el-col>
            </el-row> -->

          <el-form-item label="备注" required>
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
import axios from "axios";
import {
  DeleteConfig,
  update_project,
  add_project,
  get_project_info,
  get_project_dashboard,
  get_business_department_info,
  save_business_department,
  delete_business_department,
  get_business_department_dashboard,
  get_project_list,
  get_cases_info,
  get_testset_info,
  get_testtask_info,
  get_report_info,
  check_script_changes,
  get_project_tree,
  preview_project_file,
  sync_project_scripts,
  pull_project_git,
  get_project_git_branches,
  check_project_ini,
  clear_ini,
  get_url,
  run_testset,
} from "../../api/api";
import moment from "moment";
import Vue from "vue";
Vue.prototype.$moment = moment;

export default {
  data() {
    return {
      clean: false,
      ongoing: false,
      setdialogTableVisible:false,
      configinfodialogTableVisible:false,
      projectPreviewVisible:false,
      projectPreviewLoading:false,
      projectPreviewTitle:"项目预览",
      projectPreviewData:{
        name:"",
        path:"",
        tree:[],
      },
      filePreviewLoading:false,
      filePreviewData:null,
      dashboardVisible:false,
      dashboardTitle:"项目总览",
      projectDashboard:null,
      departmentDialogVisible:false,
      departmentFormVisible:false,
      departmentDashboardVisible:false,
      departmentDashboardTitle:"业务部门总览",
      departmentDashboard:null,
      departmentLoading:false,
      departments:[],
      departmentForm:{
        id:null,
        name:"",
        owner:"",
        description:"",
      },
      dashboardProjectId:null,
      dashboardActiveTab:"cases",
      projectDetailLoading:false,
      projectCaseList:[],
      projectTestsetList:[],
      projectTaskList:[],
      projectReportList:[],
      jsonData:{},
      project_id:null,
      project_name:"",
      set_title:"",
      filters: {
        cfg_name: "",
        business_department: "",
        business_department_id: "",
      },
      install_type_lst: [],
      addViperHost: "",
      aioLst: [],
      allProjectList: [],
      environmentOptions: [
        { label: "dev", value: "dev" },
        { label: "test", value: "test" },
        { label: "staging", value: "staging" },
        { label: "prod", value: "prod" },
      ],
      priorityOptions: [
        { label: "P0", value: "P0" },
        { label: "P1", value: "P1" },
        { label: "P2", value: "P2" },
        { label: "P3", value: "P3" },
      ],
      maintStatusOptions: [
        { label: "正常", value: "normal" },
        { label: "暂停维护", value: "paused" },
        { label: "废弃", value: "deprecated" },
      ],
      page_size: 200,
      total: 0,
      page: 0,
      addStatus: true,
      listLoading: false,
      gitBranchLoading: false,
      gitBranchOptions: [],
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
        disabled: "false",
        add_data: true,
        anaFlag: false,
        bdaFlag: false,
        nodeFlag: false,
        cfg: "",
        node_randio: 1,
        auth: false,
        controller: "",
        business_department_id: null,
        business_department: "",
        environment: "test",
        priority: "P2",
        maint_status: "normal",
        tags: "",
        git_repo_url: "",
        git_branch: "",
        git_auto_sync: true,
        value: "",
        options: [],
        set_time: "",
        note: "",
        config_id: null,
        config_name: "",
        set_flag: true,
      },

      lstForm: [
        { prop: "id", label: "项目id", width: 100 },
        { prop: "name", label: "脚本项目名称", width: 130 },
        { prop: "controller", label: "项目管理者", width: 200 },
        { prop: "description", label: "项目描述", width: 500 },
        { prop: "created_time", label: "创建时间", width: 200 },
        { prop: "updated_time", label: "更新时间", width: 200 },

      ],
      ReportForm: [
                { prop: "name", label: "项目名称", width: 240 },
                { prop: "status", label: "项目添加状态", width: 130 },
                { prop: "py_file_count", label: "py文件数", width: 100 },
                { prop: "path", label: "项目路径", width: 420 },
                { prop: "mtime", label: "目录更新时间", width: 180 },
            ],
    };
  },
  computed: {
    departmentOptions() {
      return this.departments || [];
    },
  },
  methods: {
    async loadDepartments() {
      this.departmentLoading = true;
      await get_business_department_info({}).then((res) => {
        this.departments = res.data.data || [];
      }).finally(() => {
        this.departmentLoading = false;
      });
    },
    openDepartmentManager() {
      this.departmentDialogVisible = true;
      this.loadDepartments();
    },
    openDepartmentEdit(row) {
      this.departmentForm = {
        id: row ? row.id : null,
        name: row ? row.name : "",
        owner: row ? (row.owner || "") : "",
        description: row ? (row.description || "") : "",
      };
      this.departmentFormVisible = true;
    },
    async saveDepartment() {
      await save_business_department(this.departmentForm).then((res) => {
        let { msg, code } = res.data;
        this.$message({
          message: msg,
          type: code === 200 ? "success" : "warning",
        });
        if (code === 200) {
          this.departmentFormVisible = false;
          this.loadDepartments();
          this.getConfigList();
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
          let { msg, code } = res.data;
          this.$message({
            message: msg,
            type: code === 200 ? "success" : "warning",
          });
          if (code === 200) {
            this.loadDepartments();
          }
        });
      }).catch(() => {});
    },
    async openDepartmentDashboard(row) {
      this.departmentDashboardTitle = "业务部门总览：" + row.name;
      this.departmentDashboardVisible = true;
      this.departmentDashboard = null;
      await get_business_department_dashboard({ id: row.id }).then((res) => {
        if (res.data.code !== 200) {
          this.$message({ message: res.data.msg, type: "warning" });
          this.departmentDashboardVisible = false;
          return false;
        }
        this.departmentDashboard = res.data.data;
      });
    },
    handleDepartmentChange(value) {
      const dept = (this.departments || []).find(item => item.id === value);
      this.addForm.business_department = dept ? dept.name : "";
    },
    async loadGitBranches() {
      const repoUrl = (this.addForm.git_repo_url || "").trim();
      const projectId = this.addForm.config_id || null;
      if (!repoUrl && !projectId) {
        this.$message({
          message: "请先填写 Git 仓库地址",
          type: "warning",
        });
        return false;
      }
      this.gitBranchLoading = true;
      await get_project_git_branches({
        id: projectId,
        repo_url: repoUrl,
      }).then((res) => {
        const { code, msg, data } = res.data;
        if (code !== 200) {
          this.$message({
            message: msg,
            type: "warning",
            duration: 6000,
          });
          return false;
        }
        this.gitBranchOptions = (data && data.branches) || [];
        if (!this.addForm.git_branch && data && data.default_branch) {
          this.addForm.git_branch = data.default_branch;
        }
        this.$message({
          message: "已加载 " + this.gitBranchOptions.length + " 个远端分支",
          type: "success",
        });
      }).finally(() => {
        this.gitBranchLoading = false;
      });
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
    formatPassRate(value) {
      if (value === null || value === undefined || value === "") {
        return "暂无";
      }
      return Number(value).toFixed(2) + "%";
    },
    formatDuration(value) {
      if (value === null || value === undefined || value === "") {
        return "0.00";
      }
      return Number(value).toFixed(2);
    },
    trendBarHeight(value) {
      const rate = Math.max(0, Math.min(100, Number(value || 0)));
      return Math.max(8, Math.round(rate * 0.48)) + "px";
    },
    trendRateClass(value) {
      const rate = Number(value || 0);
      return rate >= 90 ? "is-good" : rate >= 70 ? "is-warn" : "is-bad";
    },
    formatTrendList(values) {
      if (!values || !values.length) {
        return "暂无";
      }
      return values.join(" / ");
    },
    splitTags(value) {
      if (!value) {
        return [];
      }
      return String(value)
        .split(/[,，]/)
        .map((item) => item.trim())
        .filter((item) => item);
    },
    environmentTagType(value) {
      if (value === "prod") {
        return "danger";
      }
      if (value === "staging") {
        return "warning";
      }
      if (value === "dev") {
        return "info";
      }
      return "success";
    },
    maintStatusText(value) {
      if (value === "paused") {
        return "暂停维护";
      }
      if (value === "deprecated") {
        return "废弃";
      }
      return "正常";
    },
    maintStatusTagType(value) {
      if (value === "paused") {
        return "warning";
      }
      if (value === "deprecated") {
        return "info";
      }
      return "success";
    },
    passRateClass(value) {
      if (value === null || value === undefined || value === "") {
        return "rate-muted";
      }
      return Number(value) >= 90 ? "rate-good" : Number(value) >= 70 ? "rate-warn" : "rate-bad";
    },
    healthTagType(status) {
      if (status === "ok") {
        return "success";
      }
      if (status === "warning") {
        return "warning";
      }
      if (status === "error") {
        return "danger";
      }
      return "info";
    },
    healthStatusText(status) {
      if (status === "ok") {
        return "正常";
      }
      if (status === "warning") {
        return "提醒";
      }
      if (status === "error") {
        return "异常";
      }
      return "未知";
    },
    changeChipClass(value, type) {
      if (!value) {
        return "metric-chip change-chip";
      }
      if (type === "danger") {
        return "metric-chip change-chip change-danger";
      }
      if (type === "warning") {
        return "metric-chip change-chip change-warning";
      }
      return "metric-chip change-chip change-success";
    },
    projectTreeIcon(data) {
      if (data.type === "dir") {
        return "el-icon-folder project-tree-icon is-dir";
      }
      if (data.ext === "py") {
        return "el-icon-document project-tree-icon is-python";
      }
      if (["ini", "cfg", "yaml", "yml", "json"].indexOf(data.ext) !== -1) {
        return "el-icon-setting project-tree-icon is-config";
      }
      return "el-icon-document project-tree-icon is-file";
    },
    formatFileSize(size) {
      const value = Number(size || 0);
      if (value >= 1024 * 1024) {
        return (value / 1024 / 1024).toFixed(2) + " MB";
      }
      if (value >= 1024) {
        return (value / 1024).toFixed(1) + " KB";
      }
      return value + " B";
    },
    parseIdList(value) {
      if (!value) {
        return [];
      }
      if (Array.isArray(value)) {
        return value;
      }
      if (typeof value === "number") {
        return [value];
      }
      try {
        const parsed = JSON.parse(String(value).replace(/'/g, '"'));
        if (Array.isArray(parsed)) {
          return parsed;
        }
        if (typeof parsed === "number") {
          return [parsed];
        }
      } catch (e) {
        return [];
      }
      return [];
    },
    async previewProject(row) {
      this.projectPreviewVisible = true;
      this.projectPreviewLoading = true;
      this.projectPreviewTitle = "项目预览：" + row.name;
      this.dashboardProjectId = row.id;
      this.filePreviewData = null;
      this.projectPreviewData = {
        name: row.name,
        path: "",
        tree: [],
      };
      await get_project_tree({ id: row.id }).then((res) => {
        if (res.data.code !== 200) {
          this.$message({
            message: res.data.msg,
            type: "warning",
          });
          this.projectPreviewVisible = false;
          return false;
        }
        this.projectPreviewData = res.data.data;
      }).finally(() => {
        this.projectPreviewLoading = false;
      });
    },
    async handleProjectFileClick(data) {
      if (!data || data.type !== "file") {
        return false;
      }
      this.filePreviewLoading = true;
      await preview_project_file({
        id: this.dashboardProjectId,
        path: data.path,
      }).then((res) => {
        if (res.data.code !== 200) {
          this.$message({
            message: res.data.msg,
            type: "warning",
          });
          return false;
        }
        this.filePreviewData = res.data.data;
      }).finally(() => {
        this.filePreviewLoading = false;
      });
    },
    async openProjectDashboard(row, tabName) {
      this.dashboardTitle = "项目总览：" + row.name;
      this.dashboardVisible = true;
      this.projectDashboard = null;
      this.dashboardProjectId = row.id;
      this.dashboardActiveTab = tabName || "cases";
      this.projectCaseList = [];
      this.projectTestsetList = [];
      this.projectTaskList = [];
      this.projectReportList = [];
      await get_project_dashboard({ id: row.id }).then((res) => {
        if (res.data.code !== 200) {
          this.$message({
            message: res.data.msg,
            type: "warning",
          });
          this.dashboardVisible = false;
          return false;
        }
        this.projectDashboard = res.data.data;
      });
      this.loadProjectDetailTab();
    },
    async syncProjectScripts(row) {
      this.$confirm("将扫描项目目录并同步pytest用例到平台，是否继续?", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(async () => {
        this.listLoading = true;
        await sync_project_scripts({ id: row.id }).then((res) => {
          let { msg, code } = res.data;
          this.$message({
            message: msg,
            type: code === 200 ? "success" : "warning",
            duration: 5000,
          });
        }).finally(() => {
          this.listLoading = false;
          this.getConfigList();
        });
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消同步",
        });
      });
    },
    async pullProjectGit(row) {
      const gitStatus = row.git_status || {};
      const autoSync = row.git_auto_sync === undefined ? true : row.git_auto_sync !== 0;
      const branchText = row.git_branch || gitStatus.branch || "当前分支";
      this.$confirm(
        "将在脚本项目目录执行 git pull --ff-only，分支：" + branchText + (autoSync ? "，成功后会自动同步用例。" : "。") + " 是否继续?",
        "Git 拉取最新代码",
        {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        }
      ).then(async () => {
        this.listLoading = true;
        await pull_project_git({
          id: row.id,
          branch: row.git_branch || "",
          auto_sync: autoSync,
        }).then((res) => {
          let { msg, code, data } = res.data;
          let output = "";
          if (data && data.git) {
            output = data.git.stdout || data.git.stderr || "";
          }
          this.$message({
            message: output ? msg + "：" + output : msg,
            type: code === 200 ? "success" : "warning",
            duration: 7000,
          });
        }).finally(() => {
          this.listLoading = false;
          this.getConfigList();
        });
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消 Git 拉取",
        });
      });
    },
    async runDefaultTestset(row) {
      this.$confirm("将运行该项目优先级最高的测试集，是否继续?", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(async () => {
        this.listLoading = true;
        await get_testset_info({ project_id: row.id, page_no: 0, page_size: 100 }).then(async (res) => {
          const testsets = res.data.data || [];
          if (!testsets.length) {
            this.$message({
              message: "该项目暂无测试集",
              type: "warning",
            });
            return false;
          }
          const defaultSet = testsets.sort((a, b) => {
            const priorityDiff = Number(b.priority || 0) - Number(a.priority || 0);
            if (priorityDiff !== 0) {
              return priorityDiff;
            }
            return Number(b.id || 0) - Number(a.id || 0);
          })[0];
          const cfgIds = this.parseIdList(defaultSet.config);
          if (!cfgIds.length) {
            this.$message({
              message: "默认测试集没有关联配置，无法运行：" + defaultSet.title,
              type: "warning",
              duration: 5000,
            });
            return false;
          }
          await run_testset({
            id: defaultSet.id,
            cfg_id: cfgIds,
            version_id: defaultSet.version_id,
            script_type: Number(defaultSet.type || 1),
            priority_value: defaultSet.priority || 0,
          }).then((runRes) => {
            let { msg, code } = runRes.data;
            this.$message({
              message: "默认测试集：" + defaultSet.title + "，" + msg,
              type: code === 200 ? "success" : "warning",
              duration: 5000,
            });
          });
        }).finally(() => {
          this.listLoading = false;
          this.getConfigList();
        });
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消运行",
        });
      });
    },
    async refreshScriptChanges() {
      if (!this.dashboardProjectId) {
        return false;
      }
      await check_script_changes({ id: this.dashboardProjectId }).then((res) => {
        if (res.data.code !== 200) {
          this.$message({
            message: res.data.msg,
            type: "warning",
          });
          return false;
        }
        this.$set(this.projectDashboard, "script_changes", res.data.data);
        this.$message({
          message: "脚本变更检测完成",
          type: "success",
        });
      });
    },
    async loadProjectDetailTab() {
      if (!this.dashboardProjectId) {
        return false;
      }
      this.projectDetailLoading = true;
      const params = {
        project_id: this.dashboardProjectId,
        page_no: 0,
        page: 0,
        page_size: 100,
      };
      try {
        if (this.dashboardActiveTab === "cases") {
          await get_cases_info(params).then((res) => {
            this.projectCaseList = res.data.data || [];
          });
        } else if (this.dashboardActiveTab === "testsets") {
          await get_testset_info(params).then((res) => {
            this.projectTestsetList = res.data.data || [];
          });
        } else if (this.dashboardActiveTab === "tasks") {
          await get_testtask_info(params).then((res) => {
            this.projectTaskList = res.data.data || [];
          });
        } else if (this.dashboardActiveTab === "reports") {
          await get_report_info(params).then((res) => {
            this.projectReportList = res.data.data || [];
          });
        }
      } finally {
        this.projectDetailLoading = false;
      }
    },
    previewReport(row) {
      if (!row.report_path) {
        this.$message({
          message: "没有可预览的报告文件",
          type: "warning",
        });
        return false;
      }
      axios({
        method: "POST",
        url: get_url() + "/testset/report_content",
        data: { filename: row.report_path },
      }).then((res) => {
        if (res.data && res.data.code === 404) {
          this.$message({
            message: res.data.msg,
            type: "warning",
          });
          return false;
        }
        const reportWindow = window.open("", "_blank");
        if (!reportWindow) {
          this.$message({
            message: "浏览器阻止了报告预览窗口",
            type: "warning",
          });
          return false;
        }
        reportWindow.document.open();
        reportWindow.document.write(res.data);
        reportWindow.document.close();
      });
    },
    //获取项目列表
    async getConfigList() {
      this.ongoing = false;
      let para = {
        name: this.filters.cfg_name,
        business_department: this.filters.business_department,
        business_department_id: this.filters.business_department_id,
        page: this.page,
        page_size: this.page_size,
      };
      this.listLoading = true;
      await get_project_info(para).then((res) => {
        this.aioLst = res.data.data;
        if (!this.filters.business_department && !this.filters.business_department_id && !this.filters.cfg_name) {
          this.allProjectList = res.data.data || [];
        }
        this.listLoading = false;
        this.total = res.data.total || res.data.data.length
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
          name: this.addForm.config_name,
          description: this.addForm.cfg,
          controller: this.addForm.controller,
          business_department_id: this.addForm.business_department_id,
          business_department: this.addForm.business_department,
          environment: this.addForm.environment || "test",
          priority: this.addForm.priority || "P2",
          maint_status: this.addForm.maint_status || "normal",
          tags: this.addForm.tags,
          git_repo_url: this.addForm.git_repo_url,
          git_branch: this.addForm.git_branch,
          git_auto_sync: this.addForm.git_auto_sync ? 1 : 0,
          id: this.addForm.config_id
        };


        await add_project(para).then((res) => {
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
        // this.getProtList();
        this.detailFormVisible = false;
      }
      this.getConfigList();
      // this.getProtList();
    },
    cellStyle({ row, column, rowIndex, columnIndex }) {
            let cell_Style
            switch (row.status) {
                case '已新建':
                    cell_Style = 'color:#00FF00'
                    break;
                case '未新建':
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

            //返回最终处理过的样式 只让项目添加状态这个属性的属性被style修饰
            if (column.label == '项目添加状态') {
                return cell_Style
            }
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

    //   let para = { name: row.name };
    //   await update(para).then((res) => {
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
      this.addForm.config_id = "";
      this.addForm.set_time = new Date();
      this.detailFormVisible = true;
      this.addForm.add_data = true;
      this.addForm.cfg = null;
      this.addForm.config_name = null;
      this.addForm.controller = null;
      this.addForm.business_department_id = null;
      this.addForm.business_department = "";
      this.addForm.environment = "test";
      this.addForm.priority = "P2";
      this.addForm.maint_status = "normal";
      this.addForm.tags = "";
      this.addForm.git_repo_url = "";
      this.addForm.git_branch = "";
      this.addForm.git_auto_sync = true;
      this.gitBranchOptions = [];
      // await this.getproinfo();
    },
    async set_id(index, row) {
      this.addForm.disabled = "true";
      this.addForm.config_id = row.id;
      this.addForm.cfg = row.description;
      this.addForm.config_name = row.name;
      this.addForm.controller = row.controller;
      this.addForm.business_department_id = row.business_department_id || null;
      this.addForm.business_department = row.business_department || "";
      this.addForm.environment = row.environment || "test";
      this.addForm.priority = row.priority || "P2";
      this.addForm.maint_status = row.maint_status || "normal";
      this.addForm.tags = row.tags || "";
      this.addForm.git_repo_url = row.git_repo_url || (row.git_status && row.git_status.repo_url) || "";
      this.addForm.git_branch = row.git_branch || (row.git_status && row.git_status.branch) || "";
      this.addForm.git_auto_sync = row.git_auto_sync === undefined ? true : row.git_auto_sync !== 0;
      this.gitBranchOptions = this.addForm.git_branch ? [this.addForm.git_branch] : [];
      this.detailFormVisible = true;
      this.setdialogTableVisible = false;
      // await this.getproinfo();

    },
      //获取该项目列表
    async getProtList(index, row) {
            this.setdialogTableVisible = true
            this.set_title = "全部脚本项目列表";
            // let para = {
            //     page: this.page,
            //     page_size: this.page_size,
            //     set_id: row.id
            // };
            this.listLoading = true;
      await get_project_list().then((res) => {
                this.ReportList = res.data.data;
                this.listLoading = false;
                this.setcasetotal = res.data.total || res.data.data.length;
                this.count_info = [];
                if (res.data.count !== null) {
                    this.count_info = [res.data.count];
                }
            });
        },
      //获取该测试任务的报告列表
      async check_config(index, row) {
            this.configinfodialogTableVisible = true
            this.set_title = row.name+'项目的配置信息';
            this.project_id = row.id;
            this.project_name=row.name;
            let para = {
                // id: row.id,
                // page_size: this.page_size,
                id: row.id
            };
            this.listLoading = true;
            await check_project_ini(para).then((res) => {
                this.listLoading = false;
                this.jsonData = res.data.data;
                // this.listLoading = false;
            });
        },
      async clear_ini_info(index, row) {
            this.$confirm("此操作将清空该配置信息, 是否继续?", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            })
                .then(() => {
                    let para = {
                        id: this.project_id,
                    };

                    clear_ini(para).then((res) => {
                        // this.listLoading = false;
                        this.configinfodialogTableVisible = false
                        let { msg, code } = res.data;
                        if (code != 200) {
                            this.$message({
                                message: msg,
                                type: "warning",
                                duration: 5000
                            });
                        } else {

                            this.$message({
                                message: "删除的项目配置项:"+ this.project_name,
                                type: "success",
                                duration: 5000
                            });

                        }

                    });

                })
                .catch(() => {
                    this.$message({
                        type: "info",
                        message: "已取消",
                    });
                });
        },

    //显示详情界面
    selsChange: function (sels) {
      this.sels = sels;
    },


    // refreshViper_v2() {
    //   // var install_type = this.addForm.install_type;
    //   this.addForm.options = [];
    //   if (this.vipers) {
    //     var server_len = this.vipers.length;

    //     var cnt = 0;
    //     for (var i in this.vipers) {
    //       cnt++;
    //       this.addForm.options.push({
    //         value: this.vipers[i]["id"],
    //         label: cnt + "/" + server_len + " " + this.vipers[i]["name"],
    //       });
    //     }
    //   }
    // },




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
      // await this.refreshViper_v2();
    },
  },

  mounted() {
    this.loadDepartments();
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

.project-page {
  padding-bottom: 18px;
}

.project-list-panel {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
}

.project-name-cell {
  line-height: 1.5;
  white-space: normal;
}

.project-name {
  color: #303133;
  font-size: 15px;
  font-weight: 700;
}

.project-name-button {
  padding: 0;
  font-size: 15px;
  font-weight: 700;
}

.project-desc {
  margin-top: 4px;
  color: #606266;
  word-break: break-word;
}

.project-owner,
.muted-text {
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

.project-tag-row {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.project-meta-cell {
  color: #606266;
  line-height: 1.8;
}

.meta-label {
  display: inline-block;
  margin-right: 6px;
  color: #909399;
  font-size: 12px;
}

.meta-tag-line {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.dashboard-meta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  color: #606266;
}

.dashboard-meta-grid > div {
  min-height: 38px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.metric-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  white-space: normal;
}

.change-row {
  margin-top: 8px;
}

.button-container {
  display: flex;
  flex-direction: column;
}

.project-action-menu .el-button {
  width: 150px;
  margin-left: 0;
  border-radius: 0;
  text-align: left;
}

.department-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.department-stat-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.dashboard-stat-card {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #fafafa;
}

.dashboard-stat-card span {
  display: block;
  color: #909399;
  font-size: 12px;
}

.dashboard-stat-card strong {
  display: block;
  margin-top: 6px;
  color: #303133;
  font-size: 22px;
}

.metric-chip {
  display: inline-block;
  padding: 3px 8px;
  color: #409eff;
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 4px;
  font-size: 12px;
  line-height: 20px;
}

.change-chip {
  color: #909399;
  background: #f4f4f5;
  border-color: #e9e9eb;
}

.change-success {
  color: #67c23a;
  background: #f0f9eb;
  border-color: #e1f3d8;
}

.change-warning {
  color: #e6a23c;
  background: #fdf6ec;
  border-color: #faecd8;
}

.change-danger {
  color: #f56c6c;
  background: #fef0f0;
  border-color: #fde2e2;
}

.last-run-cell,
.time-cell {
  color: #606266;
  line-height: 1.7;
  white-space: normal;
}

.last-run-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.last-run-counts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
}

.trend-cell {
  line-height: 1.7;
}

.trend-bars {
  display: flex;
  align-items: flex-end;
  gap: 5px;
  height: 52px;
  margin-bottom: 4px;
}

.trend-bar {
  width: 12px;
  border-radius: 3px 3px 0 0;
  background: #dcdfe6;
}

.trend-bar.is-good,
.trend-column-bar.is-good {
  background: #67c23a;
}

.trend-bar.is-warn,
.trend-column-bar.is-warn {
  background: #e6a23c;
}

.trend-bar.is-bad,
.trend-column-bar.is-bad {
  background: #f56c6c;
}

.trend-line {
  color: #606266;
  font-size: 12px;
}

.rate-good {
  color: #67c23a;
  font-weight: 700;
}

.rate-warn {
  color: #e6a23c;
  font-weight: 700;
}

.rate-bad {
  color: #f56c6c;
  font-weight: 700;
}

.rate-muted {
  color: #909399;
}

.dashboard-panel {
  padding: 2px 0 10px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.dashboard-card {
  padding: 16px;
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.dashboard-label {
  color: #909399;
  font-size: 13px;
}

.dashboard-card strong {
  display: block;
  margin-top: 8px;
  color: #303133;
  font-size: 26px;
}

.dashboard-row {
  margin-top: 14px;
}

.dashboard-info-line {
  margin-bottom: 10px;
  color: #606266;
  line-height: 1.6;
  word-break: break-all;
}

.execution-summary {
  display: flex;
  gap: 16px;
}

.execution-main {
  width: 240px;
  padding: 14px;
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.execution-run {
  color: #303133;
  font-weight: 700;
}

.execution-rate {
  margin: 8px 0;
  font-size: 30px;
  font-weight: 700;
}

.execution-metrics {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.execution-metric {
  padding: 14px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.execution-metric span {
  color: #909399;
  font-size: 12px;
}

.execution-metric strong {
  display: block;
  margin-top: 8px;
  color: #303133;
  font-size: 24px;
}

.execution-metric.is-pass {
  background: #f0f9eb;
  border-color: #e1f3d8;
}

.execution-metric.is-fail {
  background: #fef0f0;
  border-color: #fde2e2;
}

.execution-metric.is-error {
  background: #fdf6ec;
  border-color: #faecd8;
}

.trend-detail {
  padding: 4px 0;
}

.trend-chart {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.trend-column {
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  text-align: center;
}

.trend-column-bar-wrap {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  height: 56px;
}

.trend-column-bar {
  width: 28px;
  border-radius: 4px 4px 0 0;
}

.trend-column-rate {
  margin-top: 8px;
  font-weight: 700;
}

.project-preview {
  min-height: 420px;
}

.project-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  margin-bottom: 12px;
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.preview-project-name {
  color: #303133;
  font-size: 16px;
  font-weight: 700;
}

.project-tree {
  height: 560px;
  width: 36%;
  padding: 8px 0;
  overflow: auto;
  background: #fbfdff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.project-preview-body {
  display: flex;
  gap: 12px;
}

.project-tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 12px;
  font-size: 13px;
}

.project-tree-icon {
  margin-right: 6px;
}

.project-tree-icon.is-dir {
  color: #e6a23c;
}

.project-tree-icon.is-python {
  color: #3776ab;
}

.project-tree-icon.is-config {
  color: #67c23a;
}

.project-tree-icon.is-file {
  color: #909399;
}

.project-tree-label.is-dir {
  color: #303133;
  font-weight: 700;
}

.project-tree-label.is-file {
  color: #606266;
}

.project-tree-meta {
  color: #c0c4cc;
  font-size: 12px;
}

.file-preview-panel {
  flex: 1;
  height: 560px;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.file-preview-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.file-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid #e4e7ed;
  background: #f8fafc;
}

.file-preview-name {
  color: #303133;
  font-weight: 700;
}

.file-preview-meta {
  color: #909399;
  font-size: 12px;
}

.file-preview-code {
  flex: 1;
  margin: 0;
  padding: 14px;
  overflow: auto;
  color: #d4d4d4;
  background: #1e1e1e;
  font-family: Consolas, "Courier New", monospace;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre;
}

.file-preview-code.is-python {
  color: #c9d1d9;
  background: #0d1117;
}

.file-preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
  background: #fbfdff;
}

.card-header-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.change-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.change-summary-item {
  padding: 5px 10px;
  color: #606266;
  background: #f4f4f5;
  border-radius: 4px;
  font-size: 12px;
}

.change-summary-item.is-success {
  color: #67c23a;
  background: #f0f9eb;
}

.change-summary-item.is-warning {
  color: #e6a23c;
  background: #fdf6ec;
}

.change-summary-item.is-danger {
  color: #f56c6c;
  background: #fef0f0;
}

.health-summary {
  margin-bottom: 12px;
  color: #606266;
}

.health-check-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.health-check-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #ffffff;
}

.health-check-item.is-ok {
  background: #f0f9eb;
  border-color: #e1f3d8;
}

.health-check-item.is-warning {
  background: #fdf6ec;
  border-color: #faecd8;
}

.health-check-item.is-error {
  background: #fef0f0;
  border-color: #fde2e2;
}

.health-check-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #303133;
  font-weight: 700;
}

.health-check-message {
  margin-top: 8px;
  color: #606266;
  font-size: 12px;
  line-height: 1.5;
}

.change-detail-tabs /deep/ .el-tabs__header {
  margin-bottom: 8px;
}

.project-detail-tabs {
  margin-top: 18px;
}

.project-detail-tabs /deep/ .el-tabs__header {
  margin-bottom: 12px;
}

.git-branch-field {
  display: flex;
  align-items: center;
  gap: 8px;
}

.git-branch-field .el-button {
  flex: 0 0 auto;
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

.section-name {
  color: rgb(60, 255, 0); /* sectionName的颜色 */
}
.key-name {
  color: blue; /* key的颜色 */
}
.value-name {
  color: green; /* value的颜色 */
}
</style>
  
