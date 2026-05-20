import time
import requests

FOG_ALERTS_URL = "http://127.0.0.1:5001/alerts"
FOG_HEALTH_URL = "http://127.0.0.1:5001/health"
POLL_INTERVAL_SECONDS = 3
RECENT_ALERT_COUNT = 5

def print_separator():
    print("-" * 70)

def print_alert(alert):
    timestamp = alert.get("timestamp", "unknown")
    device_id = alert.get("device_id", "unknown")
    camera_id = alert.get("camera_id", "unknown")
    threat_label = alert.get("threat_label", "unknown")
    detected_object = alert.get("object", "unknown")
    confidence = alert.get("confidence", 0)
 
    print(
        f"  [{timestamp}] {device_id} | cam:{camera_id} | "
        f"{detected_object} -> {threat_label} | conf:{confidence:.2f}"
    )

def main():
    print("ThreatSense terminal dashboard started. Press Ctrl+C to stop.")
    print_separator()

    while True:
        try:
            health_response = requests.get(FOG_HEALTH_URL, timeout=3)
            health = health_response.json()
            total_alerts = health.get("alert_count", 0)
 
            alerts_response = requests.get(FOG_ALERTS_URL, timeout=3)
            data = alerts_response.json()
            recent_alerts = data.get("alerts", [])[-RECENT_ALERT_COUNT:]
 
            print(f"\nFog server status: running | Total alerts logged: {total_alerts}")
            print(f"Last {RECENT_ALERT_COUNT} alerts:")
            print_separator()
 
            if recent_alerts:
                for alert in recent_alerts:
                    print_alert(alert)
            else:
                print("  No alerts received yet.")
 
            print_separator()
 
        except requests.RequestException as error:
            print(f"Could not reach fog server: {error}")
 
        time.sleep(POLL_INTERVAL_SECONDS)
