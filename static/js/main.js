// JavaScript SPA para carrinho, modal de customização e checkout

const MIN_CHECKOUT_SUBTOTAL = 25;
const FRETE_GRATIS_TAG_SUBTOTAL = 50;

function maskPhone(value) {
    let digits = value.replace(/\D/g, '');
    if (digits.length > 11) digits = digits.slice(0, 11);
    let formatted = '';
    if (digits.length > 0) formatted += '(' + digits.substring(0, 2);
    if (digits.length >= 3) formatted += ') ' + digits.substring(2, 7);
    if (digits.length >= 8) formatted += '-' + digits.substring(7);
    return formatted;
}

function maskCep(value) {
    let digits = value.replace(/\D/g, '').slice(0, 8);
    if (digits.length > 5) {
        return digits.slice(0, 5) + '-' + digits.slice(5);
    }
    return digits;
}

window.addEventListener('DOMContentLoaded', () => {
    const cartKey = 'pedidos_delicia_cart';

    const products = {};
    document.querySelectorAll('.product-card').forEach(card => {
        const dataEl = card.querySelector('.product-data');
        if (!dataEl) return;
        try {
            const productData = JSON.parse(dataEl.textContent);
            products[productData.id] = productData;
        } catch (error) {
            console.error('Erro no parsing do item', error);
        }
    });

    let cart = JSON.parse(localStorage.getItem(cartKey) || '[]');

    const cartCountEl = document.getElementById('cartCount');
    const cartTotalEl = document.getElementById('cartTotal');
    const drawerTotalEl = document.getElementById('drawerTotal');
    const deliveryFeeEl = document.getElementById('deliveryFee');
    const cartItemsList = document.getElementById('cartItemsList');
    const openCartBtn = document.getElementById('openCartBtn');
    const closeCartBtn = document.getElementById('closeCartBtn');
    const cartDrawer = document.getElementById('cartDrawer');
    const checkoutBtn = document.getElementById('checkoutBtn');
    const productModal = document.getElementById('customizeModal');
    const closeCustomizeBtn = document.getElementById('closeCustomizeBtn');
    const modalProductName = document.getElementById('modalProductName');
    const modalProductPrice = document.getElementById('modalProductPrice');
    const modalCoverings = document.getElementById('modalCoverings');
    const modalFlavors = document.getElementById('modalFlavors');
    const addToCartBtn = document.getElementById('addToCartBtn');

    const hiddenForm = document.getElementById('submitOrderForm');
    const hiddenBuyerName = document.getElementById('hidden_buyer_name');
    const hiddenBuyerPhone = document.getElementById('hidden_buyer_phone');
    const hiddenBuyerEmail = document.getElementById('hidden_buyer_email');
    const hiddenDeliveryMethod = document.getElementById('hidden_delivery_method');
    const hiddenDeliveryAddress = document.getElementById('hidden_delivery_address');
    const hiddenBuyerCep = document.getElementById('hidden_buyer_cep');
    const hiddenCartItems = document.getElementById('hidden_cart_items');

    const buyerNameInput = document.getElementById('drawer_buyer_name');
    const buyerPhoneInput = document.getElementById('drawer_buyer_phone');
    const buyerEmailInput = document.getElementById('drawer_buyer_email');
    const deliveryMethodInput = document.getElementById('drawer_delivery_method');
    const deliveryAddressInput = document.getElementById('drawer_delivery_address');
    const addressLabel = document.getElementById('drawer-address-label');

    const buyerCepInput = document.getElementById('buyer_cep');
    const calcFreteBtn = document.getElementById('calcFreteBtn');
    const drawerCepRow = document.getElementById('drawer-cep-row');
    const freightEtaLine = document.getElementById('freightEtaLine');
    const freightEta = document.getElementById('freightEta');
    const freteGratisTag = document.getElementById('freteGratisTag');

    let freightCalculated = false;
    let lastFreightValue = 0;
    let subtotalWhenFreightLocked = null;

    function invalidateFreight() {
        freightCalculated = false;
        lastFreightValue = 0;
        subtotalWhenFreightLocked = null;
        if (freightEtaLine) freightEtaLine.hidden = true;
        if (freightEta) freightEta.textContent = '';
    }

    function syncFreightValidityWithSubtotal() {
        if (!deliveryMethodInput || deliveryMethodInput.value !== 'Entrega') return;
        if (!freightCalculated || subtotalWhenFreightLocked === null) return;
        const sub = calculateCartTotal();
        if (Math.abs(sub - subtotalWhenFreightLocked) > 0.001) {
            invalidateFreight();
        }
    }

    [buyerPhoneInput].forEach(input => {
        if (!input) return;
        input.addEventListener('input', event => {
            event.target.value = maskPhone(event.target.value);
        });
    });

    if (buyerCepInput) {
        buyerCepInput.addEventListener('input', () => {
            buyerCepInput.value = maskCep(buyerCepInput.value);
            invalidateFreight();
            updateFreightDisplayOnly();
        });
    }

    let activeProduct = null;

    function saveCart() {
        localStorage.setItem(cartKey, JSON.stringify(cart));
    }

    function formatCurrency(value) {
        return `R$ ${value.toFixed(2).replace('.', ',')}`;
    }

    function calculateCartTotal() {
        return cart.reduce((sum, item) => sum + item.quantity * item.item_total, 0);
    }

    function updateFreightDisplayOnly() {
        syncFreightValidityWithSubtotal();

        if (!cart.length) {
            if (freteGratisTag) freteGratisTag.hidden = true;
            deliveryFeeEl.textContent = formatCurrency(0);
            drawerTotalEl.textContent = formatCurrency(0);
            return;
        }

        const subtotal = calculateCartTotal();
        const isEntrega = deliveryMethodInput && deliveryMethodInput.value === 'Entrega';

        if (freteGratisTag) {
            freteGratisTag.hidden = !(subtotal > FRETE_GRATIS_TAG_SUBTOTAL);
        }

        let deliveryFee = 0;
        if (isEntrega) {
            if (freightCalculated) {
                deliveryFee = lastFreightValue;
                deliveryFeeEl.textContent = formatCurrency(deliveryFee);
            } else {
                deliveryFeeEl.textContent = '—';
                deliveryFee = 0;
            }
        } else {
            deliveryFeeEl.textContent = formatCurrency(0);
        }

        const totalComFrete = subtotal + (isEntrega && freightCalculated ? lastFreightValue : 0);
        drawerTotalEl.textContent = formatCurrency(totalComFrete);
    }

    function renderCart() {
        syncFreightValidityWithSubtotal();
        cartItemsList.innerHTML = '';

        if (cart.length === 0) {
            cartItemsList.innerHTML = '<p>Carrinho vazio.</p>';
        }

        let total = 0;
        cart.forEach((item, index) => {
            total += item.quantity * item.item_total;
            const itemEl = document.createElement('div');
            itemEl.className = 'cart-item';
            let flavorList = '';
            item.flavors.forEach(flavor => {
                flavorList += `<li>${flavor.name} x ${flavor.qty}</li>`;
            });
            itemEl.innerHTML = `
                <div class="cart-item-header">
                    <strong>${item.name}</strong> (${item.covering})
                    <span>${formatCurrency(item.item_total)} por unidade</span>
                </div>
                <div><ul>${flavorList}</ul></div>
                <div class="cart-item-actions">
                    <span>Qtd: ${item.quantity}</span>
                    <button type="button" data-index="${index}" class="decrease-btn">-</button>
                    <button type="button" data-index="${index}" class="increase-btn">+</button>
                    <button type="button" data-index="${index}" class="remove-btn">Remover</button>
                </div>
            `;
            cartItemsList.appendChild(itemEl);
        });

        cartCountEl.textContent = cart.reduce((q, i) => q + i.quantity, 0);
        cartTotalEl.textContent = formatCurrency(total);

        const isEntrega = deliveryMethodInput && deliveryMethodInput.value === 'Entrega';
        if (drawerCepRow) {
            drawerCepRow.style.display = isEntrega ? 'block' : 'none';
        }
        if (!isEntrega) {
            invalidateFreight();
        }

        updateFreightDisplayOnly();

        document.querySelectorAll('.decrease-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const i = Number(btn.dataset.index);
                if (cart[i].quantity > 1) cart[i].quantity -= 1;
                else cart.splice(i, 1);
                saveCart();
                invalidateFreight();
                renderCart();
            });
        });

        document.querySelectorAll('.increase-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const i = Number(btn.dataset.index);
                cart[i].quantity += 1;
                saveCart();
                invalidateFreight();
                renderCart();
            });
        });

        document.querySelectorAll('.remove-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const i = Number(btn.dataset.index);
                cart.splice(i, 1);
                saveCart();
                invalidateFreight();
                renderCart();
            });
        });
    }

    async function onCalcularFreteClick() {
        if (!buyerCepInput || !calcFreteBtn) return;

        const cepDigits = buyerCepInput.value.replace(/\D/g, '');
        if (cepDigits.length !== 8) {
            alert('Informe um CEP válido (8 dígitos).');
            return;
        }

        const subtotal = calculateCartTotal();
        if (subtotal < MIN_CHECKOUT_SUBTOTAL) {
            alert(
                'O pedido mínimo para entrega é de R$ 25,00. Adicione mais delícias ao seu carrinho ou escolha a opção de Retirada Local.'
            );
            return;
        }

        calcFreteBtn.disabled = true;
        try {
            const res = await fetch('/api/calcula_frete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Accept: 'application/json',
                },
                body: JSON.stringify({
                    cep: buyerCepInput.value.trim(),
                    subtotal,
                    delivery_method: 'Entrega',
                }),
            });

            let data = {};
            try {
                data = await res.json();
            } catch (_) {
                data = {};
            }

            if (!res.ok || !data.ok) {
                alert(data.error || 'Não foi possível calcular o frete. Tente novamente.');
                invalidateFreight();
                renderCart();
                return;
            }

            lastFreightValue = Number(data.freight_value) || 0;
            freightCalculated = true;
            subtotalWhenFreightLocked = subtotal;

            if (freightEta && freightEtaLine) {
                const eta = (data.estimated_time || '').trim();
                freightEta.textContent = eta;
                freightEtaLine.hidden = !eta;
            }

            renderCart();
        } catch (err) {
            console.error(err);
            alert('Erro de rede ao calcular o frete. Verifique sua conexão.');
            invalidateFreight();
            renderCart();
        } finally {
            calcFreteBtn.disabled = false;
        }
    }

    if (calcFreteBtn) {
        calcFreteBtn.addEventListener('click', () => {
            onCalcularFreteClick();
        });
    }

    function setModalForProduct(productId) {
        activeProduct = products[productId];
        if (!activeProduct) return;
        modalProductName.textContent = activeProduct.name;
        modalProductPrice.textContent = `Preço base: ${formatCurrency(activeProduct.price)}`;

        if (activeProduct.coverings && activeProduct.coverings.length > 0) {
            let html = '<label>Cobertura:</label><select id="modalCoveringSelect">';
            activeProduct.coverings.forEach((cover, idx) => {
                html += `<option value="${cover.name}" data-add="${cover.additional_price}" ${idx === 0 ? 'selected' : ''}>${cover.name} ${cover.additional_price > 0 ? `( + ${formatCurrency(cover.additional_price)})` : ''}</option>`;
            });
            html += '</select>';
            modalCoverings.innerHTML = html;
        } else {
            modalCoverings.innerHTML = '<p>Sem coberturas disponíveis para este produto.</p>';
        }

        let flavorHtml = '<p>Recheios:</p>';
        activeProduct.flavors.forEach(flavor => {
            flavorHtml += `
                <div class="flavor-row">
                    <span>${flavor.name} ${flavor.additional_price > 0 ? `( + ${formatCurrency(flavor.additional_price)})` : ''}</span>
                    <input type="number" min="0" value="0" data-flavor-name="${flavor.name}" data-add="${flavor.additional_price}" class="modalFlavorQty">
                </div>
            `;
        });
        modalFlavors.innerHTML = flavorHtml;
    }

    document.querySelectorAll('.btn-customize').forEach(btn => {
        btn.addEventListener('click', () => {
            const productId = btn.dataset.productId;
            setModalForProduct(productId);
            productModal.style.display = 'flex';
        });
    });

    closeCustomizeBtn.addEventListener('click', () => {
        productModal.style.display = 'none';
    });

    addToCartBtn.addEventListener('click', () => {
        if (!activeProduct) return;

        const coveringSelect = document.getElementById('modalCoveringSelect');
        const covering = coveringSelect ? coveringSelect.value : 'Sem Cobertura';
        const coveringAdd = coveringSelect ? Number(coveringSelect.selectedOptions[0].dataset.add) : 0;

        const flavorInputs = Array.from(document.querySelectorAll('.modalFlavorQty'));

        let anyFlavorSelected = false;

        flavorInputs.forEach(input => {
            const qty = Number(input.value);
            if (qty <= 0) return;

            anyFlavorSelected = true;

            const flavorName = input.dataset.flavorName;
            const flavorAdd = Number(input.dataset.add);
            const unitPrice = activeProduct.price + coveringAdd + flavorAdd;
            const key = `${activeProduct.id}|${covering}|${flavorName}`;

            const existing = cart.find(c => c.key === key);
            if (existing) {
                existing.quantity += qty;
                existing.flavors = [{ name: flavorName, qty: existing.quantity }];
                existing.item_total = unitPrice;
            } else {
                cart.push({
                    key,
                    product_id: activeProduct.id,
                    name: activeProduct.name,
                    covering,
                    flavors: [{ name: flavorName, qty }],
                    quantity: qty,
                    item_total: unitPrice,
                });
            }
        });

        if (!anyFlavorSelected) {
            alert('Escolha pelo menos um recheio para adicionar ao carrinho.');
            return;
        }

        saveCart();
        invalidateFreight();
        renderCart();
        productModal.style.display = 'none';
    });

    openCartBtn.addEventListener('click', () => {
        cartDrawer.style.right = '0';
        renderCart();
    });

    closeCartBtn.addEventListener('click', () => {
        cartDrawer.style.right = '-450px';
    });

    deliveryMethodInput.addEventListener('change', () => {
        if (deliveryMethodInput.value === 'Entrega') {
            deliveryAddressInput.style.display = 'block';
            addressLabel.style.display = 'block';
        } else {
            deliveryAddressInput.style.display = 'none';
            addressLabel.style.display = 'none';
            deliveryAddressInput.value = '';
            invalidateFreight();
        }
        renderCart();
    });

    checkoutBtn.addEventListener('click', () => {
        if (cart.length === 0) {
            alert('Adicione ao menos um item ao carrinho.');
            return;
        }

        const subtotal = calculateCartTotal();
        const deliveryMethod = deliveryMethodInput.value;

        if (deliveryMethod === 'Entrega' && subtotal < MIN_CHECKOUT_SUBTOTAL) {
            alert(
                'O pedido mínimo para entrega é de R$ 25,00. Adicione mais delícias ao seu carrinho ou escolha a opção de Retirada Local.'
            );
            return;
        }

        const buyerName = buyerNameInput.value.trim();
        const buyerPhone = buyerPhoneInput.value.trim();
        const buyerEmail = buyerEmailInput ? buyerEmailInput.value.trim() : '';
        const deliveryAddress = deliveryAddressInput.value.trim();

        if (!buyerName || !buyerPhone) {
            alert('Informe seu nome e telefone.');
            return;
        }

        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!buyerEmail || !emailPattern.test(buyerEmail)) {
            alert('Informe um e-mail válido para continuar.');
            return;
        }

        if (deliveryMethod === 'Entrega' && !deliveryAddress) {
            alert('Informe o endereço de entrega.');
            return;
        }

        if (deliveryMethod === 'Entrega') {
            const cepDigits = buyerCepInput ? buyerCepInput.value.replace(/\D/g, '') : '';
            if (cepDigits.length !== 8) {
                alert('Informe um CEP válido (8 dígitos) para entrega.');
                return;
            }
            if (!freightCalculated) {
                alert('Calcule o frete antes de finalizar o pedido (botão Calcular Frete).');
                return;
            }
        }

        hiddenBuyerName.value = buyerName;
        hiddenBuyerPhone.value = buyerPhone;
        hiddenBuyerEmail.value = buyerEmail;
        hiddenDeliveryMethod.value = deliveryMethod;
        hiddenDeliveryAddress.value = deliveryAddress;
        hiddenBuyerCep.value = buyerCepInput ? buyerCepInput.value.trim() : '';
        hiddenCartItems.value = JSON.stringify(cart);

        hiddenForm.submit();
    });

    renderCart();
});
