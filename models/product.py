"""Modelos de domínio de produto.

Este módulo define o modelo de produto usado pela aplicação e mantém o catálogo
local de produtos disponíveis para compra.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Covering:
    """Representa uma cobertura disponível para um produto."""

    name: str
    additional_price: float = 0.0


@dataclass(frozen=True)
class Flavor:
    """Representa um sabor/recheio disponível para um produto."""

    name: str
    additional_price: float = 0.0


@dataclass(frozen=True)
class Product:
    """Representa um produto disponível para venda."""

    id: str
    name: str
    price: float
    flavors: List[Flavor]
    coverings: List[Covering]
    image_file: str


# Catálogo de produtos disponível no sistema.
# A chave do dicionário é o identificador usado no formulário HTML.
PRODUCTS: Dict[str, Product] = {
    "pao_de_mel": Product(
        id="pao_de_mel",
        name="Pão de Mel",
        price=10.00,
        flavors=[
            Flavor(name="Doce de Leite", additional_price=0.0),
            Flavor(name="Brigadeiro", additional_price=0.0),
            Flavor(name="Brigadeiro de ninho", additional_price=1.0),           
        ],
        coverings=[
            Covering(name="Chocolate Preto", additional_price=0.0),
            Covering(name="Chocolate Branco", additional_price=0.5),
        ],
        image_file="paodemel.png",
    ),
    "brownie": Product(
        id="brownie",
        name="Brownie",
        price=12.00,
        flavors=[
            Flavor(name="Brigadeiro branco de ninho", additional_price=0.0),
            Flavor(name="Brigadeiro", additional_price=0.0),
            Flavor(name="Dois amores", additional_price=0.0),
            Flavor(name="Doce de leite", additional_price=1.5),
        ],
        coverings=[ ],
        image_file="brownie.png",
    ),
    "torta": Product(
        id="torta",
        name="Torta",
        price=15.00,
        flavors=[
            Flavor(name="Morango", additional_price=0.0),
            Flavor(name="Limão", additional_price=0.0),
        ],
        coverings=[],  # Sem coberturas
        image_file="Logo_delicia.jpg",
    ),
}
