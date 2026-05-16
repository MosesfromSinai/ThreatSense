DEVICE_ID = "jetson-nano-01"
CAMERA_ID = 0

FOG_SERVER_URL = "http://192.168.1.36:5000/alert"

ALERT_COOLDOWN_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 3

MOCK_THREAT_CLASSES = {
    "banana": "mock_gun_threat",
    "cucumber": "mock_knife_threat",
}
