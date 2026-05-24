import base64
from datetime import datetime
from threading import Thread

import cv2
import requests

from config import (
    ALERT_RETRY_COUNT,
    CAMERA_ID,
    DEVICE_ID,
    FOG_SERVER_URL,
    REQUEST_TIMEOUT_SECONDS,
)


def resize_alert_frame(frame, max_width=640):
    height, width = frame.shape[:2]
    if width <= max_width:
        return frame

    scale = max_width / width
    new_size = (max_width, int(height * scale))
    return cv2.resize(frame, new_size)


def build_alert_payload(detected_object, threat_label, confidence, box):
    x1, y1, x2, y2 = [int(value) for value in box]
    timestamp = datetime.now()
    alert_id = f"{DEVICE_ID}-{timestamp.strftime('%Y%m%d-%H%M%S')}"

    return {
        "alert_id": alert_id,
        "device_id": DEVICE_ID,
        "camera_id": CAMERA_ID,
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "object": detected_object,
        "threat_label": threat_label,
        "confidence": round(float(confidence), 2),
        "bbox": {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
        },
        "image_filename": f"{alert_id}.jpg",
    }


def add_frame_image(alert_payload, frame):
    frame = frame.copy()
    bbox = alert_payload["bbox"]
    x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
    label = f"{alert_payload['threat_label']}: {alert_payload['confidence']:.2f}"

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(
        frame,
        label,
        (x1, max(y1 - 10, 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
    )
    frame = resize_alert_frame(frame)

    success, encoded_frame = cv2.imencode(
        ".jpg",
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), 60],
    )

    if not success:
        print("Could not encode alert frame")
        return alert_payload

    alert_payload["image_data"] = base64.b64encode(encoded_frame).decode("utf-8")
    return alert_payload


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
