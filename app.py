from flask import Flask, render_template, request

from models.order import Order
from models.product import PRODUCTS
from models.telegram import notify_async


app = Flask(__name__)


@app.route('/')
def index() -> str:
    """Renderiza o catálogo de produtos."""

    return render_template('index.html', products=PRODUCTS)


@app.route('/pagamento', methods=['POST'])
def pagamento() -> str:
    """Processa o formulário de pagamento e cria um pedido."""

    buyer_name = request.form.get('buyer_name', '').strip()
    buyer_phone = request.form.get('buyer_phone', '').strip()

    order = Order(buyer_name=buyer_name, buyer_phone=buyer_phone)

    for product_id, product in PRODUCTS.items():
        qty_raw = request.form.get(f'{product_id}_qty', '0')
        try:
            qty = int(qty_raw)
        except ValueError:
            qty = 0

        order.add_product(product, qty)

    notify_async(order.build_telegram_message())

    # Simulação de Pix Copia e Cola (código fictício)
    pix_code = (
        "00020101021126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-42665544000052040000530398654040.005802BR5913Fulano de Tal6008BRASILIA62070503***6304E2CA"
    )

    # Renderiza a página de checkout com o total e o código Pix
    return render_template(
        'checkout.html',
        subtotal=order.total,
        pix_code=pix_code,
        buyer_name=buyer_name,
        buyer_phone=buyer_phone,
    )


if __name__ == '__main__':
    app.run(debug=True)
