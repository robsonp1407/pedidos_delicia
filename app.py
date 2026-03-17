"""Aplicação web principal usando Flask.

Este módulo define as rotas da aplicação e atua como controlador (controller)
entre as views (templates) e a camada de negócio (models).

A lógica de negócio (cálculo de totais, geração de mensagens, etc.) está
contida em `models/` para manter a aplicação organizada seguindo o padrão MVC.
"""

from flask import Flask, render_template, request

from models.order import Order
from models.product import PRODUCTS
from models.telegram import notify_async


app = Flask(__name__)


@app.route('/')
def index() -> str:
    """Rota principal que mostra o catálogo de produtos.

    O template `index.html` usa o dicionário `PRODUCTS` para renderizar as opções
    disponíveis no formulário de pedido.
    """

    return render_template('index.html', products=PRODUCTS)


@app.route('/pagamento', methods=['POST'])
def pagamento() -> str:
    """Processa o formulário de pagamento e cria um pedido."""

    buyer_name = request.form.get('buyer_name', '').strip()
    buyer_phone = request.form.get('buyer_phone', '').strip()
    delivery_method = request.form.get('delivery_method', 'Retirada')
    delivery_address = request.form.get('delivery_address', '').strip()
    delivery_fee = 0.0

    if delivery_method == 'Entrega':
        delivery_fee = 5.00

    order = Order(
        buyer_name=buyer_name,
        buyer_phone=buyer_phone,
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
        product = PRODUCTS.get(product_id)
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

    notify_async(order.build_telegram_message())

    pix_code = (
        "00020101021126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-42665544000052040000530398654040.005802BR5913Fulano de Tal6008BRASILIA62070503***6304E2CA"
    )

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


if __name__ == '__main__':
    app.run(debug=True)
