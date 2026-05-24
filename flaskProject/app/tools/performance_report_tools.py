# -*- coding: utf-8 -*-
import datetime
import os
from html import escape

from app.tools.api_common_tools import loads
from config import report_path


def perf_report_filename(run_id):
    if not run_id:
        raise ValueError("performance report run_id is required")
    return "performance_{}.html".format(run_id)


def write_perf_report_file(result, scenario=None, endpoints=None):
    endpoints = endpoints or []
    metrics = loads(result.metrics, {})
    filename = result.report_path or perf_report_filename(result.run_id)
    os.makedirs(report_path, exist_ok=True)
    report_root = os.path.realpath(report_path)
    target_path = os.path.realpath(os.path.join(report_root, filename))
    if os.path.commonpath([report_root, target_path]) != report_root:
        raise ValueError("invalid performance report path")
    stats = metrics.get("stats") or []
    rows = []
    for item in stats:
        rows.append(
            "<tr><td>{method}</td><td>{name}</td><td>{requests}</td><td>{failures}</td>"
            "<td>{avg}</td><td>{min}</td><td>{max}</td><td>{rps}</td></tr>".format(
                method=escape(str(item.get("method") or "-")),
                name=escape(str(item.get("name") or "-")),
                requests=escape(str(item.get("num_requests") or 0)),
                failures=escape(str(item.get("num_failures") or 0)),
                avg=escape(str(item.get("avg_response_time") or 0)),
                min=escape(str(item.get("min_response_time") or 0)),
                max=escape(str(item.get("max_response_time") or 0)),
                rps=escape(str(item.get("current_rps") or item.get("total_rps") or 0)),
            )
        )
    endpoint_rows = []
    for endpoint in endpoints:
        endpoint_rows.append(
            "<tr><td>{method}</td><td>{name}</td><td>{url}</td><td>{weight}</td></tr>".format(
                method=escape(str(endpoint.method or "-")),
                name=escape(str(endpoint.name or "-")),
                url=escape(str(endpoint.url or "-")),
                weight=escape(str(endpoint.weight or 1)),
            )
        )
    html = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>性能测试报告 - {run_id}</title>
  <style>
    body {{ margin: 0; background: #eef3f8; color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif; }}
    .page {{ max-width: 1180px; margin: 0 auto; padding: 28px; background: #fff; min-height: 100vh; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .sub {{ color: #64748b; margin-bottom: 22px; }}
    .cards {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 22px; }}
    .card {{ border: 1px solid #dbe4ef; border-radius: 6px; padding: 14px; background: #f8fbff; }}
    .card span {{ color: #64748b; display: block; font-size: 12px; }}
    .card strong {{ font-size: 22px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ border: 1px solid #dbe4ef; padding: 10px; text-align: left; font-size: 13px; }}
    th {{ background: #eaf1f8; }}
    section {{ margin-top: 24px; }}
  </style>
</head>
<body>
  <main class="page">
    <h1>性能测试报告</h1>
    <div class="sub">{scenario_name} · run_id {run_id} · {report_time}</div>
    <div class="cards">
      <div class="card"><span>状态</span><strong>{status}</strong></div>
      <div class="card"><span>用户数</span><strong>{users}</strong></div>
      <div class="card"><span>启动速率</span><strong>{spawn_rate}</strong></div>
      <div class="card"><span>运行时长</span><strong>{run_time}</strong></div>
      <div class="card"><span>耗时(ms)</span><strong>{elapsed_ms}</strong></div>
    </div>
    <section>
      <h2>Locust 指标</h2>
      <table>
        <thead><tr><th>方法</th><th>接口</th><th>请求数</th><th>失败数</th><th>平均响应(ms)</th><th>最小(ms)</th><th>最大(ms)</th><th>RPS</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    <section>
      <h2>场景接口</h2>
      <table>
        <thead><tr><th>方法</th><th>名称</th><th>URL</th><th>权重</th></tr></thead>
        <tbody>{endpoint_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>""".format(
        run_id=escape(str(result.run_id)),
        scenario_name=escape(str(scenario.name if scenario else "性能测试场景")),
        report_time=escape(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        status=escape(str(result.status_text or result.run_status or "-")),
        users=escape(str(result.users or 0)),
        spawn_rate=escape(str(result.spawn_rate or 0)),
        run_time=escape(str(result.run_time or "")),
        elapsed_ms=escape(str(result.elapsed_ms or 0)),
        rows="".join(rows) or "<tr><td colspan='8'>暂无指标</td></tr>",
        endpoint_rows="".join(endpoint_rows) or "<tr><td colspan='4'>暂无接口</td></tr>",
    )
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(html)
    return filename
