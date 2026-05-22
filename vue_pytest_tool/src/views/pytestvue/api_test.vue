<template>
  <section class="api-test-page">
    <el-row :gutter="14" class="api-workbench">
      <el-col :span="7" class="api-side-col">
        <div class="api-side">
          <div class="api-side-head">
            <div>
              <strong>{{ sideMode === "case" ? "接口用例" : "接口集合" }}</strong>
              <span>{{ sidebarSummary }}</span>
            </div>
            <el-button size="mini" icon="el-icon-refresh" @click="reloadSideList">刷新</el-button>
          </div>
          <div class="api-side-toolbar">
            <el-input v-model="filters.keyword" size="small" clearable placeholder="接口名称" @keyup.enter.native="reloadSideList">
              <i slot="prefix" class="el-input__icon el-icon-search"></i>
            </el-input>
            <el-button type="primary" size="small" icon="el-icon-search" @click="reloadSideList">查询</el-button>
          </div>
          <div class="api-side-toolbar">
            <el-select v-model="filters.project_id" size="small" clearable placeholder="脚本项目" @change="handleProjectChange">
              <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id"></el-option>
            </el-select>
            <el-button v-if="sideMode === 'case'" type="success" size="small" icon="el-icon-plus" @click="newCase">新增接口</el-button>
            <el-button v-else type="success" size="small" icon="el-icon-plus" @click="newSuite">新增集合</el-button>
          </div>
          <div class="api-side-toolbar">
            <el-select v-model="filters.run_status" size="small" clearable placeholder="执行状态" @change="reloadSideList">
              <el-option label="成功" value="passed"></el-option>
              <el-option label="失败" value="failed"></el-option>
              <el-option label="未执行" value="not_run"></el-option>
            </el-select>
            <el-input v-model="filters.status_code" size="small" clearable placeholder="状态码，如 200/302" @keyup.enter.native="loadCases" @blur="loadCases" @clear="loadCases"></el-input>
          </div>
          <el-tabs v-model="sideMode" class="api-side-tabs" @tab-click="reloadSideList">
            <el-tab-pane label="接口用例" name="case">
              <el-table :data="cases" stripe height="575" v-loading="caseLoading" @row-click="selectCase">
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
            </el-tab-pane>
            <el-tab-pane label="接口集合" name="suite">
              <div class="suite-side-actions">
                <el-select v-model="quickSuiteEnvironmentId" size="mini" clearable placeholder="选择运行环境">
                  <el-option v-for="item in environments" :key="item.id" :label="item.name" :value="item.id"></el-option>
                </el-select>
                <el-button type="primary" size="mini" icon="el-icon-video-play" :loading="suiteRunning" @click="runPlatformSuite">平台全量</el-button>
              </div>
              <el-table :data="suites" stripe height="528" @row-click="selectSuite">
                <el-table-column label="接口集合" min-width="220">
                  <template slot-scope="scope">
                    <div class="case-row" :class="{ active: suiteForm.id === scope.row.id }">
                      <el-tag size="mini" type="primary">{{ (scope.row.case_ids || []).length }} 个接口</el-tag>
                      <strong>{{ scope.row.name }}</strong>
                      <span>{{ scope.row.description || "未填写备注" }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="82">
                  <template slot-scope="scope">
                    <el-button type="primary" size="mini" :loading="suiteRunning" @click.stop="runSuiteRow(scope.row)">运行</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-col>

      <el-col :span="17" class="api-main-col">
        <div class="api-main">
          <div class="api-main-head">
            <div>
              <span class="api-main-kicker">{{ sideMode === "case" ? "API CASE" : "API SUITE" }}</span>
              <h2>{{ workspaceTitle }}</h2>
              <p>{{ workspaceSubtitle }}</p>
            </div>
            <div class="api-main-status">
              <el-tag v-if="lastResult" :type="resultTagType(lastResult)">{{ resultStatusText(lastResult) }}</el-tag>
              <span v-if="lastResult">Status {{ lastResult.response_status || "-" }} · {{ lastResult.elapsed_ms || 0 }} ms</span>
              <span v-else>{{ sideMode === "case" ? "未执行" : ((suiteForm.case_ids || []).length + " 个接口") }}</span>
            </div>
          </div>
          <div v-if="sideMode === 'case'">
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
            <el-tab-pane label="依赖" name="dependencies">
              <el-alert
                title="运行当前接口时会先按依赖链执行前置接口，并把提取出的变量传给后续接口。"
                type="info"
                :closable="false"
                show-icon>
              </el-alert>
              <el-select
                v-model="currentCase.pre_case_ids"
                multiple
                filterable
                clearable
                style="width: 100%; margin-top: 12px"
                placeholder="选择前置依赖接口">
                <el-option
                  v-for="item in dependencyOptions"
                  :key="item.id"
                  :label="item.name + '  [' + item.method + '] ' + item.url"
                  :value="item.id">
                </el-option>
              </el-select>
            </el-tab-pane>
            <el-tab-pane label="变量提取" name="extractors">
              <div class="assertion-tools">
                <el-button size="mini" icon="el-icon-plus" @click="addExtractor('json')">JSON提取</el-button>
                <el-button size="mini" icon="el-icon-plus" @click="addExtractor('header')">Header提取</el-button>
                <el-button size="mini" icon="el-icon-plus" @click="addExtractor('regex')">正则提取</el-button>
              </div>
              <el-table :data="currentCase.extractors" border size="mini">
                <el-table-column label="变量名" width="140">
                  <template slot-scope="scope">
                    <el-input v-model="scope.row.name" size="mini" placeholder="token"></el-input>
                  </template>
                </el-table-column>
                <el-table-column label="来源" width="120">
                  <template slot-scope="scope">
                    <el-select v-model="scope.row.from" size="mini">
                      <el-option label="JSON" value="json"></el-option>
                      <el-option label="Header" value="header"></el-option>
                      <el-option label="正则" value="regex"></el-option>
                      <el-option label="Body全文" value="body"></el-option>
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="路径/Header/正则" min-width="220">
                  <template slot-scope="scope">
                    <el-input v-model="scope.row.path" size="mini" placeholder="data.token / Authorization / token=(.+?)&"></el-input>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="70">
                  <template slot-scope="scope">
                    <el-button type="text" size="mini" @click="currentCase.extractors.splice(scope.$index, 1)">删除</el-button>
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
            <el-tab-pane v-if="false" label="接口集合" name="suite">
              <div class="suite-layout">
                <div class="suite-list">
                  <div class="suite-toolbar">
                    <el-button type="success" size="small" icon="el-icon-plus" @click="newSuite">新增集合</el-button>
                    <el-button type="primary" size="small" icon="el-icon-video-play" :loading="suiteRunning" @click="runPlatformSuite">平台全量测试</el-button>
                    <el-button size="small" icon="el-icon-refresh" @click="loadSuites">刷新</el-button>
                  </div>
                  <el-table :data="suites" border size="mini" height="260" @row-click="selectSuite">
                    <el-table-column prop="name" label="集合名称" min-width="160"></el-table-column>
                    <el-table-column label="接口数" width="70">
                      <template slot-scope="scope">{{ (scope.row.case_ids || []).length }}</template>
                    </el-table-column>
                    <el-table-column label="结果" width="80">
                      <template slot-scope="scope">
                        <el-tag v-if="scope.row.last_success !== null && scope.row.last_success !== undefined" size="mini" :type="scope.row.last_success ? 'success' : 'danger'">
                          {{ scope.row.last_success ? "通过" : "失败" }}
                        </el-tag>
                        <span v-else>-</span>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <div class="suite-editor">
                  <el-form label-width="80px" size="small">
                    <el-form-item label="集合名称">
                      <el-input v-model="suiteForm.name" placeholder="例如：登录下单流程"></el-input>
                    </el-form-item>
                    <el-form-item label="所属项目">
                      <el-select v-model="suiteForm.project_id" clearable placeholder="可选">
                        <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id"></el-option>
                      </el-select>
                    </el-form-item>
                    <el-form-item label="环境">
                      <el-select v-model="suiteForm.environment_id" clearable placeholder="可选">
                        <el-option v-for="item in environments" :key="item.id" :label="item.name" :value="item.id"></el-option>
                      </el-select>
                    </el-form-item>
                    <el-form-item label="执行规则">
                      <el-checkbox v-model="suiteForm.stop_on_fail">失败后中断</el-checkbox>
                    </el-form-item>
                    <el-form-item label="接口顺序">
                      <el-select v-model="suiteForm.case_ids" multiple filterable clearable style="width: 100%" placeholder="按选择顺序运行接口">
                        <el-option
                          v-for="item in cases"
                          :key="item.id"
                          :label="item.name + '  [' + item.method + '] ' + item.url"
                          :value="item.id">
                        </el-option>
                      </el-select>
                    </el-form-item>
                    <el-form-item label="备注">
                      <el-input v-model="suiteForm.description" type="textarea" :rows="2"></el-input>
                    </el-form-item>
                    <el-form-item>
                      <el-button type="primary" icon="el-icon-check" @click="saveSuite">保存集合</el-button>
                      <el-button type="success" icon="el-icon-video-play" :loading="suiteRunning" @click="runSuite">运行集合</el-button>
                      <el-button type="danger" icon="el-icon-delete" :disabled="!suiteForm.id" @click="removeSuite">删除集合</el-button>
                    </el-form-item>
                  </el-form>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
          </div>

          <div v-else class="suite-editor-page" :class="{ 'suite-editor-collapsed': suiteEditorCollapsed }">
            <div class="suite-page-head">
              <div>
                <h3>{{ suiteForm.id ? "编辑接口集合" : "新建接口集合" }}</h3>
                <p>选择运行环境，编排接口顺序后即可保存或直接运行。</p>
              </div>
              <div class="suite-page-actions">
                <el-button plain icon="el-icon-sort" @click="suiteEditorCollapsed = !suiteEditorCollapsed">
                  {{ suiteEditorCollapsed ? "展开编排" : "收起编排" }}
                </el-button>
                <el-button type="primary" icon="el-icon-check" @click="saveSuite">保存集合</el-button>
                <el-button type="success" icon="el-icon-video-play" :loading="suiteRunning" @click="runSuite">运行集合</el-button>
                <el-button type="danger" icon="el-icon-delete" :disabled="!suiteForm.id" @click="removeSuite">删除集合</el-button>
              </div>
            </div>
            <div v-if="suiteEditorCollapsed" class="suite-collapsed-summary" @click="suiteEditorCollapsed = false">
              <span>接口编排已收起</span>
              <strong>{{ (suiteForm.case_ids || []).length }} 个接口</strong>
              <em>点击展开编辑集合信息和接口顺序</em>
            </div>
            <el-form v-else label-width="90px" size="small" class="suite-form">
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="集合名称">
                    <el-input v-model="suiteForm.name" placeholder="例如：平台接口全量冒烟"></el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="所属项目">
                    <el-select v-model="suiteForm.project_id" clearable placeholder="可选">
                      <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id"></el-option>
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="运行环境">
                    <el-select v-model="suiteForm.environment_id" clearable placeholder="选择环境" @change="quickSuiteEnvironmentId = suiteForm.environment_id">
                      <el-option v-for="item in environments" :key="item.id" :label="item.name" :value="item.id"></el-option>
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="执行规则">
                    <el-checkbox v-model="suiteForm.stop_on_fail">失败后中断</el-checkbox>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="备注">
                    <el-input v-model="suiteForm.description" placeholder="集合用途或执行说明"></el-input>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="接口编排" class="suite-transfer-item">
                <div class="suite-case-picker">
                  <div class="suite-case-panel">
                    <div class="suite-case-panel-head">
                      <strong>可选接口用例</strong>
                      <span>{{ suiteAvailableOptions.length }}/{{ suiteTransferData.length }}</span>
                    </div>
                    <el-input v-model="suiteCaseKeyword" size="small" clearable prefix-icon="el-icon-search" placeholder="搜索接口名称、方法或URL"></el-input>
                    <el-checkbox-group v-model="suitePickAvailableIds" class="suite-case-list">
                      <el-checkbox
                        v-for="option in suiteAvailableOptions"
                        :key="option.key"
                        :label="option.key"
                        class="suite-case-row">
                        <div class="suite-case-info" :title="option.fullLabel || option.label">
                          <div class="suite-case-title-line">
                            <strong>{{ option.name || option.label }}</strong>
                            <el-tag size="mini" :type="caseResultTagType(option)" class="suite-case-result-tag">
                              {{ caseResultText(option) }}
                            </el-tag>
                          </div>
                          <span>{{ option.meta }}</span>
                        </div>
                      </el-checkbox>
                    </el-checkbox-group>
                  </div>
                  <div class="suite-case-actions">
                    <el-button type="primary" :disabled="!suitePickSelectedIds.length" @click="removeSuiteCases">
                      <i class="el-icon-arrow-left"></i> 移除
                    </el-button>
                    <el-button type="primary" :disabled="!suitePickAvailableIds.length" @click="addSuiteCases">
                      添加 <i class="el-icon-arrow-right"></i>
                    </el-button>
                  </div>
                  <div class="suite-case-panel">
                    <div class="suite-case-panel-head">
                      <strong>已选接口顺序</strong>
                      <span>{{ suiteSelectedOptions.length }}/{{ (suiteForm.case_ids || []).length }}</span>
                    </div>
                    <el-input v-model="suiteSelectedKeyword" size="small" clearable prefix-icon="el-icon-search" placeholder="搜索已选接口"></el-input>
                    <el-checkbox-group v-model="suitePickSelectedIds" class="suite-case-list">
                      <el-checkbox
                        v-for="option in suiteSelectedOptions"
                        :key="option.key"
                        :label="option.key"
                        class="suite-case-row">
                        <div class="suite-case-info" :title="option.fullLabel || option.label">
                          <div class="suite-case-title-line">
                            <strong>{{ option.name || option.label }}</strong>
                            <el-tag size="mini" :type="caseResultTagType(option)" class="suite-case-result-tag">
                              {{ caseResultText(option) }}
                            </el-tag>
                          </div>
                          <span>{{ option.meta }}</span>
                        </div>
                      </el-checkbox>
                    </el-checkbox-group>
                  </div>
                </div>
              </el-form-item>
            </el-form>
          </div>

          <div class="response-panel">
            <div class="response-head">
              <div class="response-title">
                <strong>{{ sideMode === "case" ? "接口结果" : "集合结果" }}</strong>
                <span>{{ sideMode === "case" ? "单接口执行响应、断言、变量和历史" : "接口集合执行步骤、统计和历史" }}</span>
              </div>
              <div class="response-status">
                <el-tag v-if="lastResult" :type="resultTagType(lastResult)">{{ resultStatusText(lastResult) }}</el-tag>
                <el-tag v-else type="info">未执行</el-tag>
                <span>Status {{ lastResult ? (lastResult.response_status || "-") : "-" }}</span>
                <span>{{ lastResult ? (lastResult.elapsed_ms || 0) : 0 }} ms</span>
                <span v-if="lastResult && lastResult.run_id">run_id {{ lastResult.run_id }}</span>
              </div>
              <el-button
                size="mini"
                icon="el-icon-refresh"
                :disabled="sideMode === 'case' ? !currentCase.id : !suiteForm.id"
                @click="sideMode === 'case' ? loadHistory() : loadSuiteHistory()">
                刷新历史
              </el-button>
            </div>
            <el-tabs v-model="responseTab" class="response-tabs">
              <el-tab-pane label="响应Body" name="body">
                <pre v-if="lastResult" class="response-body">{{ prettyBody(lastResult.response_body) }}</pre>
                <div v-else class="response-empty-state">暂无响应Body，发送接口或选择执行历史后展示</div>
              </el-tab-pane>
              <el-tab-pane label="响应Headers" name="headers">
                <pre v-if="lastResult" class="response-body">{{ prettyJson(lastResult.response_headers) }}</pre>
                <div v-else class="response-empty-state">暂无响应Headers</div>
              </el-tab-pane>
              <el-tab-pane label="断言结果" name="assertions">
                <el-table :data="lastResult ? (lastResult.assertion_result || []) : []" size="mini" border height="300" empty-text="暂无断言结果">
                  <el-table-column label="结果" width="90">
                    <template slot-scope="scope">
                      <el-tag size="mini" :type="resultTagType(scope.row)">{{ resultStatusText(scope.row) }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="name" label="名称" min-width="160"></el-table-column>
                  <el-table-column prop="expected" label="期望" min-width="160"></el-table-column>
                  <el-table-column prop="actual" label="实际" min-width="160"></el-table-column>
                  <el-table-column prop="error" label="错误" min-width="180"></el-table-column>
                </el-table>
              </el-tab-pane>
              <el-tab-pane label="提取变量" name="extractors">
                <el-table :data="lastResult ? (lastResult.extractor_result || []) : []" size="mini" border height="300" empty-text="暂无变量提取结果">
                  <el-table-column label="结果" width="90">
                    <template slot-scope="scope">
                      <el-tag size="mini" :type="scope.row.success ? 'success' : 'danger'">{{ scope.row.success ? "成功" : "失败" }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="name" label="变量名" width="140"></el-table-column>
                  <el-table-column prop="from" label="来源" width="100"></el-table-column>
                  <el-table-column prop="path" label="路径" min-width="180"></el-table-column>
                  <el-table-column label="提取值" min-width="200" show-overflow-tooltip>
                    <template slot-scope="scope">
                      <span class="copy-value" title="点击复制提取值" @click.stop="copyText(scope.row.value, '提取值已复制')">{{ formatCopyValue(scope.row.value) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="error" label="错误" min-width="180"></el-table-column>
                </el-table>
              </el-tab-pane>
              <el-tab-pane label="依赖链" name="chain">
                <el-table :data="lastResult ? (lastResult.chain_results || []) : []" size="mini" border height="300" empty-text="暂无依赖链结果">
                  <el-table-column prop="case_name" label="接口" min-width="180"></el-table-column>
                  <el-table-column prop="method" label="方法" width="80"></el-table-column>
                  <el-table-column prop="response_status" label="状态" width="80"></el-table-column>
                  <el-table-column prop="elapsed_ms" label="耗时ms" width="90"></el-table-column>
                  <el-table-column label="结果" width="80">
                    <template slot-scope="scope">
                      <el-tag size="mini" :type="resultTagType(scope.row)">{{ resultStatusText(scope.row) }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="提取变量" min-width="200">
                    <template slot-scope="scope">
                      <code>{{ scope.row.extracted_variables || {} }}</code>
                    </template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>
              <el-tab-pane label="执行历史" name="history">
                <el-table
                  v-if="sideMode === 'case'"
                  :data="history"
                  size="mini"
                  border
                  height="300"
                  empty-text="暂无接口执行历史"
                  @row-click="selectCaseHistory">
                  <el-table-column label="结果" width="82">
                    <template slot-scope="scope">
                      <el-tag size="mini" :type="resultTagType(scope.row)">{{ resultStatusText(scope.row) }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="run_id" min-width="160" show-overflow-tooltip>
                    <template slot-scope="scope">
                      <span class="copy-run-id" title="点击复制run_id" @click.stop="copyRunId(scope.row.run_id)">{{ scope.row.run_id || "-" }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="method" label="方法" width="75"></el-table-column>
                  <el-table-column prop="response_status" label="状态" width="75"></el-table-column>
                  <el-table-column prop="elapsed_ms" label="耗时ms" width="85"></el-table-column>
                  <el-table-column prop="created_time" label="执行时间" width="155"></el-table-column>
                  <el-table-column prop="url" label="URL" min-width="220" show-overflow-tooltip></el-table-column>
                </el-table>
                <el-table
                  v-else
                  :data="suiteHistory"
                  size="mini"
                  border
                  height="300"
                  v-loading="suiteHistoryLoading"
                  empty-text="暂无集合执行历史"
                  @row-click="selectSuiteHistory">
                  <el-table-column label="结果" width="82">
                    <template slot-scope="scope">
                      <el-tag size="mini" :type="resultTagType(scope.row)">{{ resultStatusText(scope.row) }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="run_id" min-width="165" show-overflow-tooltip>
                    <template slot-scope="scope">
                      <span class="copy-run-id" title="点击复制run_id" @click.stop="copyRunId(scope.row.run_id)">{{ scope.row.run_id || "-" }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="统计" min-width="145">
                    <template slot-scope="scope">
                      总 {{ scope.row.total_count || 0 }} / 过 {{ scope.row.pass_count || 0 }} / 败 {{ scope.row.fail_count || 0 }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="elapsed_ms" label="耗时ms" width="85"></el-table-column>
                  <el-table-column prop="run_by_name" label="执行人" width="95"></el-table-column>
                  <el-table-column prop="created_time" label="执行时间" width="155"></el-table-column>
                </el-table>
              </el-tab-pane>
              <el-tab-pane :label="sideMode === 'case' ? '接口结果' : '集合结果'" name="suite_result">
                <div v-if="sideMode === 'case' && lastResult">
                  <div class="suite-summary">
                    <el-tag :type="resultTagType(lastResult)">{{ resultStatusText(lastResult) }}</el-tag>
                    <strong>Status {{ lastResult.response_status || "-" }}</strong>
                    <span>耗时 {{ lastResult.elapsed_ms || 0 }} ms</span>
                    <span>方法 {{ lastResult.method || currentCase.method || "-" }}</span>
                    <span v-if="lastResult.run_id">run_id {{ lastResult.run_id }}</span>
                  </div>
                  <div class="result-info-grid">
                    <div><span>接口名称</span><strong>{{ lastResult.case_name || currentCase.name || "-" }}</strong></div>
                    <div><span>请求地址</span><strong>{{ lastResult.url || currentCase.url || "-" }}</strong></div>
                    <div><span>执行时间</span><strong>{{ lastResult.created_time || "-" }}</strong></div>
                    <div><span>错误信息</span><strong>{{ lastResult.error_message || "-" }}</strong></div>
                  </div>
                </div>
                <div v-else-if="sideMode === 'case'" class="response-empty-state">暂无接口结果，发送接口或选择执行历史后展示</div>
                <div v-else-if="suiteResult">
                  <div class="suite-summary">
                    <el-tag :type="resultTagType(suiteResult)">{{ resultStatusText(suiteResult) }}</el-tag>
                    <strong>总 {{ suiteResult.total_count || 0 }}</strong>
                    <span>通过 {{ suiteResult.pass_count || 0 }}</span>
                    <span>失败 {{ suiteResult.fail_count || 0 }}</span>
                    <span>耗时 {{ suiteResult.elapsed_ms || 0 }} ms</span>
                    <span>执行人 {{ suiteResult.run_by_name || "-" }}</span>
                  </div>
                  <el-table
                    class="suite-step-table"
                    :data="suiteResult.step_results || []"
                    size="mini"
                    border
                    height="300"
                    @row-click="selectSuiteStepResult">
                    <el-table-column prop="suite_index" label="#" width="55"></el-table-column>
                    <el-table-column prop="case_name" label="接口" min-width="180"></el-table-column>
                    <el-table-column prop="method" label="方法" width="75"></el-table-column>
                    <el-table-column prop="response_status" label="状态" width="75"></el-table-column>
                    <el-table-column prop="elapsed_ms" label="耗时ms" width="85"></el-table-column>
                    <el-table-column label="结果" width="80">
                      <template slot-scope="scope">
                        <el-tag size="mini" :type="resultTagType(scope.row)">{{ resultStatusText(scope.row) }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="error_message" label="错误" min-width="160" show-overflow-tooltip></el-table-column>
                  </el-table>
                </div>
                <div v-else class="response-empty-state">暂无集合结果，运行集合或选择集合执行历史后展示</div>
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
  delete_api_suite,
  get_api_case_info,
  get_api_environment_info,
  get_api_run_history,
  get_api_run_result,
  get_api_suite_history,
  get_api_suite_info,
  get_api_suite_result,
  get_project_info,
  run_api_case,
  run_api_suite,
  save_api_case,
  save_api_environment,
  save_api_suite,
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
    pre_case_ids: [],
    extractors: [],
  };
}

function emptySuite() {
  return {
    id: "",
    name: "",
    project_id: "",
    environment_id: "",
    case_ids: [],
    case_list: [],
    stop_on_fail: true,
    description: "",
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
      headersPlaceholder: '{"Authorization": "Basic {{token|basic}}"}',
      envPlaceholder: '{"host": "http://127.0.0.1:5400", "token": "xxx"}',
      caseLoading: false,
      running: false,
      envDialogVisible: false,
      sideMode: "case",
      filters: { keyword: "", project_id: "", run_status: "", status_code: "" },
      cases: [],
      suites: [],
      caseOptionMap: {},
      projects: [],
      environments: [],
      currentCase: emptyCase(),
      suiteForm: emptySuite(),
      quickSuiteEnvironmentId: "",
      suiteRunning: false,
      suiteEditorCollapsed: false,
      suiteResult: null,
      suiteCaseKeyword: "",
      suiteSelectedKeyword: "",
      suitePickAvailableIds: [],
      suitePickSelectedIds: [],
      suiteHistory: [],
      suiteHistoryLoading: false,
      casePollTimer: null,
      suitePollTimer: null,
      currentEnvironment: {},
      envForm: { id: "", name: "", project_id: "", variablesText: "{\n  \n}", description: "" },
      lastResult: null,
      history: [],
    };
  },
  computed: {
    sidebarSummary() {
      if (this.sideMode === "suite") {
        return `${this.suites.length} 个集合`;
      }
      return `${this.cases.length} 个用例`;
    },
    workspaceTitle() {
      if (this.sideMode === "suite") {
        return this.suiteForm.name || "新建接口集合";
      }
      return this.currentCase.name || "新建接口用例";
    },
    workspaceSubtitle() {
      if (this.sideMode === "suite") {
        const count = (this.suiteForm.case_ids || []).length;
        const env = this.environments.find((item) => item.id === this.suiteForm.environment_id);
        return `${count} 个接口${env ? " · " + env.name : ""}`;
      }
      const method = this.currentCase.method || "GET";
      return this.currentCase.url ? `${method} ${this.currentCase.url}` : "填写请求地址后即可发送调试";
    },
    dependencyOptions() {
      return this.cases.filter((item) => item.id && item.id !== this.currentCase.id);
    },
    suiteTransferData() {
      const optionMap = {};
      const putOption = (item) => {
        if (!item || !item.id) {
          return;
        }
        optionMap[item.id] = {
          key: item.id,
          label: `${item.name}  [${item.method}] ${item.url}`,
          fullLabel: `${item.name}  [${item.method}] ${item.url}`,
          name: item.name,
          meta: `[${item.method}] ${item.url}`,
          last_status: item.last_status,
          last_success: item.last_success,
          last_elapsed_ms: item.last_elapsed_ms,
          disabled: false,
        };
      };
      this.cases.forEach(putOption);
      (this.suiteForm.case_list || []).forEach(putOption);
      (this.suiteForm.case_ids || []).forEach((id) => {
        if (!optionMap[id] && this.caseOptionMap[id]) {
          optionMap[id] = this.caseOptionMap[id];
        }
      });
      const selectedIds = new Set(this.suiteForm.case_ids || []);
      const visibleOptions = this.cases.map((item) => optionMap[item.id]).filter(Boolean);
      const selectedOptions = (this.suiteForm.case_ids || [])
        .map((id) => optionMap[id])
        .filter((item) => item && !visibleOptions.some((option) => option.key === item.key));
      return visibleOptions.concat(selectedOptions).map((item) => ({
        key: item.key,
        label: selectedIds.has(item.key) && !this.cases.some((caseItem) => caseItem.id === item.key)
          ? `${item.label}（不在当前筛选结果）`
          : item.label,
        fullLabel: item.fullLabel || item.label,
        name: item.name || item.label,
        meta: item.meta || "",
        last_status: item.last_status,
        last_success: item.last_success,
        last_elapsed_ms: item.last_elapsed_ms,
        disabled: false,
      }));
    },
    suiteOptionMap() {
      const map = {};
      this.suiteTransferData.forEach((item) => {
        map[item.key] = item;
      });
      return map;
    },
    suiteAvailableOptions() {
      const selected = new Set(this.suiteForm.case_ids || []);
      const keyword = String(this.suiteCaseKeyword || "").toLowerCase();
      return this.suiteTransferData.filter((item) => {
        if (selected.has(item.key)) {
          return false;
        }
        if (!keyword) {
          return true;
        }
        return String(item.fullLabel || item.label || "").toLowerCase().indexOf(keyword) !== -1;
      });
    },
    suiteSelectedOptions() {
      const keyword = String(this.suiteSelectedKeyword || "").toLowerCase();
      return (this.suiteForm.case_ids || [])
        .map((id) => this.suiteOptionMap[id])
        .filter(Boolean)
        .filter((item) => {
          if (!keyword) {
            return true;
          }
          return String(item.fullLabel || item.label || "").toLowerCase().indexOf(keyword) !== -1;
        });
    },
    bodyPlaceholder() {
      return this.currentCase.body_type === "form" ? '{"username": "admin"}' : '{\n  "name": "demo"\n}';
    },
  },
  methods: {
    copyText(value, message) {
      if (value === undefined || value === null || value === "") {
        return;
      }
      const text = typeof value === "string" ? value : JSON.stringify(value);
      const done = () => this.$message.success(message || "已复制");
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done).catch(() => this.fallbackCopy(text, done));
        return;
      }
      this.fallbackCopy(text, done);
    },
    formatCopyValue(value) {
      if (value === undefined || value === null || value === "") {
        return "-";
      }
      return typeof value === "string" ? value : JSON.stringify(value);
    },
    copyRunId(runId) {
      if (!runId) {
        return;
      }
      this.copyText(String(runId), "run_id 已复制");
    },
    fallbackCopy(text, done) {
      const input = document.createElement("textarea");
      input.value = text;
      input.setAttribute("readonly", "readonly");
      input.style.position = "fixed";
      input.style.left = "-9999px";
      document.body.appendChild(input);
      input.select();
      try {
        document.execCommand("copy");
        done();
      } catch (e) {
        this.$message.warning("复制失败，请手动复制");
      }
      document.body.removeChild(input);
    },
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
        pre_case_ids: row.pre_case_ids || [],
        extractors: row.extractors || [],
      };
    },
    methodType(method) {
      return { GET: "success", POST: "primary", PUT: "warning", PATCH: "warning", DELETE: "danger" }[method] || "info";
    },
    resultTagType(row) {
      const status = row && row.run_status;
      if (status === "queued" || status === "pending") {
        return "info";
      }
      if (status === "running") {
        return "warning";
      }
      if (status === "failed") {
        return "danger";
      }
      if (row && row.success === null) {
        return "info";
      }
      return row && row.success ? "success" : "danger";
    },
    resultStatusText(row) {
      if (!row) {
        return "-";
      }
      if (row.status_text) {
        return row.status_text;
      }
      if (row.run_status === "queued") {
        return "排队中";
      }
      if (row.run_status === "pending") {
        return "待执行";
      }
      if (row.run_status === "running") {
        return "执行中";
      }
      if (row.success === null || row.success === undefined) {
        return "-";
      }
      return row.success ? "通过" : "失败";
    },
    caseResultTagType(option) {
      if (!option || option.last_success === null || option.last_success === undefined) {
        return "info";
      }
      return option.last_success ? "success" : "danger";
    },
    caseResultText(option) {
      if (!option || option.last_success === null || option.last_success === undefined) {
        return "未执行";
      }
      const status = option.last_status || "-";
      const result = option.last_success ? "通过" : "失败";
      const elapsed = option.last_elapsed_ms !== null && option.last_elapsed_ms !== undefined ? ` ${option.last_elapsed_ms}ms` : "";
      return `${status} ${result}${elapsed}`;
    },
    addSuiteCases() {
      const exists = new Set(this.suiteForm.case_ids || []);
      const picked = this.suitePickAvailableIds.filter((id) => !exists.has(id));
      this.suiteForm.case_ids = (this.suiteForm.case_ids || []).concat(picked);
      this.suitePickAvailableIds = [];
    },
    removeSuiteCases() {
      const removeSet = new Set(this.suitePickSelectedIds);
      this.suiteForm.case_ids = (this.suiteForm.case_ids || []).filter((id) => !removeSet.has(id));
      this.suitePickSelectedIds = [];
    },
    rememberCaseOptions(items) {
      const next = Object.assign({}, this.caseOptionMap);
      (items || []).forEach((item) => {
        if (!item || !item.id) {
          return;
        }
        next[item.id] = {
          key: item.id,
          label: `${item.name}  [${item.method}] ${item.url}`,
          fullLabel: `${item.name}  [${item.method}] ${item.url}`,
          name: item.name,
          meta: `[${item.method}] ${item.url}`,
          last_status: item.last_status,
          last_success: item.last_success,
          last_elapsed_ms: item.last_elapsed_ms,
          disabled: false,
        };
      });
      this.caseOptionMap = next;
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
      const params = {
        page_no: 0,
        page_size: 1000,
        keyword: this.filters.keyword,
        project_id: this.filters.project_id,
        run_status: this.filters.run_status,
        status_code: this.filters.status_code,
      };
      await get_api_case_info(params).then((res) => {
        if (!res.data || res.data.code !== 200) {
          this.$message.warning((res.data && res.data.msg) || "接口测试用例加载失败");
          this.cases = [];
          return;
        }
        this.cases = res.data.data || [];
        this.rememberCaseOptions(this.cases);
      }).catch((err) => {
        this.cases = [];
        this.$message.warning((err.response && err.response.data && err.response.data.msg) || "接口测试用例加载失败，请确认后端已重启");
      }).finally(() => {
        this.caseLoading = false;
      });
    },
    async loadSuites() {
      const params = {
        page_no: 0,
        page_size: 1000,
        keyword: this.filters.keyword,
        project_id: this.filters.project_id,
        run_status: this.filters.run_status,
      };
      await get_api_suite_info(params).then((res) => {
        if (res.data && res.data.code === 200) {
          this.suites = res.data.data || [];
        } else {
          this.suites = [];
        }
      }).catch(() => {
        this.suites = [];
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
      this.loadSuites();
      this.loadEnvironments();
    },
    reloadSideList() {
      if (this.sideMode === "suite") {
        this.loadSuites();
        this.loadCases();
      } else {
        this.loadCases();
      }
    },
    selectCase(row) {
      this.sideMode = "case";
      if (this.activeTab === "suite") {
        this.activeTab = "params";
      }
      this.currentCase = this.normalizeCase(row);
      this.lastResult = null;
      this.responseTab = "body";
      this.loadHistory();
    },
    newCase() {
      this.sideMode = "case";
      if (this.activeTab === "suite") {
        this.activeTab = "params";
      }
      this.currentCase = emptyCase();
      this.currentCase.project_id = this.filters.project_id || "";
      this.lastResult = null;
      this.responseTab = "body";
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
        pre_case_ids: this.currentCase.pre_case_ids || [],
        extractors: this.currentCase.extractors || [],
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
      this.clearCasePoll();
      await run_api_case(Object.assign({}, payload, { async: true })).then((res) => {
        if (!res.data || res.data.code !== 200) {
          this.$message.warning((res.data && res.data.msg) || "执行失败");
          this.running = false;
          return;
        }
        this.lastResult = res.data.data;
        this.responseTab = "body";
        this.pollCaseResult(this.lastResult.id);
      }).catch(() => {
        this.running = false;
      });
    },
    clearCasePoll() {
      if (this.casePollTimer) {
        clearTimeout(this.casePollTimer);
        this.casePollTimer = null;
      }
    },
    pollCaseResult(resultId) {
      if (!resultId) {
        this.running = false;
        return;
      }
      get_api_run_result({ id: resultId }).then((res) => {
        if (res.data && res.data.code === 200) {
          this.lastResult = res.data.data;
          const status = this.lastResult.run_status;
          if (status === "queued" || status === "running") {
            this.casePollTimer = setTimeout(() => this.pollCaseResult(resultId), 1000);
            return;
          }
          this.running = false;
          this.loadCases();
          this.loadHistory();
          return;
        }
        this.running = false;
      }).catch(() => {
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
    addExtractor(source) {
      this.currentCase.extractors.push({
        name: "",
        from: source,
        path: source === "json" ? "data.token" : "",
      });
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
        this.history = [];
        return;
      }
      const res = await get_api_run_history({ case_id: this.currentCase.id, limit: 20 });
      if (res.data && res.data.code === 200) {
        this.history = res.data.data || [];
      }
    },
    selectCaseHistory(row) {
      this.lastResult = row;
      this.responseTab = "body";
    },
    newSuite() {
      this.sideMode = "suite";
      this.suiteEditorCollapsed = false;
      this.suiteForm = emptySuite();
      this.suiteForm.project_id = this.filters.project_id || "";
      this.suiteForm.environment_id = this.quickSuiteEnvironmentId || "";
      this.suitePickAvailableIds = [];
      this.suitePickSelectedIds = [];
      this.suiteResult = null;
      this.suiteHistory = [];
      this.responseTab = "suite_result";
    },
    selectSuite(row) {
      this.sideMode = "suite";
      this.suiteEditorCollapsed = true;
      this.suiteForm = {
        id: row.id || "",
        name: row.name || "",
        project_id: row.project_id || "",
        environment_id: this.quickSuiteEnvironmentId || row.environment_id || "",
        case_ids: row.case_ids || [],
        case_list: row.case_list || [],
        stop_on_fail: !!row.stop_on_fail,
        description: row.description || "",
      };
      this.rememberCaseOptions(this.suiteForm.case_list);
      this.suitePickAvailableIds = [];
      this.suitePickSelectedIds = [];
      this.suiteResult = null;
      this.responseTab = "suite_result";
      this.loadSuiteHistory();
    },
    async saveSuite() {
      const payload = Object.assign({}, this.suiteForm, {
        stop_on_fail: this.suiteForm.stop_on_fail ? 1 : 0,
      });
      const res = await save_api_suite(payload);
      if (!res.data || res.data.code !== 200) {
        this.$message.warning((res.data && res.data.msg) || "保存失败");
        return;
      }
      this.$message.success(res.data.msg);
      this.selectSuite(res.data.data);
      this.loadSuites();
    },
    async runSuite() {
      if (!this.suiteForm.id) {
        await this.saveSuite();
        if (!this.suiteForm.id) {
          return;
        }
      }
      this.suiteRunning = true;
      this.clearSuitePoll();
      await run_api_suite({ id: this.suiteForm.id, environment_id: this.suiteForm.environment_id, async: true }).then((res) => {
        if (!res.data || res.data.code !== 200) {
          this.$message.warning((res.data && res.data.msg) || "执行失败");
          this.suiteRunning = false;
          return;
        }
        this.suiteResult = res.data.data;
        this.lastResult = { success: this.suiteResult.success, run_status: this.suiteResult.run_status, status_text: this.suiteResult.status_text, response_status: "-", elapsed_ms: this.suiteResult.elapsed_ms, assertion_result: [], extractor_result: [] };
        this.responseTab = "suite_result";
        this.pollSuiteResult(this.suiteResult.id);
      }).catch(() => {
        this.suiteRunning = false;
      });
    },
    clearSuitePoll() {
      if (this.suitePollTimer) {
        clearTimeout(this.suitePollTimer);
        this.suitePollTimer = null;
      }
    },
    pollSuiteResult(resultId) {
      if (!resultId) {
        this.suiteRunning = false;
        return;
      }
      get_api_suite_result({ id: resultId }).then((res) => {
        if (res.data && res.data.code === 200) {
          this.suiteResult = res.data.data;
          this.lastResult = { success: this.suiteResult.success, run_status: this.suiteResult.run_status, status_text: this.suiteResult.status_text, response_status: "-", elapsed_ms: this.suiteResult.elapsed_ms, assertion_result: [], extractor_result: [] };
          const status = this.suiteResult.run_status;
          if (status === "queued" || status === "running") {
            this.suitePollTimer = setTimeout(() => this.pollSuiteResult(resultId), 1000);
            return;
          }
          this.suiteRunning = false;
          this.loadSuites();
          this.loadSuiteHistory();
          return;
        }
        this.suiteRunning = false;
      }).catch(() => {
        this.suiteRunning = false;
      });
    },
    async runSuiteRow(row) {
      this.selectSuite(row);
      if (this.quickSuiteEnvironmentId) {
        this.suiteForm.environment_id = this.quickSuiteEnvironmentId;
      }
      if (!this.suiteForm.environment_id) {
        const env = this.environments.find((item) => item.name === "本地测试平台") || this.environments[0];
        this.suiteForm.environment_id = env && env.id ? env.id : "";
      }
      if (!this.suiteForm.environment_id) {
        this.$message.warning("请选择接口测试环境后再运行集合");
        return;
      }
      await this.runSuite();
    },
    async loadSuiteHistory() {
      if (!this.suiteForm.id) {
        this.suiteHistory = [];
        return;
      }
      this.suiteHistoryLoading = true;
      await get_api_suite_history({ suite_id: this.suiteForm.id, limit: 30 }).then((res) => {
        if (res.data && res.data.code === 200) {
          this.suiteHistory = res.data.data || [];
        } else {
          this.suiteHistory = [];
        }
      }).catch(() => {
        this.suiteHistory = [];
      }).finally(() => {
        this.suiteHistoryLoading = false;
      });
    },
    selectSuiteHistory(row) {
      this.suiteResult = row;
      this.lastResult = {
        success: row.success,
        run_status: row.run_status,
        status_text: row.status_text,
        response_status: "-",
        elapsed_ms: row.elapsed_ms,
        assertion_result: [],
        extractor_result: [],
      };
      this.responseTab = "suite_result";
    },
    selectSuiteStepResult(row) {
      if (!row) {
        return;
      }
      this.lastResult = Object.assign({}, row, {
        case_name: row.case_name || row.name || "",
        assertion_result: row.assertion_result || [],
        extractor_result: row.extractor_result || [],
        chain_results: row.chain_results || [],
      });
      this.responseTab = "body";
    },
    async runPlatformSuite() {
      await Promise.all([this.loadSuites(), this.loadEnvironments()]);
      const suite = this.suites.find((item) => item.name === "平台接口全量冒烟");
      if (!suite) {
        this.$message.warning("未找到平台接口全量冒烟集合，请先执行后端同步脚本");
        return;
      }
      const env = this.quickSuiteEnvironmentId
        ? this.environments.find((item) => item.id === this.quickSuiteEnvironmentId)
        : (this.environments.find((item) => item.name === "本地测试平台") || this.environments[0]);
      this.selectSuite(suite);
      if (env && env.id) {
        this.suiteForm.environment_id = env.id;
        this.quickSuiteEnvironmentId = env.id;
      }
      if (!this.suiteForm.environment_id) {
        this.$message.warning("请选择接口测试环境后再运行集合");
        return;
      }
      await this.runSuite();
    },
    async removeSuite() {
      if (!this.suiteForm.id) {
        return;
      }
      await this.$confirm("确认删除这个接口集合？", "提示", { type: "warning" });
      const res = await delete_api_suite({ id: this.suiteForm.id });
      if (res.data && res.data.code === 200) {
        this.$message.success(res.data.msg);
        this.newSuite();
        this.loadSuites();
      } else {
        this.$message.warning((res.data && res.data.msg) || "删除失败");
      }
    },
  },
  mounted() {
    this.loadProjects();
    this.loadCases();
    this.loadSuites();
    this.loadEnvironments();
  },
  beforeDestroy() {
    this.clearCasePoll();
    this.clearSuitePoll();
  },
};
</script>

<style scoped>
.api-test-page {
  min-height: calc(100vh - 72px);
  padding: 14px 16px 18px;
  background: #f4f7fb;
  overflow-x: hidden;
  box-sizing: border-box;
}
.api-workbench {
  display: flex;
  width: 100%;
  margin-left: 0 !important;
  margin-right: 0 !important;
  box-sizing: border-box;
}
.api-side-col,
.api-main-col {
  float: none;
  box-sizing: border-box;
}
.api-side-col {
  width: 30%;
  flex: 0 0 30%;
}
.api-main-col {
  width: 0;
  flex: 1;
}
.api-side,
.api-main {
  background: #fff;
  border: 1px solid #dde5f0;
  border-radius: 6px;
  box-shadow: 0 8px 22px rgba(40, 64, 95, 0.06);
}
.api-side {
  height: calc(100vh - 108px);
  display: flex;
  flex-direction: column;
  padding: 12px;
  overflow: hidden;
}
.api-main {
  min-height: calc(100vh - 108px);
  padding: 16px 18px 18px;
}
.api-side-head,
.api-main-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.api-side-head {
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e7edf5;
}
.api-side-head div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.api-side-head strong {
  color: #16263a;
  font-size: 16px;
}
.api-side-head span {
  color: #7a8aa0;
  font-size: 12px;
}
.api-main-head {
  margin-bottom: 14px;
  padding: 0 0 14px;
  border-bottom: 1px solid #e7edf5;
}
.api-main-head h2 {
  max-width: 760px;
  margin: 2px 0 5px;
  color: #16263a;
  font-size: 20px;
  line-height: 1.25;
  word-break: break-all;
}
.api-main-head p {
  max-width: 900px;
  margin: 0;
  color: #6e7f95;
  font-size: 12px;
  line-height: 1.5;
  word-break: break-all;
}
.api-main-kicker {
  color: #2f80ed;
  font-size: 12px;
  font-weight: 700;
}
.api-main-status {
  min-width: 150px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  color: #6e7f95;
  font-size: 12px;
  white-space: nowrap;
}
.api-side-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 9px;
}
.api-side-toolbar .el-input,
.api-side-toolbar .el-select {
  flex: 1;
}
.api-side-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.api-side-tabs /deep/ .el-tabs__content {
  flex: 1;
  min-height: 0;
}
.api-side-tabs /deep/ .el-tab-pane {
  height: 100%;
}
.api-side-tabs /deep/ .el-table {
  border: 1px solid #e6edf6;
  border-radius: 4px;
}
.api-side-tabs /deep/ .el-table__row {
  cursor: pointer;
}
.case-row {
  display: flex;
  flex-direction: column;
  gap: 5px;
  line-height: 1.35;
  padding: 2px 0;
}
.case-row strong {
  color: #1f4f99;
  word-break: break-all;
}
.case-row span {
  color: #6b778c;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-all;
}
.case-row.active strong {
  color: #0b63ce;
}
.request-line {
  display: grid;
  grid-template-columns: 112px minmax(320px, 1fr) 190px auto auto;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
  padding: 12px;
  background: #f7faff;
  border: 1px solid #e2eaf5;
  border-radius: 6px;
}
.method-select {
  width: 100%;
}
.env-select {
  width: 100%;
}
.case-form {
  display: grid;
  grid-template-columns: minmax(360px, 1fr) 280px;
  gap: 10px 18px;
  margin-bottom: 8px;
}
.case-form /deep/ .el-form-item {
  margin-bottom: 8px;
}
.case-form /deep/ .el-form-item__content {
  width: auto;
}
.request-tabs {
  margin-top: 8px;
  border: 1px solid #e4ebf5;
  border-radius: 6px;
  padding: 0 12px 12px;
}
.request-tabs /deep/ .el-tabs__header {
  margin-bottom: 12px;
}
.request-tabs /deep/ .el-tabs__item {
  height: 44px;
  line-height: 44px;
}
.body-tools,
.assertion-tools,
.env-toolbar {
  margin-bottom: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.json-editor /deep/ textarea {
  font-family: Consolas, "Courier New", monospace;
  font-size: 13px;
  line-height: 1.6;
  min-height: 240px !important;
  color: #203247;
  background: #fbfdff;
}
.response-panel {
  margin-top: 16px;
  padding: 12px;
  border: 1px solid #dfe8f4;
  border-radius: 6px;
  background: #fbfdff;
}
.response-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  gap: 14px;
}
.response-title {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.response-title strong {
  color: #24364b;
  font-size: 16px;
}
.response-title span {
  color: #7a8aa0;
  font-size: 12px;
}
.response-status {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-left: auto;
}
.response-tabs /deep/ .el-tabs__header {
  margin-bottom: 12px;
}
.response-body {
  min-height: 300px;
  max-height: 520px;
  overflow: auto;
  margin: 0;
  padding: 14px;
  color: #24364b;
  background: #f5f8fc;
  border: 1px solid #dfe7f1;
  border-radius: 4px;
  font-family: Consolas, "Courier New", monospace;
  line-height: 1.55;
}
.response-empty-state {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7a8aa0;
  background: #f5f8fc;
  border: 1px solid #dfe7f1;
  border-radius: 4px;
}
.copy-run-id,
.copy-value {
  color: #2f80ed;
  cursor: pointer;
  user-select: none;
}
.copy-run-id:hover,
.copy-value:hover {
  text-decoration: underline;
}
.suite-layout {
  display: block;
}
.suite-list {
  display: none;
}
.suite-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.suite-side-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  padding: 10px;
  background: #f7faff;
  border: 1px solid #e3ebf5;
  border-radius: 5px;
}
.suite-side-actions .el-select {
  flex: 1;
}
.suite-editor-page {
  min-height: 690px;
}
.suite-editor-page.suite-editor-collapsed {
  min-height: 0;
  margin-bottom: 8px;
}
.suite-page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  padding: 14px;
  background: #f7faff;
  border: 1px solid #e1eaf4;
  border-radius: 6px;
}
.suite-page-head h3 {
  margin: 0 0 6px;
  font-size: 18px;
  color: #24364b;
}
.suite-page-head p {
  margin: 0;
  color: #7a8aa0;
}
.suite-page-actions {
  display: flex;
  gap: 8px;
  white-space: nowrap;
}
.suite-collapsed-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 0;
  padding: 12px 14px;
  color: #4b6078;
  background: #fbfdff;
  border: 1px dashed #c9d6e6;
  border-radius: 6px;
  cursor: pointer;
}
.suite-collapsed-summary span {
  color: #7a8aa0;
}
.suite-collapsed-summary strong {
  color: #2f80ed;
}
.suite-collapsed-summary em {
  color: #7a8aa0;
  font-style: normal;
}
.suite-form {
  padding: 0 2px;
}
.suite-form .el-select {
  width: 100%;
}
.suite-form /deep/ .el-form-item__content {
  max-width: none;
}
.suite-transfer-item /deep/ .el-form-item__content {
  width: calc(100% - 110px);
}
.suite-case-picker {
  display: grid;
  grid-template-columns: minmax(430px, 1fr) 116px minmax(430px, 1fr);
  align-items: center;
  gap: 18px;
  width: 100%;
}
.suite-case-panel {
  border: 1px solid #dfe6f0;
  border-radius: 6px;
  background: #fff;
  overflow: hidden;
}
.suite-case-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 40px;
  padding: 0 14px;
  background: #f4f7fb;
  border-bottom: 1px solid #dfe6f0;
}
.suite-case-panel-head strong {
  color: #24364b;
}
.suite-case-panel-head span {
  color: #7a8aa0;
  font-size: 12px;
}
.suite-case-panel .el-input {
  display: block;
  width: calc(100% - 24px);
  margin: 12px;
}
.suite-case-list {
  height: 520px;
  overflow: auto;
  padding: 0 12px 12px;
}
.suite-case-row {
  display: flex;
  align-items: flex-start;
  width: 100%;
  min-height: 70px;
  margin: 0;
  padding: 10px 0;
  border-bottom: 1px solid #edf1f7;
  box-sizing: border-box;
}
.suite-case-row /deep/ .el-checkbox__input {
  margin-top: 4px;
}
.suite-case-row /deep/ .el-checkbox__label {
  display: block;
  width: calc(100% - 24px);
  padding-left: 10px;
  line-height: 1.35;
  white-space: normal;
}
.suite-case-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}
.suite-case-title-line {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
}
.suite-case-info strong {
  color: #24364b;
  line-height: 18px;
  white-space: normal;
  word-break: break-all;
  min-width: 0;
}
.suite-case-info span {
  color: #7a8aa0;
  font-size: 12px;
  line-height: 16px;
  white-space: normal;
  word-break: break-all;
}
.suite-case-result-tag {
  flex: 0 0 auto;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.suite-case-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}
.suite-case-actions .el-button {
  width: 96px;
  margin: 0;
}
.suite-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.result-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(240px, 1fr));
  border: 1px solid #dfe8f4;
  border-radius: 4px;
  overflow: hidden;
}
.result-info-grid div {
  min-height: 44px;
  padding: 8px 10px;
  border-right: 1px solid #dfe8f4;
  border-bottom: 1px solid #dfe8f4;
  background: #fff;
}
.result-info-grid div:nth-child(2n) {
  border-right: none;
}
.result-info-grid div:nth-last-child(-n + 2) {
  border-bottom: none;
}
.result-info-grid span {
  display: block;
  margin-bottom: 4px;
  color: #7a8aa0;
  font-size: 12px;
}
.result-info-grid strong {
  display: block;
  color: #24364b;
  font-size: 13px;
  font-weight: 500;
  word-break: break-all;
}
.suite-history-panel {
  border: 1px solid #dfe8f4;
  border-radius: 6px;
  background: #fff;
  overflow: hidden;
}
.suite-bottom-grid {
  display: grid;
  grid-template-columns: minmax(420px, 1fr) minmax(420px, 1fr);
  gap: 14px;
  margin-top: 16px;
}
.case-bottom-grid {
  display: grid;
  grid-template-columns: minmax(520px, 1.35fr) minmax(430px, 1fr);
  gap: 14px;
  margin-top: 16px;
}
.suite-result-panel {
  border: 1px solid #dfe8f4;
  border-radius: 6px;
  background: #fff;
  overflow: hidden;
}
.case-result-panel,
.case-history-panel {
  border: 1px solid #dfe8f4;
  border-radius: 6px;
  background: #fff;
  overflow: hidden;
}
.case-result-body {
  padding: 12px;
}
.suite-result-body {
  padding: 12px;
}
.suite-empty-state {
  min-height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7a8aa0;
  background: #fbfdff;
}
.suite-history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  background: #f7faff;
  border-bottom: 1px solid #dfe8f4;
}
.suite-history-head div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.suite-history-head strong {
  color: #24364b;
}
.suite-history-head span {
  color: #7a8aa0;
  font-size: 12px;
}
.suite-history-panel /deep/ .el-table__row {
  cursor: pointer;
}
.case-history-panel /deep/ .el-table__row {
  cursor: pointer;
}
.suite-step-table /deep/ .el-table__row {
  cursor: pointer;
}
code {
  color: #4b6078;
}

@media (max-width: 1360px) {
  .api-side-col {
    width: 32%;
    flex-basis: 32%;
  }
  .request-line {
    grid-template-columns: 104px minmax(240px, 1fr) 160px;
  }
  .request-line .el-button,
  .request-line .el-dropdown {
    width: 100%;
  }
}

@media (max-width: 1500px) {
  .suite-case-picker {
    grid-template-columns: 1fr;
    align-items: stretch;
  }
  .suite-case-actions {
    flex-direction: row;
    justify-content: center;
  }
  .suite-case-list {
    height: 320px;
  }
  .suite-bottom-grid {
    grid-template-columns: 1fr;
  }
  .case-bottom-grid {
    grid-template-columns: 1fr;
  }
}
</style>
