import json
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
LOG_FILE = Path("cloud/data/alerts.jsonl")


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


def log_alert(alert):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOG_FILE.open("a") as log_file:
        log_file.write(json.dumps(alert) + "\n")


@app.route("/", methods=["GET"])
def dashboard():
    return "ThreatSense cloud server running"


@app.route("/cloud-alert", methods=["POST"])
def receive_cloud_alert():
    alert = request.get_json()

    if not alert:
        return jsonify({"error": "missing JSON alert"}), 400

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
