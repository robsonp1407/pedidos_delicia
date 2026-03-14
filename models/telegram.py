"""Telegram notification helpers."""

import os
import threading
from typing import Optional

import requests


TELEGRAM_BOT_TOKEN: Optional[str] = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "8443861878:AAFYnujIgLAgC4htb2jUh6_cQNozkhXKxcM"
)
TELEGRAM_CHAT_ID: Optional[str] = os.environ.get("TELEGRAM_CHAT_ID", "8783789185")


def send_telegram_message(message: str) -> None:
    """Envia mensagem para o Telegram via Bot API."""
    if not TELEGRAM_BOT_TOKEN or "YOUR_TELEGRAM_BOT_TOKEN" in TELEGRAM_BOT_TOKEN:
        print("Telegram token não configurado, mensagem não enviada:", message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}

    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print("Falha ao enviar telegram:", e)


def notify_async(message: str) -> None:
    """Envia a mensagem em background para não bloquear a requisição."""

    thread = threading.Thread(target=send_telegram_message, args=(message,))
    thread.daemon = True
    thread.start()
