# -*- coding: utf-8 -*-
import datetime
import json
import os
import re
from html import escape

from app.commom.create_report import style as pytest_report_style, _build_result_pie, _percent
from config import report_path


def _loads(value, default=None):
    if default is None:
        default = {}
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _format_time(value):
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def _api_report_filename(target_type, run_id):
    if not run_id:
        raise ValueError("api report run_id is required")
    safe_type = re.sub(r"[^A-Za-z0-9_-]+", "_", str(target_type or "case")).strip("_") or "case"
    return "api_{}_{}.html".format(safe_type, run_id)


def _display_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
    return str(value)


def _html_pre(value):
    return escape(_display_text(value))


def _result_status_text(success):
    if success in (1, True, "1", "true", "True"):
        return "passed"
    if success in (0, False, "0", "false", "False"):
        return "failed"
    return "error"


def _api_status_class(status):
    if status == "passed":
        return "status-passed"
    if status == "failed":
        return "status-failed"
    if status == "error":
        return "status-error"
    return "status-other"


def _api_report_row(index, item):
    if not isinstance(item, dict):
        item = {"case_name": str(item), "success": None}
    status = _result_status_text(item.get("success"))
    method = escape(str(item.get("method") or "-"))
    url = escape(str(item.get("url") or "-"))
    case_name = escape(str(item.get("case_name") or item.get("name") or item.get("url") or "-"))
    step_type = escape(str(item.get("step_type_name") or item.get("status_text") or "接口用例"))
    response_status = escape(str(item.get("response_status") or item.get("status") or "-"))
    elapsed = escape(str(item.get("elapsed_ms") or 0))
    error_message = escape(str(item.get("error_message") or ""))
    request_detail = {
        "method": item.get("method"),
        "url": item.get("url"),
        "headers": item.get("request_headers") or {},
        "params": item.get("request_params") or {},
        "body": item.get("request_body") or "",
    }
    response_detail = {
        "status": item.get("response_status") or item.get("status"),
        "headers": item.get("response_headers") or {},
        "body": item.get("response_body") or "",
    }
    assertion_detail = item.get("assertion_result") or item.get("assertions") or []
    extractor_detail = item.get("extractor_result") or item.get("extracted_variables") or []
    chain_detail = item.get("chain_results") or []
    detail = {
        "请求参数": request_detail,
        "响应参数": response_detail,
        "断言结果": assertion_detail,
        "变量提取": extractor_detail,
        "依赖链": chain_detail,
        "数据行": item.get("data_row") or {},
        "错误信息": item.get("error_message") or "",
    }
    return """<tr>
                            <td class="case-title-cell api-name-cell">{case_name}<div class="summary-extra">{step_type}</div></td>
                            <td class="case-name-cell api-request-cell"><span class="api-method">{method}</span><span class="api-url">{url}</span></td>
                            <td class="api-result-cell"><span class="status-badge {status_class}">{status}</span><div class="summary-extra">HTTP {response_status}</div></td>
                            <td class="api-log-cell">
                                <span class="api-detail-toggle" onclick="toggleApiDetail(this)">展开详情</span>
                            </td>
                            <td class="duration-cell api-duration-cell">{elapsed}ms</td>
                            <td class="api-error-cell">{error_message}</td>
                            </tr>
                            <tr class="api-detail-row">
                              <td colspan="6">
                                <div class="case-log-block api-detail-block">
                                  <h4>接口日志</h4>
                                  <pre><code>{detail}</code></pre>
                                </div>
                              </td>
                            </tr>""".format(
        index=index,
        case_name=case_name,
        step_type=step_type,
        method=method,
        url=url,
        status=status,
        status_class=_api_status_class(status),
        response_status=response_status,
        detail=_html_pre(detail),
        elapsed=elapsed,
        error_message=error_message,
    )


def write_api_report_file(report, detail=None):
    detail = detail or _loads(report.detail, {})
    summary = _loads(report.summary, {})
    run_id = report.run_id
    if not run_id:
        raise ValueError("api report run_id is required")
    filename = report.report_path or _api_report_filename(report.target_type, run_id)
    os.makedirs(report_path, exist_ok=True)
    report_root = os.path.realpath(report_path)
    target_path = os.path.realpath(os.path.join(report_root, filename))
    if os.path.commonpath([report_root, target_path]) != report_root:
        raise ValueError("invalid api report path")
    steps = detail.get("step_results") or detail.get("data_results") or detail.get("chain_results") or []
    if not isinstance(steps, list):
        steps = []
    if not steps:
        steps = [detail]
        steps[0]["case_name"] = report.target_name or detail.get("url") or "接口用例"
        steps[0]["success"] = report.success

    step_rows = "".join(_api_report_row(index, item) for index, item in enumerate(steps, start=1))
    all_count = report.total_count or len(steps)
    pass_count = report.pass_count or 0
    fail_count = report.fail_count or 0
    error_count = max(all_count - pass_count - fail_count, 0)
    pass_rate = _percent(pass_count, all_count)
    elapsed_seconds = round((report.elapsed_ms or 0) / 1000, 4)
    result_pie = _build_result_pie(pass_count, fail_count, error_count, all_count)
    report_time = _format_time(getattr(report, "created_time", None)) or _format_time(datetime.datetime.now())
    status_text = _result_status_text(report.success)
    run_type_text = "接口集合" if report.target_type == "suite" else "接口用例"
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
    html = f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    <title>{escape(report.title or "接口测试报告")}</title>
    {pytest_report_style}
    <style type="text/css">
      table.api-report-table {{
        min-width: 1180px;
        table-layout: fixed;
      }}
      table.api-report-table th,
      table.api-report-table td {{
        word-break: normal;
        overflow-wrap: anywhere;
      }}
      table.api-report-table .api-name-cell {{
        width: 260px;
        min-width: 260px;
        white-space: normal;
      }}
      table.api-report-table .api-request-cell {{
        width: 330px;
        min-width: 330px;
        white-space: normal;
        font-family: Consolas, "Courier New", monospace;
        font-size: 12px;
        line-height: 1.6;
      }}
      table.api-report-table .api-result-cell {{
        width: 120px;
        min-width: 120px;
      }}
      table.api-report-table .api-log-cell {{
        width: 320px;
        min-width: 320px;
      }}
      table.api-report-table .api-duration-cell {{
        width: 100px;
        min-width: 100px;
        white-space: nowrap;
      }}
      table.api-report-table .api-error-cell {{
        width: 220px;
        min-width: 220px;
      }}
      table.api-report-table tr.api-detail-row {{
        display: none;
      }}
      table.api-report-table tr.api-detail-row td {{
        padding: 0 18px 18px;
        background: #f7fbff;
      }}
      .api-detail-toggle {{
        cursor: pointer;
        color: #2563eb;
        font-weight: 800;
      }}
      .api-detail-toggle:before {{
        content: "▶";
        margin-right: 6px;
        font-size: 11px;
      }}
      .api-detail-toggle.open:before {{
        content: "▼";
      }}
      .api-detail-block {{
        margin: 0;
        padding: 16px 0 0;
      }}
      .api-detail-block pre {{
        width: 100%;
        min-width: 0;
        max-height: 720px;
        white-space: pre-wrap;
        overflow-x: auto;
        overflow-y: auto;
      }}
      .api-method {{
        display: inline-block;
        margin-bottom: 6px;
        padding: 2px 6px;
        border-radius: 4px;
        background: #e8f1ff;
        color: #2563eb;
        font-weight: 800;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
      }}
      .api-url {{
        display: block;
        color: #475569;
      }}
    </style>
    <script type="text/javascript">
      {script_value}
      function toggleApiDetail(trigger) {{
        var detailRow = trigger.closest("tr").nextElementSibling;
        if (!detailRow || !detailRow.classList.contains("api-detail-row")) {{
          return;
        }}
        var isOpen = detailRow.style.display === "table-row";
        detailRow.style.display = isOpen ? "none" : "table-row";
        trigger.textContent = isOpen ? "展开详情" : "收起详情";
        if (isOpen) {{
          trigger.classList.remove("open");
        }} else {{
          trigger.classList.add("open");
        }}
      }}
    </script>
  </head>
  <body>
    <main class="report-page">
      <section class="report-hero">
        <h1 class="report-title">{escape(report.title or "接口测试报告")}</h1>
        <div class="report-subtitle">接口测试执行结果概览，包含结果占比、筛选、请求响应、断言和变量提取信息。</div>
        <div class="report-meta">
          <div class="report-meta-item"><span class="meta-label">报告时间</span><span class="meta-value">{escape(str(report_time))}</span></div>
          <div class="report-meta-item"><span class="meta-label">报告来源</span><span class="meta-value">接口测试</span></div>
          <div class="report-meta-item"><span class="meta-label">目标名称</span><span class="meta-value">{escape(str(report.target_name or "-"))}</span></div>
          <div class="report-meta-item"><span class="meta-label">运行 ID</span><span class="meta-value">{escape(str(run_id))}</span></div>
          <div class="report-meta-item"><span class="meta-label">运行方式</span><span class="meta-value">{escape(run_type_text)}</span></div>
        </div>
      </section>
      <section class="report-body">
        <h2 class="section-title">执行概览</h2>
        <div class="summary-grid">
          <div class="summary-card all"><span class="summary-label">全部用例</span><strong>{all_count}</strong><div class="summary-extra">总耗时 {elapsed_seconds}s</div></div>
          <div class="summary-card rate"><span class="summary-label">通过率</span><strong>{pass_rate}%</strong><div class="summary-extra">passed / all</div></div>
          <div class="summary-card passed"><span class="summary-label">passed</span><strong>{pass_count}</strong><div class="summary-extra">{_percent(pass_count, all_count)}%</div></div>
          <div class="summary-card failed"><span class="summary-label">failed</span><strong>{fail_count}</strong><div class="summary-extra">{_percent(fail_count, all_count)}%</div></div>
          <div class="summary-card error"><span class="summary-label">error</span><strong>{error_count}</strong><div class="summary-extra">{_percent(error_count, all_count)}%</div></div>
        </div>
        <div class="visual-grid">
          {result_pie}
          <div class="filter-panel">
            <div class="filter-title">快速筛选</div>
            <div class="filter-buttons">
              <button onclick="filterTable('')" type="button" class="filter-btn filter-all">全部接口</button>
              <button onclick="filterTable('passed')" type="button" class="filter-btn filter-passed">passed</button>
              <button onclick="filterTable('failed')" type="button" class="filter-btn filter-failed">failed</button>
              <button onclick="filterTable('error')" type="button" class="filter-btn filter-error">error</button>
            </div>
            <div class="summary-extra" style="margin-top:14px;">当前整体状态：{escape(status_text)}</div>
          </div>
        </div>
        <h2 class="section-title">接口明细</h2>
        <div class="table-panel">
          <div class="table-scroll">
            <table id="myTable" class="gridtable api-report-table">
              <thead>
                <tr>
                  <th class="api-name-cell">接口名称</th>
                  <th class="api-request-cell">请求</th>
                  <th class="api-result-cell">测试结果</th>
                  <th class="api-log-cell">请求/响应/断言日志</th>
                  <th class="api-duration-cell">耗时</th>
                  <th class="api-error-cell">错误信息</th>
                </tr>
              </thead>
              <tbody>{step_rows}</tbody>
            </table>
          </div>
        </div>
      </section>
    </main>
  </body>
</html>"""
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(html)
    return filename


