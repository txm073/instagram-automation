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
    #binary = os.path.join(os.getcwd(), "api.exe")
    #print(f"Invoking executable {binary!r} with command: {cmd}")
    #proc = subprocess.Popen([binary, cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = api.execute(cmd)
    #stdout = proc.stdout.read().decode()
    #stderr = proc.stderr.read().decode()
    return jsonify({"status": "success", "stdout": stdout})


if __name__ == "__main__" and "--local" in sys.argv:
    app.run(debug=True)