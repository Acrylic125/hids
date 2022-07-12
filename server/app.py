import os
from sqlite3 import IntegrityError
from datetime import datetime
import uuid
from flask import Flask, render_template, request, send_file
import repository
import traceback
from werkzeug.utils import secure_filename

from os.path import join, dirname, realpath

UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'uploads/')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


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
        return {"ok": False, "message": "Invalid name"}, 400
    if password is None or type(password) is not str or not (0 <= len(password.strip()) <= 65535):
        return {"ok": False, "message": "Invalid password"}, 400

    try:
        device = repository.create_device(name, password)
        return {"ok": True, "data": device}, 201
    except IntegrityError:
        return {"ok": False, "message": "Device already exists"}, 422
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "message": "Internal server error"}, 500


@app.route("/devices", methods=["GET"])
def find_all_devices():
    try:
        devices = repository.find_all_devices()
        return {"ok": True, "data": devices}, 200
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "message": "Internal server error"}, 500


@app.route("/devices/<deviceId>", methods=["GET"])
def find_device(deviceId=None):
    try:
        device = repository.find_device_by_id(deviceId)
        if device is None:
            return {"ok": False, "message": "Device Not Found"}, 404
        else:
            return {"ok": True, "data": device}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "message": "Internal server error"}, 500


@app.route("/devices/<deviceId>/settings", methods=["GET"])
def find_device_settings(deviceId=None):
    try:
        device_settings = repository.find_device_settings(deviceId)
        if device_settings is None:
            return {"ok": False, "message": "settings for device could not be found or it does not exist"}, 404
        else:
            return {"ok": True, "data": device_settings}, 200
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "message": "Internal server error"}, 500


@app.route("/devices/<deviceId>/captures", methods=["GET"])
def find_device_captures(deviceId=None):
    try:
        device_captures = repository.find_device_captures(deviceId)
        if device_captures is None:
            return {"ok": False, "message": "Device does not have any captures"}, 200
        else:
            return {"ok": True, "data": device_captures}, 200
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "message": "Internal server error"}, 500


@app.route("/devices/<deviceId>/settings", methods=["PUT"])
def update_device_settings(deviceId):
    payload = request.json

    try:
        result = repository.update_device_settings(deviceId, payload)
        if result is False:
            return {"ok": False, "message": "Device failed to update"}, 400
        else:
            return {"ok": True, "data": {}}
    except IntegrityError:
        return {"ok": False, "message": "Device does not exist"}, 422
    except ValueError as e:
        return {"ok": False, "message": str(e)}, 400
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "message": "Internal server error"}, 500


@app.route("/users/<userId>/devices", methods=["POST"])
def create_user_device(userId):
    payload = request.json
    name = payload.get("name")
    password = payload.get("password")
    try:
        device = repository.find_device_by_credentials(name, password)
        if device is None:
            return {"ok": False, "message": "Invalid device credentials"}, 404
        userDevice = repository.add_device_to_user(userId, device["id"])
        return {"ok": True, "data": userDevice}, 201
    except IntegrityError:
        print(traceback.format_exc())
        return {"ok": False, "message": "Device already added to user, or device or user does not exist"}, 422
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "message": "Internal server error"}, 500


@app.route("/users/<userId>/devices", methods=["GET"])
def find_user_devices(userId):
    try:
        device = repository.find_all_devices_for_user(userId)
        return {"ok": True, "data": device}, 200
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "message": "Internal server error"}, 500


def upload_file(file, filename=None):
    if filename is None:
        filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename


@app.route("/devices/<deviceId>/captures", methods=["POST"])
def create_device_capture(deviceId):
    # payload = request.json
    if 'file' not in request.files:
        return {"ok": False, "message": "No file part"}, 400

    file = request.files.get("file")
    filename = file.filename
    if filename == '':
        return {"ok": False, "message": "No file selected"}, 400
    if '.' not in filename:
        return {"ok": False, "message": "No file extension"}, 400

    file_extension = filename.rsplit('.', 1)[1]

    if file_extension.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        return {"ok": False, "message": "File type not allowed"}, 400
    uploaded_filename = upload_file(file, secure_filename(str(uuid.uuid4()) + "." + file_extension))

    try:
        result = repository.add_device_capture(deviceId, uploaded_filename, datetime.timestamp(datetime.now()))
        return {"ok": True, "data": result}, 201
    except IntegrityError:
        return {"ok": False, "message": "Device does not exist"}, 422
    except ValueError as e:
        return {"ok": False, "message": str(e)}, 400
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "message": "Internal server error"}, 500


@app.route("/capture-images/<image_loc>")
def find_device_capture_image(image_loc):
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_loc)
    if os.path.isfile(image_path):
        return send_file(image_path), 200
    else:
        return {"ok": False, "message": "Image does not exist"}, 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
