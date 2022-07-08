from flask import render_template, url_for, request, jsonify, redirect
from webapp import app, client
from instagrapi.exceptions import *

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", ip=request.remote_addr, data={"name": "Tom"})

@app.route("/api/get-data", methods=["POST"])
def api_get_data():
    user = request.json.get("user")
    _type = request.json.get("type")
    if not user:
        return jsonify({"status": "error", "reason": "Enter a username"})
    elif not _type:
        return jsonify({"status": "error", "reason": "Specify a type - (following or followers)"})
    print(f"Getting {_type} for {user!r}")
    try:
        info = client.user_info_by_username(user)
    except LoginRequired:
        if not client.relogin():
            return jsonify({"status": "error", "reason": "Instagram authentication failed"})
        info = client.user_info_by_username(user)
    except (ClientNotFoundError, UserNotFound):
        return jsonify({"status": "error", "reason": "User not found"})
    print(info)
    if info.is_private:
        return jsonify({"status": "error", "reason": "User account is private"})
    return jsonify({"status": "success"})

