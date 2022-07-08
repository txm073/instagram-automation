from flask import Flask, render_template, url_for, request, jsonify, redirect
from instagrapi import Client

client = Client()
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", ip=request.remote_addr)

@app.route("/api/get-data", methods=["POST"])
def api_get_data():
    user = request.json.get("user")
    _type = request.json.get("type")
    if not user:
        return jsonify({"status": "error", "reason": "Enter a username"})
    elif not _type:
        return jsonify({"status": "error", "reason": "Specify a type - (following or followers)"})
    info = client.user_info_by_username(user)
    if info["is_private"]:
        return jsonify({"status": "error", "reason": "User account is private"})
    return jsonify({"status": "success"})

def login(username, pwd):
    client.login(username, pwd)