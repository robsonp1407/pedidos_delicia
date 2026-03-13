from flask import Flask, render_template, request, redirect, url_for
import threading
import requests

app = Flask(__name__)

# Dicionário de produtos
products = {
    'pao_de_mel': {'name': 'Pão de Mel', 'price': 10.00},
    'brownie': {'name': 'Brownie', 'price': 12.00}
}

# Frete fixo
FRETE = 5.00

# --- Telegram configuration (replace with your bot token) ---
import os
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8443861878:AAFYnujIgLAgC4htb2jUh6_cQNozkhXKxcM')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '8783789185')  # destinatário


def send_telegram_message(message: str):
    """Envia mensagem para o Telegram via Bot API."""
    if not TELEGRAM_BOT_TOKEN or 'YOUR_TELEGRAM_BOT_TOKEN' in TELEGRAM_BOT_TOKEN:
        # não configurado; apenas log
        print('Telegram token não configurado, mensagem não enviada:', message)
        return
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print('Falha ao enviar telegram:', e)


# dispara em segundo plano

def notify_async(message: str):
    thread = threading.Thread(target=send_telegram_message, args=(message,))
    thread.daemon = True
    thread.start()

@app.route('/')
def index():
    # Renderiza o catálogo de produtos
    return render_template('index.html', products=products)

@app.route('/pagamento', methods=['POST'])
def pagamento():
    # Recebe dados do formulário via POST
    buyer_name = request.form.get('buyer_name', '').strip()
    buyer_phone = request.form.get('buyer_phone', '').strip()

    total = 0.0
    order_lines = []
    for product_id, product in products.items():
        qty = int(request.form.get(product_id + '_qty', 0))
        if qty > 0:
            total += product['price'] * qty
            order_lines.append(f"{product['name']} x {qty} = R$ {product['price'] * qty:.2f}")
    
    # Adiciona frete
    subtotal = total + FRETE

    # prepara mensagem para telegram
    message = f"<b>Novo pedido</b>\n"
    message += f"Nome: {buyer_name}\n"
    message += f"Telefone: {buyer_phone}\n"
    message += "Produtos:\n"
    for line in order_lines:
        message += f"- {line}\n"
    message += f"Frete: R$ {FRETE:.2f}\n"
    message += f"Total: R$ {subtotal:.2f}"

    notify_async(message)

    # Simulação de Pix Copia e Cola (código fictício)
    pix_code = "00020101021126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-42665544000052040000530398654040.005802BR5913Fulano de Tal6008BRASILIA62070503***6304E2CA"
    
    # Renderiza a página de checkout com o total e o código Pix
    # encaminha informações do comprador para a view (opcional)
    return render_template('checkout.html', subtotal=subtotal, pix_code=pix_code,
                           buyer_name=buyer_name, buyer_phone=buyer_phone)

if __name__ == '__main__':
    app.run(debug=True)