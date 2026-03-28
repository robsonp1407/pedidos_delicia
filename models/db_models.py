"""Modelos ORM (SQLAlchemy) para persistência em PostgreSQL.

Este módulo define as tabelas relacionais da aplicação. Ele convive com os
modelos de domínio em `order.py` e `product.py` (JSON/lógica de negócio);
importe explicitamente de `models.db_models` quando for trabalhar com o banco.

Convenções:
    - Nomes de tabela no plural em inglês (`products`, `orders`, `freight_cache`).
    - Valores monetários em `Numeric` para precisão decimal.
    - `status` do pedido: apenas os valores documentados na classe `Order`.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from extensions import db


class OrderStatus(str, enum.Enum):
    """Estados possíveis de um pedido no banco."""

    pendente = "pendente"
    pago = "pago"
    cancelado = "cancelado"


class Product(db.Model):
    """Catálogo persistido: produto vendável com preço e mídia."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    image_file: Mapped[str | None] = mapped_column(String(512), nullable=True)

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r}>"


class Order(db.Model):
    """Pedido do cliente: dados de contato, entrega e totais."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buyer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    buyer_phone: Mapped[str] = mapped_column(String(64), nullable=False)
    buyer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_method: Mapped[str] = mapped_column(String(64), nullable=False)
    delivery_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    cep: Mapped[str | None] = mapped_column(String(10), nullable=True)
    freight_value: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    total_value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", native_enum=True),
        nullable=False,
        default=OrderStatus.pendente,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} status={self.status!s}>"


class FreightCache(db.Model):
    """Cache de distância por CEP para reduzir chamadas à API de roteamento."""

    __tablename__ = "freight_cache"

    cep_destination: Mapped[str] = mapped_column(String(10), primary_key=True)
    distance_km: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<FreightCache cep={self.cep_destination!r}>"
