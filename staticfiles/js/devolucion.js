// Variables globales
let currentSale = null;
let currentDetalles = [];
let devolucionSelecciones = {};

// Función para mostrar mensajes
function showMessage(message, type = 'success') {
    const container = document.getElementById('messageContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message show message-${type}`;
    messageDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        ${message}
    `;
    container.innerHTML = '';
    container.appendChild(messageDiv);
    
    if (type === 'success') {
        setTimeout(() => {
            messageDiv.classList.remove('show');
        }, 3000);
    }
}

// Escape HTML para seguridad
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

// Buscar venta por ID
async function buscarVenta() {
    const ventaId = document.getElementById('ventaIdInput').value.trim();
    
    if (!ventaId) {
        showMessage('Por favor ingresa un ID de venta', 'error');
        return;
    }
    
    if (isNaN(ventaId) || ventaId <= 0) {
        showMessage('El ID debe ser un número válido', 'error');
        return;
    }
    
    const searchBtn = document.getElementById('searchBtn');
    const searchStatus = document.getElementById('searchStatus');
    searchBtn.disabled = true;
    searchBtn.textContent = 'Buscando...';
    searchStatus.textContent = 'Buscando venta...';
    
    try {
        const response = await fetch(`/ventas/buscar_devolucion/?venta_id=${ventaId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.exito) {
            showMessage(`❌ ${data.error || 'Venta no encontrada'}`, 'error');
            searchStatus.textContent = '';
            resetForm();
            searchBtn.disabled = false;
            searchBtn.textContent = 'Buscar';
            return;
        }
        
        // Guardar datos de la venta
        currentSale = data.venta;
        currentDetalles = data.detalles;
        devolucionSelecciones = {};
        
        // Mostrar información de la venta
        mostrarInfoVenta();
        
        // Mostrar tabla de productos
        mostrarProductos();
        
        searchStatus.textContent = `✓ Venta encontrada: ${data.detalles.length} artículo(s)`;
        searchBtn.disabled = false;
        searchBtn.textContent = 'Buscar';
        
    } catch (error) {
        console.error('Error:', error);
        showMessage(`❌ Error: ${error.message}`, 'error');
        searchBtn.disabled = false;
        searchBtn.textContent = 'Buscar';
    }
}

// Mostrar información de venta
function mostrarInfoVenta() {
    document.getElementById('saleFolio').textContent = `#${String(currentSale.id).padStart(8, '0')}`;
    document.getElementById('saleDate').textContent = currentSale.fecha;
    document.getElementById('saleTotal').textContent = `$${parseFloat(currentSale.total).toFixed(2)}`;
    document.getElementById('salePaymentMethod').textContent = currentSale.metodo_pago === 'efectivo' ? 'EFECTIVO' : 'TRANSFERENCIA';
    
    document.getElementById('saleInfo').classList.add('show');
}

// Mostrar productos para devolución
function mostrarProductos() {
    const tbody = document.getElementById('productsTableBody');
    tbody.innerHTML = '';
    
    currentDetalles.forEach((detalle, index) => {
        const row = document.createElement('tr');
        
        const subtotalInput = document.createElement('td');
        const subtotalDisplay = document.createElement('span');
        subtotalDisplay.textContent = `$${parseFloat(detalle.subtotal).toFixed(2)}`;
        subtotalDisplay.id = `subtotal-${index}`;
        subtotalInput.appendChild(subtotalDisplay);
        
        row.innerHTML = `
            <td>${escapeHtml(detalle.producto_nombre)}</td>
            <td><strong>${detalle.cantidad}</strong> ${detalle.tipo_venta === 'paquete' ? 'paq.' : 'pza.'}</td>
            <td>
                <div class="quantity-control">
                    <button class="qty-btn" onclick="decreaseQty(${index})">−</button>
                    <input type="number" class="qty-input" id="qty-${index}" value="0" min="0" max="${detalle.cantidad}" onchange="updateSubtotal(${index})">
                    <button class="qty-btn" onclick="increaseQty(${index})">+</button>
                </div>
            </td>
            <td>$${parseFloat(detalle.precio_unitario).toFixed(2)}</td>
            <td id="subtotal-${index}">$0.00</td>
        `;
        
        tbody.appendChild(row);
        devolucionSelecciones[detalle.id] = 0;
    });
    
    document.getElementById('productsTable').classList.add('show');
    document.getElementById('returnForm').classList.add('show');
}

// Aumentar cantidad
function increaseQty(index) {
    const input = document.getElementById(`qty-${index}`);
    const max = currentDetalles[index].cantidad;
    let value = parseInt(input.value) || 0;
    
    if (value < max) {
        value++;
        input.value = value;
        updateSubtotal(index);
    }
}

// Disminuir cantidad
function decreaseQty(index) {
    const input = document.getElementById(`qty-${index}`);
    let value = parseInt(input.value) || 0;
    
    if (value > 0) {
        value--;
        input.value = value;
        updateSubtotal(index);
    }
}

// Actualizar subtotal
function updateSubtotal(index) {
    const input = document.getElementById(`qty-${index}`);
    const qty = parseInt(input.value) || 0;
    const detalle = currentDetalles[index];
    const subtotal = qty * parseFloat(detalle.precio_unitario);
    
    document.getElementById(`subtotal-${index}`).textContent = `$${subtotal.toFixed(2)}`;
    devolucionSelecciones[detalle.id] = qty;
    
    // Actualizar resumen
    actualizarResumen();
}

// Actualizar resumen de devolución
function actualizarResumen() {
    let totalItems = 0;
    let totalAmount = 0;
    
    Object.keys(devolucionSelecciones).forEach((detalleId, index) => {
        const cantidad = devolucionSelecciones[detalleId];
        const detalle = currentDetalles[index];
        
        if (cantidad > 0) {
            totalItems += cantidad;
            totalAmount += cantidad * parseFloat(detalle.precio_unitario);
        }
    });
    
    document.getElementById('itemCount').textContent = totalItems;
    document.getElementById('returnAmount').textContent = `$${totalAmount.toFixed(2)}`;
    document.getElementById('totalReturn').textContent = `$${totalAmount.toFixed(2)}`;
}

// Procesar devolución
async function procesarDevolucion() {
    // Validar que haya artículos seleccionados
    let totalItems = 0;
    const detalles = [];
    
    currentDetalles.forEach((detalle, index) => {
        const cantidad = devolucionSelecciones[detalle.id];
        if (cantidad > 0) {
            totalItems += cantidad;
            detalles.push({
                detalle_venta_id: detalle.id,
                cantidad: cantidad
            });
        }
    });
    
    if (detalles.length === 0) {
        showMessage('Selecciona al menos un artículo para devolver', 'error');
        return;
    }
    
    // Validar formulario
    const motivo = document.getElementById('motivo').value;
    const tipoReembolso = document.getElementById('tipoReembolso').value;
    const notas = document.getElementById('notas').value;
    
    if (!motivo) {
        showMessage('Selecciona un motivo de devolución', 'error');
        return;
    }
    
    if (!tipoReembolso) {
        showMessage('Selecciona un tipo de reembolso', 'error');
        return;
    }
    
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Procesando...';
    
    try {
        const response = await fetch('/ventas/procesar_devolucion/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                venta_id: currentSale.id,
                detalles: detalles,
                motivo: motivo,
                tipo_reembolso: tipoReembolso,
                notas: notas
            })
        });
        
        const resultado = await response.json();
        
        if (!response.ok || !resultado.exito) {
            showMessage(`❌ Error: ${resultado.error || 'Error desconocido'}`, 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Procesar Devolución';
            return;
        }
        
        // Éxito
        showMessage(`✓ ¡Devolución procesada exitosamente! Folio: ${resultado.devolucion_id} | Monto: $${parseFloat(resultado.total_devuelto).toFixed(2)}`, 'success');
        
        // Resetear después de 2 segundos
        setTimeout(() => {
            resetForm();
            document.getElementById('ventaIdInput').focus();
        }, 2000);
        
        submitBtn.disabled = false;
        submitBtn.textContent = 'Procesar Devolución';
        
    } catch (error) {
        console.error('Error:', error);
        showMessage(`❌ Error: ${error.message}`, 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Procesar Devolución';
    }
}

// Resetear formulario
function resetForm() {
    document.getElementById('ventaIdInput').value = '';
    document.getElementById('motivo').value = '';
    document.getElementById('tipoReembolso').value = '';
    document.getElementById('notas').value = '';
    document.getElementById('searchStatus').textContent = '';
    
    document.getElementById('saleInfo').classList.remove('show');
    document.getElementById('productsTable').classList.remove('show');
    document.getElementById('returnForm').classList.remove('show');
    
    currentSale = null;
    currentDetalles = [];
    devolucionSelecciones = {};
    
    document.getElementById('itemCount').textContent = '0';
    document.getElementById('returnAmount').textContent = '$0.00';
    document.getElementById('totalReturn').textContent = '$0.00';
}

// Obtener CSRF token
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

// Enter en input para buscar
document.addEventListener('DOMContentLoaded', () => {
    const ventaIdInput = document.getElementById('ventaIdInput');
    if (ventaIdInput) {
        ventaIdInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                buscarVenta();
            }
        });
    }
});
