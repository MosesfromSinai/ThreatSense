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

    # dashboard only displays the 10 most recent alerts so page doesn't get flooded.
    displayed_alert_count = min(len(alerts), 10)
    # count each device that has sent alerts to the fog server.
    active_devices = len({alert.get("device_id", "unknown") for alert in alerts})

    for alert in reversed(alerts[-10:]):
        # escape text values before inserting them into html to prevent rendering issues.
        timestamp = escape(str(alert.get("timestamp", "unknown")))
        device = escape(str(alert.get("device_id", "unknown")))

        # turn internal threat labels into clearer dashboard display names.
        raw_label = str(alert.get("threat_label", "unknown"))

        label_display_names = {
            "mock_gun_threat": "Mock Gun Threat",
            "mock_knife_thrat": "Mock Knife Threat",
        }

        label = escape(label_display_names.get(raw_label, raw_label.replace("_", " ").title()))

        # displays cpnfidence as a percentage.
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
                <td><span class="badge">{label}</span></td>
                <td>{confidence}</td>
            </tr>
            """
        )
    # shows message when server is running but no alerts have arrived yet.
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
    <style>
        body{{
            font-family: Arial, sans-serif;
            background-color: #f4f6f8;
            margin: 0;
            padding: 30px;
            color: #222;
        }}

        .container{{
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 24px;
            border-radius: 10px;
        }}

        h1{{
        margin-bottom: 5px;
        }}

        .subtitle{{
            color: #555;
            margin-top: 0;
        }}

        table{{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }}

        th, td{{
            padding: 12px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }}

        th{{
            background-color: #222;
            color: white;
        }}

        tr:hover{{
            background-color: #f1f1f1;
        }}

        .badge{{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            background-color: #ffe0e0;
            color: #9b1c1c;
            font-weight: bold;
            font-size: 0.9em;
        }}

        .note{{
            color: #555;
            margin-top: 20px;
        }}
    </style>

    <div class="container">
        <h1>ThreatSense Fog Dashboard</h1>
        <p>Real-time alert monitoring from edge devices.</p>

        <table border="1" cellpadding="8" cellspacing="0">
            <tr>
                <th>Total Alerts</th>
                <th>Displayed Alerts</th>
                <th>Active Devices</th>
            </tr>
            <tr>
                <td>{len(alerts)}</td>
                <td>{displayed_alert_count}</td>
                <td>{active_devices}</td>
            </tr>
        </table>

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

    <p class="note">Dashboard auto-refreshes every 3 seconds.</p>
</div>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
