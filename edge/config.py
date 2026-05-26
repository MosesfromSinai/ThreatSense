import os

DEVICE_ID = os.getenv("DEVICE_ID", "jetson-orin-01")
CAMERA_ID = int(os.getenv("CAMERA_ID", "0"))

FOG_SERVER_URL = os.getenv("FOG_SERVER_URL", "http://127.0.0.1:5001/alert")

ALERT_COOLDOWN_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 3
ALERT_RETRY_COUNT = 2
CONFIDENCE_THRESHOLD = 0.30
DETECTION_MEMORY_SECONDS = 1.0

MOCK_THREAT_CLASSES = {
    "banana": "mock_gun_threat",
    "carrot": "mock_knife_threat",
    "scissors": "mock_knife_threat",
}
