from flask import Flask, jsonify, request

app = Flask(__name__)


@app.post("/profiles")
def create_profile():
    payload = request.get_json()
    name = payload.get("name")
    return jsonify({"profile": {"name": name}, "status": "created"}), 201
