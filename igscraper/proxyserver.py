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

@app.route("/service", methods=["POST"])
def service():
    """Service endpoint to forward directly to the Instagram API"""
    cmd = request.json.get("command", None)
    if cmd is None:
        return jsonify({"status": "error", "reason": "no command provided"})
    ip = request.remote_addr
    client = api.clients.get(ip)
    if client is None:
        client = api.InstagramAPI()
        api.clients[ip] = client
    resp = api.execute(cmd, client)
    return jsonify({"status": "success", "api_response": resp})

@app.route("/restart", methods=["POST"])
def restart():
    """Endpoint to reset the API class state"""
    client = api.clients.get(request.remote_addr)
    if client is not None:
        client[request.remote_addr] = InstagramAPI()
    return jsonify({"status": "success", "api_response": {"status": "success"}})

@app.route("/", methods=["GET"])
def index():
    return "<h1>Hello World!</h1>"


if __name__ == "__main__" and "--local" in sys.argv:
    app.run(debug=True, port=9102)