// ========================================
// AGREGAR_EXISTENTE.JS - Gestión de Stock
// ========================================

const productCache = {};

// Cambiar entre tabs de búsqueda
function switchTab(tabName) {
    const skuTab = document.getElementById('sku-tab');
    const nameTab = document.getElementById('name-tab');
    
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => btn.classList.remove('active'));
    
    if (tabName === 'sku') {
        skuTab.classList.add('active');
        nameTab.classList.remove('active');
        tabBtns[0].classList.add('active');
        document.getElementById('skuInput').focus();
    } else {
        nameTab.classList.add('active');
        skuTab.classList.remove('active');
        tabBtns[1].classList.add('active');
        document.getElementById('productSearchInput').focus();
    }
    
    const dropdown = document.getElementById('searchResults');
    dropdown.innerHTML = '';
    dropdown.classList.remove('show');
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

// Buscar producto por SKU desde BD
async function findProductFromDB(sku) {
    const cleanSku = sku.toString().trim();
    
    if (productCache[cleanSku]) {
        return productCache[cleanSku];
    }
    
    try {
        const response = await fetch(`/productos/buscar-sku/?sku=${encodeURIComponent(cleanSku)}`);
        if (response.ok) {
            const data = await response.json();
            const product = {
                name: data.nombre,
                stock: data.stock_actual,
                id: data.id
            };
            productCache[cleanSku] = product;
            return product;
        } else {
            return null;
        }
    } catch (error) {
        console.error('Error buscando producto:', error);
        return null;
    }
}

// Buscar productos por nombre (misma lógica que en venta.js)
async function searchProducts() {
    const query = document.getElementById('productSearchInput').value.trim();
    const dropdown = document.getElementById('searchResults');
    
    if (query.length < 1) {
        dropdown.classList.remove('show');
        return;
    }
    
    try {
        // Descargar todos los productos y filtrar localmente (igual que venta.js)
        const response = await fetch(`/productos/api/listar/`);
        if (!response.ok) throw new Error('Error en búsqueda');
        
        const data = await response.json();
        const productos = data.productos || [];
        
        // Normalizar búsqueda para ignorar acentos
        const normalizedQuery = normalizeText(query);
        
        // Filtrar por nombre o SKU
        const filtered = productos.filter(p => 
            normalizeText(p.nombre).includes(normalizedQuery) || 
            p.sku.toString().includes(query)
        );
        
        if (filtered.length === 0) {
            dropdown.innerHTML = '<div class="search-result-item">Sin resultados</div>';
            dropdown.classList.add('show');
            return;
        }
        
        dropdown.innerHTML = filtered.map(p => `
            <div class="search-result-item" onclick="selectProduct('${p.sku}', '${escapeHtml(p.nombre)}')">
                <div class="search-result-name">${escapeHtml(p.nombre)}</div>
                <div class="search-result-sku">SKU: ${p.sku} | Stock: ${p.stock_actual}</div>
            </div>
        `).join('');
        
        dropdown.classList.add('show');
    } catch (error) {
        console.error('Error buscando productos:', error);
        dropdown.innerHTML = '<div class="search-result-item">Error en búsqueda</div>';
        dropdown.classList.add('show');
    }
}

// Seleccionar producto del dropdown
function selectProduct(sku, nombre) {
    document.getElementById('skuInput').value = sku;
    const dropdown = document.getElementById('searchResults');
    dropdown.classList.remove('show');
    document.getElementById('productSearchInput').value = '';
    // Mostrar detalles del producto seleccionado
    showProductDetails(sku);
}

// Mostrar detalles del producto seleccionado
async function showProductDetails(sku) {
    try {
        const response = await fetch(`/productos/buscar-sku/?sku=${encodeURIComponent(sku)}`);
        if (!response.ok) {
            return;
        }
        
        const data = await response.json();
        
        // Llenar la tarjeta de producto seleccionado
        document.getElementById('productName').textContent = data.nombre;
        document.getElementById('productSku').textContent = sku;
        document.getElementById('productStock').textContent = data.stock_actual;
        
        // Categoría
        if (data.categoria) {
            document.getElementById('productCategory').innerHTML = `<p><strong>Categoría:</strong> ${escapeHtml(data.categoria)}</p>`;
        }
        
        // Mostrar la tarjeta
        const card = document.getElementById('selectedProductCard');
        card.classList.add('show');
        
        // Enfocar en cantidad
        document.getElementById('qtyInput').focus();
        
    } catch (error) {
        console.error('Error mostrando detalles:', error);
    }
}

// Cambiar producto (limpiar selección)
function changeProduct() {
    document.getElementById('skuInput').value = '';
    document.getElementById('qtyInput').value = 1;
    document.getElementById('selectedProductCard').classList.remove('show');
    
    // Volver a la pestaña de búsqueda activa
    const activeTab = document.querySelector('.search-tab.active');
    if (activeTab.id === 'sku-tab') {
        document.getElementById('skuInput').focus();
    } else {
        document.getElementById('productSearchInput').focus();
    }
}

// Ocultar dropdown al hacer click fuera
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('searchResults');
    const search = document.getElementById('productSearchInput');
    if (!event.target.closest('#productSearchInput') && !event.target.closest('.search-dropdown')) {
        dropdown.classList.remove('show');
    }
});

// Obtener CSRF token de cookies
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

// Función para agregar stock
async function addStock() {
    const skuInput = document.getElementById('skuInput');
    const qtyInput = document.getElementById('qtyInput');
    
    const sku = skuInput.value.trim();
    const qty = parseInt(qtyInput.value);

    if (!sku) {
        showError('Código SKU requerido', 'Escanea o escribe un código SKU para continuar');
        skuInput.focus();
        return;
    }

    if (!qty || qty < 1) {
        showError('Cantidad inválida', 'La cantidad debe ser mayor a 0');
        qtyInput.value = 1;
        qtyInput.focus();
        return;
    }

    const product = await findProductFromDB(sku);
    
    if (!product) {
        showError('Producto no encontrado', `No existe producto con SKU ${sku}`);
        skuInput.value = '';
        skuInput.focus();
        return;
    }

    // Intentar actualizar el stock en la BD
    try {
        const response = await fetch(`/productos/agregar-stock/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                sku: sku,
                cantidad: qty
            })
        });

        if (response.ok) {
            const data = await response.json();
            const newStock = data.nuevo_stock || (product.stock + qty);
            
            productCache[sku].stock = newStock;
            
            showSuccess(
                `${qty} unidades agregadas`,
                `${product.name}: ${product.stock} → ${newStock}`
            );
            
            console.log(`Stock actualizado en BD: ${product.name} +${qty} (${product.stock} → ${newStock})`);
            
            // Limpiar formulario para siguiente entrada
            skuInput.value = '';
            qtyInput.value = 1;
            document.getElementById('selectedProductCard').classList.remove('show');
            skuInput.focus();
        } else {
            showError('Error de actualización', 'No se pudo actualizar el stock en la base de datos');
        }
    } catch (error) {
        console.error('Error actualizando stock:', error);
        showError('Error de conexión', 'Verifica tu conexión y intenta nuevamente');
        return;
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    const skuInput = document.getElementById('skuInput');
    const qtyInput = document.getElementById('qtyInput');

    // Enter en SKU
    skuInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (skuInput.value.trim()) {
                showProductDetails(skuInput.value.trim());
                qtyInput.focus();
            }
        }
    });

    // Enter en cantidad
    qtyInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addStock();
        }
    });

    // Limpiar mensaje al escribir
    skuInput.addEventListener('input', () => {
        const confirmMsg = document.getElementById('confirmMessage');
        confirmMsg.classList.remove('show');
    });

    // Validar cantidad mínima
    qtyInput.addEventListener('blur', () => {
        if (qtyInput.value < 1) qtyInput.value = 1;
    });
});
