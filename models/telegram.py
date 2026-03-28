"""Helpers de notificação via Telegram.

Este módulo encapsula a lógica de envio de mensagens para o Telegram usando a
API de bots. O objetivo é manter o envio de notificações separado da lógica de
pedido, permitindo testes e manutenção mais fáceis.
"""

import os
import threading
from typing import Optional

import requests


# Tokens e IDs podem ser sobrescritos via variáveis de ambiente para não hardcodear
# valores sensíveis no código.
#TELEGRAM_BOT_TOKEN: Optional[str] = os.environ.get("TELEGRAM_BOT_TOKEN")
#TELEGRAM_CHAT_ID: Optional[str] = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram_message(message: str) -> None:
    """Envia mensagem para o Telegram via Bot API.

    Caso o token não esteja configurado, apenas escreve um log e não faz a
    chamada HTTP.    
    """
    TELEGRAM_BOT_TOKEN: Optional[str] = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.environ.get("TELEGRAM_CHAT_ID")

    if not TELEGRAM_BOT_TOKEN or "YOUR_TELEGRAM_BOT_TOKEN" in TELEGRAM_BOT_TOKEN:
        print("Telegram token não configurado, mensagem não enviada:", message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}

    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        # Erros de rede não devem quebrar o fluxo principal da aplicação.
        print("Falha ao enviar telegram:", e)


def notify_async(message: str) -> None:
    """Envia a mensagem em background para não bloquear a requisição."""

    thread = threading.Thread(target=send_telegram_message, args=(message,))
    thread.daemon = True
    thread.start()
