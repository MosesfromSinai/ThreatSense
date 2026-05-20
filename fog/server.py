import json
from html import escape
from pathlib import Path
 
from flask import Flask, jsonify, request
 
app = Flask(__name__)
LOG_FILE = Path("data/logs/alerts.jsonl")
REQUIRED_ALERT_FIELDS = [
    "device_id",
    "camera_id",
    "timestamp",
    "object",
    "threat_label",
    "confidence",
    "box",
]
 
DEDUPLICATE_WINDOW_SECONDS = 5
 
def load_logged_alerts():
    if not LOG_FILE.exists():
        return []
 
    loaded_alerts = []
    with LOG_FILE.open() as log_file:
        for line in log_file:
            try:
                loaded_alerts.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return loaded_alerts
 
alerts = load_logged_alerts()
_last_seen: dict[tuple, str] = {}
 
def get_missing_fields(alert):
    return [field for field in REQUIRED_ALERT_FIELDS if field not in alert]
 
def is_duplicate(alert) -> bool:
    from datetime import datetime
 
    key = (alert.get("device_id"), alert.get("threat_label"))
    incoming_time_str = alert.get("timestamp", "")
 
    try:
        incoming_time = datetime.strptime(incoming_time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False
 
    last_time_str = _last_seen.get(key)
    if last_time_str:
        try:
            last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
            delta = (incoming_time - last_time).total_seconds()
            if abs(delta) < DEDUPLICATE_WINDOW_SECONDS:
                return True
        except ValueError:
            pass
 
    _last_seen[key] = incoming_time_str
    return False
 
def log_alert(alert):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
 
    with LOG_FILE.open("a") as log_file:
        log_file.write(json.dumps(alert) + "\n")
 
@app.route("/alert", methods=["POST"])
def receive_alert():
    alert = request.get_json()
 
    if not alert:
        return jsonify({"error": "missing JSON alert"}), 400
 
    missing_fields = get_missing_fields(alert)
    if missing_fields:
        return (
            jsonify(
                {
                    "error": "missing required alert fields",
                    "missing_fields": missing_fields,
                }
            ),
            400,
        )
 
    if is_duplicate(alert):
        print(
            f"Duplicate alert suppressed from {alert.get('device_id')}: "
            f"{alert.get('threat_label')}"
        )
        return jsonify({"status": "duplicate, suppressed"}), 200
 
    alerts.append(alert)
    log_alert(alert)
    print(f"Alert received from {alert.get('device_id')}: {alert.get('threat_label')}")
 
    return jsonify({"status": "received"}), 200
 
@app.route("/alerts", methods=["GET"])
def list_alerts():
    return (
        jsonify(
            {
                "count": len(alerts),
                "alerts": alerts,
            }
        ),
        200,
    )
 
@app.route("/health", methods=["GET"])
def health_check():
    return (
        jsonify(
            {
                "status": "running",
                "alert_count": len(alerts),
            }
        ),
        200,
    )
 
@app.route("/devices", methods=["GET"])
def list_devices():
    device_counts = {}
    for alert in alerts:
        device_id = alert.get("device_id", "unknown")
        device_counts[device_id] = device_counts.get(device_id, 0) + 1
 
    return (
        jsonify(
            {
                "count": len(device_counts),
                "devices": device_counts,
            }
        ),
        200,
    )
 
def _threat_color(threat_label: str) -> str:
    """Return a background color for the alert row based on threat type."""
    label = threat_label.lower()
    if "gun" in label:
        return "#ffe5e5"
    if "knife" in label:
        return "#fff4e5"
    return "#fffde5"
 
@app.route("/", methods=["GET"])
def dashboard():
    rows = []
    for alert in reversed(alerts[-10:]):
        timestamp = escape(str(alert.get("timestamp", "unknown")))
        device = escape(str(alert.get("device_id", "unknown")))
        camera = escape(str(alert.get("camera_id", "unknown")))
        detected_object = escape(str(alert.get("object", "unknown")))
        label = escape(str(alert.get("threat_label", "unknown")))
        confidence = escape(str(alert.get("confidence", "unknown")))
        color = _threat_color(alert.get("threat_label", ""))
 
        rows.append(
            f'<tr style="background:{color}">'
            f"<td>{timestamp}</td>"
            f"<td>{device}</td>"
            f"<td>cam:{camera}</td>"
            f"<td>{detected_object}</td>"
            f"<td><strong>{label}</strong></td>"
            f"<td>{confidence}</td>"
            f"</tr>"
        )
 
    if not rows:
        rows.append(
            '<tr><td colspan="6" style="text-align:center">No alerts received yet.</td></tr>'
        )
 
    table_rows = "".join(rows)
 
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta http-equiv="refresh" content="3">
      <title>ThreatSense Fog Dashboard</title>
      <style>
        body {{ font-family: Arial, sans-serif; padding: 24px; background: #f9f9f9; }}
        h1 {{ color: #333; }}
        .stats {{ margin-bottom: 16px; color: #555; }}
        table {{ border-collapse: collapse; width: 100%; background: white;
                 box-shadow: 0 1px 4px rgba(0,0,0,0.1); }}
        th {{ background: #333; color: white; padding: 10px 14px; text-align: left; }}
        td {{ padding: 9px 14px; border-bottom: 1px solid #eee; }}
        tr:last-child td {{ border-bottom: none; }}
      </style>
    </head>
    <body>
      <h1>ThreatSense Fog Dashboard</h1>
      <div class="stats">
        Total alerts logged: <strong>{len(alerts)}</strong> &nbsp;|&nbsp;
        Showing last 10 &nbsp;|&nbsp; Auto-refreshes every 3s
      </div>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Device</th>
            <th>Camera</th>
            <th>Object</th>
            <th>Threat Label</th>
            <th>Confidence</th>
          </tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
    </body>
    </html>
    """
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
