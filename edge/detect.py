import cv2
from ultralytics import YOLO

# Load YOLOv8 nano model.
# The first time you run this, it may automatically download yolov8n.pt.
model = YOLO("yolov8n.pt")

# Safe demo objects that we will treat as mock threats.
# Pretrained YOLOv8 can detect "banana".
# Cucumber is not usually a built-in YOLO class, so we can add it later after custom training.
MOCK_THREAT_MAP = {
    "banana": "mock_gun_threat"
}

CONFIDENCE_THRESHOLD = 0.40


def main():
    # MacBook camera backend
    camera = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

    if not camera.isOpened():
        print("Error: could not open webcam")
        return

    print("ThreatSense YOLO detection started. Press q to quit.")

    while True:
        ret, frame = camera.read()

        if not ret:
            print("Error: could not read frame")
            break

        # Run YOLO detection on the current frame
        results = model(frame, verbose=False)

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                detected_object = model.names[class_id]

                # Check if detected object is one of our safe mock threat objects
                if detected_object in MOCK_THREAT_MAP and confidence >= CONFIDENCE_THRESHOLD:
                    mock_threat_label = MOCK_THREAT_MAP[detected_object]

                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

                    # Draw bounding box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # Display mock threat label instead of banana
                    label_text = f"{mock_threat_label}: {confidence:.2f}"

                    cv2.putText(
                        frame,
                        label_text,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                    print(
                        f"Detected {detected_object} as {mock_threat_label} "
                        f"with confidence {confidence:.2f}"
                    )

        cv2.imshow("ThreatSense Mock Threat Detection", frame)

        # Press q to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()