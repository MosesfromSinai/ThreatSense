import requests

from config import (
    CLOUD_FORWARDING_ENABLED,
    CLOUD_REQUEST_TIMEOUT_SECONDS,
    CLOUD_SERVER_URL,
)


def forward_alert_to_cloud(alert):
    if not CLOUD_FORWARDING_ENABLED:
        return False

    try:
        response = requests.post(
            CLOUD_SERVER_URL,
            json=alert,
            timeout=CLOUD_REQUEST_TIMEOUT_SECONDS,
        )
        if 200 <= response.status_code < 300:
            print("Alert forwarded to cloud")
            return True
        print(f"Cloud server returned status code {response.status_code}")
    except requests.RequestException as error:
        print(f"Could not forward alert to cloud: {error}")

    return False
