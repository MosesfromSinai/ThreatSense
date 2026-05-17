from datetime import datetime

import requests

from config import CAMERA_ID, DEVICE_ID, FOG_SERVER_URL, REQUEST_TIMEOUT_SECONDS


def send_alert(alert_payload):
    for attempt in range(2):
        try:
            response = requests.post(
                FOG_SERVER_URL,
                json=alert_payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            if response.status_code == 200:
                print("Alert sent to fog server")
                return True

            print(f"Fog server returned status code {response.status_code}")

        except requests.RequestException as error:
            print(f"Alert send attempt {attempt + 1} failed: {error}")

    print("Alert was not sent to fog server")
    return False


if __name__ == "__main__":
    test_alert = {
        "device_id": DEVICE_ID,
        "camera_id": CAMERA_ID,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "object": "banana",
        "threat_label": "mock_gun_threat",
        "confidence": 0.95,
        "box": [100, 100, 300, 300],
    }

    send_alert(test_alert)
