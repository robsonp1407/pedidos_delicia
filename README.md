# Edelicia (Flask)

Aplicação web simples de checkout/pedido com envio de notificação via Telegram.

## 🧱 Arquitetura

A aplicação segue uma estrutura **MVC / Layered Architecture**:

- **`app.py`**: Controlador (rotas Flask) — recebe requisições, monta o pedido e renderiza templates.
- **`models/`**: Camada de negócio (Model) — contém lógica de pedido, produtos e notificação.
  - `models/product.py` — definição de `Product` e catálogo (`PRODUCTS`).
  - `models/order.py` — lógica de pedido (`Order`, cálculo, geração de mensagem).
  - `models/telegram.py` — integração com a API de Telegram.

## 🍨 Suporte a Sabores/Recheios

A partir desta versão, os produtos suportam variações de sabores com preços adicionais opcionais.

### Estrutura do Produto (JSON-like)

Cada produto no catálogo (`PRODUCTS`) agora inclui uma lista de `flavors`:

```json
{
  "id": "pao_de_mel",
  "name": "Pão de Mel",
  "price": 10.00,
  "flavors": [
    {"name": "Doce de Leite", "additional_price": 0.0},
    {"name": "Brigadeiro", "additional_price": 2.0}
  ]
}
```

### Lógica de Pedido

- Um `OrderItem` (anteriormente `OrderLine`) pode conter múltiplas seleções de sabores.
- Cálculo: `(preço_base + preço_adicional_do_sabor) * quantidade_do_sabor`
- Validação: Sabores devem pertencer ao produto selecionado.

### Classes Atualizadas

- `Flavor`: Representa um sabor com preço adicional opcional.
- `Product`: Agora inclui `flavors: List[Flavor]`.
- `FlavorSelection`: Seleção de sabor + quantidade.
- `OrderItem`: Substitui `OrderLine`, agrupa seleções por produto.
- `Order`: Usa `items: List[OrderItem]` em vez de `lines`.

## 🚀 Como rodar

1. Crie e ative um ambiente virtual (recomendado):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instale dependências:

```powershell
pip install -r requirements.txt
```

3. Execute a aplicação:

```powershell
python app.py
```

A aplicação ficará disponível em `http://127.0.0.1:5000/`.

## 🧩 Configuração de Telegram

Para enviar notificações reais via Telegram, informe as variáveis de ambiente:

- `TELEGRAM_BOT_TOKEN`: token do bot (obtido via BotFather)
- `TELEGRAM_CHAT_ID`: chat_id do canal/grupo onde as notificações serão enviadas

Exemplo (PowerShell):

```powershell
$env:TELEGRAM_BOT_TOKEN = "seu_token_aqui"
$env:TELEGRAM_CHAT_ID = "seu_chat_id_aqui"
python app.py
```

Caso não seja configurado, o aplicativo apenas loga a mensagem e não faz a chamada HTTP.

## 🧪 Testes rápidos

- Abra a página inicial e selecione quantidades de produto.
- Preencha nome e telefone, envie o formulário.
- O template `checkout.html` mostrará o total e o código PIX simulado.

## 🧭 Estrutura de pastas

```
edelicia/
├─ app.py
├─ models/
│  ├─ __init__.py
│  ├─ order.py
│  ├─ product.py
│  └─ telegram.py
├─ static/
│  ├─ css/
│  ├─ img/
│  └─ js/
└─ templates/
   ├─ checkout.html
   └─ index.html
```
