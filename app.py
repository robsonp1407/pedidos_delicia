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
    """Processa o formulário de pagamento e cria um pedido.

    Recebe os dados do comprador e as quantidades selecionadas, monta um
    objeto `Order` e dispara a notificação para o Telegram em background.
    """

    # Captura dados do comprador (nome/telefone) do formulário.
    buyer_name = request.form.get('buyer_name', '').strip()
    buyer_phone = request.form.get('buyer_phone', '').strip()

    # Cria o pedido (modelo de negócio)
    order = Order(buyer_name=buyer_name, buyer_phone=buyer_phone)

    # Percorre o catálogo de produtos e lê as quantidades do formulário.
    # O campo do formulário segue o padrão '<product_id>_qty'.
    for product_id, product in PRODUCTS.items():
        qty_raw = request.form.get(f'{product_id}_qty', '0')
        try:
            qty = int(qty_raw)
        except ValueError:
            # Caso o cliente envie algo inválido, tratamos como zero.
            qty = 0

        order.add_product(product, qty)

    # Envia notificação em background (não bloqueia a resposta HTTP).
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
