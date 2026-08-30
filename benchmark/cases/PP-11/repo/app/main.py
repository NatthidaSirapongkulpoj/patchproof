from flask import Flask, jsonify, request

app = Flask(__name__)
ACCOUNTS = {1: {"id": 1, "display_name": "Nora", "notifications": "daily"}}
VALID_FREQUENCIES = {"never", "daily", "weekly"}


def reset_accounts() -> None:
    ACCOUNTS.clear()
    ACCOUNTS[1] = {"id": 1, "display_name": "Nora", "notifications": "daily"}


@app.get("/accounts/<int:account_id>")
def get_account(account_id: int):
    account = ACCOUNTS.get(account_id)
    if account is None:
        return jsonify({"error": "account not found"}), 404
    return jsonify({"account": account})


@app.patch("/accounts/<int:account_id>")
def update_account(account_id: int):
    account = ACCOUNTS.get(account_id)
    if account is None:
        return jsonify({"error": "account not found"}), 404
    payload = request.get_json()
    if "display_name" in payload:
        account["display_name"] = payload["display_name"]
    if "notifications" in payload and payload["notifications"] not in VALID_FREQUENCIES:
        return jsonify({"error": "invalid notification frequency"}), 400
    if "notifications" in payload:
        account["notifications"] = payload["notifications"]
    return jsonify({"account": account})
