import requests

from config import FOG_SERVER_URL, REQUEST_TIMEOUT_SECONDS


def send_alert(alert_payload):
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
        return False

    except requests.RequestException as error:
        print(f"Could not send alert to fog server: {error}")
        return False
