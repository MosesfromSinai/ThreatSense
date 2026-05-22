import os
import time

import requests

FOG_ALERTS_URL = os.getenv("FOG_ALERTS_URL", "http://127.0.0.1:5001/alerts")


def main():
    print("ThreatSense terminal dashboard started. Press Ctrl+C to stop.")

    while True:
        try:
            response = requests.get(FOG_ALERTS_URL, timeout=3)
            data = response.json()

            print("\nRecent alerts:")
            for alert in data.get("alerts", [])[-5:]:
                print(
                    f"{alert.get('timestamp')} | {alert.get('device_id')} | "
                    f"{alert.get('threat_label')} | {alert.get('confidence')}"
                )

        except requests.RequestException as error:
            print(f"Could not reach fog server: {error}")

        time.sleep(3)


if __name__ == "__main__":
    main()
