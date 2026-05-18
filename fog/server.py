import json
from html import escape
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
alerts = []
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


def get_missing_fields(alert):
    return [field for field in REQUIRED_ALERT_FIELDS if field not in alert]


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
        return jsonify({
            "error": "missing required alert fields",
            "missing_fields": missing_fields,
        }), 400

    alerts.append(alert)
    log_alert(alert)
    print(f"Alert received from {alert.get('device_id')}: {alert.get('threat_label')}")

    return jsonify({"status": "received"}), 200


@app.route("/alerts", methods=["GET"])
def list_alerts():
    return jsonify({
        "count": len(alerts),
        "alerts": alerts,
    }), 200


@app.route("/", methods=["GET"])
def dashboard():
    rows = []
    for alert in reversed(alerts[-10:]):
        timestamp = escape(str(alert.get("timestamp", "unknown")))
        device = escape(str(alert.get("device_id", "unknown")))
        label = escape(str(alert.get("threat_label", "unknown")))
        confidence = escape(str(alert.get("confidence", "unknown")))
        rows.append(f"<li>{timestamp} - {device} - {label} ({confidence})</li>")

    if not rows:
        rows.append("<li>No alerts received yet.</li>")

    return f"""
    <meta http-equiv="refresh" content="3">
    <h1>ThreatSense Fog Dashboard</h1>
    <p>Total alerts: {len(alerts)}</p>
    <ul>{''.join(rows)}</ul>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
