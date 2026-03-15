from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import base64
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ================== ENV VARIABLES ==================

CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
PASSKEY = os.getenv("MPESA_PASSKEY")
SHORTCODE = os.getenv("MPESA_SHORTCODE")

CALLBACK_URL = os.getenv(
    "CALLBACK_URL",
    "https://spherespike-credit.onrender.com/api/mpesa/callback"
)

# Safaricom endpoints
TOKEN_URL = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
STK_PUSH_URL = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

# ===================================================


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "OK", "service": "MPESA DARAKA BACKEND RUNNING"}), 200


# ================== ACCESS TOKEN ==================

def get_access_token():

    response = requests.get(
        TOKEN_URL,
        auth=(CONSUMER_KEY, CONSUMER_SECRET)
    )

    return response.json()["access_token"]


# ================== STK PUSH ==================

@app.route("/api/stk-push", methods=["POST"])
def stk_push():

    data = request.get_json()

    phone = data.get("phone")
    amount = data.get("amount")

    if not phone or not amount:
        return jsonify({"error": "phone and amount required"}), 400

    access_token = get_access_token()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password_str = SHORTCODE + PASSKEY + timestamp
    password = base64.b64encode(password_str.encode()).decode()

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": "OkoaChapaa",
        "TransactionDesc": "Payment"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        STK_PUSH_URL,
        json=payload,
        headers=headers
    )

    return jsonify(response.json()), response.status_code


# ================== CALLBACK ==================

@app.route("/api/mpesa/callback", methods=["POST"])
def mpesa_callback():

    data = request.get_json()

    print("==== MPESA CALLBACK RECEIVED ====")
    print(data)

    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)