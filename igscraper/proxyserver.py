"""
Google Colab cannot access the Instagram API directly therefore
https://instagram-automation-sand.vercel.app/service acts as a proxy server
and forwards a command (in a JSON format) to the InstagramAPI class found in ./api.py
which will return a JSON response to the proxy server and back to the user
"""

from flask import Flask, request, jsonify
import os, sys

from igscraper import api

app = Flask(__name__)

@app.route("/service", methods=["GET", "POST"])
def service():
    """Service endpoint to forward directly to the Instagram API"""
    auth = request.json.get("auth", None)
    if auth != os.getenv("PROXYSERVER_AUTH_KEY"): # stored on the web server
        return jsonify({"status": "error", "reason": "bad authorisation"})
    cmd = request.json.get("command", None)
    if cmd is None:
        return jsonify({"status": "error", "reason": "no command provided"})
    resp = api.execute(cmd)
    return jsonify({"status": "success", "api_response": resp})

@app.route("/", methods=["GET"])
def index():
    return "<h1>Hello World!</h1>"


if __name__ == "__main__" and "--local" in sys.argv:
    app.run(debug=True, port=9102)