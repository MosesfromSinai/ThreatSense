from flask import Flask

app = Flask(__name__)


@app.route("/", methods=["GET"])
def dashboard():
    return "ThreatSense cloud server running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
