import base64
import binascii
import json
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from flask import Flask, jsonify, redirect, request, render_template

app = Flask(__name__)
ALERTS_FILE = Path("cloud/data/alerts.json")
IMAGE_DIR = Path("cloud/static/alerts")
ADMIN_CODE = "1234"
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT", "587")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
TEST_EMAIL_RECIPIENTS = ["mavil072@ucr.edu", "amaga084@ucr.edu"]
CLOUD_BASE_URL = "http://52.53.150.132:5001"
EMAIL_SUBJECT = "[ThreatSense Demo] Verified Mock Threat Alert"
ALERT_MERGE_WINDOW_SECONDS = float(os.getenv("ALERT_MERGE_WINDOW_SECONDS", "3"))
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
        existing_alert["image_url"] = incoming_alert.get("image_url")

    return existing_alert


def add_or_merge_alert(incoming_alert):
    for existing_alert in reversed(alerts):
        if is_merge_candidate(existing_alert, incoming_alert):
            return merge_alert(existing_alert, incoming_alert), True

    alerts.append(incoming_alert)
    return incoming_alert, False


def prepare_alert_for_review(alert):
    alert_id = f"{alert['device_id']}-{alert['timestamp']}"
    alert_id = alert_id.replace(" ", "-").replace(":", "").replace("/", "-")

    alert.setdefault("alert_id", alert_id)
    alert.setdefault("verification_status", "pending")
    alert.setdefault("verified_by", None)
    alert.setdefault("verified_at", None)
    alert.setdefault("email_status", "not_sent")
    alert.setdefault("merged_alert_count", 1)

    return alert


def save_alert_image(alert):
    image_data = alert.pop("image_data", None)
    if not image_data:
        return

    image_filename = alert.get("image_filename") or f"{alert['alert_id']}.jpg"
    image_filename = Path(image_filename).name
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        image_bytes = base64.b64decode(image_data, validate=True)
    except (binascii.Error, ValueError, TypeError):
        alert["image_error"] = "invalid base64 image data"
        return

    (IMAGE_DIR / image_filename).write_bytes(image_bytes)
    alert["image_filename"] = image_filename
    alert["image_url"] = f"/static/alerts/{image_filename}"


def load_logged_alerts():
    if not ALERTS_FILE.exists():
        return []

    with ALERTS_FILE.open() as alerts_file:
        try:
            loaded_alerts = json.load(alerts_file)
        except json.JSONDecodeError:
            return []

    if not isinstance(loaded_alerts, list):
        return []

    for alert in loaded_alerts:
        if isinstance(alert, dict) and not get_missing_fields(alert):
            prepare_alert_for_review(alert)

    return loaded_alerts


alerts = load_logged_alerts()


def save_alerts():
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with ALERTS_FILE.open("w") as alerts_file:
        json.dump(alerts, alerts_file, indent=2)


def build_demo_email_body(alert):
    location = alert.get("location") or "Demo location not specified"
    image_url = alert.get("image_url") or "No captured alert frame available"
    if image_url.startswith("/"):
        image_url = f"{CLOUD_BASE_URL}{image_url}"

    return f"""This is a ThreatSense demo/test notification.

A mock threat alert was verified as credible in the demo system.

Location:
{location}

Alert details:
- Alert ID: {alert.get("alert_id")}
- Device: {alert.get("device_id")}
- Camera: {alert.get("camera_id")}
- Object: {alert.get("object")}
- Threat Label: {alert.get("threat_label")}
- Confidence: {alert.get("confidence")}
- Timestamp: {alert.get("timestamp")}

Captured alert frame:
{image_url}

This is not an official UCR emergency notification.
Do not treat this as a real emergency alert."""


def send_demo_email(alert):
    if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL]):
        return "not_configured"

    message = EmailMessage()
    message["Subject"] = EMAIL_SUBJECT
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = ", ".join(TEST_EMAIL_RECIPIENTS)
    message.set_content(build_demo_email_body(alert))

    try:
        with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT), timeout=10) as smtp:
            if SMTP_USE_TLS:
                smtp.starttls()
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)
        return "sent"
    except Exception as error:
        return f"failed: {str(error)[:80]}"


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
        error=request.args.get("error"),
    )


@app.route("/cloud-alert", methods=["POST"])
def receive_cloud_alert():
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

    alert = prepare_alert_for_review(alert)
    save_alert_image(alert)
    dashboard_alert, was_merged = add_or_merge_alert(alert)
    save_alerts()
    print(f"Cloud alert received from {alert.get('device_id')}")
    if was_merged:
        print(
            "Merged cloud alert into event with "
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


@app.route("/verify/<alert_id>", methods=["POST"])
def verify_alert(alert_id):
    verification_status = request.form.get("verification_status")

    if verification_status not in {"credible", "not_credible"}:
        return jsonify({"error": "invalid verification status"}), 400

    admin_code = request.form.get("admin_code", "").strip()
    if admin_code != ADMIN_CODE:
        return redirect("/?error=invalid_admin_code")

    for alert in alerts:
        if alert.get("alert_id") == alert_id:
            alert["verification_status"] = verification_status
            alert["verified_by"] = "demo-admin"
            alert["verified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if (
                verification_status == "credible"
                and alert.get("email_status") != "sent"
            ):
                alert["email_status"] = send_demo_email(alert)
            save_alerts()
            return redirect("/")

    return jsonify({"error": "alert not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
