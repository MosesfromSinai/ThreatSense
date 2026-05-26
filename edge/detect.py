import cv2
import time
from ultralytics import YOLO

from alert_sender import add_frame_image, build_alert_payload, send_alert_async
from camera import open_camera
from config import (
    ALERT_COOLDOWN_SECONDS,
    CAMERA_ID,
    CONFIDENCE_THRESHOLD,
    DETECTION_MEMORY_SECONDS,
    DEVICE_ID,
    FOG_SERVER_URL,
    MOCK_THREAT_CLASSES,
)

model = YOLO("yolov8n.pt")

last_detection = None
last_detection_time = 0
last_alert_time = 0


def main():
    global last_detection, last_detection_time, last_alert_time

    camera = open_camera(CAMERA_ID)

    if not camera.isOpened():
        print(f"Error: could not open webcam at CAMERA_ID={CAMERA_ID}")
        return

    print("ThreatSense YOLO detection started. Press q to quit.")
    print(f"Device ID: {DEVICE_ID}")
    print(f"Camera ID: {CAMERA_ID}")
    print(f"Sending alerts to: {FOG_SERVER_URL}")

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

                if (
                    detected_object in MOCK_THREAT_CLASSES
                    and confidence >= CONFIDENCE_THRESHOLD
                ):
                    mock_threat_label = MOCK_THREAT_CLASSES[detected_object]

                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

                    last_detection = {
                        "label": mock_threat_label,
                        "object": detected_object,
                        "confidence": confidence,
                        "box": (x1, y1, x2, y2),
                    }

                    last_detection_time = current_time
                    detection_found = True

                    if current_time - last_alert_time >= ALERT_COOLDOWN_SECONDS:
                        alert_payload = build_alert_payload(
                            detected_object,
                            mock_threat_label,
                            confidence,
                            (x1, y1, x2, y2),
                        )
                        alert_payload = add_frame_image(alert_payload, frame)

                        print("-" * 50)
                        print("New ThreatSense alert")
                        print(
                            f"Detected {detected_object} as {mock_threat_label} "
                            f"with confidence {confidence:.2f}"
                        )
                        print(
                            f"Next alert available in {ALERT_COOLDOWN_SECONDS} seconds"
                        )
                        print("-" * 50)

                        send_alert_async(alert_payload)
                        last_alert_time = current_time

        # Draw the most recent detection for a short time
        if (
            last_detection
            and current_time - last_detection_time <= DETECTION_MEMORY_SECONDS
        ):
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
