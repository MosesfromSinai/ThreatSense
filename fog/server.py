from flask import Flask, jsonify, request

app = Flask(__name__)
alerts = []


@app.route("/alert", methods=["POST"])
def receive_alert():
    alert = request.get_json()

    if not alert:
        return jsonify({"error": "missing JSON alert"}), 400

    alerts.append(alert)
    print(f"Alert received from {alert.get('device_id')}: {alert.get('threat_label')}")

    return jsonify({"status": "received"}), 200


@app.route("/alerts", methods=["GET"])
def list_alerts():
    return jsonify({
        "count": len(alerts),
        "alerts": alerts,
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
