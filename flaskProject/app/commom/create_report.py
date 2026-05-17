#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
import os
from config import report_path
from config import logs
from datetime import datetime
import aiofiles
from html import escape

style = """
    <style type="text/css" media="screen">
     * {
          box-sizing: border-box;
          }
     body {
          min-height: 100vh;
          margin: 0;
          padding: 32px 18px;
          border: 0;
          background: #eef3f8;
          color: #233044;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
          font-size: 14px;
          font-weight: 400;
          }
     .report-page {
          max-width: 1280px;
          margin: 0 auto;
          }
     .report-hero {
          padding: 28px 32px;
          color: #ffffff;
          text-align: left;
          background: linear-gradient(135deg, #214d76 0%, #2d6f83 50%, #2f855a 100%);
          border-radius: 10px 10px 0 0;
          box-shadow: 0 14px 34px rgba(26, 49, 78, 0.18);
          }
     .report-title {
          margin: 0;
          font-size: 30px;
          line-height: 1.2;
          font-weight: 800;
          letter-spacing: 0;
          }
     .report-subtitle {
          margin-top: 10px;
          color: rgba(255, 255, 255, 0.86);
          font-size: 15px;
          }
     .report-meta {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 12px;
          margin-top: 24px;
          }
     .report-meta-item {
          min-height: 74px;
          padding: 12px 14px;
          background: rgba(255, 255, 255, 0.13);
          border: 1px solid rgba(255, 255, 255, 0.22);
          border-radius: 8px;
          }
     .meta-label {
          display: block;
          color: rgba(255, 255, 255, 0.72);
          font-size: 12px;
          }
     .meta-value {
          display: block;
          margin-top: 7px;
          overflow-wrap: break-word;
          font-size: 16px;
          font-weight: 700;
          }
     .report-body {
          padding: 26px 30px 34px;
          background: #ffffff;
          border: 1px solid #dce4ef;
          border-top: 0;
          border-radius: 0 0 10px 10px;
          box-shadow: 0 14px 34px rgba(26, 49, 78, 0.12);
          }
     .section-title {
          margin: 0 0 14px;
          color: #233044;
          text-align: left;
          font-size: 20px;
          font-weight: 800;
          }
     .summary-grid {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 14px;
          margin-bottom: 22px;
          }
     .summary-card {
          min-height: 112px;
          padding: 16px;
          border: 1px solid #dce4ef;
          border-radius: 8px;
          background: #f8fafc;
          text-align: left;
          }
     .summary-card strong {
          display: block;
          margin-top: 8px;
          color: #172033;
          font-size: 28px;
          line-height: 1.1;
          }
     .summary-label {
          color: #66758a;
          font-size: 13px;
          font-weight: 700;
          }
     .summary-card.all {
          border-left: 5px solid #2563eb;
          }
     .summary-card.passed {
          border-left: 5px solid #16a34a;
          }
     .summary-card.failed {
          border-left: 5px solid #dc2626;
          }
     .summary-card.error {
          border-left: 5px solid #f97316;
          }
     .summary-card.rate {
          border-left: 5px solid #0f766e;
          }
     .summary-extra {
          margin-top: 8px;
          color: #7c8aa0;
          font-size: 12px;
          }
     .visual-grid {
          display: grid;
          grid-template-columns: 420px minmax(0, 1fr);
          gap: 20px;
          align-items: stretch;
          margin-bottom: 24px;
          }
     .filter-panel {
          padding: 20px;
          border: 1px solid #dce4ef;
          border-radius: 8px;
          background: #f8fafc;
          text-align: left;
          }
     .filter-title {
          margin-bottom: 12px;
          color: #233044;
          font-size: 17px;
          font-weight: 800;
          }
     .filter-buttons {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px;
          }
     .filter-btn {
          height: 42px;
          border: 0;
          border-radius: 6px;
          color: #ffffff;
          font-size: 14px;
          font-weight: 800;
          cursor: pointer;
          transition: transform 0.12s ease, box-shadow 0.12s ease;
          }
     .filter-btn:hover {
          transform: translateY(-1px);
          box-shadow: 0 6px 14px rgba(35, 48, 68, 0.14);
          }
     .filter-all {
          background: #2563eb;
          }
     .filter-passed {
          background: #16a34a;
          }
     .filter-failed {
          background: #dc2626;
          }
     .filter-error {
          background: #f97316;
          }
     .table-panel {
          margin-top: 8px;
          overflow: hidden;
          border: 1px solid #dce4ef;
          border-radius: 8px;
          background: #ffffff;
          }
     .table-scroll {
          overflow-x: auto;
          }
     table.gridtable {
          width: 100%;
          min-width: 1280px;
          border-collapse: collapse;
          font-size: 13px;
          color: #334155;
          }
     table.gridtable th {
          position: sticky;
          top: 0;
          z-index: 1;
          padding: 13px 14px;
          text-align: left;
          color: #233044;
          background: #edf2f7;
          border-bottom: 1px solid #dce4ef;
          }
     table.gridtable td {
          padding: 13px 14px;
          vertical-align: top;
          text-align: left;
          border-bottom: 1px solid #e8eef6;
          background: #ffffff;
          }
     table.gridtable tr:nth-child(even) td {
          background: #fbfdff;
          }
     table.gridtable tr:hover td {
          background: #f1f7ff;
          }
     .case-title-cell {
          max-width: 300px;
          word-break: break-word;
          font-weight: 700;
          color: #233044;
          }
     .case-name-cell {
          max-width: 240px;
          word-break: break-word;
          color: #475569;
          }
     .status-badge {
          display: inline-block;
          min-width: 72px;
          padding: 5px 9px;
          border-radius: 999px;
          text-align: center;
          color: #ffffff;
          font-size: 12px;
          font-weight: 800;
          text-transform: uppercase;
          }
     .status-passed {
          background: #16a34a;
          }
     .status-failed {
          background: #dc2626;
          }
     .status-error {
          background: #f97316;
          }
     .status-other {
          background: #64748b;
          }
     details summary {
          cursor: pointer;
          color: #2563eb;
          font-weight: 800;
          outline: none;
          }
     .case-log-block {
          margin-top: 14px;
          text-align: left;
          }
     .case-log-block h4 {
          margin: 16px 0 8px;
          font-size: 15px;
          color: #233044;
          }
     .case-log-block pre {
          width: 100%;
          min-width: 620px;
          min-height: 180px;
          max-height: 680px;
          overflow: auto;
          white-space: pre-wrap;
          word-break: break-word;
          background: #111827;
          border: 1px solid #263244;
          border-radius: 8px;
          padding: 18px;
          color: #d1d5db;
          font-family: Consolas, "Courier New", monospace;
          font-size: 14px;
          line-height: 1.7;
          font-weight: 400;
          }
     .report-chart {
          width: 100%;
          height: 100%;
          margin: 0;
          padding: 20px;
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 28px;
          background: #f8fafc;
          border: 1px solid #dce4ef;
          border-radius: 8px;
          }
     .report-pie {
          width: 180px;
          height: 180px;
          flex: 0 0 180px;
          border-radius: 50%;
          border: 8px solid #ffffff;
          box-shadow: 0 0 0 1px #d8e1ef, inset 0 0 18px rgba(0, 0, 0, 0.12);
          }
     .report-legend {
          flex: 1;
          min-width: 190px;
          text-align: left;
          font-size: 15px;
          line-height: 1.9;
          color: #475569;
          }
     .report-legend-title {
          margin-bottom: 8px;
          font-size: 18px;
          font-weight: 800;
          color: #1f3656;
          }
     .report-legend-item {
          display: flex;
          justify-content: space-between;
          gap: 16px;
          border-bottom: 1px dashed #d8e1ef;
          }
     .report-legend-label {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          font-weight: 800;
          }
     .report-legend-dot {
          display: inline-block;
          width: 11px;
          height: 11px;
          border-radius: 50%;
          }
     .duration-cell {
          white-space: nowrap;
          color: #475569;
          font-weight: 700;
          }
     @media (max-width: 980px) {
          body {
               padding: 14px;
               }
          .report-hero,
          .report-body {
               padding: 20px;
               }
          .report-meta,
          .summary-grid,
          .visual-grid {
               grid-template-columns: 1fr;
               }
          .report-chart {
               flex-direction: column;
               align-items: stretch;
               }
          .filter-buttons {
               grid-template-columns: 1fr;
               }
          }
    </style>
    """


def _case_value(case, key, default=""):
    if isinstance(case, dict):
        return case.get(key, default)
    return getattr(case, key, default)


def _read_case_log(case):
    file_path_name = _case_value(case, "file_path_name")
    file_name = _case_value(case, "file_name")
    log_path = file_path_name or (os.path.join(logs, file_name) if file_name else "")
    if not log_path:
        return "暂无日志"
    if not os.path.exists(log_path):
        return f"日志文件不存在: {log_path}"
    try:
        with open(log_path, "r", encoding="utf-8") as log_file:
            content = log_file.read().strip()
            return content or "暂无日志"
    except UnicodeDecodeError:
        with open(log_path, "r", encoding="gbk", errors="replace") as log_file:
            content = log_file.read().strip()
            return content or "暂无日志"
    except Exception as e:
        return f"读取日志失败: {e}"


def _case_row(each):
    duration = _case_value(each, "duration")
    case_title = escape(str(_case_value(each, "case_title")))
    case_name = escape(str(_case_value(each, "case_name")))
    run_case_result = escape(str(_case_value(each, "run_case_result")))
    longrepr = escape(str(_case_value(each, "longrepr")))
    log_content = escape(_read_case_log(each))
    status_class = _status_class(run_case_result)
    return """<tr>
                            <td class="case-title-cell">%s</td>
                            <td class="case-name-cell">%s</td>
                            <td><span class="status-badge %s">%s</span></td>
                            <td>
                                <details>
                                    <summary>展开日志</summary>
                                    <div class="case-log-block">
                                        <h4>失败/异常信息</h4>
                                        <pre><code>%s</code></pre>
                                        <h4>用例日志</h4>
                                        <pre><code>%s</code></pre>
                                    </div>
                                </details>
                            </td>
                            <td class="duration-cell">%s</td>
                            </tr>""" % (
        case_title, case_name, status_class, run_case_result, longrepr, log_content, duration)


def _status_class(run_case_result):
    if run_case_result == "passed":
        return "status-passed"
    if run_case_result == "failed":
        return "status-failed"
    if run_case_result == "error":
        return "status-error"
    return "status-other"


def _percent(count, total):
    return round(count / total * 100, 2) if total else 0


def _build_result_pie(pass_count, fail_count, error_count, all_count):
    other_count = max(all_count - pass_count - fail_count - error_count, 0)
    passed_end = _percent(pass_count, all_count) / 100 * 360 if all_count else 0
    failed_end = _percent(pass_count + fail_count, all_count) / 100 * 360 if all_count else 0
    error_end = _percent(pass_count + fail_count + error_count, all_count) / 100 * 360 if all_count else 0
    if all_count:
        pie_background = (
            "conic-gradient("
            f"#00AA00 0deg {passed_end:.2f}deg, "
            f"#FF0000 {passed_end:.2f}deg {failed_end:.2f}deg, "
            f"#FF9900 {failed_end:.2f}deg {error_end:.2f}deg, "
            f"#9CA3AF {error_end:.2f}deg 360deg)"
        )
    else:
        pie_background = "#E5E7EB"

    other_legend = ""
    if other_count:
        other_legend = f"""
                        <div class="report-legend-item">
                            <span class="report-legend-label"><span class="report-legend-dot" style="background:#9CA3AF;"></span>其他</span>
                            <span>{other_count} 条 / {_percent(other_count, all_count)}%</span>
                        </div>"""

    return f"""
                    <div class="report-chart">
                        <div class="report-pie" style="background: {pie_background};"></div>
                        <div class="report-legend">
                            <div class="report-legend-title">测试结果占比</div>
                            <div class="report-legend-item">
                                <span class="report-legend-label"><span class="report-legend-dot" style="background:#00AA00;"></span>passed</span>
                                <span>{pass_count} 条 / {_percent(pass_count, all_count)}%</span>
                            </div>
                            <div class="report-legend-item">
                                <span class="report-legend-label"><span class="report-legend-dot" style="background:#FF0000;"></span>failed</span>
                                <span>{fail_count} 条 / {_percent(fail_count, all_count)}%</span>
                            </div>
                            <div class="report-legend-item">
                                <span class="report-legend-label"><span class="report-legend-dot" style="background:#FF9900;"></span>error</span>
                                <span>{error_count} 条 / {_percent(error_count, all_count)}%</span>
                            </div>
                            {other_legend}
                        </div>
                    </div>
    """


def case_report(cases, report_name, case_all_time, info, run_type):
    """

    :param cases:
    :param report_name:
    :param case_all_time:
    :return:
    """
    values = """
               <div class="table-panel">
               <div class="table-scroll">
               <table class="gridtable" id="myTable">
               <thead>
               <tr>
               <th width="22%">用例 title</th>
               <th width="14%">用例名</th>
               <th width="8%">测试结果</th>
               <th width="46%">日志详情</th>
               <th width="10%">耗时/s</th>
               </tr>
               </thead>
               <tbody>
               """
    pass_count = fail_count = error_count = 0
    for each in cases:
        run_case_result = _case_value(each, "run_case_result")
        if run_case_result == "passed":
            pass_count += 1
            values += _case_row(each)
        elif run_case_result == "failed":
            fail_count += 1
            values += _case_row(each)
        elif run_case_result == "error":
            error_count += 1
            values += _case_row(each)
        else:
            values += _case_row(each)
    all_count = len(cases)
    # pass_rate = pass_count / all_count * 100
    pass_rate = _percent(pass_count, all_count)
    result_pie = _build_result_pie(pass_count, fail_count, error_count, all_count)
    values += "</tbody></table></div></div>"
    value = """
        <h2 class="section-title">用例明细</h2>
        {values}
            """.format(values=values)
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report_title = escape(str(report_name))
    project_name = escape(str(info[0])) if len(info) > 0 else ""
    testset_name = escape(str(info[1])) if len(info) > 1 else ""
    run_id = escape(str(info[2])) if len(info) > 2 else ""
    run_type_text = escape(str(run_type))
    case_all_time_text = round(case_all_time, 4)
    script_value = """function filterTable(value) {
  var table = document.getElementById("myTable");
  var rows = table.getElementsByTagName("tbody")[0].getElementsByTagName("tr");
  for (var i = 0; i < rows.length; i++) {
    var statusCol = rows[i].getElementsByTagName("td")[2];
    if (statusCol) {
      rows[i].style.display = (statusCol.textContent || statusCol.innerText).toLowerCase().indexOf(value.toLowerCase()) > -1 ? "" : "none";
    }
  }
}"""
    html = f"""
        <html>
              <head>
                    <meta charset="utf-8">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
                    <link rel="stylesheet" href="http://cdn.bootcss.com/bootstrap/3.3.0/css/bootstrap.min.css">
                    {style}
                    <script src="http://cdn.bootcss.com/html5shiv/3.7.2/html5shiv.min.js"></script>
                    <script src="http://cdn.bootcss.com/respond.js/1.4.2/respond.min.js"></script>
                    <script type="text/javascript">
                    {script_value}
                    </script>
              </head>
              <body>
                    <main class="report-page">
                        <section class="report-hero">
                            <h1 class="report-title">{report_title}_pytest 测试报告</h1>
                            <div class="report-subtitle">pytest 执行结果概览，包含结果占比、筛选和每条用例日志。</div>
                            <div class="report-meta">
                                <div class="report-meta-item">
                                    <span class="meta-label">报告时间</span>
                                    <span class="meta-value">{report_time}</span>
                                </div>
                                <div class="report-meta-item">
                                    <span class="meta-label">项目名</span>
                                    <span class="meta-value">{project_name}</span>
                                </div>
                                <div class="report-meta-item">
                                    <span class="meta-label">测试集</span>
                                    <span class="meta-value">{testset_name}</span>
                                </div>
                                <div class="report-meta-item">
                                    <span class="meta-label">运行 ID</span>
                                    <span class="meta-value">{run_id}</span>
                                </div>
                                <div class="report-meta-item">
                                    <span class="meta-label">运行方式</span>
                                    <span class="meta-value">{run_type_text}</span>
                                </div>
                            </div>
                        </section>
                        <section class="report-body">
                            <h2 class="section-title">执行概览</h2>
                            <div class="summary-grid">
                                <div class="summary-card all">
                                    <span class="summary-label">全部用例</span>
                                    <strong>{all_count}</strong>
                                    <div class="summary-extra">总耗时 {case_all_time_text}s</div>
                                </div>
                                <div class="summary-card rate">
                                    <span class="summary-label">通过率</span>
                                    <strong>{pass_rate}%</strong>
                                    <div class="summary-extra">passed / all</div>
                                </div>
                                <div class="summary-card passed">
                                    <span class="summary-label">passed</span>
                                    <strong>{pass_count}</strong>
                                    <div class="summary-extra">{_percent(pass_count, all_count)}%</div>
                                </div>
                                <div class="summary-card failed">
                                    <span class="summary-label">failed</span>
                                    <strong>{fail_count}</strong>
                                    <div class="summary-extra">{_percent(fail_count, all_count)}%</div>
                                </div>
                                <div class="summary-card error">
                                    <span class="summary-label">error</span>
                                    <strong>{error_count}</strong>
                                    <div class="summary-extra">{_percent(error_count, all_count)}%</div>
                                </div>
                            </div>
                            <div class="visual-grid">
                                {result_pie}
                                <div class="filter-panel">
                                    <div class="filter-title">快速筛选</div>
                                    <div class="filter-buttons">
                                        <button onclick="filterTable('')" type="button" class="filter-btn filter-all">全部用例</button>
                                        <button onclick="filterTable('passed')" type="button" class="filter-btn filter-passed">passed</button>
                                        <button onclick="filterTable('failed')" type="button" class="filter-btn filter-failed">failed</button>
                                        <button onclick="filterTable('error')" type="button" class="filter-btn filter-error">error</button>
                                    </div>
                                </div>
                            </div>
                            {value}
                        </section>
                    </main>
              </body>
        </html>
    """
    return html


def report_file(title, html_content):
    """

    :param title:
    :param html_content:
    :return:
    """
    name = title + ".html"
    dir_path = os.path.join(report_path, name)
    if not os.path.exists(report_path):
        os.makedirs(report_path)
    with open(dir_path, "w", encoding='utf-8') as html:
        html.write(html_content)
    return name


async def report_file2(title, html_content):
    name = title + ".html"
    dir_path = os.path.join(report_path, name)
    if not os.path.exists(report_path):
        os.makedirs(report_path)
    async with aiofiles.open(dir_path, "w", encoding='utf-8') as html:
        await html.write(html_content)
    return name


def case_report2():
    report = """<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告</title>
    <link href="https://cdn.bootcss.com/bootstrap/3.3.5/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.bootcss.com/font-awesome/4.4.0/css/font-awesome.min.css" rel="stylesheet">
    <link href="https://cdn.bootcss.com/animate.css/3.5.2/animate.min.css" rel="stylesheet">
    <link href="https://cdn.bootcss.com/chosen/1.8.2/chosen.css" rel="stylesheet">
    <base target="_blank"><style type="text/css"></style></head>
<body class="gray-bg">
<div class="row  border-bottom white-bg dashboard-header">
    <div class="col-sm-12 text-center">
        <span style="color: #1ab394; font-size: 20px; font-weight: 700">测试报告</span>
    </div>
</div>
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row">
        <div class="col-sm-12">
            <div class="ibox float-e-margins">
                <div class="ibox-title">
                    <h5>报告汇总</h5>
                    <div class="ibox-tools">
                        <a class="collapse-link">
                            <i class="fa fa-chevron-up"></i>
                        </a>
                        <a class="close-link">
                            <i class="fa fa-times"></i>
                        </a>
                    </div>
                </div>
                <div class="ibox-content">
                    <div class="row">
                        <div class="col-sm-6 b-r" style="height:350px">
                            <form class="form-horizontal">
                                <div class="form-group">
                                    <label class="col-sm-2 control-label text-navy">用例名称:</label>
                                    <div class="col-sm-5">
                                        <span class="form-control" id="testName"></span>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label class="col-sm-2 control-label text-navy">用例总数:</label>
                                    <div class="col-sm-5">
                                        <span class="form-control" id="testAll"></span>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label class="col-sm-2 control-label text-navy">用例通过:</label>
                                    <div class="col-sm-5">
                                        <span class="form-control" id="testPass"></span>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label class="col-sm-2 control-label text-danger">用例失败:</label>
                                    <div class="col-sm-5">
                                        <span class="form-control text-danger" id="testFail"></span>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label class="col-sm-2 control-label text-warning">用例跳过:</label>
                                    <div class="col-sm-5">
                                        <span class="form-control text-warning" id="testSkip"></span>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label class="col-sm-2 control-label text-navy">开始时间:</label>
                                    <div class="col-sm-5">
                                        <span class="form-control" id="beginTime"></span>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label class="col-sm-2 control-label text-navy">运行时间:</label>
                                    <div class="col-sm-5">
                                        <span class="form-control" id="totalTime"></span>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="col-sm-6">
                            <div style="height:350px" id="echarts-map-chart"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-sm-12">
            <div class="ibox float-e-margins">
                <div class="ibox-title">
                    <h5>详细数据</h5>
                    <div class="ibox-tools">
                        <a class="collapse-link">
                            <i class="fa fa-chevron-up"></i>
                        </a>
                        <a class="close-link">
                            <i class="fa fa-times"></i>
                        </a>
                    </div>
                </div>
                <div class="ibox-content">
                    <div class="input-group panel-heading" style="width: 100%; background-color: #1ab394; margin-bottom: 10px; text-align: left; font-family: Consolas;">
                        <label style="color: snow">测试类:</label>
                        <select class="chosen-select form-control" data-placeholder="----------" style="width: 300px;" name="filterClass" id="filterClass">
                            <option value="">----------</option>
                        </select>
                        <label style="color: snow">结果:</label>
                        <select class="chosen-select form-control" data-placeholder="----------" style="width: 300px;" name="filterResult" id="filterResult">
                            <option value="">----------</option>
                        </select>
                        <div style="float: right">
                            <label class="form-control">
                                <span class="text-navy">用例数: </span><span class="text-navy b-r" id="filterAll"></span><span> | </span>
                                <span style="color: green">成功: </span><span style="color: green" id="filterOk"></span><span> | </span>
                                <span class="text-danger">失败: </span><span class="text-danger" id="filterFail"></span><span> | </span>
                                <span class="text-warning">跳过: </span><span class="text-warning" id="filterSkip"></span>
                            </label>
                        </div>
                    </div>
                    <table class="table table-bordered">
                        <thead>
                        <tr>
                            <th>编号</th><th>测试类</th><th>测试方法</th><th>用例描述</th><th>耗时</th><th>结果</th><th>操作</th>
                        </tr>
                        </thead>
                        <tbody id="detailBody">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
<script src="https://cdn.bootcss.com/jquery/2.1.4/jquery.min.js"></script>
<script src="https://cdn.bootcss.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
<script src="https://cdn.bootcss.com/echarts/3.8.5/echarts.min.js"></script>
<script src="https://cdn.bootcss.com/chosen/1.8.2/chosen.jquery.js"></script>
<script type="text/javascript">
	function $childNode(o) {
	    return window.frames[o]
	}
	function animationHover(o, e) {
	    o = $(o), o.hover(function () {
	        o.addClass("animated " + e)
	    }, function () {
	        window.setTimeout(function () {
	            o.removeClass("animated " + e)
	        }, 2e3)
	    })
	}
	function WinMove() {
	    var o = "[class*=col]", e = ".ibox-title", i = "[class*=col]";
	    $(o).sortable({
	        handle: e,
	        connectWith: i,
	        tolerance: "pointer",
	        forcePlaceholderSize: !0,
	        opacity: .8
	    }).disableSelection()
	}
	var $parentNode = window.parent.document;
	if ($(".tooltip-demo").tooltip({
	        selector: "[data-toggle=tooltip]",
	        container: "body"
	    }), $(".modal").appendTo("body"), $("[data-toggle=popover]").popover(), $(".collapse-link").click(function () {
	        var o = $(this).closest("div.ibox"), e = $(this).find("i"), i = o.find("div.ibox-content");
	        i.slideToggle(200), e.toggleClass("fa-chevron-up").toggleClass("fa-chevron-down"), o.toggleClass("").toggleClass("border-bottom"), setTimeout(function () {
	            o.resize(), o.find("[id^=map-]").resize()
	        }, 50)
	    }), $(".close-link").click(function () {
	        var o = $(this).closest("div.ibox");
	        o.remove()
	    }), top == this) {
	}
</script>
<script type="text/javascript">
    var resultData = ${resultData};

    function clickRow(obj){
        $("#detailBody").children("tr").attr("style","font-family: Consolas");
        $(obj).attr("style","font-family: Consolas; background-color: #b0d877");
    }

    function details(obj) {
        if ($(obj).text() == '展开') {
            var len = $(obj).parent().parent().children().length;
            var detailLog = "";
            var logs = resultData["testResult"][parseInt($(obj).attr("buttonIndex"))]["log"];
            $(obj).text("收缩");
            $(obj).removeClass("btn-primary");
            $(obj).addClass("btn-danger");
            $.each(logs, function (i, n) {
                detailLog = detailLog + "<p>" + n + "</p>";
            });
            $(obj).parent().parent().after("<tr><td colspan='" + len + "'><div style='font-family: Consolas;font-size:12px'>" + detailLog + "</div></td></tr>");
        } else if ($(obj).text() == '收缩') {
            $(obj).parent().parent().next().remove();
            $(obj).text("展开");
            $(obj).removeClass("btn-danger");
            $(obj).addClass("btn-primary");
        }

    }
    $(function () {
        $("#testName").text(resultData["testName"]);
        $("#testPass").text(resultData["testPass"]);
        $("#testFail").text(resultData["testFail"]);
        $("#testSkip").text(resultData["testSkip"]);
        $("#testAll").text(resultData["testAll"]);
        $("#beginTime").text(resultData["beginTime"]);
        $("#totalTime").text(resultData["totalTime"]);
        $("#filterAll").text(resultData["testAll"]);
        $("#filterOk").text(resultData["testPass"]);
        $("#filterFail").text(resultData["testFail"]);
        $("#filterSkip").text(resultData["testSkip"]);
        var classNames = [];
        var results = [];
        $.each(resultData["testResult"], function (i, n) {
            if (classNames.indexOf(n["className"]) == -1) {
                classNames.push(n["className"]);
            }
            if (results.indexOf(n["status"]) == -1) {
                results.push(n["status"]);
            }
        });

        $.each(classNames, function (i, n) {
            $("#filterClass").append("<option value='" + n + "' hassubinfo='true'>" + n + "</option>");
        });
        $.each(results, function (i, n) {
            $("#filterResult").append("<option value='" + n + "' hassubinfo='true'>" + n + "</option>");
        });

        $("#filterClass").chosen({search_contains: true});
        $("#filterResult").chosen({search_contains: true});

        function generateResult(className, caseResult) {
            $("#detailBody").children().remove();
            var filterAll = 0;
            var filterOk = 0;
            var filterFail = 0;
            var filterSkip = 0;
            $.each(resultData["testResult"], function (i, n) {
                if ((className == "" || n["className"] == className) && (caseResult == "" || n["status"] == caseResult)) {
                    filterAll += 1;
                    var status = "";
                    if (n["status"] == '成功') {
                        filterOk += 1;
                        status = "<td><span class='text-navy'>成功</span></td>";
                    } else if (n["status"] == '失败') {
                        filterFail += 1;
                        status = "<td><span class='text-danger'>失败</span></td>";
                    } else if (n["status"] == '跳过') {
                        filterSkip += 1;
                        status = "<td><span class='text-warning'>跳过</span></td>";
                    } else {
                        status = "<td><span>" + n["status"] + "</span></td>";
                    }
                    var tr = "<tr style='font-family: Consolas'>" +
                        "<td>" + (i + 1) + "</td>" +
                        "<td>" + n["className"] + "</td>" +
                        "<td>" + n["methodName"] + "</td>" +
                        "<td>" + n["description"] + "</td>" +
                        "<td>" + n["spendTime"] + "</td>" +
                        status + "<td><button type='button' onclick='details(this)' buttonIndex='" + i + "' class='btn btn-primary btn-xs' style='margin-bottom: 0px'>展开</button></td></tr>"
                    $("#detailBody").append(tr);
                }
            });
            $("#filterAll").text(filterAll);
            $("#filterOk").text(filterOk);
            $("#filterFail").text(filterFail);
            $("#filterSkip").text(filterSkip);
        }

        generateResult("", "");

        $("#filterClass").on('change', function () {
            var className = $("#filterClass").val();
            var caseResult = $("#filterResult").val();
            generateResult(className, caseResult);
        });

        $("#filterResult").on('change', function () {
            var className = $("#filterClass").val();
            var caseResult = $("#filterResult").val();
            generateResult(className, caseResult);
        });

        //$(".chosen-select").trigger("chosen:updated");

        function pie() {
            var option = {
                title: {
                    text: '测试用例运行结果',
                    subtext: '',
                    x: 'center'
                },
                tooltip: {
                    trigger: 'item',
                    formatter: "{a} <br/>{b} : {c} ({d}%)"
                },
                legend: {
                    orient: 'vertical',
                    left: 'left',
                    data: ['失败', '跳过', '成功']
                },
                series: [
                    {
                        name: '运行结果',
                        type: 'pie',
                        radius: '55%',
                        center: ['50%', '60%'],
                        data: [
                            {value: resultData["testFail"], name: '失败'},
                            {value: resultData["testSkip"], name: '跳过'},
                            {value: resultData["testPass"], name: '成功'}
                        ],
                        itemStyle: {
                            emphasis: {
                                shadowBlur: 10,
                                shadowOffsetX: 0,
                                shadowColor: 'rgba(0, 0, 0, 0.5)'
                            }
                        }
                    }
                ]
            };
            var chart = echarts.init(document.getElementById("echarts-map-chart"));
            chart.setOption(option);
        }

        pie();
    });

</script>
</body>
</html>"""
