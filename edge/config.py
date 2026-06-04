import os

DEVICE_ID = os.getenv("DEVICE_ID", "jetson-orin-01")
CAMERA_ID = int(os.getenv("CAMERA_ID", "0"))
FRAME_WIDTH = int(os.getenv("FRAME_WIDTH", "640"))
FRAME_HEIGHT = int(os.getenv("FRAME_HEIGHT", "480"))
CAMERA_FPS = int(os.getenv("CAMERA_FPS", "30"))
PROCESS_EVERY_N_FRAMES = int(os.getenv("PROCESS_EVERY_N_FRAMES", "2"))

FOG_SERVER_URL = os.getenv("FOG_SERVER_URL", "http://127.0.0.1:5001/alert")

ALERT_COOLDOWN_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 3
ALERT_RETRY_COUNT = 2
CONFIDENCE_THRESHOLD = 0.30
DETECTION_MEMORY_SECONDS = 1.0

MOCK_THREAT_CLASSES = {
    "banana": "mock_gun_threat",
    "carrot": "mock_knife_threat",
    "cucumber": "mock_knife_threat",
}
