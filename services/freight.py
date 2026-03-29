"""Motor de regras de frete: cache, Google Distance Matrix e tabelas de preço.

Requer contexto de aplicação Flask ativo (`app.app_context()`) para acessar o
SQLAlchemy (`db.session`).

Variáveis de ambiente:
    MAPS_API_KEY — chave da Google Maps Distance Matrix API.
    WHATSAPP_URL (opcional) — link `https://wa.me/55...` exibido na mensagem de fallback.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import requests

from extensions import db
from models.db_models import FreightCache

# Endereço da confeitaria (origem das rotas). Ajuste cidade/UF se o geocode falhar.
BAKERY_ORIGIN = "Rua Capitão Leônidas Marques, 2410, Brasil"

GOOGLE_DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
REQUEST_TIMEOUT_S = 12

MIN_CHECKOUT_SUBTOTAL = Decimal("25.00")
FREE_SHIPPING_SUBTOTAL = Decimal("50.00")

# Faixas em km (valores da API convertidos de metros): (máximo inclusivo, preço)
_DISTANCE_PRICE_RULES: tuple[tuple[float, Decimal], ...] = (
    (3.0, Decimal("6.90")),
    (6.0, Decimal("9.90")),
    (10.0, Decimal("13.90")),
)

DEFAULT_ESTIMATED_TIME_CACHE = "40-60 min"
DEFAULT_ESTIMATED_TIME_FALLBACK = "40-60 min"
PICKUP_ESTIMATED_TIME = "Retirada no local"


class ForaDaAreaEntregaError(Exception):
    """Distância acima do limite de entrega (regra de negócio)."""

    def __init__(self, message: str = "Fora da área de entrega") -> None:
        super().__init__(message)


class PedidoMinimoNaoAtingidoError(Exception):
    """Subtotal abaixo do mínimo para finalizar o pedido."""

    def __init__(
        self,
        message: str = (
            "O valor mínimo do pedido para checkout é R$ 25,00. "
            "Adicione mais itens ao carrinho."
        ),
    ) -> None:
        super().__init__(message)


class FreteIndisponivelError(Exception):
    """Falha na API de mapas ou resposta inválida — orientar contato humano."""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = _fallback_whatsapp_message()
        super().__init__(message)


@dataclass(frozen=True)
class FreightCalculationResult:
    """Resultado do cálculo de frete para a camada de apresentação."""

    freight_value: float
    estimated_time: str


def _fallback_whatsapp_message() -> str:
    base = (
        "Não foi possível calcular o frete no momento. "
        "Entre em contato pelo WhatsApp para finalizar seu pedido."
    )
    url = (os.environ.get("WHATSAPP_URL") or "").strip()
    if url:
        return f"{base} {url}"
    return base


def _normalize_subtotal(subtotal: Decimal | float | str) -> Decimal:
    if isinstance(subtotal, Decimal):
        return subtotal.quantize(Decimal("0.01"))
    return Decimal(str(subtotal)).quantize(Decimal("0.01"))


def normalize_cep_key(cep_destino: str) -> str:
    """Retorna 8 dígitos (sem hífen) para uso como chave em `FreightCache`."""

    digits = re.sub(r"\D", "", (cep_destino or "").strip())
    if len(digits) != 8:
        raise ValueError("CEP inválido. Informe 8 dígitos.")
    return digits


def _cep_for_google(cep_key: str) -> str:
    return f"{cep_key[:5]}-{cep_key[5:]}, Brasil"


def _freight_amount_for_distance_km(distance_km: float) -> Decimal:
    """Aplica a tabela 0–3 / 3,1–6 / 6,1–10 km; acima disso levanta ForaDaAreaEntregaError."""

    if distance_km < 0:
        raise FreteIndisponivelError("Distância retornada inválida. Tente novamente.")

    if distance_km > 10.0:
        raise ForaDaAreaEntregaError()

    for max_km, price in _DISTANCE_PRICE_RULES:
        if distance_km <= max_km:
            return price

    raise ForaDaAreaEntregaError()


def _fetch_distance_from_google(cep_key: str) -> tuple[float, str]:
    """Chama Distance Matrix; retorna (distância_km, texto_duração) ou levanta FreteIndisponivelError."""

    api_key = (os.environ.get("MAPS_API_KEY") or "").strip()
    if not api_key:
        raise FreteIndisponivelError()

    params = {
        "origins": BAKERY_ORIGIN,
        "destinations": _cep_for_google(cep_key),
        "units": "metric",
        "language": "pt-BR",
        "key": api_key,
    }

    try:
        response = requests.get(
            GOOGLE_DISTANCE_MATRIX_URL,
            params=params,
            timeout=REQUEST_TIMEOUT_S,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise FreteIndisponivelError() from exc

    status = payload.get("status")
    if status != "OK":
        raise FreteIndisponivelError()

    rows = payload.get("rows") or []
    if not rows:
        raise FreteIndisponivelError()

    elements = rows[0].get("elements") or []
    if not elements:
        raise FreteIndisponivelError()

    element = elements[0]
    el_status = element.get("status")
    if el_status != "OK":
        raise FreteIndisponivelError()

    distance = element.get("distance") or {}
    duration = element.get("duration") or {}

    meters = distance.get("value")
    if meters is None or not isinstance(meters, (int, float)):
        raise FreteIndisponivelError()

    distance_km = float(meters) / 1000.0
    duration_text = (duration.get("text") or "").strip() or DEFAULT_ESTIMATED_TIME_FALLBACK

    return distance_km, duration_text


def _persist_freight_cache(cep_key: str, distance_km: float) -> None:
    """Grava ou atualiza a distância em `freight_cache`."""

    row = db.session.get(FreightCache, cep_key)
    if row is None:
        row = FreightCache(cep_destination=cep_key, distance_km=distance_km)
        db.session.add(row)
    else:
        row.distance_km = distance_km

    db.session.commit()


def _resolve_distance_km_and_eta(
    cep_key: str,
) -> tuple[float, str, bool]:
    """
    Obtém distância e texto de tempo estimado.

    Retorna:
        (distance_km, estimated_time, from_cache)
    """

    cached = db.session.get(FreightCache, cep_key)
    if cached is not None and cached.distance_km is not None:
        return float(cached.distance_km), DEFAULT_ESTIMATED_TIME_CACHE, True

    distance_km, eta_text = _fetch_distance_from_google(cep_key)
    _persist_freight_cache(cep_key, distance_km)
    return distance_km, eta_text, False


def calculate_freight(
    cep_destino: str,
    subtotal: Decimal | float | str,
    delivery_method: str = "Entrega",
) -> FreightCalculationResult:
    """
    Calcula frete e tempo estimado conforme regras de negócio.

    Args:
        cep_destino: CEP do cliente (com ou sem hífen). Ignorado se `delivery_method` for retirada.
        subtotal: Total dos itens antes do frete.
        delivery_method: ``\"Entrega\"`` ou ``\"Retirada\"`` (mesma convenção do formulário).

    Returns:
        FreightCalculationResult com ``freight_value`` (float, 2 casas) e ``estimated_time``.

    Raises:
        PedidoMinimoNaoAtingidoError: subtotal < R$ 25,00 (apenas para entrega).
        ForaDaAreaEntregaError: distância > 10 km.
        FreteIndisponivelError: falha de API / chave / resposta inválida (mensagem com WhatsApp).
        ValueError: CEP inválido em modo entrega.
    """

    method = (delivery_method or "").strip()
    subtotal_dec = _normalize_subtotal(subtotal)

    if method == "Retirada":
        return FreightCalculationResult(
            freight_value=0.0,
            estimated_time=PICKUP_ESTIMATED_TIME,
        )

    if method != "Entrega":
        raise ValueError(
            'Método de entrega desconhecido. Use "Entrega" ou "Retirada".'
        )

    if subtotal_dec < MIN_CHECKOUT_SUBTOTAL:
        raise PedidoMinimoNaoAtingidoError()

    cep_key = normalize_cep_key(cep_destino)

    distance_km, estimated_time, _from_cache = _resolve_distance_km_and_eta(cep_key)

    if distance_km > 10.0:
        raise ForaDaAreaEntregaError()

    if subtotal_dec >= FREE_SHIPPING_SUBTOTAL:
        freight_dec = Decimal("0.00")
    else:
        freight_dec = _freight_amount_for_distance_km(distance_km)

    freight_float = float(freight_dec.quantize(Decimal("0.01")))

    return FreightCalculationResult(
        freight_value=freight_float,
        estimated_time=estimated_time,
    )
