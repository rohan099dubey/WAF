import json
import os
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template_string

APP = Flask(__name__)

WAF_METRICS_URL = os.getenv("WAF_METRICS_URL", "http://localhost:8080/metrics")
WAF_EVENTS_URL = os.getenv("WAF_EVENTS_URL", "http://localhost:8080/events?limit=25")
LOG_FILE = Path(os.getenv("WAF_LOG_FILE", "logs/waf_events.jsonl"))

HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>WAF Dashboard</title>
  <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
  <style>
    body { font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f2f4f8; }
    h1 { margin-bottom: 8px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(220px,1fr)); gap: 12px; }
    .card { background: white; border-radius: 10px; padding: 14px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
    table { width: 100%; border-collapse: collapse; background: white; margin-top: 16px; }
    th, td { padding: 10px; border-bottom: 1px solid #eceff4; text-align: left; font-size: 14px; }
    .blocked { color: #b42318; font-weight: 700; }
    .allowed { color: #067647; font-weight: 700; }
  </style>
</head>
<body>
  <h1>Web Application Firewall Dashboard</h1>
  <div class=\"grid\" id=\"cards\"></div>
  <div class=\"card\" style=\"margin-top:16px;\">
    <canvas id=\"latencyChart\" height=\"100\"></canvas>
  </div>
  <table>
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>Method</th>
        <th>Path</th>
        <th>Status</th>
        <th>Decision</th>
        <th>Latency (ms)</th>
      </tr>
    </thead>
    <tbody id=\"eventsBody\"></tbody>
  </table>

  <script>
    async function loadData() {
      const response = await fetch('/api/data');
      const data = await response.json();
      const metrics = data.metrics || {};
      const events = data.events || [];

      document.getElementById('cards').innerHTML = `
        <div class=\"card\"><h3>Total</h3><p>${metrics.total ?? 0}</p></div>
        <div class=\"card\"><h3>Blocked</h3><p>${metrics.blocked ?? 0}</p></div>
        <div class=\"card\"><h3>Allowed</h3><p>${metrics.allowed ?? 0}</p></div>
        <div class=\"card\"><h3>Avg Latency</h3><p>${metrics.avg_latency_ms ?? 0} ms</p></div>
      `;

      const rows = events.map(evt => `
        <tr>
          <td>${evt.timestamp}</td>
          <td>${evt.method}</td>
          <td>${evt.path}</td>
          <td>${evt.status_code}</td>
          <td class=\"${evt.blocked ? 'blocked' : 'allowed'}\">${evt.blocked ? 'BLOCKED' : 'ALLOWED'}</td>
          <td>${evt.latency_ms}</td>
        </tr>
      `).join('');
      document.getElementById('eventsBody').innerHTML = rows;

      const labels = events.slice().reverse().map((_, idx) => `Req ${idx + 1}`);
      const latencies = events.slice().reverse().map(evt => evt.latency_ms);
      const ctx = document.getElementById('latencyChart').getContext('2d');
      if (window.latencyChartInstance) {
        window.latencyChartInstance.destroy();
      }
      window.latencyChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [{ label: 'Latency (ms)', data: latencies, borderColor: '#2065d1', tension: 0.25 }]
        }
      });
    }

    loadData();
    setInterval(loadData, 5000);
  </script>
</body>
</html>
"""


def read_recent_events(limit: int = 25):
    events = []
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()[-limit:]
        for line in reversed(lines):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


@APP.route("/")
def home():
    return render_template_string(HTML)


@APP.route("/api/data")
def api_data():
    metrics = {}
    events = read_recent_events(limit=25)

    try:
        metrics = requests.get(WAF_METRICS_URL, timeout=3).json()
    except Exception:
        metrics = {}

    if not events:
        try:
            events = requests.get(WAF_EVENTS_URL, timeout=3).json().get("events", [])
        except Exception:
            events = []

    return jsonify({"metrics": metrics, "events": events})


if __name__ == "__main__":
    APP.run(host="0.0.0.0", port=int(os.getenv("DASHBOARD_PORT", "8501")))
