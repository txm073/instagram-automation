from flask import Flask, request, jsonify
from selenium import webdriver
import os

app = Flask(__name__)

@app.route("/service", methods=["POST"])
def service():
    return jsonify({"status": "success"})

