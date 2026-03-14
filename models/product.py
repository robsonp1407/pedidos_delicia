"""Modelos de domínio de produto.

Este módulo define o modelo de produto usado pela aplicação e mantém o catálogo
local de produtos disponíveis para compra.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Product:
    """Representa um produto disponível para venda."""

    id: str
    name: str
    price: float


# Catálogo de produtos disponível no sistema.
# A chave do dicionário é o identificador usado no formulário HTML.
PRODUCTS: Dict[str, Product] = {
    "pao_de_mel": Product(id="pao_de_mel", name="Pão de Mel", price=10.00),
    "brownie": Product(id="brownie", name="Brownie", price=12.00),
}
