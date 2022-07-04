from sqlite3 import IntegrityError

from flask import Flask, render_template, request
import repository
import traceback

app = Flask(__name__)


# Endpoints
@app.route("/", methods=["GET"])
def index():
    return render_template("dashboard.html")


@app.route("/devices", methods=["POST"])
def create_device():
    payload = request.json
    name = payload.get("name")
    password = payload.get("password")

    if name is None or type(name) is not str or not (0 <= len(name.strip()) <= 32):
        return "Invalid name", 400
    if password is None or type(password) is not str or not (0 <= len(password.strip()) <= 65535):
        return "Invalid password", 400

    try:
        device = repository.create_device(name, password)
        return device, 201
    except IntegrityError:
        return "Device already exists", 422
    except Exception:
        print(traceback.format_exc())
        return "Internal server error", 500


@app.route("/devices/", methods=["GET"])
def find_all_devices():
    try:
        devices = repository.find_all_devices()
        return devices, 200
    except Exception:
        print(traceback.format_exc())
        return "Internal server error", 500


@app.route("/devices/<deviceId>", methods=["GET"])
def find_device(deviceId=None):
    return repository.find_device_by_id(deviceId)


@app.route("/devices/<deviceId>/settings", methods=["GET"])
def find_device_settings(deviceId=None):
    return repository.find_device_settings(deviceId)


@app.route("/devices/<deviceId>/captures", methods=["GET"])
def find_device_captures(deviceId=None):
    return repository.find_device_settings(deviceId)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
