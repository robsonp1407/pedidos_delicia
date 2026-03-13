from flask import Flask, render_template, request

app = Flask(__name__)

# Dicionário de produtos
products = {
    'pao_de_mel': {'name': 'Pão de Mel', 'price': 5.00},
    'brownie': {'name': 'Brownie', 'price': 8.00}
}

# Frete fixo
FRETE = 5.00

@app.route('/')
def index():
    # Renderiza o catálogo de produtos
    return render_template('index.html', products=products)

@app.route('/pagamento', methods=['POST'])
def pagamento():
    # Recebe dados do formulário via POST
    total = 0.0
    for product_id, product in products.items():
        qty = int(request.form.get(product_id + '_qty', 0))
        total += product['price'] * qty
    
    # Adiciona frete
    subtotal = total + FRETE
    
    # Simulação de Pix Copia e Cola (código fictício)
    pix_code = "00020101021126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-42665544000052040000530398654040.005802BR5913Fulano de Tal6008BRASILIA62070503***6304E2CA"
    
    # Renderiza a página de checkout com o total e o código Pix
    return render_template('checkout.html', subtotal=subtotal, pix_code=pix_code)

if __name__ == '__main__':
    app.run(debug=True)