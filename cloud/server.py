import json
from html import escape
from pathlib import Path

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)
ALERTS_FILE = Path("cloud/data/alerts.json")
REQUIRED_ALERT_FIELDS = [
    "device_id",
    "camera_id",
    "timestamp",
    "object",
    "threat_label",
    "confidence",
    "bbox",
]


def get_missing_fields(alert):
    return [field for field in REQUIRED_ALERT_FIELDS if field not in alert]


def load_logged_alerts():
    if not ALERTS_FILE.exists():
        return []

    loaded_alerts = []
    with ALERTS_FILE.open() as log_file:
        for line in log_file:
            try:
                loaded_alerts.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return loaded_alerts


alerts = load_logged_alerts()


def log_alert(alert):
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with ALERTS_FILE.open("a") as log_file:
        log_file.write(json.dumps(alert) + "\n")


@app.route("/", methods=["GET"])
def dashboard():
    '''
    rows = []
    for alert in reversed(alerts[-10:]):
        timestamp = escape(str(alert.get("timestamp", "unknown")))
        device = escape(str(alert.get("device_id", "unknown")))
        label = escape(str(alert.get("threat_label", "unknown")))
        confidence = escape(str(alert.get("confidence", "unknown")))
        rows.append(f"<li>{timestamp} - {device} - {label} ({confidence})</li>")

    if not rows:
        rows.append("<li>No cloud alerts received yet.</li>")

    return f"""
    <meta http-equiv="refresh" content="3">
    <h1>ThreatSense Cloud Dashboard</h1>
    <p>Total cloud alerts: {len(alerts)}</p>
    <ul>{''.join(rows)}</ul>
    """
    '''
    displayed_alert_count = min(len(alerts), 10)

    active_devices = len(
        {alert.get("device_id", "unknown") for alert in alerts}
    )

    return render_template(
        "dashboard.html",
        alerts=list(reversed(alerts[-10:])),
        total_alerts=len(alerts),
        displayed_alert_count=displayed_alert_count,
        active_devices=active_devices,
    )

@app.route("/cloud-alert", methods=["POST"])
def receive_cloud_alert():
    alert = request.get_json()

    if not alert:
        return jsonify({"error": "missing JSON alert"}), 400

    missing_fields = get_missing_fields(alert)
    if missing_fields:
        return jsonify({
            "error": "missing required alert fields",
            "missing_fields": missing_fields,
        }), 400

    alerts.append(alert)
    log_alert(alert)
    print(f"Cloud alert received from {alert.get('device_id')}")

    return jsonify({"status": "received"}), 200


@app.route("/alerts", methods=["GET"])
def list_alerts():
    return jsonify({
        "count": len(alerts),
        "alerts": alerts,
    }), 200


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "running",
        "alert_count": len(alerts),
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
