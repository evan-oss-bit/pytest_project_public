<template>
    <section>
        <!--工具条-->
        <el-col :span="24" class="toolbar" style="padding-bottom: 0px">
            <el-form :inline="true" :model="filters">
                <el-col :span="20" justify="">
                    <el-form-item>
                        <el-input v-model="filters.cfg_name" placeholder="任务名称" clearable>
                            <i slot="prefix" class="el-input__icon el-icon-search"></i>
                        </el-input>
                    </el-form-item>
                    <el-select v-model="value2" clearable placeholder="请选择">
                        <el-option v-for="item in options2" :key="item.value2" :label="item.label" :value="item.value2">
                        </el-option>
                    </el-select>
                    <el-form-item>
                        <el-button type="primary" icon="el-icon-search" v-on:click="getConfigList">查询</el-button>
                    </el-form-item>
                    <div>
                        <el-form-item>
                            <el-button @click="handleaddEvent" type="primary"
                                style="float: right; text-align: right; margin-left: 10px">新增测试任务</el-button>
                        </el-form-item>
                    </div>
                    <div>
                        <el-form-item>
                            <el-button @click="stop_set" type="danger"
                                style="float: right; text-align: right; margin-left: 10px">批量终止测试任务</el-button>
                        </el-form-item>
                    </div>
                </el-col>
            </el-form>
        </el-col>
        <!-- <template>
            <div v-html="htmlContent"></div>
        </template> -->
        <!--列表-->
        <el-col :span="24" type="“flex”" style="white-space: pre">
            <el-table :data="aioLst" highlight-current-row stripe height="600" v-loading="listLoading"
                @selection-change="selsChange" style="width: 100%" :cell-style="cellStyle">

                <!-- <el-table-column type="selection" width="2">
                </el-table-column> -->
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in lstForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column>
                <el-table-column label="测试集进度"><template slot-scope="scope"><el-progress :percentage="percentagenum2(scope.row)" :format="format"></el-progress></template></el-table-column>
                <el-table-column label="测试集">
                    <template slot-scope="scope">
                        <el-tag
                            v-for="tag in scope.row.set_name"
                            :key="tag"
                            type="primary"
                            style="margin-right: 4px;">
                            {{ tag }}
                        </el-tag>
                    </template>
                </el-table-column>
                <!-- <el-table-column label="全局配置">
                    <template slot-scope="scope">
                        <el-tag
                            v-for="tag in scope.row.cfg_name"
                            :key="tag"
                            type="primary"
                            style="margin-right: 4px;">
                            {{ tag }}
                        </el-tag>
                    </template>
                </el-table-column> -->
                <el-table-column label="定时任务倒计时（时:分:秒）" width="95"><template slot-scope="scope">{{ scope.row.countdown}}</template></el-table-column>
                <el-table-column label="已测试时间（时:分:秒）" width="95"><template slot-scope="scope">{{ scope.row.run_task_time}}</template></el-table-column>
                <!-- <el-table-column label="用例数量（条）" width="80"><template slot-scope="scope">{{ JSON.parse(scope.row.case_ids).length}}</template></el-table-column> -->
                <el-table-column label="运行状态" width="100"><template slot-scope="scope">{{ scope.row.run_status | stateFmt
                }}</template></el-table-column>
                
                <el-table-column label="测试进度"><template slot-scope="scope"><el-progress :percentage="percentagenum(scope.row)" :format="format"></el-progress></template></el-table-column>
                <el-table-column label="操作">
                    <template slot-scope="scope">
                        <el-row>
                            <el-dropdown split-button type="primary" @click="handleAddEvent(scope.$index, scope.row)"
                                trigger="click">
                                运行
                                <el-dropdown-menu slot="dropdown">
                                    <el-button-group class="button-container">
                                        <el-button type="primary"
                                            @click="handleEditEvent(scope.$index, scope.row)">编辑</el-button>
                                        <!-- <el-button @click="handleAddEvent_rerun(scope.$index, scope.row, 1)"
                                            type="primary">失败用例重试</el-button> -->
                                        <el-button type="primary" icon="el-icon-search"
                                            @click="getSetListNow(scope.$index, scope.row)">任务测试集详情</el-button>
                                        <!-- <el-button type="primary" icon="el-icon-search"
                                            @click="getCaseList(scope.$index, scope.row)">查看用例</el-button> -->
                                        <el-button type="primary"
                                            @click="getSetReportList(scope.$index, scope.row)">最新任务报告列表</el-button>
                                        <el-button type="primary" icon="el-icon-time"
                                            @click="getTaskTimeline(scope.$index, scope.row)">任务执行时间线</el-button>
                                        <el-button type="primary" icon="el-icon-date"
                                            @click="getTaskHistory(scope.$index, scope.row)">任务运行历史</el-button>
                                        <el-button type="primary" icon="el-icon-document"
                                            @click="getTaskConfigSnapshot(scope.$index, scope.row)">任务级配置快照</el-button>
                                        <!-- <el-button type="primary" icon="el-icon-share"
                                            @click="get_html(scope.$index, scope.row)">查看最新报告</el-button> -->
                                        <!-- <el-button type="primary" icon="el-icon-share"
                                            @click="download(scope.$index, scope.row)">下载最新报告</el-button> -->
                                        
                                        <el-button type="warning" @click="delete_id_new(scope.$index, scope.row)">终止</el-button>
                                        <el-button type="danger" @click="is_deletes(scope.$index, scope.row)">删除</el-button>
                                    </el-button-group>
                                </el-dropdown-menu>
                            </el-dropdown>
                            <el-button-group>
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
        <!-- <el-dialog title="用例列表" :visible.sync="dialogTableVisible">
            <el-table :data="gridData">
                <el-table-column property="date" label="日期" width="150"></el-table-column>
                <el-table-column property="name" label="姓名" width="200"></el-table-column>
                <el-table-column property="address" label="地址"></el-table-column>
            </el-table>
        </el-dialog> -->
        <el-dialog :title="set_title" :visible.sync="dialogTableVisible">
            <el-col class="toolbar" height="600">
                <el-pagination layout="total" :total="setcasetotal" style="float: right">
                </el-pagination>
            </el-col>
            <el-button type="primary" @click="getCaseList(1, testset_row)">刷新当前页</el-button>
            <template>
                <el-table :data="count_info" style="width: 100%">
                    <el-table-column prop="schedule" label="测试进度（%）"></el-table-column>
                    <el-table-column prop="all_count" label="全部用例数"></el-table-column>
                    <el-table-column prop="pass_count" label="通过用例数"></el-table-column>
                    <el-table-column prop="pass_rate" label="用例通过率（%）"></el-table-column>
                    <el-table-column prop="fail_count" label="失败用例数"></el-table-column>
                    <el-table-column prop="error_count" label="错误用例数"></el-table-column>
                    <el-table-column prop="executed_ing" label="测试中用例数"></el-table-column>
                    <el-table-column prop="un_executed" label="未测试用例数"></el-table-column>
                </el-table>
            </template>
            <!-- <el-col :span="24" type="“flex”" style="white-space: pre"> -->
            <el-table :data="CaseList" highlight-current-row stripe height="400" v-loading="listLoading" id="exportTab"
                @selection-change="selsChange" style="width: 100%" :cell-style="CasecellStyle">
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in lstForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column>
                <el-table-column label="定时任务倒计时（时:分:秒）" width="95"><template slot-scope="scope">{{ scope.row.countdown}}</template></el-table-column>
                <el-table-column label="已测试时间（时:分:秒）" width="95"><template slot-scope="scope">{{ scope.row.run_task_time}}</template></el-table-column>
                <!-- <el-table-column label="用例数量（条）" width="80"><template slot-scope="scope">{{ JSON.parse(scope.row.case_ids).length}}</template></el-table-column> -->
                <el-table-column label="运行状态" width="100"><template slot-scope="scope">{{ scope.row.run_status | stateFmt
                }}</template></el-table-column>
                
                <el-table-column label="测试进度"><template slot-scope="scope"><el-progress :percentage="percentagenum(scope.row)" :format="format"></el-progress></template></el-table-column>
                <el-table-column label="任务优先级" width="65"><template slot-scope="scope">{{ scope.row.priority | PriorityFmt
                }}</template></el-table-column>
                <!-- <el-table-column label="操作">
                    <template scope="scope">
                        <el-row>
                        </el-row>
                    </template>
                </el-table-column> -->
            </el-table>
            <!-- </el-col> -->
        </el-dialog>

        <el-dialog :title="set_title" :visible.sync="casenow_dialogTableVisible">
            <el-col class="toolbar" height="600">
                <el-pagination layout="total" :total="setcasetotal" style="float: right">
                </el-pagination>
            </el-col>
            <el-button type="primary" @click="getSetListNow(1, testset_row)">刷新当前页</el-button>
            <!-- <template>
                <el-table :data="count_info" style="width: 100%">
                    <el-table-column prop="schedule" label="测试进度（%）"></el-table-column>
                    <el-table-column prop="all_count" label="全部用例数"></el-table-column>
                    <el-table-column prop="pass_count" label="通过用例数"></el-table-column>
                    <el-table-column prop="pass_rate" label="用例通过率（%）"></el-table-column>
                    <el-table-column prop="fail_count" label="失败用例数"></el-table-column>
                    <el-table-column prop="error_count" label="错误用例数"></el-table-column>
                    <el-table-column prop="executed_ing" label="测试中用例数"></el-table-column>
                    <el-table-column prop="un_executed" label="未测试用例数"></el-table-column>
                </el-table>
            </template> -->
            <!-- <el-col :span="24" type="“flex”" style="white-space: pre"> -->
            <el-table :data="CaseList" highlight-current-row stripe height="400" v-loading="listLoading" id="exportTab"
                @selection-change="selsChange" style="width: 100%" :cell-style="CasecellStyle">
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in CaseForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column>
                <!-- <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in lstForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column> -->
                <!-- <el-table-column label="定时任务倒计时（时:分:秒）" width="95"><template slot-scope="scope">{{ scope.row.countdown}}</template></el-table-column> -->
                <!-- <el-table-column label="已测试时间（时:分:秒）" width="95"><template slot-scope="scope">{{ scope.row.run_task_time}}</template></el-table-column> -->
                <!-- <el-table-column label="用例数量（条）" width="80"><template slot-scope="scope">{{ scope.row.case_count_total}}</template></el-table-column> -->
                <el-table-column label="运行状态" width="100"><template slot-scope="scope">{{ scope.row.run_status | stateFmt
                }}</template></el-table-column>
                
                <el-table-column label="测试进度"><template slot-scope="scope"><el-progress :percentage="percentagenum(scope.row)" :format="format"></el-progress></template></el-table-column>
                <!-- <el-table-column label="任务优先级" width="65"><template slot-scope="scope">{{ scope.row.priority | PriorityFmt
                }}</template></el-table-column> -->
                <!-- <el-table-column label="操作">
                    <template scope="scope">
                        <el-row>
                        </el-row>
                    </template>
                </el-table-column> -->
            </el-table>
            <!-- </el-col> -->
        </el-dialog>
        <el-dialog :title="set_title" :visible.sync="setdialogTableVisible">
            <el-col class="toolbar" height="600">
                <el-pagination layout="total" :total="setcasetotal" style="float: right">
                </el-pagination>
            </el-col>
            <el-table :data="ReportList" highlight-current-row stripe height="400" v-loading="listLoading" id="exportTab"
                @selection-change="selsChange" style="width: 100%" :cell-style="CasecellStyle">
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column v-for="item in ReportForm" :key="item.prop" :prop="item.prop" :label="item.label"
                    :width="item.width" style="white-space: pre" sortable>
                </el-table-column>

                <!-- <el-table-column label="用例类型" width="120"><template slot-scope="scope">{{ scope.row.type | testFmt
                }}</template></el-table-column> -->
                <el-table-column label="操作" width="300">
                    <template slot-scope="scope">
                        <el-row>
                            <el-button-group>
                                <el-button type="primary" icon="el-icon-share"
                                    @click="get_html_list(scope.$index, scope.row)">查看在线报告</el-button>
                                <el-button type="primary" icon="el-icon-share"
                                    @click="download_list(scope.$index, scope.row)">下载报告</el-button>
                            </el-button-group>
                        </el-row>

                    </template>

                </el-table-column>
            </el-table>
        </el-dialog>

        <el-dialog :title="timelineTitle" :visible.sync="timelineVisible" width="76%" top="5vh">
            <div class="task-timeline-summary" v-loading="timelineLoading">
                <div class="task-timeline-card">
                    <span>运行ID</span>
                    <strong>{{ taskTimeline.run_id || "-" }}</strong>
                </div>
                <div class="task-timeline-card">
                    <span>测试集数</span>
                    <strong>{{ taskTimeline.set_count || 0 }}</strong>
                </div>
                <div class="task-timeline-card">
                    <span>报告数</span>
                    <strong>{{ taskTimeline.report_count || 0 }}</strong>
                </div>
                <div class="task-timeline-card">
                    <span>任务进度</span>
                    <strong>{{ taskTimeline.schedule || 0 }}%</strong>
                </div>
            </div>
            <el-timeline class="task-timeline-list">
                <el-timeline-item
                    v-for="(item, index) in taskTimeline.timeline"
                    :key="index"
                    :timestamp="item.time || '暂无时间'"
                    :type="timelineStatusType(item.status)"
                    placement="top">
                    <div class="task-timeline-item">
                        <div class="task-timeline-head">
                            <strong>{{ item.title }}</strong>
                            <el-tag size="mini" :type="timelineStatusType(item.status)">{{ timelineStatusText(item.status) }}</el-tag>
                        </div>
                        <div class="task-timeline-desc">{{ item.desc }}</div>
                        <div v-if="item.type === 'testset'" class="task-timeline-meta">
                            <span>项目：{{ item.project_name || '-' }}</span>
                            <span>用例：{{ item.all_count || 0 }}</span>
                            <span>耗时/s：{{ item.case_all_time || '-' }}</span>
                            <span v-if="item.report_title">报告：{{ item.report_title }}</span>
                        </div>
                        <div v-if="item.report_path" class="task-timeline-actions">
                            <el-button size="mini" type="primary" icon="el-icon-view" @click="previewTimelineReport(item)">
                                预览报告
                            </el-button>
                        </div>
                    </div>
                </el-timeline-item>
            </el-timeline>
            <div v-if="!timelineLoading && (!taskTimeline.timeline || taskTimeline.timeline.length === 0)" class="task-timeline-empty">
                暂无执行时间线
            </div>
        </el-dialog>

        <!--详情界面-->
        <!-- <el-dialog title="详情" v-model="detailFormVisible" :close-on-click-modal="false"> -->
        <el-dialog :title="historyTitle" :visible.sync="historyVisible" width="82%" top="5vh">
            <el-table :data="taskHistory" height="560" stripe v-loading="historyLoading" class="task-history-table">
                <el-table-column prop="run_id" label="运行ID" width="150"></el-table-column>
                <el-table-column prop="end_time" label="完成时间" width="170"></el-table-column>
                <el-table-column prop="set_names" label="测试集" min-width="220"></el-table-column>
                <el-table-column prop="report_count" label="报告数" width="80"></el-table-column>
                <el-table-column prop="all_count" label="用例数" width="80"></el-table-column>
                <el-table-column prop="pass_rate" label="通过率" width="90">
                    <template slot-scope="scope">{{ scope.row.pass_rate }}%</template>
                </el-table-column>
                <el-table-column prop="fail_count" label="失败" width="70"></el-table-column>
                <el-table-column prop="error_count" label="错误" width="70"></el-table-column>
                <el-table-column prop="case_all_time" label="耗时/s" width="90"></el-table-column>
                <el-table-column label="状态" width="90">
                    <template slot-scope="scope">
                        <el-tag size="mini" :type="scope.row.status === 'passed' ? 'success' : 'danger'">
                            {{ scope.row.status === 'passed' ? '通过' : '异常' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="160" fixed="right">
                    <template slot-scope="scope">
                        <el-button type="text" icon="el-icon-time" @click="openHistoryTimeline(scope.row)">时间线</el-button>
                        <el-button type="text" icon="el-icon-document" @click="openHistoryConfigSnapshot(scope.row)">配置</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <div v-if="!historyLoading && taskHistory.length === 0" class="task-timeline-empty">
                暂无运行历史
            </div>
        </el-dialog>

        <el-dialog :title="snapshotTitle" :visible.sync="snapshotVisible" width="84%" top="5vh">
            <div class="task-snapshot-summary" v-loading="snapshotLoading">
                <div class="task-timeline-card">
                    <span>运行ID</span>
                    <strong>{{ taskConfigSnapshot.run_id || "-" }}</strong>
                </div>
                <div class="task-timeline-card">
                    <span>任务级配置</span>
                    <strong>{{ (taskConfigSnapshot.task_configs || []).length }}</strong>
                </div>
                <div class="task-timeline-card">
                    <span>测试集快照</span>
                    <strong>{{ taskConfigSnapshot.report_count || 0 }}</strong>
                </div>
            </div>
            <div class="task-snapshot-section">
                <div class="task-snapshot-title">任务级配置</div>
                <el-table :data="taskConfigSnapshot.task_configs || []" height="220" size="mini" stripe>
                    <el-table-column prop="id" label="ID" width="70"></el-table-column>
                    <el-table-column prop="cfg_name" label="配置名称" width="180"></el-table-column>
                    <el-table-column prop="mark" label="备注" width="180"></el-table-column>
                    <el-table-column label="配置内容" min-width="360">
                        <template slot-scope="scope">
                            <pre class="task-snapshot-json">{{ formatConfigText(scope.row.cfg) }}</pre>
                        </template>
                    </el-table-column>
                </el-table>
            </div>
            <div class="task-snapshot-section">
                <div class="task-snapshot-title">测试集实际配置快照</div>
                <el-table :data="taskConfigSnapshot.set_snapshots || []" height="360" size="mini" stripe>
                    <el-table-column type="expand">
                        <template slot-scope="scope">
                            <el-table :data="scope.row.configs || []" size="mini" stripe>
                                <el-table-column prop="id" label="ID" width="70"></el-table-column>
                                <el-table-column prop="cfg_name" label="配置名称" width="180"></el-table-column>
                                <el-table-column prop="mark" label="备注" width="180"></el-table-column>
                                <el-table-column label="配置内容" min-width="360">
                                    <template slot-scope="configScope">
                                        <pre class="task-snapshot-json">{{ formatConfigText(configScope.row.cfg) }}</pre>
                                    </template>
                                </el-table-column>
                            </el-table>
                        </template>
                    </el-table-column>
                    <el-table-column prop="set_name" label="测试集" min-width="180"></el-table-column>
                    <el-table-column prop="project_name" label="项目" min-width="140"></el-table-column>
                    <el-table-column prop="config_count" label="配置数" width="80"></el-table-column>
                    <el-table-column prop="updated_time" label="报告时间" width="170"></el-table-column>
                    <el-table-column prop="report_title" label="报告" min-width="220"></el-table-column>
                    <el-table-column label="操作" width="110" fixed="right">
                        <template slot-scope="scope">
                            <el-button
                                v-if="scope.row.report_path"
                                type="text"
                                icon="el-icon-view"
                                @click="previewTimelineReport(scope.row)">
                                预览报告
                            </el-button>
                            <span v-else class="task-snapshot-muted">无报告</span>
                        </template>
                    </el-table-column>
                </el-table>
            </div>
            <div v-if="!snapshotLoading && !(taskConfigSnapshot.set_snapshots || []).length && !(taskConfigSnapshot.task_configs || []).length" class="task-timeline-empty">
                暂无配置快照
            </div>
        </el-dialog>

        <el-dialog :title="runset_title" :close-on-click-modal="false" :visible.sync="detailFormVisible">
            <el-form :model="addForm" label-width="150px" :rules="detailFormRules" ref="addForm">
                <el-col :span="24" style="margin-right: 100px">
                    <el-row><el-form-item>
                            <pre>1.测试集按照所选顺序依次运行</pre>
                        </el-form-item></el-row>
                        <el-row>
                        <el-col :span="18">
                            <el-form-item label="测试集与执行顺序" class="len_input" required>
                                <div class="block" style="">
                                    <span class="demonstration">
                                    </span>
                                    <el-select v-model="addForm.value5" filterable multiple clearable default-first-option placeholder="请选择关联测试集(也可输入测试集搜索)">
                                        <el-option
                                        v-for="item in addForm.options5"
                                        :key="item.value"
                                        :label="item.label"
                                        :value="item.value">
                                        </el-option>   
                                    </el-select>
                                    <div class="task-set-order-panel">
                                        <div class="task-set-order-title">已选执行顺序</div>
                                        <draggable v-model="selectedTaskSets" handle=".task-set-drag" @end="syncTaskSetIdsFromSelected">
                                            <div v-for="(item, index) in selectedTaskSets" :key="item.value" class="task-set-order-item">
                                                <span class="task-set-index">{{ index + 1 }}</span>
                                                <i class="el-icon-rank task-set-drag"></i>
                                                <span class="task-set-name">{{ item.label }}</span>
                                                <el-button type="text" icon="el-icon-arrow-up" :disabled="index === 0" @click="moveTaskSet(index, -1)"></el-button>
                                                <el-button type="text" icon="el-icon-arrow-down" :disabled="index === selectedTaskSets.length - 1" @click="moveTaskSet(index, 1)"></el-button>
                                                <el-button type="text" icon="el-icon-close" class="task-set-remove" @click="removeTaskSet(index)"></el-button>
                                            </div>
                                        </draggable>
                                        <div v-if="selectedTaskSets.length === 0" class="task-set-empty">请选择测试集</div>
                                    </div>
                                </div>
                            </el-form-item>
                        </el-col>
                        <!-- <el-col :span="9">
                        </el-col> -->
                    </el-row>
                    <el-row>
                        <el-col :span="9">
                            <el-form-item label="全局配置" class="len_input">
                                <div class="block" style="">
                                    <span class="demonstration">
                                    </span>
                                    <el-select v-model="addForm.value3" filterable multiple clearable default-first-option placeholder="请选择关联配置(也可输入配置搜索)">
                                        <el-option
                                        v-for="item in addForm.options3"
                                        :key="item.value"
                                        :label="item.label"
                                        :value="item.value">
                                        </el-option>   
                                    </el-select>
                                </div>
                            </el-form-item>
                        </el-col>
                        <!-- <el-col :span="9">
                            <p>当前所选项序号:</p>
                            <ul>
                                <li v-for="(selectedItem, index) in addForm.value3" :key="selectedItem">
                                {{ index + 1 }}
                                </li>
                            </ul>
                            </el-col> -->
                        <!-- <el-col :span="9">
                        </el-col> -->
                    </el-row>
             
        
       
                    <el-form-item label="是否发送邮件">
                        <el-tooltip  :content="'绿色则为发送,红色则为不发送'" placement="top">
                            <el-switch v-model="sent_email" active-color="#13ce66" inactive-color="#ff4949" active-value=1
                                inactive-value=0>
                            </el-switch>
                        </el-tooltip>
                    </el-form-item>
                    <el-form-item label="邮件地址">
                        <el-input placeholder="输入邮件地址即可发送邮件，多个邮件间请用;来区分" type="input" v-model="addForm.email_to"></el-input>
                    </el-form-item>

                    <el-form-item label="备注信息">
                        <el-input type="textarea" v-model="addForm.mark" placeholder="填写测试任务备注信息"></el-input>
                    </el-form-item>
                    <el-form-item label="定时任务开启时间">
                        <!-- <span class="demonstration">带快捷选项</span> -->
                        <el-date-picker v-model="datevalue2" type="datetime" value-format="yyyy-MM-dd HH:mm:ss"
                            placeholder="选择时间则开启定时任务">
                        </el-date-picker>
                    </el-form-item>

                </el-col>
            </el-form>
            <div slot="footer" class="dialog-footer">
                <el-button type="primary" :disabled="false" @click="previewExecutionPlan">预览执行计划
                </el-button>
                <el-button @click.native="detailFormVisible = false">返回</el-button>
            </div>
        </el-dialog>
        <el-dialog title="任务执行计划预览" :visible.sync="executionPreviewVisible" width="78%" top="5vh">
            <div class="execution-preview">
                <div class="execution-preview-grid">
                    <div class="execution-preview-card">
                        <span>测试集数量</span>
                        <strong>{{ executionPreview.set_count }}</strong>
                    </div>
                    <div class="execution-preview-card">
                        <span>总用例数</span>
                        <strong>{{ executionPreview.case_count }}</strong>
                    </div>
                    <div class="execution-preview-card">
                        <span>预计耗时/s</span>
                        <strong>{{ executionPreview.estimated_time }}</strong>
                    </div>
                    <div class="execution-preview-card">
                        <span>执行方式</span>
                        <strong>{{ executionPreview.run_mode }}</strong>
                    </div>
                </div>
                <el-row :gutter="16" class="execution-preview-row">
                    <el-col :span="12">
                        <div class="execution-preview-section">
                            <div class="execution-preview-title">运行配置</div>
                            <div class="execution-preview-line">配置：{{ executionPreview.config_names || "未选择" }}</div>
                            <div class="execution-preview-line">邮件：{{ executionPreview.email_to || "不发送" }}</div>
                            <div class="execution-preview-line">定时：{{ executionPreview.timed_task_time || "立即执行" }}</div>
                            <div class="execution-preview-line">备注：{{ executionPreview.mark || "无" }}</div>
                        </div>
                    </el-col>
                    <el-col :span="12">
                        <div class="execution-preview-section">
                            <div class="execution-preview-title">执行说明</div>
                            <div class="execution-preview-line">测试集会按下方顺序串行执行。</div>
                            <div class="execution-preview-line">确认后会写入配置文件并开始运行或创建定时任务。</div>
                        </div>
                    </el-col>
                </el-row>
                <el-table :data="executionPreview.sets" height="360" stripe size="mini">
                    <el-table-column prop="order" label="#" width="60"></el-table-column>
                    <el-table-column prop="title" label="测试集" min-width="180"></el-table-column>
                    <el-table-column prop="project_name" label="项目" min-width="140"></el-table-column>
                    <el-table-column prop="case_count" label="用例数" width="90"></el-table-column>
                    <el-table-column prop="type_name" label="类型" width="90"></el-table-column>
                    <el-table-column prop="estimated_time" label="预计耗时/s" width="110"></el-table-column>
                    <el-table-column prop="config_names" label="测试集配置" min-width="180"></el-table-column>
                </el-table>
            </div>
            <div slot="footer" class="dialog-footer">
                <el-button @click.native="executionPreviewVisible = false">返回修改</el-button>
                <el-button type="primary" @click="confirmExecutionPlan">确认运行</el-button>
            </div>
        </el-dialog>
        <el-dialog :title="runset_title" :close-on-click-modal="false" :visible.sync="EditSetVisible">
            <el-form :model="addForm" label-width="150px" :rules="detailFormRules" ref="addForm">
            <el-form-item label="测试任务名称:">
            <el-input v-model="set_title" placeholder="测试任务名称" clearable>
                <i slot="prefix" class="el-input__icon el-icon-search"></i>
            </el-input>
           </el-form-item>
           <el-row>
                <el-col :span="18">
                    <el-form-item label="测试集与执行顺序" class="len_input" required>
                        <div class="block" style="">
                            <span class="demonstration">
                            </span>
                            <el-select v-model="addForm.value5" filterable multiple clearable default-first-option placeholder="请选择关联测试集(也可输入测试集搜索)">
                                <el-option
                                v-for="item in addForm.options5"
                                :key="item.value"
                                :label="item.label"
                                :value="item.value">
                                </el-option>   
                            </el-select>
                            <div class="task-set-order-panel">
                                <div class="task-set-order-title">已选执行顺序</div>
                                <draggable v-model="selectedTaskSets" handle=".task-set-drag" @end="syncTaskSetIdsFromSelected">
                                    <div v-for="(item, index) in selectedTaskSets" :key="item.value" class="task-set-order-item">
                                        <span class="task-set-index">{{ index + 1 }}</span>
                                        <i class="el-icon-rank task-set-drag"></i>
                                        <span class="task-set-name">{{ item.label }}</span>
                                        <el-button type="text" icon="el-icon-arrow-up" :disabled="index === 0" @click="moveTaskSet(index, -1)"></el-button>
                                        <el-button type="text" icon="el-icon-arrow-down" :disabled="index === selectedTaskSets.length - 1" @click="moveTaskSet(index, 1)"></el-button>
                                        <el-button type="text" icon="el-icon-close" class="task-set-remove" @click="removeTaskSet(index)"></el-button>
                                    </div>
                                </draggable>
                                <div v-if="selectedTaskSets.length === 0" class="task-set-empty">请选择测试集</div>
                            </div>
                        </div>
                    </el-form-item>
                </el-col>
                <!-- <el-col :span="9">
                </el-col> -->
            </el-row>
            <el-row>
                <el-col :span="9">
                    <el-form-item label="全局配置" class="len_input">
                        <div class="block" style="">
                            <span class="demonstration">
                            </span>
                            <el-select v-model="addForm.value3" filterable multiple clearable default-first-option placeholder="请选择全局配置(也可输入配置搜索)">
                                <el-option
                                v-for="item in addForm.options3"
                                :key="item.value"
                                :label="item.label"
                                :value="item.value">
                                </el-option>   
                            </el-select>
                        </div>
                    </el-form-item>
                </el-col>
                <!-- <el-col :span="9">
                    <p>当前所选项序号:</p>
                    <ul>
                        <li v-for="(selectedItem, index) in addForm.value3" :key="selectedItem">
                        {{ index + 1 }}
                        </li>
                    </ul>
                    </el-col> -->
                <!-- <el-col :span="9">
                </el-col> -->
            </el-row>
            <el-form-item label="邮件地址:">
                <el-input placeholder="输入邮件地址即可发送邮件，多个邮件间请用;来区分" type="input" v-model="addForm.email_to"></el-input>
            </el-form-item>
            <el-form-item label="备注信息:">
                <el-input type="textarea" v-model="addForm.mark" placeholder="填写测试任务备注信息"></el-input>
            </el-form-item>
        </el-form>
            <!-- <div class="block" style="">
                <span class="demonstration"></span>
                <el-cascader :filterable="true" :clearable="true" :disabled="false" placeholder="请选择关联脚本项目(也可输入项目搜索)"
                    separator="=>" v-model="addForm.value" :options="addForm.options"
                    :props="{ expandTrigger: 'hover' }"></el-cascader>
                <el-button type="primary" icon="el-icon-search" v-on:click="getConfigList">查询</el-button>
            </div> -->
            <!-- <div style="text-align: center">
                <el-transfer style="text-align: left; display: inline-block" v-model="value4" filterable
                    @mouseover.native="addTitle" :left-default-checked="[2, 3]" :right-default-checked="[1]"
                    :titles="['未添加用例列表', '已添加用例列表']" :button-texts="['到左边', '到右边']" :format="{
                        noChecked: '${total}',
                        hasChecked: '${checked}/${total}'
                    }" @change="handleChange" :data="case_data">
                    <span slot-scope="{ option }" v-if="option.case_count > 1" style="color: #00FF00;">{{ option.label }}</span>
                    <span slot-scope="{ option }" v-else-if="option.run_status == 'error'" style="color: #FF0000;">{{ option.label }}</span>
                    <span slot-scope="{ option }" v-else>{{ option.label }}</span>
            
                </el-transfer>
            </div> -->
            <div slot="footer" class="dialog-footer">
                <el-button type="primary" :disabled="false" @click="add_test_task">保存
                </el-button>
                <el-button @click.native="EditSetVisible = false">返回</el-button>
            </div>
        </el-dialog>
    </section>
</template>
<style>  .button-container {
      display: flex;
      flex-direction: column;
  }

  .len_input .el-select {
      width: 100%;
  }

  .task-set-order-panel {
      margin-top: 6px;
      padding: 10px;
      background: #f8fafc;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
  }

  .task-set-order-title {
      margin-bottom: 8px;
      color: #303133;
      font-size: 13px;
      font-weight: 700;
  }

  .task-set-order-item {
      display: flex;
      align-items: center;
      gap: 6px;
      min-height: 34px;
      margin-bottom: 6px;
      padding: 6px 8px;
      background: #ffffff;
      border: 1px solid #dcdfe6;
      border-radius: 4px;
  }

  .task-set-index {
      width: 24px;
      color: #409eff;
      font-weight: 700;
      text-align: center;
  }

  .task-set-drag {
      color: #909399;
      cursor: move;
  }

  .task-set-name {
      flex: 1;
      overflow: hidden;
      color: #606266;
      text-overflow: ellipsis;
      white-space: nowrap;
  }

  .task-set-remove {
      color: #f56c6c;
  }

  .task-set-empty {
      color: #909399;
      font-size: 12px;
  }

  .execution-preview-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 14px;
  }

  .execution-preview-card {
      padding: 12px;
      background: #f8fafc;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
  }

  .execution-preview-card span {
      display: block;
      color: #909399;
      font-size: 12px;
  }

  .execution-preview-card strong {
      display: block;
      margin-top: 6px;
      color: #303133;
      font-size: 20px;
  }

  .execution-preview-row {
      margin-bottom: 14px;
  }

  .execution-preview-section {
      min-height: 112px;
      padding: 12px;
      background: #ffffff;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
  }

  .execution-preview-title {
      margin-bottom: 8px;
      color: #303133;
      font-weight: 700;
  }

  .execution-preview-line {
      color: #606266;
      line-height: 1.8;
      word-break: break-word;
  }

  .task-timeline-summary {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
  }

  .task-timeline-card {
      padding: 12px;
      background: #f8fafc;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
  }

  .task-timeline-card span {
      display: block;
      color: #909399;
      font-size: 12px;
  }

  .task-timeline-card strong {
      display: block;
      margin-top: 6px;
      color: #303133;
      font-size: 18px;
      word-break: break-all;
  }

  .task-timeline-list {
      max-height: 560px;
      overflow: auto;
      padding: 4px 8px 4px 0;
  }

  .task-timeline-item {
      padding: 12px;
      background: #ffffff;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
  }

  .task-timeline-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 8px;
  }

  .task-timeline-desc {
      color: #606266;
      line-height: 1.7;
  }

  .task-timeline-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 8px;
      color: #909399;
      font-size: 12px;
  }

  .task-timeline-actions {
      margin-top: 10px;
  }

  .task-timeline-empty {
      padding: 30px 0;
      color: #909399;
      text-align: center;
  }

  .task-history-table /deep/ .el-table__row {
      cursor: default;
  }

  .task-snapshot-summary {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 14px;
  }

  .task-snapshot-section {
      margin-bottom: 16px;
  }

  .task-snapshot-title {
      margin-bottom: 8px;
      color: #303133;
      font-weight: 700;
  }

  .task-snapshot-json {
      max-height: 140px;
      margin: 0;
      padding: 8px;
      overflow: auto;
      color: #303133;
      background: #f8fafc;
      border: 1px solid #e4e7ed;
      border-radius: 4px;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
  }

  .task-snapshot-muted {
      color: #909399;
      font-size: 12px;
  }
</style>    
<script>
import axios from "axios";
import draggable from 'vuedraggable';
import {
    // DeleteConfig,
    get_config_info,
    get_project_info,
    get_version_info,
    get_testset_info,
    get_testtask_info,
    run_testtask,
    get_testtask_set,
    get_testtask_timeline,
    get_testtask_history,
    get_testtask_config_snapshot,
    // stop_testset,
    stop_testtask,
    // delete_testset,
    delete_testtask,
    add_tesetask,
    get_files,
    get_url,
    get_cases_info,
    add_testset,
    get_report_info,
} from "../../api/api";
import moment from "moment";
import Vue from "vue";
Vue.prototype.$moment = moment;

export default {
    components: {
        draggable,
    },
    data() {
        return {
            datevalue2: "",
            deadline2: '11111111111111',
            runset_title: "运行测试任务",
            set_title: '',
            pros_value: '',
            sent_email:0,
            dialogTableVisible: false,
            setdialogTableVisible: false,
            casenow_dialogTableVisible: false,
            EditSetVisible: false, //编辑测试集页面是否显示
            timelineVisible: false,
            timelineLoading: false,
            timelineTitle: "任务执行时间线",
            historyVisible: false,
            historyLoading: false,
            historyTitle: "任务运行历史",
            historyTaskRow: null,
            taskHistory: [],
            snapshotVisible: false,
            snapshotLoading: false,
            snapshotTitle: "任务级配置快照",
            taskConfigSnapshot: {
                run_id: "",
                task_configs: [],
                set_snapshots: [],
                report_count: 0,
            },
            taskTimeline: {
                run_id: "",
                set_count: 0,
                report_count: 0,
                schedule: 0,
                timeline: [],
            },
            executionPreviewVisible: false,
            executionPreview: {
                set_count: 0,
                case_count: 0,
                estimated_time: "0.00",
                run_mode: "立即执行",
                config_names: "",
                email_to: "",
                timed_task_time: "",
                mark: "",
                sets: [],
            },
            setcasetotal: 0,
            setids: [],
            value4: [],
            selectedTaskSets: [],
            CaseList: [],
            ReportList: [],
            case_data: [],
            count_info: [],
            pros_options: [{
                value: 2,
                label: '进程数2'
            }, {
                value: 3,
                label: '进程数3'
            }, {
                value: 4,
                label: '进程数4'
            }, {
                value: 5,
                label: '进程数5'
            }],
            options2: [{
                value2: 0,
                label: '未运行'
            }, {
                value2: 1,
                label: '运行中'
            }, {
                value2: 2,
                label: '运行完成'
            }],
            value2: null,
            timer: "",
            htmlcontent: null,
            priority_options: [{
                value: 0,
                label: 'P0'
            },
            {
                value: 1,
                label: 'P1'
            },
            {
                value: 2,
                label: 'P2'
            },
            {
                value: 3,
                label: 'P3'
            },
            {
                value: 4,
                label: 'P4'
            },
            {
                value: 5,
                label: 'P5'
            },
            {
                value: 6,
                label: 'P6'
            },
            {
                value: 7,
                label: 'P7'
            },
            {
                value: 8,
                label: 'P8'
            },
            {
                value: 9,
                label: 'P9'
            },
            {
                value: 10,
                label: 'P10'
            }],
            options: [{
                value: 1,
                label: 'pytest'
            }],
            value: 1,
            priority_value: 0,
            clean: false,
            ongoing: false,
            filters: {
                cfg_name: "",
            },
            install_type_lst: [],
            addViperHost: "",
            aioLst: [],
            testset_row: "",
            run_id: "",
            page_size: 5000,
            total: 0,
            page: 0,
            rerun_type: 0,
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
                email_to: "",
                add_data: true,
                anaFlag: false,
                bdaFlag: false,
                nodeFlag: false,
                cfg: "",
                node_randio: 1,
                auth: false,
                mark: "",
                value: "",
                options: [],
                value2: "",
                options2: [],
                value3: "",
                value5: [],
                options3: [],
                options5: [],
                set_time: "",
                note: "",
                config_id: null,
                config_name: "",
                set_flag: true,
            },

            lstForm: [
                // { prop: "id", label: "id", width: 60 },
                { prop: "name", label: "测试任务名称", width: 145 },
                // { prop: "project_name", label: "脚本项目", width: 140 },
                { prop: "run_id", label: "最新运行id", width: 120 },
                // { prop: "mark", label: "备注", width: 120 },
                // { prop: "version_id", label: "版本id", width: 100 },
                // { prop: "case_ids", label: "测试集内用例id", width: 160 },
                // { prop: "run_status", label: "运行状态", width: 120 },
                
                { prop: "updated_time", label: "更新时间", width: 140 },
                // { prop: "case_count_total", label: "用例数量（条）", width: 80 },
                { prop: "mark", label: "备注", width: 100 },
                // { prop: "run_type", label: "运行方式", width: 80 },
                // { prop: "progress", label: "当前运行测试集", width: 100 },
                // { prop: "set_schedule", label: "测试集测试进度（%）", width: 80 },
                { prop: "timed_task_time", label: "定时任务开启时间", width: 120 },
                { prop: "progress", label: "当前运行测试集", width: 100 },
                
            ],
            CaseForm: [
                // { prop: "id", label: "id", width: 60 },
                { prop: "title", label: "测试集名称", width: 145 },
                { prop: "project_name", label: "脚本项目", width: 140 },
                { prop: "run_id", label: "最新运行id", width: 120 },
                // { prop: "previous_level", label: "所属文件夹", width: 80 },
                // { prop: "version_id", label: "版本id", width: 100 },
                // { prop: "case_ids", label: "测试集内用例id", width: 160 },
                // { prop: "run_status", label: "运行状态", width: 120 },
                // { prop: "schedule", label: "测试进度（%）", width: 80 },
                { prop: "updated_time", label: "更新时间", width: 175 },
                // { prop: "case_count_total", label: "用例数量（条）", width: 80 },
                // { prop: "mark_info", label: "备注", width: 100 },
                { prop: "run_type", label: "运行方式", width: 80 },
                // { prop: "timed_task_time", label: "定时任务开启时间", width: 140 }
            ],
            ReportForm: [
                // { prop: "id", label: "报告id", width: 100 },
                // { prop: "config_id", label: "配置id", width: 100 },
                // { prop: "project_name", label: "脚本项目", width: 120 },
                { prop: "set_title", label: "测试集名", width: 120 },
                // { prop: "title", label: "测试报告名（项目名_测试集名_运行id）", width: 300 },
                { prop: "mark", label: "备注", width: 200 },
                { prop: "case_all_time", label: "用例总耗时/s", width: 100 },
                { prop: "all_count", label: "全部用例数", width: 100 },
                { prop: "pass_count", label: "通过用例数", width: 100 },
                { prop: "pass_rate", label: "用例通过率（%）", width: 100 },
                { prop: "fail_count", label: "失败用例数", width: 100 },
                { prop: "error_count", label: "错误用例数", width: 100 },
                { prop: "updated_time", label: "更新时间", width: 200 },

            ],
        };
    },

    created() {
        // 在组件创建时调用后端接口，获取HTML内容
        this.fetchHtmlContent();
    },
    filters: {
        stateFmt(state) {
            return (
                {
                    0: "未运行",
                    1: "运行中",
                    2: "运行完成",
                }[state] || "其他"
            );
        },
        testFmt(state) {
            return (
                {
                    1: "pytest",
                    2: "函数式",
                }[state] || "其他"
            );
        },
        PriorityFmt(state) {
            return (
                {
                    0: "P0",
                    1: "P1",
                    2: "P2",
                    3: "P3",
                    4: "P4",
                    5: "P5",
                    6: "P6",
                    7: "P7",
                    8: "P8",
                    9: "P9",
                    10: "P10",
                }[state] || "其他"
            );
        },
    },
    watch: {
        "addForm.value5": function () {
            this.syncSelectedTaskSetsFromIds();
        },
    },
//     computed: {
//     computedOptions() {
//       return this.addForm.options3.map((item) => {
//         const index = this.addForm.value3.indexOf(item.value);
//         const label = index > -1 ? `${index + 1}. ${item.label}` : item.label;
//         return {item, label};
//       });
//     }
//   },
    methods: {

        start() {
            this.timer = setInterval(this.valChange, 10000); // 注意: 第一个参数为方法名的时候不要加括号;
        },
        valChange() {
            this.getConfigList();
        },
        format(percentage) {
        return percentage === 100 ? '完成' : `${percentage}%`;
            },
        percentagenum(row){
                if (!row.schedule){
                    return 0
                }
                else{return row.schedule}
            },
        percentagenum2(row){
                if (!row.set_schedule){
                    return 0
                }
                else{return row.set_schedule}
            },
        progress_status(row){
            if (!row.schedule)
                {return ""}
            if(row.schedule === 100){
                return 'success'
            }

        },
        mounted() { },
        beforeDestroy() {
            clearInterval(this.timer);
        },
        // selectBlur(e) {
        //     Vue.set(this.addForm, "viper_version", e.target.value);
        // },
        radioChangeEvt() {
            if (this.addForm.node_randio % 2 != 0) {
                this.addForm.aIp = "";
            }
        },
        handleCurrentChange(val) {
            this.page = val;
            this.getConfigList();
        },
        handleChange(value, direction, movedKeys) {
        },
        normalizeIdList(value) {
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
        syncSelectedTaskSetsFromIds() {
            const ids = this.normalizeIdList(this.addForm.value5);
            const optionMap = {};
            (this.addForm.options5 || []).forEach((item) => {
                optionMap[String(item.value)] = item;
            });
            const oldMap = {};
            (this.selectedTaskSets || []).forEach((item) => {
                oldMap[String(item.value)] = item;
            });
            this.selectedTaskSets = ids.map((id) => {
                const key = String(id);
                const option = optionMap[key] || oldMap[key] || {};
                return {
                    value: id,
                    label: option.label || ("测试集 " + id),
                };
            });
        },
        syncTaskSetIdsFromSelected() {
            this.addForm.value5 = (this.selectedTaskSets || []).map((item) => item.value);
        },
        moveTaskSet(index, step) {
            const targetIndex = index + step;
            if (targetIndex < 0 || targetIndex >= this.selectedTaskSets.length) {
                return false;
            }
            const next = this.selectedTaskSets.slice();
            const item = next.splice(index, 1)[0];
            next.splice(targetIndex, 0, item);
            this.selectedTaskSets = next;
            this.syncTaskSetIdsFromSelected();
        },
        removeTaskSet(index) {
            this.selectedTaskSets.splice(index, 1);
            this.syncTaskSetIdsFromSelected();
        },
        cellStyle({ row, column, rowIndex, columnIndex }) {
            let cell_Style
            switch (row.run_status) {
                case 0:
                    cell_Style = 'color:#0000FF'
                    break;
                case 1:
                    cell_Style = 'color:#FF0000'
                    break;
                case 2:
                    cell_Style = 'color:#00FF00'
                    break;
                default:
                    cell_Style = ''
                    break;
            }
            // 返回最终处理过的样式 这样写就是让全部行被style修饰
            // return cell_Style

            //返回最终处理过的样式 只让测试结果这个属性的属性被style修饰
            if (column.label == '运行状态') {
                return cell_Style
            }
        },
        CasecellStyle({ row, column, rowIndex, columnIndex }) {
            let cell_Style
            switch (row.run_status) {
                case 'passed':
                    cell_Style = 'color:#00FF00'
                    break;
                case 'failed':
                    cell_Style = 'color:#FF0000'
                    break;
                case 'error':
                    cell_Style = 'color:#FF0000'
                    break;
                case '测试中':
                    cell_Style = 'color:#0000FF'
                    break;
                default:
                    cell_Style = ''
                    break;
            }
            // 返回最终处理过的样式 这样写就是让全部行被style修饰
            // return cell_Style

            //返回最终处理过的样式 只让测试结果这个属性的属性被style修饰
            if (column.label == '测试结果') {
                return cell_Style
            }
        },

        format_info(row, column) {
      return () => {
        if (column.label === '里程数') {
          return row.num + 'km'
        }
      }
    },
        //获取测试集列表
        getOptionLabels(ids, options) {
            const idList = this.normalizeIdList(ids);
            const optionMap = {};
            (options || []).forEach((item) => {
                optionMap[String(item.value)] = item.label;
            });
            return idList.map((id) => optionMap[String(id)] || id).join(" / ");
        },
        getTestsetCaseCount(item) {
            if (!item) {
                return 0;
            }
            if (item.case_count_total !== undefined && item.case_count_total !== null) {
                return Number(item.case_count_total || 0);
            }
            if (item.case_count !== undefined && item.case_count !== null) {
                return Number(item.case_count || 0);
            }
            return this.normalizeIdList(item.case_ids).length;
        },
        getTestsetEstimatedTime(item) {
            if (item && item.case_all_time !== undefined && item.case_all_time !== null) {
                return Number(item.case_all_time || 0);
            }
            return 0;
        },
        testsetTypeName(type) {
            return Number(type) === 2 ? "函数式" : "pytest";
        },
        buildExecutionPreview() {
            this.syncTaskSetIdsFromSelected();
            const selectedIds = this.normalizeIdList(this.addForm.value5);
            const setMap = {};
            (this.vipers5 || []).forEach((item) => {
                setMap[String(item.id)] = item;
            });
            const sets = selectedIds.map((id, index) => {
                const item = setMap[String(id)] || {};
                return {
                    order: index + 1,
                    id: id,
                    title: item.title || ("测试集 " + id),
                    project_name: item.project_name || "",
                    case_count: this.getTestsetCaseCount(item),
                    type_name: this.testsetTypeName(item.type),
                    estimated_time: this.getTestsetEstimatedTime(item).toFixed(2),
                    config_names: this.getOptionLabels(item.config, this.addForm.options3) || "无",
                };
            });
            this.executionPreview = {
                set_count: sets.length,
                case_count: sets.reduce((total, item) => total + Number(item.case_count || 0), 0),
                estimated_time: sets.reduce((total, item) => total + Number(item.estimated_time || 0), 0).toFixed(2),
                run_mode: this.datevalue2 ? "定时执行" : "立即执行",
                config_names: this.getOptionLabels(this.addForm.value3, this.addForm.options3),
                email_to: Number(this.sent_email) === 1 ? this.addForm.email_to : "",
                timed_task_time: this.datevalue2 || "",
                mark: this.addForm.mark || "",
                sets: sets,
            };
        },
        previewExecutionPlan() {
            this.buildExecutionPreview();
            if (!this.executionPreview.set_count) {
                this.$message({
                    message: "测试集不能为空",
                    type: "warning",
                });
                return false;
            }
            this.executionPreviewVisible = true;
        },
        confirmExecutionPlan() {
            this.executionPreviewVisible = false;
            this.AIOOIA();
        },
        async getConfigList() {
            this.ongoing = false;
            let para = {
                run_status: this.value2,
        
                task_name: this.filters.cfg_name,
                page: this.page,
                page_size: this.page_size,
            };
            this.listLoading = true;
            await get_testtask_info(para).then((res) => {
                this.aioLst = res.data.data;
                this.listLoading = false;
                this.total = res.data.data.length;
            });
        },
        //获取用例列表
        async getCaseList(index, row) {
            this.dialogTableVisible = true
            this.ongoing = false;
            this.testset_row = row;
            this.set_title = "测试集[" + row.title + "]的用例列表";
            this.run_id = row.run_id;
            let para = {
                page: this.page,
                page_size: this.page_size,
                cases_in: row.case_ids,
                run_id: this.run_id
            };
            this.listLoading = true;
            await get_cases_info(para).then((res) => {
                this.CaseList = res.data.data;
                this.listLoading = false;
                this.setcasetotal = res.data.data.length;
                this.count_info = [];
                if (res.data.count !== null) {
                    this.count_info = [res.data.count];
                }
            });
        },
        //获取测试任务的测试集列表
        async getSetListNow(index, row) {
            this.casenow_dialogTableVisible = true
            this.ongoing = false;
            this.testset_row = row;
            this.set_title = "测试任务[" + row.name + "]的测试集列表";
            this.run_id = row.run_id;
            let check_case = row.case_ids
            if (row.rerun_type == 1){
                check_case = row.fail_ids
                this.set_title = "测试集[" + row.title + "]的实时失败用例重试测试用例列表";
            }
            if (row.run_status == 0 || row.run_status == 2){
                check_case = 'no_case'
            }
            let para = {
                page: this.page,
                page_size: this.page_size,
                task_id: row.id
            };
            this.listLoading = true;
            await get_testtask_set(para).then((res) => {
                this.CaseList = res.data.data;
                this.listLoading = false;
                this.setcasetotal = res.data.data.length;
                this.count_info = [];
                if (res.data.count !== null) {
                    this.count_info = [res.data.count];
                }
            });
        },

        //获取该测试任务的报告列表
        async getSetReportList(index, row) {
            this.setdialogTableVisible = true
            this.set_title = "测试任务[" + row.name + "]的测试报告列表";
            let para = {
                page: this.page,
                page_size: this.page_size,
                run_id: row.run_id
            };
            this.listLoading = true;
            await get_report_info(para).then((res) => {
                this.ReportList = res.data.data;
                this.listLoading = false;
                this.setcasetotal = res.data.data.length;
                this.count_info = [];
                if (res.data.count !== null) {
                    this.count_info = [res.data.count];
                }
            });
        },

        timelineStatusType(status) {
            const statusMap = {
                created: "info",
                scheduled: "warning",
                running: "warning",
                finished: "success",
                pending: "info",
            };
            return statusMap[status] || "info";
        },
        timelineStatusText(status) {
            const statusMap = {
                created: "已创建",
                scheduled: "等待中",
                running: "运行中",
                finished: "已完成",
                pending: "待执行",
            };
            return statusMap[status] || "未知";
        },
        async getTaskTimeline(index, row) {
            this.timelineVisible = true;
            this.timelineLoading = true;
            this.timelineTitle = "测试任务[" + row.name + "]执行时间线";
            this.taskTimeline = {
                run_id: row.run_id || "",
                set_count: 0,
                report_count: 0,
                schedule: row.schedule || 0,
                timeline: [],
            };
            let para = {
                task_id: row.id,
                run_id: row.run_id,
            };
            await get_testtask_timeline(para).then((res) => {
                if (res.data.code === 200) {
                    this.taskTimeline = res.data.data || this.taskTimeline;
                } else {
                    this.$message({
                        message: res.data.msg || "获取任务执行时间线失败",
                        type: "warning",
                    });
                }
                this.timelineLoading = false;
            }).catch(() => {
                this.timelineLoading = false;
                this.$message({
                    message: "获取任务执行时间线失败",
                    type: "error",
                });
            });
        },
        async getTaskHistory(index, row) {
            this.historyVisible = true;
            this.historyLoading = true;
            this.historyTaskRow = row;
            this.historyTitle = "测试任务[" + row.name + "]运行历史";
            this.taskHistory = [];
            let para = {
                task_id: row.id,
                page_size: 50,
            };
            await get_testtask_history(para).then((res) => {
                if (res.data.code === 200) {
                    this.taskHistory = res.data.data || [];
                } else {
                    this.$message({
                        message: res.data.msg || "获取任务运行历史失败",
                        type: "warning",
                    });
                }
                this.historyLoading = false;
            }).catch(() => {
                this.historyLoading = false;
                this.$message({
                    message: "获取任务运行历史失败",
                    type: "error",
                });
            });
        },
        openHistoryTimeline(row) {
            if (!this.historyTaskRow) {
                return false;
            }
            this.historyVisible = false;
            this.getTaskTimeline(0, {
                id: this.historyTaskRow.id,
                name: this.historyTaskRow.name,
                run_id: row.run_id,
                schedule: 100,
            });
        },
        previewTimelineReport(item) {
            if (!item || !item.report_path) {
                this.$message({
                    message: "当前节点没有可预览报告",
                    type: "warning",
                });
                return false;
            }
            let params = { filename: item.report_path };
            axios({
                method: 'POST',
                url: get_url() + '/testset/report_content',
                data: params
            }).then(res => {
                const content = res.data;
                if (content.code == 404) {
                    this.$message(content.msg);
                    return false;
                }
                let newwindow = window.open("", "_blank");
                newwindow.document.write(content);
            });
        },
        formatConfigText(value) {
            if (!value) {
                return "";
            }
            try {
                return JSON.stringify(JSON.parse(value), null, 2);
            } catch (e) {
                return String(value);
            }
        },
        async getTaskConfigSnapshot(index, row, runId) {
            this.snapshotVisible = true;
            this.snapshotLoading = true;
            this.snapshotTitle = "测试任务[" + row.name + "]配置快照";
            this.taskConfigSnapshot = {
                run_id: runId || row.run_id || "",
                task_configs: [],
                set_snapshots: [],
                report_count: 0,
            };
            let para = {
                task_id: row.id,
                run_id: runId || row.run_id,
            };
            await get_testtask_config_snapshot(para).then((res) => {
                if (res.data.code === 200) {
                    this.taskConfigSnapshot = res.data.data || this.taskConfigSnapshot;
                } else {
                    this.$message({
                        message: res.data.msg || "获取任务配置快照失败",
                        type: "warning",
                    });
                }
                this.snapshotLoading = false;
            }).catch(() => {
                this.snapshotLoading = false;
                this.$message({
                    message: "获取任务配置快照失败",
                    type: "error",
                });
            });
        },
        openHistoryConfigSnapshot(row) {
            if (!this.historyTaskRow) {
                return false;
            }
            this.historyVisible = false;
            this.getTaskConfigSnapshot(0, this.historyTaskRow, row.run_id);
        },

        //选择列
        selsChange: function (sels) {
            this.sels = sels;
            this.caseids = [];
            for (let caseid in this.sels) {
                this.caseids.push(this.sels[caseid]["id"])
            }

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
                //version_id可传可不传
                if (this.addForm.value2 == null) {
                    this.addForm.value2 = []
                }
                this.syncTaskSetIdsFromSelected();


                let para = {
                    config_ids: this.addForm.value3,
                    set_ids: this.addForm.value5,
                    task_id: this.addForm.config_id,
                    script_type: this.value,
                    priority_value: this.priority_value,
                    rerun_type: this.rerun_type,
                    mark: this.addForm.mark,
                    email_to: this.addForm.email_to,
                    timed_task_time: this.datevalue2,
                    // start_process: this.pros_value,
                    sent_email:this.sent_email,
                };


                await run_testtask(para).then((res) => {
                    this.listLoading = false;
                    let { msg, code } = res.data;
                    if (code !== 200) {
                        this.$message({
                            message: msg,
                            type: "warning",
                            duration: 5000
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
                                duration: 5000
                            });
                        } else {
                            this.$message({
                                message: msg,
                                type: "success",
                                duration: 5000
                            });
                        }
                        // this.getproinfo();
                        // this.getversioninfo()
                        this.getmoduleinfo()
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
        async handleAddEvent(index, row) {
            this.addForm.set_time = new Date();
            // this.addForm.sltFlagLst = ["os", "business", "connect", "play"];
            this.addForm.options = [];
            this.priority_value = row.priority;
            this.addForm.value = row.project_id;
            this.addForm.options2 = [];
            this.addForm.value2 = [row.version_id];
            this.addForm.options3 = [];
            this.addForm.options5 = [];
            this.addForm.value3 = JSON.parse(row.config_ids);
            this.addForm.value5 = JSON.parse(row.test_set_ids);
            // this.addForm.value3 = [row.config];
            this.addForm.mark = row.mark;
            this.detailFormVisible = true;
            this.addForm.add_data = true;
            this.datevalue2 = "";
            this.runset_title = "运行测试任务:" + row.name;
            this.pros_value = '';
            this.sent_email = 0;
            this.addForm.email_to = row.email_to;
            // this.addForm.email_to = "";
            this.addForm.config_id = row.id;
            this.rerun_type = 0

            // await this.getproinfo();
            // await this.getversioninfo()
            await this.getmoduleinfo()
            await this.getsetinfo()
        },

        async handleAddEvent_rerun(index, row, rerun_type) {
            this.addForm.set_time = new Date();
            // this.addForm.sltFlagLst = ["os", "business", "connect", "play"];
            this.addForm.options = [];
            this.priority_value = row.priority;
            this.addForm.value = row.project_id;
            this.addForm.options2 = [];
            this.addForm.value2 = [row.version_id];
            this.addForm.options3 = [];
            this.addForm.options5 = [];
            this.addForm.value3 = JSON.parse(row.config_ids);
            this.addForm.value5 = JSON.parse(row.test_set_ids);
            // this.addForm.value3 = [row.config];
            this.addForm.mark = row.mark;
            this.detailFormVisible = true;
            this.addForm.add_data = true;
            this.datevalue2 = "";
            this.runset_title = "失败用例重试测试任务:" + row.name;
            this.pros_value = '';
            this.sent_email = 0;
            this.addForm.email_to = row.email_to;
            // this.addForm.email_to = "";
            this.addForm.config_id = row.id;
            this.rerun_type = rerun_type
            // await this.getproinfo();
            // await this.getversioninfo()
            await this.getmoduleinfo()
            await this.getsetinfo()
        },
        async set_id(index, row) {
            this.addForm.config_id = row.id
            this.addForm.cfg = row.cfg
            this.addForm.config_name = row.cfg_name;
            this.detailFormVisible = true;
            // await this.getproinfo();
            // await this.getversioninfo()
            await this.getmoduleinfo()

        },
        //新增测试任务
        async handleaddEvent(index, row) {
            this.addForm.set_time = new Date();
            this.EditSetVisible = true;
            this.runset_title = "";
            this.addForm.config_id = "";
            this.set_title = "";
            this.addForm.mark = "";
            // this.addForm.value3 = [row.config];
            this.addForm.value3 = "";
            this.addForm.value5 = [];
            this.selectedTaskSets = [];
            this.addForm.email_to ="";
            this.case_data = [];
            this.value4 = [];
            // await this.getproinfo();
            await this.getConfigList();
            await this.getmoduleinfo();
            await this.getsetinfo();
            let para = {
                page: this.page,
                page_size: 10000,
                project_id: row.project_id
            };

            let para2 = {
                page: this.page,
                page_size: this.page_size,
                cases_in: row.case_ids,
            };
            await get_cases_info(para2).then((res) => {
                this.CaseList = res.data.data;
                this.setcasetotal = res.data.data.length
                for (let i = 0; i < this.CaseList.length; i++) {
                    this.value4.push(
                        this.CaseList[i].id
                    )
                }


            });


        },
        //修改测试集用例
        async handleEditEvent(index, row) {
            this.addForm.set_time = new Date();
            this.EditSetVisible = true;
            this.runset_title = "修改测试任务:" + row.name;
            this.addForm.config_id = row.id;
            this.set_title = row.name;
            this.addForm.mark = row.mark;
            this.addForm.value = row.project_id;
            this.priority_value = row.priority;
            // this.addForm.value3 = [row.config];
            this.addForm.value3 = JSON.parse(row.config_ids);
            this.addForm.value5 = JSON.parse(row.test_set_ids);
            this.addForm.value2 = [row.version_id];
            this.addForm.email_to = row.email_to;
            this.case_data = [];
            this.value4 = [];
            // await this.getproinfo();
            await this.getConfigList();
            await this.getmoduleinfo();
            await this.getsetinfo();
            let para = {
                page: this.page,
                page_size: 10000,
                project_id: row.project_id
            };
            await get_cases_info(para).then((res) => {
                this.CaseList = res.data.data;
                this.setcasetotal = res.data.data.length
                for (let i = 0; i < this.CaseList.length; i++) {
                    this.case_data.push(
                        {
                            key: this.CaseList[i].id,
                            label: this.CaseList[i].case_count+ "-" + this.CaseList[i].case_name + "-" + this.CaseList[i].project_name,
                            disabled: false,
                            subscript: i,
                            case_count: this.CaseList[i].case_count,
                            run_status: this.CaseList[i].run_status
                        }
                    )
                }


            });
            let para2 = {
                page: this.page,
                page_size: this.page_size,
                cases_in: row.case_ids,
            };
            await get_cases_info(para2).then((res) => {
                this.CaseList = res.data.data;
                this.setcasetotal = res.data.data.length
                for (let i = 0; i < this.CaseList.length; i++) {
                    this.value4.push(
                        this.CaseList[i].id
                    )
                }


            });


        },
        //获取用例列表
        async GetCasesInfo() {
            this.ongoing = false;
            let para = {
                case_name: this.filters.cfg_name,
                page: this.page,
                page_size: this.page_size,
           
                script_type: this.value
            };
            this.listLoading = true;
            await get_cases_info(para).then((res) => {
                this.aioLst = res.data.data;
                this.listLoading = false;
                this.total = res.data.data.length
            });
        },
        async add_test_task() {
            // this.ongoing = false;
            this.syncTaskSetIdsFromSelected();
            let para = {
                // case_ids: this.value4,
                task_name: this.set_title,
                // project_id: this.addForm.value,
                task_id: this.addForm.config_id,
                mark:this.addForm.mark,
                config_ids: this.addForm.value3,
                set_ids: this.addForm.value5,
                // version_id: this.addForm.value2[0],
                email_to: this.addForm.email_to,
                // priority_value: this.priority_value,

            };
            this.listLoading = true;
            await add_tesetask(para).then((res) => {
                this.aioLst = res.data.data;
                let { msg, code } = res.data;
                this.listLoading = false;
                // this.total = res.data.length;
                if (code != 200) {
                    this.$message({
                        message: msg,
                        type: "warning",
                        duration: 5000
                    });
                } else {
                    //   this.serial = this.result.serial;
                    this.$message({
                        message: msg,
                        type: "success",
                        duration: 5000
                    });
                }
            });
            this.EditSetVisible = false;
            this.getConfigList()

        },
        addTitle(e) {
            // 手动给鼠标滑过的元素加一个title
            let target_el = e.target;
            if (target_el.title) return;
            target_el.title = target_el.innerText;
        },

        download(index, row) {
            this.htmlcontent = null
            let params = { filename: row.report, set_id: row.id }
            axios({
                method: 'POST',
                url: get_url() + '/testset/report_content',
                // responseType: 'blob',
                data: params
            }).then(res => {
                const content = res.data
                this.htmlcontent = res.data
                const blob = new Blob([content])
                const fileName = row.report
                if (content.code == 404) {
                    this.$message(content.msg);
                    return false
                }
                if ('download' in document.createElement('a')) {
                    const elink = document.createElement('a')
                    elink.download = fileName
                    elink.style.display = 'none'
                    elink.href = URL.createObjectURL(blob)

                    // let url = 'data:text/html;charset=utf-8,' + encodeURIComponent(elink.href);
                    // window.open(url, '_blank');

                    document.body.appendChild(elink)
                    elink.click()
                    URL.revokeObjectURL(elink.href)
                    document.body.removeChild(elink)
                } else {
                    navigator.msSaveBlob(blob, fileName)
                }

                // window.open('data:text/html,' + encodeURIComponent(content), '_blank');

                // window.open(document.write(content));
                // let url = 'data:text/html;charset=utf-8,' + encodeURIComponent(this.htmlcontent);
                // window.open(url, '_blank');

            })

        },
        download_list(index, row) {
            this.htmlcontent = null
            let params = { filename: row.report_path }
            axios({
                method: 'POST',
                url: get_url() + '/testset/report_content',
                // responseType: 'blob',
                data: params
            }).then(res => {
                const content = res.data
                this.htmlcontent = res.data
                const blob = new Blob([content])
                const fileName = row.report_path
                if (content.code == 404) {
                    this.$message(content.msg);
                    return false
                }
                if ('download' in document.createElement('a')) {
                    const elink = document.createElement('a')
                    elink.download = fileName
                    elink.style.display = 'none'
                    elink.href = URL.createObjectURL(blob)

                    // let url = 'data:text/html;charset=utf-8,' + encodeURIComponent(elink.href);
                    // window.open(url, '_blank');

                    document.body.appendChild(elink)
                    elink.click()
                    URL.revokeObjectURL(elink.href)
                    document.body.removeChild(elink)
                } else {
                    navigator.msSaveBlob(blob, fileName)
                }

                // window.open('data:text/html,' + encodeURIComponent(content), '_blank');

                // window.open(document.write(content));
                // let url = 'data:text/html;charset=utf-8,' + encodeURIComponent(this.htmlcontent);
                // window.open(url, '_blank');

            })

        },
        // openNewWindow() {
        //     // 调用后端接口获取HTML内容
        //     window.open('data:text/html,' + encodeURIComponent(this.htmlcontent), '_blank');
        // },

        get_html(index, row) {
            this.htmlcontent = null;
            let params = { filename: row.report, set_id: row.id }
            axios({
                method: 'POST',
                url: get_url() + '/testset/report_content',
                // responseType: 'blob',
                data: params
            }).then(res => {
                this.htmlcontent = res.data
                if (this.htmlcontent.code == 404) {
                    this.$message(this.htmlcontent.msg);
                    return false
                }
                let newwindow = window.open("", "_blank");
                newwindow.document.write(this.htmlcontent);
            })

        },

        get_html_list(index, row) {
            this.htmlcontent = null
            let params = { filename: row.report_path }
            axios({
                method: 'POST',
                url: get_url() + '/testset/report_content',
                // responseType: 'blob',
                data: params
            }).then(res => {
                this.htmlcontent = res.data
                if (this.htmlcontent.code == 404) {
                    this.$message(this.htmlcontent.msg);
                    return false
                }
                let newwindow = window.open("", "_blank");
                newwindow.document.write(this.htmlcontent);
            })

        },
        async delete_id_new(index, row) {
            this.$confirm("此操作将终止该测试任务, 是否继续?", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            })
                .then(() => {
                    let para = {
                        ids: [row.id],
                    };

                    stop_testtask(para).then((res) => {
                        this.listLoading = false;
                        let { msg, code } = res.data;
                        let set_titles = res.data.data;
                        this.getConfigList();

                        if (code != 200) {
                            this.$message({
                                message: msg,
                                type: "warning",
                                duration: 5000
                            });
                        } else {

                            this.$message({
                                message: "终止的测试任务:" + set_titles,
                                type: "success",
                                duration: 5000
                            });

                        }

                    });

                })
                .catch(() => {
                    this.$message({
                        type: "info",
                        message: "已取消终止",
                    });
                });
        },

        async is_deletes(index, row) {
            this.$confirm("此操作将删除该测试任务, 是否继续?", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            })
                .then(() => {
                    let para = {
                        ids: [row.id],
                    };

                    delete_testtask(para).then((res) => {
                        this.listLoading = false;
                        let { msg, code } = res.data;
                        let set_titles = res.data.data;
                        this.getConfigList();

                        if (code != 200) {
                            this.$message({
                                message: msg,
                                type: "warning",
                                duration: 5000
                            });
                        } else {

                            this.$message({
                                message: "删除的测试任务:" + set_titles,
                                type: "success",
                                duration: 5000
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

        async stop_set() {
            this.$confirm("此操作将终止所选测试任务, 是否继续?", "提示", {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            })
                .then(() => {
                    let para = {
                        ids: this.setids
                    };
                    stop_testtask(para).then((res) => {
                        this.listLoading = false;
                        let { msg, code } = res.data;
                        let set_titles = res.data.data;

                        this.getConfigList();
                        if (code != 200) {
                            this.$message({
                                message: msg,
                                type: "warning",
                                duration: 5000
                            });
                        }
                        else {
                            this.$message({
                                message: "终止的测试任务:" + set_titles,
                                type: "success",
                                duration: 5000
                            });

                        }

                    });

                })
                .catch(() => {
                    this.$message({
                        type: "info",
                        message: "已取消终止",
                    });
                });
        },

        //显示详情界面
        selsChange: function (sels) {
            this.sels = sels;
            this.setids = [];
            for (let setid in this.sels) {
                this.setids.push(this.sels[setid]["id"])
            }

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

        refreshViper_v4() {
            // var install_type = this.addForm.install_type;
            this.addForm.options3 = [];
            if (this.vipers3) {
                var server_len3 = this.vipers3.length;

                var cnt3 = 0;
                for (var i3 in this.vipers3) {
                    cnt3++;
                    this.addForm.options3.push({
                        value: this.vipers3[i3]["id"],
                        label: this.vipers3[i3]["cfg_name"],
                    });
                }
            }
        },
        refreshViper_v5() {
            // var install_type = this.addForm.install_type;
            this.addForm.options5 = [];
            if (this.vipers5) {
                var server_len3 = this.vipers5.length;

                var cnt5 = 0;
                for (var i3 in this.vipers5) {
                    cnt5++;
                    this.addForm.options5.push({
                        value: this.vipers5[i3]["id"],
                        label: this.vipers5[i3]["title"],
                    });
                }
            }
            this.syncSelectedTaskSetsFromIds();
        },



        async getproinfo() {
            this.ongoing = false;
            let para = {
                page: 0,
                name: "",
                page_size: 1000

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
                page_size: 1000

            };
            await get_version_info(para).then((res) => {
                this.vipers2 = res.data.data;

            });
            await this.refreshViper_v3();
        },
        async getmoduleinfo() {
            this.ongoing = false;
            let para = {
                page: 0,
                cfg_name: "",
                page_size: 5000

            };
            await get_config_info(para).then((res) => {
                this.vipers3 = res.data.data;

            });
            await this.refreshViper_v4();
        },
        async getsetinfo() {
            this.ongoing = false;
            let para = {
                page: 0,
                cfg_name: "",
                page_size: 5000

            };
            await get_testset_info(para).then((res) => {
                this.vipers5 = res.data.data;

            });
            await this.refreshViper_v5();
        },
    },

    // startCountdown(futureTime) {
    //     const timerInterval = setInterval(() => {
    //         const now = new Date().getTime();
    //         const distance = futureTime - now;
    //         const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    //         const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    //         const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    //         const seconds = Math.floor((distance % (1000 * 60)) / 100);
    //         // 将计算结果更新到el-countdown组件的timer属性中  
    //         this.timer = { days, hours, minutes, seconds };
    //     }, 1000);
    // },




    mounted() {
        this.getConfigList();
        this.getproinfo();
        // this.getversioninfo();
        this.getmoduleinfo();
        //定时任务开启
        this.start()
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
    
