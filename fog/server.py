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
        return (
            jsonify(
                {
                    "error": "missing required alert fields",
                    "missing_fields": missing_fields,
                }
            ),
            400,
        )

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


@app.route("/", methods=["GET"])
def dashboard():
    rows = []

    for alert in reversed(alerts[-10:]):
        timestamp = escape(str(alert.get("timestamp", "unknown")))
        device = escape(str(alert.get("device_id", "unknown")))
        label = escape(str(alert.get("threat_label", "unknown")))
        #confidence = escape(str(alert.get("confidence", "unknown")))
        raw_confidence = alert.get("confidence", "unknown")

        try:
            confidence = f"{float(raw_confidence) * 100:.1f}%"
        except (ValueError, TypeError):
            confidence = escape(str(raw_confidence))

        rows.append(
            f"""
            <tr>
                <td>{timestamp}</td>
                <td>{device}</td>
                <td>{label}</td>
                <td>{confidence}</td>
            </tr>
            """
        )

    if not rows:
        rows.append(
            """
            <tr>
                <td colspan="4">System running, waiting for alerts from edge devices...</td>
            </tr>
            """
        )

    return f"""
    <meta http-equiv="refresh" content="3">
    <h1>ThreatSense Fog Dashboard</h1>
    <p>Total alerts: {len(alerts)}</p>
    <p>Showing the 10 most recent alerts.</p>

    <table border="1" cellpadding="8" cellspacing="0">
        <tr>
            <th>Timestamp</th>
            <th>Device ID</th>
            <th>Threat Label</th>
            <th>Confidence</th>
        </tr>
    {''.join(rows)}
</table>
"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
