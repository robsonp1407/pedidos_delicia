"""Modelos de domínio de produto.

Este módulo define o modelo de produto usado pela aplicação e mantém o catálogo
local de produtos disponíveis para compra.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
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
    active: bool = True


def load_products() -> Dict[str, Product]:
    """Carrega os produtos do arquivo products.json e retorna apenas os ativos."""
    products_path = Path(__file__).parent.parent / "products.json"
    with open(products_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    products = {}
    for product_id, product_data in data.items():
        if not product_data.get("active", True):
            continue
        
        flavors = [Flavor(**f) for f in product_data["flavors"]]
        coverings = [Covering(**c) for c in product_data["coverings"]]
        
        product = Product(
            id=product_data["id"],
            name=product_data["name"],
            price=product_data["price"],
            flavors=flavors,
            coverings=coverings,
            image_file=product_data["image_file"],
            active=product_data.get("active", True)
        )
        products[product_id] = product
    
    return products
