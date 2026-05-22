// Global variables
let currentSale = null;
let currentDetalles = [];
let devolucionSelecciones = {};

// Function to show messages
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

// Escape HTML for security
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

// Get CSRF token
function getCSRFToken() {
    const input = document.querySelector('input[name=csrfmiddlewaretoken]');
    if (input) return input.value;
    return '';
}

// Search sale by ID
async function buscarVenta() {
    const ventaId = document.getElementById('ventaIdInput').value.trim();
    
    if (!ventaId) {
        showMessage('Please enter a sale ID', 'error');
        return;
    }
    
    if (isNaN(ventaId) || ventaId <= 0) {
        showMessage('The ID must be a valid number', 'error');
        return;
    }
    
    const searchBtn = document.getElementById('searchBtn');
    const searchStatus = document.getElementById('searchStatus');
    searchBtn.disabled = true;
    searchBtn.textContent = 'Searching...';
    searchStatus.textContent = 'Searching sale...';
    
    try {
        const response = await fetch(`/ventas/buscar_devolucion/?venta_id=${ventaId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.exito) {
            showMessage(`Error: ${data.error || 'Sale not found'}`, 'error');
            searchStatus.textContent = '';
            resetForm();
            searchBtn.disabled = false;
            searchBtn.textContent = 'Search';
            return;
        }
        
        // Save sale data
        currentSale = data.venta;
        currentDetalles = data.detalles;
        devolucionSelecciones = {};
        
        // Show sale information
        mostrarInfoVenta();
        
        // Show products table
        mostrarProductos();
        
        searchStatus.textContent = `Sale found: ${data.detalles.length} item(s)`;
        searchBtn.disabled = false;
        searchBtn.textContent = 'Search';
        
    } catch (error) {
        console.error('Error:', error);
        showMessage(`Error: ${error.message}`, 'error');
        searchBtn.disabled = false;
        searchBtn.textContent = 'Search';
    }
}

// Show sale information
function mostrarInfoVenta() {
    document.getElementById('saleFolio').textContent = `#${String(currentSale.id).padStart(8, '0')}`;
    document.getElementById('saleDate').textContent = currentSale.fecha;
    document.getElementById('saleTotal').textContent = `$${parseFloat(currentSale.total).toFixed(2)}`;
    document.getElementById('salePaymentMethod').textContent = currentSale.metodo_pago === 'efectivo' ? 'CASH' : 'TRANSFER';
    
    document.getElementById('saleInfo').classList.add('show');
}

// Show products for return
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
            <td><strong>${detalle.cantidad}</strong> ${detalle.tipo_venta === 'paquete' ? 'pkg' : 'pc'}</td>
            <td>
                <div class="quantity-control">
                    <button class="qty-btn" onclick="decreaseQty(${index})">-</button>
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

// Increase quantity
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

// Decrease quantity
function decreaseQty(index) {
    const input = document.getElementById(`qty-${index}`);
    let value = parseInt(input.value) || 0;
    
    if (value > 0) {
        value--;
        input.value = value;
        updateSubtotal(index);
    }
}

// Update subtotal
function updateSubtotal(index) {
    const input = document.getElementById(`qty-${index}`);
    const qty = parseInt(input.value) || 0;
    const detalle = currentDetalles[index];
    const subtotal = qty * parseFloat(detalle.precio_unitario);
    
    document.getElementById(`subtotal-${index}`).textContent = `$${subtotal.toFixed(2)}`;
    devolucionSelecciones[detalle.id] = qty;
    
    // Update summary
    actualizarResumen();
}

// Update return summary
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

// Process return
async function procesarDevolucion() {
    // Validate selected items
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
        showMessage('Select at least one item to return', 'error');
        return;
    }
    
    // Validate form
    const motivo = document.getElementById('motivo').value;
    const tipoReembolso = document.getElementById('tipoReembolso').value;
    const notas = document.getElementById('notas').value;
    
    if (!motivo) {
        showMessage('Select a return reason', 'error');
        return;
    }
    
    if (!tipoReembolso) {
        showMessage('Select a refund type', 'error');
        return;
    }
    
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';
    
    try {
        const response = await fetch('/ventas/procesar_devolucion/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
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
            showMessage(`Error: ${resultado.error || 'Unknown error'}`, 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Process Return';
            return;
        }
        
        // Success
        showMessage(`Return processed successfully! ID: ${resultado.devolucion_id} | Amount: $${parseFloat(resultado.total_devuelto).toFixed(2)}`, 'success');
        
        // Reset after 2 seconds
        setTimeout(() => {
            resetForm();
            document.getElementById('ventaIdInput').focus();
        }, 2000);
        
        submitBtn.disabled = false;
        submitBtn.textContent = 'Process Return';
        
    } catch (error) {
        console.error('Error:', error);
        showMessage(`Error: ${error.message}`, 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Process Return';
    }
}

// Reset form
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

// Add Enter key listener
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
