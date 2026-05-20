from datetime import datetime
from threading import Thread

import requests

from config import (
    ALERT_RETRY_COUNT,
    CAMERA_ID,
    DEVICE_ID,
    FOG_SERVER_URL,
    REQUEST_TIMEOUT_SECONDS,
)


def build_alert_payload(detected_object, threat_label, confidence, box):
    return {
        "device_id": DEVICE_ID,
        "camera_id": CAMERA_ID,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "object": detected_object,
        "threat_label": threat_label,
        "confidence": round(float(confidence), 2),
        "box": [int(value) for value in box],
    }


def send_alert(alert_payload):
    for attempt in range(ALERT_RETRY_COUNT):
        try:
            response = requests.post(
                FOG_SERVER_URL,
                json=alert_payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            if 200 <= response.status_code < 300:
                print("Alert sent to fog server")
                return True

            print(f"Fog server returned status code {response.status_code}")

        except requests.RequestException as error:
            print(f"Alert send attempt {attempt + 1} failed: {error}")

    print("Alert was not sent to fog server")
    return False


def send_alert_async(alert_payload):
    alert_thread = Thread(target=send_alert, args=(alert_payload,), daemon=True)
    alert_thread.start()


if __name__ == "__main__":
    test_alert = build_alert_payload(
        "banana",
        "mock_gun_threat",
        0.95,
        (100, 100, 300, 300),
    )

    send_alert(test_alert)
