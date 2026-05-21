import os
import hashlib
import hmac
import base64
import requests
from flask import Flask, request, abort

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
DIFY_API_KEY = os.environ.get("DIFY_API_KEY")
DIFY_BASE_URL = os.environ.get("DIFY_BASE_URL", "https://api.dify.ai/v1")

# ユーザーごとの会話IDを記憶する辞書
conversation_ids = {}

def verify_signature(body, signature):
    hash = hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(hash).decode() == signature

def get_dify_response(user_id, message):
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    conversation_id = conversation_ids.get(user_id, "")
    data = {
        "inputs": {},
        "query": message,
        "response_mode": "blocking",
        "conversation_id": conversation_id,
        "user": user_id
    }
    res = requests.post(f"{DIFY_BASE_URL}/chat-messages", headers=headers, json=data)
    result = res.json()
    new_conversation_id = result.get("conversation_id", "")
    if new_conversation_id:
        conversation_ids[user_id] = new_conversation_id
    return result.get("answer", "申し訳ありません。エラーが発生しました。")

def reply_to_line(reply_token, message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=data)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    if not verify_signature(body.encode(), signature):
        abort(400)
    events = request.json.get("events", [])
    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_id = event["source"]["userId"]
            message = event["message"]["text"]
            reply_token = event["replyToken"]
            answer = get_dify_response(user_id, message)
            reply_to_line(reply_token, answer)
    return "OK"

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
