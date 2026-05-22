// ========================================
// VENTA.JS - Funcionalidad de Punto de Venta (MEJORADO)
// ========================================

// Carrito de compras
let cart = [];
let selectedPayment = 'efectivo';

// Elementos del DOM
let skuInput, addSkuBtn, ticketItemsEl, subtotalEl, totalEl, finishBtn, cashBtn, transferBtn;

// Inicializar elementos del DOM
function initDOMElements() {
    skuInput = document.getElementById('skuInput');
    addSkuBtn = document.getElementById('addSkuBtn');
    ticketItemsEl = document.getElementById('ticketItems');
    subtotalEl = document.getElementById('subtotal');
    totalEl = document.getElementById('total');
    finishBtn = document.getElementById('finishBtn');
    cashBtn = document.getElementById('cashBtn');
    transferBtn = document.getElementById('transferBtn');
}

// Obtener token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Normalizar texto para búsqueda sin acentos
function normalizeText(text) {
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

// Escapar HTML para prevenir XSS
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Buscar producto por SKU desde BD (sin cache)
async function findProductBySkuAsync(sku) {
    const cleanSku = sku.toString().trim();
    
    try {
        const response = await fetch(`/productos/buscar-sku/?sku=${encodeURIComponent(cleanSku)}`);
        
        if (response.ok) {
            const data = await response.json();
            const hasPaquete = data.precio_paquete && data.precio_paquete > 0 && data.cantidad_paquete && data.cantidad_paquete > 0;
            const product = {
                id: data.id,
                sku: data.sku,
                name: data.nombre,
                price: data.precio_pieza,
                price_paquete: data.precio_paquete || null,
                cantidad_paquete: data.cantidad_paquete || null,
                hasPaquete: hasPaquete,
                category: 'Productos',
                stock_actual: data.stock_actual
            };
            console.log('✓ Producto encontrado:', product.name, '| Stock:', product.stock_actual, '| Paquete:', hasPaquete ? `${data.cantidad_paquete} piezas x $${data.precio_paquete}` : 'No');
            return product;
        } else {
            console.warn('✗ Servidor respuesta no OK:', response.status);
            return null;
        }
    } catch (error) {
        console.error('✗ Error en búsqueda por SKU:', error.message);
        return null;
    }
}

// Buscar productos por nombre
async function searchProductsByName(query) {
    if (!query || query.length < 1) return [];
    
    try {
        const response = await fetch(`/productos/api/listar/`);
        if (!response.ok) throw new Error('Error en búsqueda');
        
        const data = await response.json();
        const productos = data.productos || [];
        const normalizedQuery = normalizeText(query);
        
        // Filtrar por nombre
        return productos.filter(p => 
            normalizeText(p.nombre).includes(normalizedQuery)
        );
    } catch (error) {
        console.error('✗ Error en búsqueda por nombre:', error);
        return [];
    }
}

// Variable global para almacenar el producto seleccionado
let currentProductInModal = null;

// ========================================
// FUNCIÓN PRINCIPAL: Agregar al carrito
// ========================================
async function addToCart(sku) {
    if (!sku) return false;
    
    try {
        // 1. Buscar el producto
        const product = await findProductBySkuAsync(sku);
        console.log('✅ Producto encontrado:', product?.name);
        
        if (!product) {
            showStockNotification('Error', 'Producto no encontrado', `SKU: ${sku}`);
            return false;
        }

        // 2. Validar stock
        if (product.stock_actual <= 0) {
            showStockNotification(product.name, 'Sin stock', 'No hay disponible');
            return false;
        }

        // 3. Si tiene paquete, mostrar selector ANTES de agregar
        if (product.hasPaquete) {
            console.log('🎁 Producto tiene paquete - mostrando modal');
            currentProductInModal = product;
            abrirModalSeleccion(product);
            return true;
        }

        // 4. Si NO tiene paquete, agregar directamente como pieza
        console.log('📦 Producto sin paquete - agregando como pieza');
        agregarAlCarrito(product, 1, 'pieza');
        limpiarSKU();
        return true;

    } catch (error) {
        console.error('❌ Error en addToCart:', error);
        return false;
    }
}

// ========================================
// ABRIR MODAL DE SELECCIÓN (VERSIÓN SIMPLE)
// ========================================
function abrirModalSeleccion(product) {
    console.log('🔴 Abriendo modal para:', product.name);
    
    // Actualizar nombre
    document.getElementById('productNameHeader').textContent = product.name;

    // ===== OPCIÓN 1: PIEZA =====
    document.getElementById('precioPiezaSimple').textContent = '$' + parseFloat(product.price).toFixed(2);

    // ===== OPCIÓN 2: PAQUETE =====
    if (product.hasPaquete) {
        document.getElementById('paqueteTitleSimple').textContent = 
            `Por Paquete (${product.cantidad_paquete} piezas)`;
        document.getElementById('paqueteInfoSimple').textContent = 
            `${product.cantidad_paquete} piezas`;
        document.getElementById('precioPaqueteSimple').textContent = '$' + parseFloat(product.price_paquete).toFixed(2);
        document.getElementById('paqueteOptionSimple').style.display = 'block';
    } else {
        document.getElementById('paqueteOptionSimple').style.display = 'none';
    }

    // ===== RESETEAR RADIO BUTTON =====
    document.querySelector('input[name="tipoVenta"][value="pieza"]').checked = true;

    // ===== MOSTRAR MODAL =====
    const modal = document.getElementById('selectionModal');
    if (modal) {
        modal.classList.add('show');
        console.log('✅ Modal mostrado!');
    }
}

// ========================================
// CERRAR MODAL
// ========================================
function closeSelectionModal() {
    const modal = document.getElementById('selectionModal');
    if (modal) {
        modal.classList.remove('show');
    }
    currentProductInModal = null;
    if (skuInput) skuInput.focus();
}

// ========================================
// CONFIRMAR SELECCIÓN Y AGREGAR CARRITO
// ========================================
function confirmSelection() {
    if (!currentProductInModal) {
        console.warn('❌ No hay producto en modal');
        return;
    }

    const product = currentProductInModal;
    const tipoVenta = document.querySelector('input[name="tipoVenta"]:checked')?.value || 'pieza';
    
    console.log(`✅ Confirmado: 1 ${tipoVenta} de ${product.name}`);
    
    // Agregar cantidad 1 (el usuario ajusta en el carrito)
    agregarAlCarrito(product, 1, tipoVenta);
    closeSelectionModal();
    limpiarSKU();
}

// ========================================
// AGREGAR ITEM AL CARRITO
// ========================================
function agregarAlCarrito(product, quantity, tipoVenta) {
    const existingItem = cart.find(item => 
        item.sku === product.sku && item.tipo_venta === tipoVenta
    );

    if (existingItem) {
        existingItem.quantity += quantity;
    } else {
        cart.push({
            id: product.id,
            sku: product.sku,
            name: product.name,
            price: product.price,
            price_paquete: product.price_paquete,
            cantidad_paquete: product.cantidad_paquete,
            hasPaquete: product.hasPaquete,
            tipo_venta: tipoVenta,
            quantity: quantity,
            stock_actual: product.stock_actual
        });
    }

    console.log(`✅ Agregado al carrito:`, cart[cart.length - 1] || existingItem);
    updateTicket();
}

// ========================================
// LIMPIAR SKU
// ========================================
function limpiarSKU() {
    if (skuInput) {
        skuInput.value = '';
        skuInput.focus();
    }
}

// ========================================
// ACTUALIZAR SUBTOTALES
// ========================================
// Actualizar ticket
function updateTicket() {
    if (cart.length === 0) {
        ticketItemsEl.innerHTML = `
            <div style="text-align: center; color: #bc9b8b; padding: 2rem;">
                <i class="fas fa-receipt" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <p>Busca un producto para comenzar</p>
            </div>
        `;
    } else {
        let html = '';
        cart.forEach((item, index) => {
            const currentPrice = item.tipo_venta === 'paquete' ? item.price_paquete : item.price;
            const itemTotal = currentPrice * item.quantity;
            
            // Badge para mostrar el tipo de venta
            const tipoVentaBadge = item.tipo_venta === 'paquete' ? 
                `<span class="tipo-venta-badge paquete" title="Vender por paquete">🔹 Paque</span>` :
                `<span class="tipo-venta-badge pieza" title="Vender por pieza">🔹 Pieza</span>`;
            
            html += `
                <div class="ticket-item" data-index="${index}">
                    <div class="ticket-item-info">
                        <span class="ticket-item-name">${escapeHtml(item.name)}</span>
                        <span class="ticket-item-sku">SKU: ${item.sku} ${tipoVentaBadge}</span>
                    </div>
                    <div class="ticket-item-details">
                        <div class="ticket-item-qty">
                            <button class="qty-btn" onclick="updateQuantity(${index}, -1)">−</button>
                            <input type="text" class="qty-input" id="qty-${index}" value="${item.quantity}" min="1" max="${item.stock_actual}" style="padding: 0.4rem; width: 50px; text-align: center; border: 1px solid #e5987c; border-radius: 4px; font-weight: 600;">
                            <button class="qty-btn" onclick="updateQuantity(${index}, 1)">+</button>
                        </div>
                        <span class="ticket-item-price">$${itemTotal.toFixed(2)}</span>
                        <i class="fas fa-trash-alt remove-item" onclick="removeItem(${index})"></i>
                    </div>
                </div>
            `;
        });
        ticketItemsEl.innerHTML = html;
        
        // Agregar listeners a los inputs de cantidad
        cart.forEach((item, index) => {
            setTimeout(() => {
                const qtyInput = document.getElementById(`qty-${index}`);
                if (qtyInput) {
                    // Cuando pierde el foco
                    qtyInput.addEventListener('blur', function() {
                        window.setQuantity(index, this.value);
                    });
                    // Cuando presiona Enter
                    qtyInput.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            window.setQuantity(index, this.value);
                            this.blur();
                        }
                    });
                }
            }, 10);
        });
    }

    const subtotal = cart.reduce((sum, item) => {
        const currentPrice = item.tipo_venta === 'paquete' ? item.price_paquete : item.price;
        return sum + (currentPrice * item.quantity);
    }, 0);
    subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
    totalEl.textContent = `$${subtotal.toFixed(2)}`;
    finishBtn.disabled = cart.length === 0;
}

// Actualizar cantidad
window.updateQuantity = function(index, change) {
    const item = cart[index];
    const newQty = item.quantity + change;
    
    if (newQty <= 0) {
        removeItem(index);
    } else if (newQty > item.stock_actual) {
        showStockNotification(item.name, item.stock_actual);
    } else {
        item.quantity = newQty;
        updateTicket();
        // Devolver foco al campo SKU
        if (skuInput) {
            skuInput.focus();
        }
    }
};

// Establecer cantidad directamente (por escritura manual)
window.setQuantity = function(index, value) {
    const newQty = parseInt(value) || 0;
    const item = cart[index];
    
    console.log(`📝 setQuantity llamado: índice=${index}, valor=${value}, cantidad=${newQty}`);
    
    if (newQty <= 0 || value.trim() === '') {
        removeItem(index);
        return;
    } 
    
    // Validar stock
    if (newQty > item.stock_actual) {
        console.warn(`⚠️ Cantidad excede stock: ${newQty} > ${item.stock_actual}`);
        showStockNotification(item.name, item.stock_actual);
        // Restaurar el valor anterior en el input
        const qtyInput = document.getElementById(`qty-${index}`);
        if (qtyInput) {
            qtyInput.value = item.quantity;
        }
        return;
    }
    
    // Cantidad válida - actualizar
    item.quantity = newQty;
    console.log(`✓ Cantidad actualizada a ${newQty}`);
    
    // Actualizar SOLO el precio del item
    const priceElement = document.querySelector(`[data-index="${index}"] .ticket-item-price`);
    if (priceElement) {
        const currentPrice = item.tipo_venta === 'paquete' ? item.price_paquete : item.price;
        const itemTotal = currentPrice * newQty;
        priceElement.textContent = `$${itemTotal.toFixed(2)}`;
    }
    
    // Actualizar totales
    const subtotal = cart.reduce((sum, i) => {
        const currentPrice = i.tipo_venta === 'paquete' ? i.price_paquete : i.price;
        return sum + (currentPrice * i.quantity);
    }, 0);
    if (subtotalEl) subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
    if (totalEl) totalEl.textContent = `$${subtotal.toFixed(2)}`;
};

// Cambiar tipo de venta (Pieza vs Paquete)

// Eliminar item
window.removeItem = function(index) {
    const removed = cart[index];
    console.log('✓ Producto eliminado del carrito:', removed.name);
    cart.splice(index, 1);
    updateTicket();
    // Devolver foco al campo SKU para que el scanner siga funcionando
    if (skuInput) {
        skuInput.focus();
        console.log('✓ Foco restaurado al campo SKU');
    }
};

// Buscar productos por nombre con dropdown
async function searchBySku() {
    const query = skuInput.value.trim();
    
    // Si es solo números, buscar por SKU exacto
    if (/^\d+$/.test(query)) {
        // No mostrar dropdown para búsqueda numérica, dejar que el usuario presione Enter
        return;
    }
    
    // Si tiene texto, buscar por nombre
    if (query.length < 2) {
        const dropdown = document.getElementById('skuSearchResults');
        if (dropdown) dropdown.classList.remove('show');
        return;
    }
    
    const results = await searchProductsByName(query);
    const dropdown = document.getElementById('skuSearchResults');
    
    if (!dropdown) {
        console.warn('Dropdown no encontrado en DOM');
        return;
    }
    
    if (results.length === 0) {
        dropdown.innerHTML = '<div class="sku-search-item">Sin resultados</div>';
        dropdown.classList.add('show');
        return;
    }
    
    dropdown.innerHTML = results.map(p => `
        <div class="sku-search-item" onclick="selectProductFromDropdown('${p.sku}')">
            <div class="sku-item-name">${escapeHtml(p.nombre)}</div>
            <div class="sku-item-details">SKU: ${p.sku} | Stock: ${p.stock_actual} | $${p.precio_pieza}</div>
        </div>
    `).join('');
    
    dropdown.classList.add('show');
}

// Seleccionar producto del dropdown
window.selectProductFromDropdown = async function(sku) {
    const dropdown = document.getElementById('skuSearchResults');
    if (dropdown) dropdown.classList.remove('show');
    
    skuInput.value = '';
    const success = await addToCart(sku);
    
    if (success) {
        skuInput.focus();
    }
};

// Ocultar dropdown al click fuera
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('skuSearchResults');
    if (dropdown && !event.target.closest('#skuInput') && !event.target.closest('.sku-search-dropdown')) {
        dropdown.classList.remove('show');
    }
});

// Variables para modal de pago
let currentTotal = 0;

function openPaymentModal() {
    currentTotal = cart.reduce((sum, item) => {
        const price = item.tipo_venta === 'paquete' ? item.price_paquete : item.price;
        return sum + (price * item.quantity);
    }, 0);
    document.getElementById('totalAmount').textContent = `$${currentTotal.toFixed(2)}`;
    document.getElementById('amountPaid').value = '';
    document.getElementById('changeAmount').textContent = '$0.00';
    document.getElementById('paymentModal').classList.add('show');
    document.getElementById('amountPaid').focus();
}

function closePaymentModal() {
    document.getElementById('paymentModal').classList.remove('show');
}

function calculateChange() {
    const amountPaid = parseFloat(document.getElementById('amountPaid').value) || 0;
    const change = amountPaid - currentTotal;
    const changeElement = document.getElementById('changeAmount');
    
    changeElement.textContent = `$${change.toFixed(2)}`;
    changeElement.style.color = change >= 0 ? '#2d6a4f' : '#c84754';
}

function generateTicketHTML(ventaId, cajero) {
    const amountPaid = parseFloat(document.getElementById('amountPaid').value) || 0;
    const change = amountPaid - currentTotal;
    const date = new Date();
    const dateString = date.toLocaleDateString('es-ES');
    const timeString = date.toLocaleTimeString('es-ES');
    
    // Calcular total de artículos
    let totalItems = 0;
    cart.forEach(item => {
        totalItems += item.quantity;
    });
    
    // Construir filas de productos
    let ticketItems = '';
    cart.forEach(item => {
        const currentPrice = item.tipo_venta === 'paquete' ? item.price_paquete : item.price;
        const itemTotal = (currentPrice * item.quantity).toFixed(2);
        const precio = parseFloat(currentPrice).toFixed(2);
        const nombre = escapeHtml(item.name);
        const tipoLabel = item.tipo_venta === 'paquete' ? ` (Paq)` : '';
        
        // Formato: NOMBRE        CANT   P.U     TOTAL
        ticketItems += `<div style="display: grid; grid-template-columns: 2.5fr 0.6fr 0.8fr 0.8fr; gap: 0.3rem; margin-bottom: 0.3rem; font-size: 0.75rem; font-family: 'Courier New', monospace;">
            <div>${nombre}${tipoLabel}</div>
            <div style="text-align: center;">${item.quantity}</div>
            <div style="text-align: right;">$${precio}</div>
            <div style="text-align: right;">$${itemTotal}</div>
        </div>`;
    });

    return `
        <div style="text-align: center; margin-bottom: 0.5rem;">
            <div style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; color: #e8a87c; font-weight: bold;">========================================</div>
        </div>
        
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 1rem; font-weight: bold; color: #4a4e69;">PAPELERÍA YESSY</div>
        </div>
        
        <div style="text-align: center; font-size: 0.7rem; color: #7f7b82; margin-bottom: 1rem; line-height: 1.4;">
            <div>Dirección: Tulancingo, Hidalgo</div>
            <div>Tel: Consultar en tienda</div>
        </div>
        
        <div style="text-align: center; margin-bottom: 0.8rem;">
            <div style="font-size: 0.7rem; border-top: 1px dashed #ffe9d7; border-bottom: 1px dashed #ffe9d7; padding: 0.3rem 0; color: #7f7b82;">
                <div style="font-weight: bold;">Folio: ${String(ventaId).padStart(8, '0')}</div>
                <div style="margin-top: 0.2rem;">Fecha: ${dateString}</div>
                <div>Hora: ${timeString}</div>
                <div style="margin-top: 0.2rem; font-weight: 600;">Cajero: ${escapeHtml(cajero || 'Sistema')}</div>
            </div>
        </div>
        
        <div style="text-align: center; font-size: 0.7rem; border-bottom: 1px dashed #ffe9d7; padding-bottom: 0.5rem; margin-bottom: 0.5rem; color: #7f7b82;">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</div>
        
        <div style="margin-bottom: 0.8rem;">
            <div style="display: grid; grid-template-columns: 2.5fr 0.6fr 0.8fr 0.8fr; gap: 0.3rem; margin-bottom: 0.3rem; font-size: 0.75rem; font-weight: bold; font-family: 'Courier New', monospace; padding-bottom: 0.3rem; border-bottom: 1px solid #333;">
                <div>PRODUCTO</div>
                <div style="text-align: center;">CANT</div>
                <div style="text-align: right;">P.U</div>
                <div style="text-align: right;">TOTAL</div>
            </div>
            <div style="font-size: 0.7rem; border-bottom: 1px dashed #ffe9d7; padding-bottom: 0.3rem; margin-bottom: 0.3rem; color: #7f7b82;">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</div>
            ${ticketItems}
            <div style="font-size: 0.7rem; border-top: 1px dashed #ffe9d7; padding-top: 0.3rem; margin-top: 0.3rem; color: #7f7b82;">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</div>
        </div>
        
        <div style="text-align: right; font-size: 0.8rem; margin-bottom: 0.8rem; font-family: 'Courier New', monospace;">
            <div style="color: #7f7b82;">SUBTOTAL:                $${currentTotal.toFixed(2)}</div>
            <div style="font-weight: bold; font-size: 0.9rem; color: #4a4e69; margin-top: 0.2rem;">TOTAL:                   $${currentTotal.toFixed(2)}</div>
        </div>
        
        <div style="text-align: center; font-size: 0.75rem; color: #7f7b82; margin-bottom: 0.8rem; padding: 0.5rem 0; border-top: 1px dashed #ffe9d7; border-bottom: 1px dashed #ffe9d7;">
            <div>Método de pago: ${selectedPayment === 'efectivo' ? 'EFECTIVO' : 'TRANSFERENCIA'}</div>
            <div style="margin-top: 0.3rem;">Recibido: $${amountPaid.toFixed(2)}</div>
            ${amountPaid > currentTotal ? `<div style="margin-top: 0.2rem; font-weight: bold; color: #4a4e69;">Cambio: $${change.toFixed(2)}</div>` : ''}
        </div>
        
        <div style="text-align: center; font-size: 0.75rem; color: #7f7b82; margin-bottom: 0.8rem;">
            <div>Artículos vendidos: ${totalItems}</div>
        </div>
        
        <div style="text-align: center; font-size: 0.7rem; border-top: 1px dashed #ffe9d7; border-bottom: 1px dashed #ffe9d7; padding: 0.5rem 0; margin-bottom: 0.5rem; color: #e8a87c; font-weight: bold;">
            ¡GRACIAS POR SU COMPRA!
        </div>
        
        <div style="text-align: center; font-size: 0.65rem; color: #9d6b53; line-height: 1.3;">
            <div>Este comprobante es únicamente</div>
            <div>informativo y NO es válido</div>
            <div>para efectos fiscales.</div>
        </div>
        
        <div style="text-align: center; margin-top: 0.5rem;">
            <div style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; color: #e8a87c; font-weight: bold;">========================================</div>
        </div>
    `;
}

async function finishSaleAndGenerateTicket() {
    const amountPaid = parseFloat(document.getElementById('amountPaid').value) || 0;
    
    if (amountPaid < currentTotal) {
        alert(`❌ Monto insuficiente. Total: $${currentTotal.toFixed(2)}`);
        return;
    }

    finishBtn.disabled = true;
    finishBtn.textContent = 'Procesando...';

    try {
        const response = await fetch('/ventas/crear/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                metodo_pago: selectedPayment,
                detalles: cart.map(item => ({
                    producto_id: item.id,
                    cantidad: item.quantity,
                    tipo_venta: item.tipo_venta,  // Usar el tipo_venta del item
                }))
            })
        });

        const resultado = await response.json();

        if (!response.ok || !resultado.exito) {
            alert(`❌ Error: ${resultado.error || 'Error desconocido'}`);
            finishBtn.disabled = false;
            finishBtn.textContent = 'Finalizar Venta';
            return;
        }

        document.getElementById('ticketContent').innerHTML = generateTicketHTML(resultado.venta_id, resultado.cajero);
        closePaymentModal();
        document.getElementById('ticketModal').classList.add('show');
        finishBtn.disabled = false;
        finishBtn.textContent = 'Finalizar Venta';
    } catch (error) {
        console.error('✗ Error:', error);
        alert(`❌ Error: ${error.message}`);
        finishBtn.disabled = false;
        finishBtn.textContent = 'Finalizar Venta';
    }
}

function printTicket() {
    const ticketContent = document.getElementById('ticketContent').innerHTML;
    const printWindow = window.open('', '', 'width=400,height=600');
    printWindow.document.write(`<!DOCTYPE html><html><head><title>Ticket</title><style>body{font-family:'Courier',monospace;padding:20px;background:white}</style></head><body>${ticketContent}</body></html>`);
    printWindow.document.close();
    setTimeout(() => { printWindow.print(); printWindow.close(); }, 250);
}

function closeTicketModal() {
    document.getElementById('ticketModal').classList.remove('show');
    cart = [];
    updateTicket();
    skuInput.focus();
}

function showStockNotification(productName, availableStock, message) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    const msg = typeof availableStock === 'number' ? `${productName}: máximo ${availableStock}` : (message || `${productName}: ${availableStock}`);
    
    toast.innerHTML = `<i class="fas fa-exclamation-circle"></i><div class="toast-notification-content"><div class="toast-notification-title">⚠️ Aviso</div><div class="toast-notification-message">${msg}</div></div>`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initDOMElements();
    
    if (skuInput) {
        skuInput.disabled = false;
        
        // Enter: agregar por SKU
        skuInput.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const sku = skuInput.value.trim();
                if (sku) {
                    console.log('📱 Enter presionado - Agregando:', sku);
                    const success = await addToCart(sku);
                    skuInput.value = '';  // Limpiar siempre, no solo en éxito
                }
                skuInput.focus();
            }
        });
        
        // Búsqueda por nombre mientras escribes
        skuInput.addEventListener('input', searchBySku);
        
        skuInput.focus();
    }
    
    // Botón Agregar
    if (addSkuBtn) {
        addSkuBtn.addEventListener('click', async () => {
            const sku = skuInput.value.trim();
            if (sku) {
                const success = await addToCart(sku);
                skuInput.value = '';  // Limpiar siempre, no solo en éxito
            }
            skuInput.focus();
        });
    }

    // Métodos de pago
    if (cashBtn) {
        cashBtn.addEventListener('click', () => {
            cashBtn.classList.add('active');
            transferBtn.classList.remove('active');
            selectedPayment = 'efectivo';
        });
    }
    
    if (transferBtn) {
        transferBtn.addEventListener('click', () => {
            transferBtn.classList.add('active');
            cashBtn.classList.remove('active');
            selectedPayment = 'transferencia';
        });
    }

    if (finishBtn) {
        finishBtn.addEventListener('click', () => {
            if (cart.length > 0) openPaymentModal();
        });
    }
});
