"""Modelos de domínio de pedido.

Este módulo concentra a lógica de negócio relacionada à criação e
manipulação de pedidos (Order) e linhas de pedido (OrderLine).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .product import Product


# Valor fixo do frete aplicado a cada pedido.
FRETE = 5.00


@dataclass
class OrderLine:
    """Uma linha de pedido (produto + quantidade)."""

    product: Product
    quantity: int

    @property
    def line_total(self) -> float:
        """Retorna o total desta linha de pedido."""
        return self.product.price * self.quantity

    def format_line(self) -> str:
        """Retorna uma linha formatada para apresentação em relatórios ou mensagens."""

        # Formato esperado pela view e pela mensagem de Telegram
        return f"{self.product.name} x {self.quantity} = R$ {self.line_total:.2f}"


@dataclass
class Order:
    """Representa um pedido realizado pelo cliente."""

    buyer_name: str
    buyer_phone: str
    lines: List[OrderLine] = field(default_factory=list)

    def add_product(self, product: Product, quantity: int) -> None:
        """Adiciona um produto ao pedido com a quantidade especificada.

        Se a quantidade for menor ou igual a zero, este método não altera o pedido.
        """
        if quantity <= 0:
            return

        self.lines.append(OrderLine(product=product, quantity=quantity))

    @property
    def subtotal(self) -> float:
        """Total dos produtos sem frete."""
        return sum(line.line_total for line in self.lines)

    @property
    def total(self) -> float:
        """Total do pedido incluindo frete."""
        return self.subtotal + FRETE

    def build_telegram_message(self) -> str:
        """Gera a mensagem de notificação enviada ao Telegram.

        A mensagem segue um formato simples em texto puro com marcação HTML
        mínima para negrito, o que facilita a leitura no chat.
        """
        order_lines = "\n".join(f"- {line.format_line()}" for line in self.lines)

        return (
            f"<b>Novo pedido</b>\n"
            f"Nome: {self.buyer_name}\n"
            f"Telefone: {self.buyer_phone}\n"
            f"Produtos:\n{order_lines}\n"
            f"Frete: R$ {FRETE:.2f}\n"
            f"Total: R$ {self.total:.2f}"
        )
