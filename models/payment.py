"""Módulo de integração com Mercado Pago para geração de códigos PIX.

Este módulo contém funções para gerar códigos PIX dinâmicos usando a API
oficial do Mercado Pago.
"""

import os
from typing import TYPE_CHECKING

import mercadopago

if TYPE_CHECKING:
    from .order import Order


def generate_pix_code(order: "Order") -> str:
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

        # Cria o payload de pagamento
        payment_data = {
            "transaction_amount": float(order.total),
            "payment_method_id": "pix",
            "payer": {
                "first_name": order.buyer_name,
                "email": order.buyer_email or "contato@deliciaprodutosartesanais.com.br"
            }
        }

        # Faz a requisição para criar o pagamento
        payment_response = sdk.payment().create(payment_data)
        payment = payment_response["response"]

        # Extrai o código PIX do nó point_of_interaction.transaction_data.qr_code
        qr_code = payment["point_of_interaction"]["transaction_data"]["qr_code"]

        return qr_code

    except Exception as e:
        print(f"Erro ao gerar código PIX: {e}")
        return ""