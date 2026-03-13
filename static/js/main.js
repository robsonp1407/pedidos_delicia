// JavaScript para máscara de telefone, modal de revisão e envio

// máscara de telefone simples
function maskPhone(value) {
    // remove non-digit
    let digits = value.replace(/\D/g, '');
    if (digits.length > 11) digits = digits.slice(0,11);
    let formatted = '';
    if (digits.length > 0) {
        formatted += '(' + digits.substring(0,2);
    }
    if (digits.length >= 3) {
        formatted += ') ' + digits.substring(2,7);
    }
    if (digits.length >= 8) {
        formatted += '-' + digits.substring(7);
    }
    return formatted;
}

window.addEventListener('DOMContentLoaded', () => {
    const phoneInput = document.getElementById('buyer_phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', (e) => {
            e.target.value = maskPhone(e.target.value);
        });
    }

    const reviewBtn = document.getElementById('reviewBtn');
    const modalOverlay = document.getElementById('modalOverlay');
    const backBtn = document.getElementById('backBtn');
    const confirmBtn = document.getElementById('confirmBtn');
    const orderForm = document.getElementById('orderForm');
    const summaryDiv = document.getElementById('orderSummary');

    function gatherData() {
        const name = document.getElementById('buyer_name').value.trim();
        const phone = document.getElementById('buyer_phone').value.trim();
        let total = 0;
        const products = [];
        document.querySelectorAll('.product-card').forEach(card => {
            const qtyInput = card.querySelector('input[type="number"]');
            const qty = parseInt(qtyInput.value) || 0;
            if (qty > 0) {
                const prodName = card.querySelector('.product-name').textContent;
                const priceText = card.querySelector('.product-price').textContent.replace('R$', '').replace(',', '.');
                const price = parseFloat(priceText);
                total += price * qty;
                products.push({name: prodName, qty, price});
            }
        });
        return {name, phone, products, total};
    }

    reviewBtn.addEventListener('click', () => {
        const data = gatherData();
        if (!data.name || !data.phone) {
            alert('Por favor, preencha nome e telefone antes de continuar.');
            return;
        }
        if (data.products.length === 0) {
            alert('Selecione pelo menos um produto.');
            return;
        }
        // monta resumo
        let html = `<p><strong>Nome:</strong> ${data.name}</p>`;
        html += `<p><strong>Telefone:</strong> ${data.phone}</p>`;
        html += '<ul>';
        data.products.forEach(p => {
            html += `<li>${p.name} - ${p.qty} x R$ ${p.price.toFixed(2)}</li>`;
        });
        html += '</ul>';
        html += `<p><strong>Subtotal:</strong> R$ ${data.total.toFixed(2)}</p>`;
        html += `<p><em>Frete será adicionado no checkout.</em></p>`;
        summaryDiv.innerHTML = html;

        modalOverlay.style.display = 'flex';
    });

    backBtn.addEventListener('click', () => {
        modalOverlay.style.display = 'none';
    });

    confirmBtn.addEventListener('click', () => {
        // enviando formulário normalmente
        modalOverlay.style.display = 'none';
        orderForm.submit();
    });
});