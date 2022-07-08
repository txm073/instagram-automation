from flask import Flask, render_template, url_for, request, jsonify, redirect

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", ip=request.remote_addr)

@app.route("/api", methods=["POST"])
def api_index():
    return jsonify()