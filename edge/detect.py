import cv2
import time
from ultralytics import YOLO

from alert_sender import send_alert
from config import (
    ALERT_COOLDOWN_SECONDS,
    CAMERA_ID,
    DEVICE_ID,
    MOCK_THREAT_CLASSES,
)

model = YOLO("yolov8n.pt")

CONFIDENCE_THRESHOLD = 0.30

# Keeps the box on screen briefly even if YOLO misses a frame
DETECTION_MEMORY_SECONDS = 1.0
last_detection = None
last_detection_time = 0
last_alert_time = 0


def main():
    global last_detection, last_detection_time, last_alert_time

    camera = cv2.VideoCapture(CAMERA_ID, cv2.CAP_AVFOUNDATION)

    if not camera.isOpened():
        print("Error: could not open webcam")
        return

    print("ThreatSense YOLO detection started. Press q to quit.")

    while True:
        ret, frame = camera.read()

        if not ret:
            print("Error: could not read frame")
            break

        results = model(frame, verbose=False)
        current_time = time.time()

        detection_found = False

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                detected_object = model.names[class_id]

                if detected_object in MOCK_THREAT_CLASSES and confidence >= CONFIDENCE_THRESHOLD:
                    mock_threat_label = MOCK_THREAT_CLASSES[detected_object]

                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

                    last_detection = {
                        "label": mock_threat_label,
                        "object": detected_object,
                        "confidence": confidence,
                        "box": (x1, y1, x2, y2)
                    }

                    last_detection_time = current_time
                    detection_found = True

                    print(
                        f"Detected {detected_object} as {mock_threat_label} "
                        f"with confidence {confidence:.2f}"
                    )

                    if current_time - last_alert_time >= ALERT_COOLDOWN_SECONDS:
                        alert_payload = {
                            "device_id": DEVICE_ID,
                            "camera_id": CAMERA_ID,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "object": detected_object,
                            "threat_label": mock_threat_label,
                            "confidence": round(confidence, 2),
                            "box": [x1, y1, x2, y2],
                        }

                        send_alert(alert_payload)
                        last_alert_time = current_time

        # Draw the most recent detection for a short time
        if last_detection and current_time - last_detection_time <= DETECTION_MEMORY_SECONDS:
            x1, y1, x2, y2 = last_detection["box"]
            label = last_detection["label"]
            confidence = last_detection["confidence"]

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            label_text = f"{label}: {confidence:.2f}"

            cv2.putText(
                frame,
                label_text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

        cv2.imshow("ThreatSense Mock Threat Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
