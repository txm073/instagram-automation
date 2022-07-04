from flask import Flask, request, url_for, jsonify
import os, sys
import api

app = Flask(__name__)

@app.route("/service", methods=["POST"])
def service():
    auth = request.form.get("auth", None)
    if auth != os.getenv("AUTH_KEY"):
        return jsonify({"status": "error", "reason": "bad authorisation"})
    cmd = request.form.get("command", None)
    if cmd is None:
        return jsonify({"status": "error", "reason": "no command provided"})
    stdout = api.execute(cmd)
    return jsonify({"status": "success", "output": stdout})


if __name__ == "__main__" and "--local" in sys.argv:
    app.run(debug=True)