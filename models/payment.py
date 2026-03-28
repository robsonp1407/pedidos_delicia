"""Módulo de integração com Mercado Pago para geração de códigos PIX.

Este módulo contém funções para gerar códigos PIX dinâmicos usando a API
oficial do Mercado Pago.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import mercadopago

if TYPE_CHECKING:
    from .order import Order


def extract_payment_id_from_mercadopago_notification(payload: Any) -> str | None:
    """Obtém o id do pagamento a partir do JSON de notificação (webhook / IPN)."""

    if not isinstance(payload, dict):
        return None

    data = payload.get("data")
    if isinstance(data, dict) and data.get("id") is not None:
        return str(data["id"])

    if payload.get("topic") == "payment" and payload.get("resource") is not None:
        return str(payload["resource"])

    return None


def fetch_mercado_pago_payment(payment_id: str) -> dict[str, Any] | None:
    """Consulta `GET /v1/payments/:id` via SDK. Retorna o corpo do pagamento ou None."""

    access_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")
    if not access_token:
        return None

    sdk = mercadopago.SDK(access_token)
    result = sdk.payment().get(payment_id)
    if not isinstance(result, dict):
        return None
    if result.get("status") and result.get("status") != 200:
        return None
    response = result.get("response")
    if not isinstance(response, dict):
        return None
    return response


def generate_pix_code(order: "Order", *, external_reference: str | None = None) -> str:
    """Gera um código PIX (Copia e Cola) para o pedido usando Mercado Pago.

    Args:
        order: Instância do pedido contendo os dados necessários.

    Returns:
        String com o código PIX ou string vazia em caso de erro.

    Raises:
        Nenhum erro é propagado; em caso de falha, retorna string vazia
        e imprime o erro no console.
    """
    try:
        # Lê o token de acesso da variável de ambiente
        access_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")
        if not access_token:
            raise ValueError("MERCADO_PAGO_ACCESS_TOKEN não definido nas variáveis de ambiente")

        # Inicializa o SDK do Mercado Pago
        sdk = mercadopago.SDK(access_token)

        # Cria o payload de pagamento (external_reference liga o PIX ao pedido no banco)
        payment_data = {
            "transaction_amount": float(order.total),
            "payment_method_id": "pix",
            "payer": {
                "first_name": order.buyer_name,
                "email": order.buyer_email or "contato@deliciaprodutosartesanais.com.br"
            },
        }
        if external_reference:
            payment_data["external_reference"] = external_reference

        # Faz a requisição para criar o pagamento
        payment_response = sdk.payment().create(payment_data)
        payment = payment_response["response"]

        # Extrai o código PIX do nó point_of_interaction.transaction_data.qr_code
        qr_code = payment["point_of_interaction"]["transaction_data"]["qr_code"]

        return qr_code

    except Exception as e:
        print(f"Erro ao gerar código PIX: {e}")
        return ""