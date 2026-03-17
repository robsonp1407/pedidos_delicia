"""Modelos de domínio de pedido.

Este módulo concentra a lógica de negócio relacionada à criação e
manipulação de pedidos (Order) e itens de pedido (OrderItem).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .product import Flavor, Product


# Valor fixo do frete aplicado a cada pedido.
FRETE = 5.00


@dataclass
class FlavorSelection:
    """Seleção de um sabor específico com quantidade."""

    flavor: Flavor
    quantity: int

    @property
    def selection_total(self) -> float:
        """Total desta seleção: (preço base + adicional) * quantidade."""
        return (self.flavor.additional_price) * self.quantity


@dataclass
class OrderItem:
    """Um item de pedido (produto com seleções de sabores)."""

    product: Product
    flavor_selections: List[FlavorSelection] = field(default_factory=list)

    def add_flavor_selection(self, flavor: Flavor, quantity: int) -> None:
        """Adiciona uma seleção de sabor ao item.

        Valida se o sabor pertence ao produto.
        """
        if flavor not in self.product.flavors:
            raise ValueError(f"Sabor '{flavor.name}' não disponível para o produto '{self.product.name}'.")

        if quantity <= 0:
            return

        self.flavor_selections.append(FlavorSelection(flavor=flavor, quantity=quantity))

    @property
    def total_quantity(self) -> int:
        """Quantidade total de unidades neste item."""
        return sum(fs.quantity for fs in self.flavor_selections)

    @property
    def item_total(self) -> float:
        """Total deste item: soma de (preço base + adicional) * qty para cada seleção."""
        return sum(
            (self.product.price + fs.flavor.additional_price) * fs.quantity
            for fs in self.flavor_selections
        )

    def format_item(self) -> str:
        """Retorna uma representação formatada do item para relatórios."""
        if not self.flavor_selections:
            return f"{self.product.name} (sem sabores) = R$ {self.item_total:.2f}"

        details = []
        for fs in self.flavor_selections:
            price_per_unit = self.product.price + fs.flavor.additional_price
            details.append(f"{fs.flavor.name} x {fs.quantity} (R$ {price_per_unit:.2f} cada)")

        return f"{self.product.name}: {', '.join(details)} = R$ {self.item_total:.2f}"


@dataclass
class Order:
    """Representa um pedido realizado pelo cliente."""

    buyer_name: str
    buyer_phone: str
    items: List[OrderItem] = field(default_factory=list)

    def add_item(self, product: Product) -> OrderItem:
        """Cria e adiciona um novo item ao pedido."""
        item = OrderItem(product=product)
        self.items.append(item)
        return item

    @property
    def subtotal(self) -> float:
        """Total dos produtos sem frete."""
        return sum(item.item_total for item in self.items)

    @property
    def total(self) -> float:
        """Total do pedido incluindo frete."""
        return self.subtotal + FRETE

    def build_telegram_message(self) -> str:
        """Gera a mensagem de notificação enviada ao Telegram.

        A mensagem segue um formato simples em texto puro com marcação HTML
        mínima para negrito, o que facilita a leitura no chat.
        """
        item_lines = "\n".join(f"- {item.format_item()}" for item in self.items)

        return (
            f"<b>Novo pedido</b>\n"
            f"Nome: {self.buyer_name}\n"
            f"Telefone: {self.buyer_phone}\n"
            f"Produtos:\n{item_lines}\n"
            f"Frete: R$ {FRETE:.2f}\n"
            f"Total: R$ {self.total:.2f}"
        )
