import os
import hashlib
import hmac
import requests
from flask import Flask, request, abort

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
DIFY_API_KEY = os.environ.get("DIFY_API_KEY")
DIFY_BASE_URL = os.environ.get("DIFY_BASE_URL", "https://api.dify.ai/v1")

def verify_signature(body, signature):
    hash = hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    import base64
    return base64.b64encode(hash).decode() == signature

def get_dify_response(user_id, message):
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": {},
        "query": message,
        "response_mode": "blocking",
        "conversation_id": "",
        "user": user_id
    }
    res = requests.post(f"{DIFY_BASE_URL}/chat-messages", headers=headers, json=d
