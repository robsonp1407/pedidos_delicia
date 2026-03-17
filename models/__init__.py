"""Pacote de models para a aplicação Edelicia.

Este pacote agrupa os modelos de domínio e a lógica de negócio (pedido,
produto e notificações). Ele permite que a camada de rota (Flask) importe
apenas o que precisa para compor a resposta HTTP.
"""

from .order import FlavorSelection, Order, OrderItem
from .product import Flavor, Product, PRODUCTS
from .telegram import notify_async

__all__ = [
    "Flavor",
    "FlavorSelection",
    "Order",
    "OrderItem",
    "Product",
    "PRODUCTS",
    "notify_async",
]
