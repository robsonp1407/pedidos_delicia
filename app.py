"""Aplicação web principal usando Flask.

Este módulo define as rotas da aplicação e atua como controlador (controller)
entre as views (templates) e a camada de negócio (models).

A lógica de negócio (cálculo de totais, geração de mensagens, etc.) está
contida em `models/` para manter a aplicação organizada seguindo o padrão MVC.
"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from extensions import db
from models.order import Order
from models.payment import (
    extract_payment_id_from_mercadopago_notification,
    fetch_mercado_pago_payment,
    generate_pix_code,
)
from models.product import load_products
from models.telegram import notify_async, send_telegram_message
from services.freight import (
    ForaDaAreaEntregaError,
    FreteIndisponivelError,
    PedidoMinimoNaoAtingidoError,
    calculate_freight,
)


load_dotenv()

app = Flask(__name__)

from urllib.parse import quote_plus

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise RuntimeError("Variáveis de banco não configuradas corretamente")

DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
#app.config["SQLALCHEMY_DATABASE_URI"] = _database_url
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Registra metadados das tabelas ORM no SQLAlchemy (import após db.init_app).
from models import db_models  # noqa: E402, F401


@app.route('/')
def index() -> str:
    """Rota principal que mostra o catálogo de produtos.

    O template `index.html` usa o dicionário `PRODUCTS` para renderizar as opções
    disponíveis no formulário de pedido.
    """

    return render_template('index.html', products=load_products())


@app.route('/api/calcula_frete', methods=['POST'])
def api_calcula_frete():
    """Calcula frete para o carrinho (CEP + subtotal). Usado pelo drawer no index."""

    payload = request.get_json(silent=True) or {}
    cep = (payload.get('cep') or '').strip()
    delivery_method = (payload.get('delivery_method') or 'Entrega').strip()

    raw_subtotal = payload.get('subtotal')
    if raw_subtotal is None:
        return jsonify({'ok': False, 'error': 'Informe o subtotal do pedido.'}), 400
    try:
        subtotal = float(raw_subtotal)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'Subtotal inválido.'}), 400

    if delivery_method == 'Retirada':
        return jsonify(
            {
                'ok': True,
                'freight_value': 0.0,
                'estimated_time': 'Retirada no local',
            }
        )

    try:
        result = calculate_freight(cep, subtotal, delivery_method=delivery_method)
    except PedidoMinimoNaoAtingidoError as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 400
    except ForaDaAreaEntregaError as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 422
    except (FreteIndisponivelError, ValueError) as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 503

    return jsonify(
        {
            'ok': True,
            'freight_value': result.freight_value,
            'estimated_time': result.estimated_time,
        }
    )


@app.route('/pagamento', methods=['POST'])
def pagamento() -> str:
    """Processa o formulário de pagamento e cria um pedido."""

    buyer_name = request.form.get('buyer_name', '').strip()
    buyer_phone = request.form.get('buyer_phone', '').strip()
    buyer_email = request.form.get('buyer_email', '').strip()
    delivery_method = request.form.get('delivery_method', 'Retirada')
    delivery_address = request.form.get('delivery_address', '').strip()
    buyer_cep = request.form.get('buyer_cep', '').strip()
    delivery_fee = 0.0

    order = Order(
        buyer_name=buyer_name,
        buyer_phone=buyer_phone,
        buyer_email=buyer_email,
        delivery_method=delivery_method,
        delivery_address=delivery_address,
        delivery_fee=delivery_fee,
    )

    cart_json = request.form.get('cart_items', '[]')
    try:
        import json
        cart_items = json.loads(cart_json)
    except (ValueError, TypeError):
        cart_items = []

    for entry in cart_items:
        product_id = entry.get('product_id')
        product = load_products().get(product_id)
        if not product:
            continue

        item = order.add_item(product)

        covering_name = entry.get('covering')
        if covering_name and product.coverings:
            covering = next((c for c in product.coverings if c.name == covering_name), None)
            if covering:
                item.covering = covering

        for flavor_sel in entry.get('flavors', []):
            flavor_name = flavor_sel.get('name')
            qty = int(flavor_sel.get('qty', 0))
            if qty <= 0:
                continue
            flavor = next((f for f in product.flavors if f.name == flavor_name), None)
            if flavor:
                item.add_flavor_selection(flavor, qty)

    if delivery_method == 'Entrega':
        try:
            quote = calculate_freight(buyer_cep, order.total, delivery_method='Entrega')
            delivery_fee = quote.freight_value
        except (
            PedidoMinimoNaoAtingidoError,
            ForaDaAreaEntregaError,
            FreteIndisponivelError,
            ValueError,
        ) as exc:
            return render_template(
                'index.html',
                products=load_products(),
                freight_checkout_error=str(exc),
            )

    order.delivery_fee = delivery_fee

    cep_db = None
    if delivery_method == 'Entrega' and buyer_cep:
        cep_db = buyer_cep.strip()[:10]

    db_order = db_models.Order(
        buyer_name=buyer_name,
        buyer_phone=buyer_phone,
        buyer_email=buyer_email or None,
        delivery_method=delivery_method,
        delivery_address=delivery_address or None,
        cep=cep_db,
        freight_value=delivery_fee,
        total_value=order.total,
        status=db_models.OrderStatus.pendente,
    )
    db.session.add(db_order)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    notify_async(order.build_telegram_message())

    pix_code = generate_pix_code(order, external_reference=str(db_order.id))

    return render_template(
        'checkout.html',
        subtotal=order.total,
        delivery_method=delivery_method,
        delivery_address=delivery_address,
        delivery_fee=delivery_fee,
        pix_code=pix_code,
        buyer_name=buyer_name,
        buyer_phone=buyer_phone,
        items=order.items,
    )


@app.route('/webhook/mercadopago', methods=['POST'])
def webhook_mercadopago():
    """Recebe notificações do Mercado Pago e marca o pedido como pago quando o PIX é aprovado."""

    try:
        body = request.get_json(silent=True) or {}
        payment_id = extract_payment_id_from_mercadopago_notification(body)
        if not payment_id:
            return '', 200

        payment = fetch_mercado_pago_payment(payment_id)
        if not payment:
            return '', 200

        if (payment.get('status') or '').lower() != 'approved':
            return '', 200

        ext_ref = (payment.get('external_reference') or '').strip()
        if not ext_ref.isdigit():
            return '', 200

        order_id = int(ext_ref)
        row = db.session.get(db_models.Order, order_id)
        if row is None:
            return '', 200

        if row.status == db_models.OrderStatus.pago:
            return '', 200

        row.status = db_models.OrderStatus.pago
        db.session.commit()

        send_telegram_message(
            f'✅ PAGAMENTO CONFIRMADO! Pedido #{order_id} liberado para produção!'
        )
    except Exception as exc:
        db.session.rollback()
        print(f'Webhook Mercado Pago: {exc}')

    return '', 200


if __name__ == '__main__':
    app.run(debug=True)
