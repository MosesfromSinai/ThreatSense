import json
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, render_template

from cloud_forwarder import forward_alert_to_cloud
from config import ALERT_MERGE_WINDOW_SECONDS

app = Flask(__name__)
LOG_FILE = Path("data/logs/alerts.jsonl")
REQUIRED_ALERT_FIELDS = [
    "device_id",
    "camera_id",
    "timestamp",
    "object",
    "threat_label",
    "confidence",
    "bbox",
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


def save_alerts():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOG_FILE.open("w") as log_file:
        for alert in alerts:
            log_file.write(json.dumps(alert) + "\n")


def parse_alert_timestamp(alert):
    try:
        return datetime.strptime(alert["timestamp"], "%Y-%m-%d %H:%M:%S")
    except (KeyError, TypeError, ValueError):
        return None


def get_alert_device_ids(alert):
    device_ids = alert.get("device_ids")
    if isinstance(device_ids, list):
        return device_ids

    device_id = alert.get("device_id")
    if device_id:
        return [device_id]

    return []


def is_merge_candidate(existing_alert, incoming_alert):
    if existing_alert.get("object") != incoming_alert.get("object"):
        return False

    if existing_alert.get("threat_label") != incoming_alert.get("threat_label"):
        return False

    incoming_device = incoming_alert.get("device_id")
    if not incoming_device or incoming_device in get_alert_device_ids(existing_alert):
        return False

    existing_timestamp = parse_alert_timestamp(existing_alert)
    incoming_timestamp = parse_alert_timestamp(incoming_alert)
    if not existing_timestamp or not incoming_timestamp:
        return False

    time_delta = abs((incoming_timestamp - existing_timestamp).total_seconds())
    return time_delta <= ALERT_MERGE_WINDOW_SECONDS


def merge_alert(existing_alert, incoming_alert):
    device_ids = get_alert_device_ids(existing_alert)
    incoming_device = incoming_alert.get("device_id")
    if incoming_device and incoming_device not in device_ids:
        device_ids.append(incoming_device)

    existing_alert["device_ids"] = device_ids
    existing_alert["device_id"] = ", ".join(device_ids)
    existing_alert["merged_alert_count"] = len(device_ids)
    existing_alert["merged_within_seconds"] = ALERT_MERGE_WINDOW_SECONDS

    existing_confidence = float(existing_alert.get("confidence", 0))
    incoming_confidence = float(incoming_alert.get("confidence", 0))

    if incoming_confidence > existing_confidence:
        existing_alert["confidence"] = incoming_confidence
        existing_alert["camera_id"] = incoming_alert.get("camera_id")
        existing_alert["bbox"] = incoming_alert.get("bbox")
        existing_alert["image_filename"] = incoming_alert.get("image_filename")

    return existing_alert


def add_or_merge_alert(incoming_alert):
    for existing_alert in reversed(alerts):
        if is_merge_candidate(existing_alert, incoming_alert):
            return merge_alert(existing_alert, incoming_alert), True

    alerts.append(incoming_alert)
    return incoming_alert, False


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

    local_alert = alert.copy()
    local_alert.pop("image_data", None)

    dashboard_alert, was_merged = add_or_merge_alert(local_alert)
    if was_merged:
        save_alerts()
    else:
        log_alert(dashboard_alert)

    forward_alert_to_cloud(alert)
    print(
        f"Alert received from {alert.get('device_id')}: "
        f"{alert.get('threat_label')}"
    )
    if was_merged:
        print(
            "Merged alert into dashboard event with "
            f"{dashboard_alert['merged_alert_count']} devices"
        )

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
        for device_id in get_alert_device_ids(alert) or ["unknown"]:
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
    displayed_alert_count = min(len(alerts), 10)

    active_devices = len(
        {
            device_id
            for alert in alerts
            for device_id in get_alert_device_ids(alert) or ["unknown"]
        }
    )

    return render_template(
        "dashboard.html",
        alerts=list(reversed(alerts[-10:])),
        total_alerts=len(alerts),
        displayed_alert_count=displayed_alert_count,
        active_devices=active_devices,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
