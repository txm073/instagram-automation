from flask import Flask, request, jsonify
from accountcreator import create_account
import os

app = Flask(__name__)

@app.route("/service", methods=["POST"])
def service():
    if request.json["auth"] != os.getenv("HEROKUAPP_AUTH_KEY"):
        return jsonify({"status": "error"})
    account_creds, status = create_account()
    return jsonify({"status": "success"})
