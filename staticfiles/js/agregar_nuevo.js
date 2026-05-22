// Función para escapar HTML y prevenir XSS
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

// Mostrar/ocultar opciones de paquete
function togglePackOptions() {
    const check = document.getElementById('sellsByPack');
    const packOptions = document.getElementById('packOptions');
    
    if (check.checked) {
        packOptions.classList.add('show');
        updatePackPreview();
    } else {
        packOptions.classList.remove('show');
        // Limpiar campos
        document.getElementById('packQuantity').value = '6';
        document.getElementById('pricePack').value = '';
    }
}

// Actualizar vista previa de cantidad por paquete
function updatePackPreview() {
    const packQuantity = document.getElementById('packQuantity').value || 6;
    document.getElementById('packQuantityPreview').textContent = packQuantity;
}

// Función para limpiar formulario sin pedir confirmación (después de guardar)
function resetFormClean() {
    document.getElementById('productForm').reset();
    document.getElementById('packOptions').classList.remove('show');
    document.getElementById('packQuantityPreview').textContent = '6';
    document.getElementById('sku').focus();
}

// Función para limpiar formulario con confirmación (botón Limpiar)
function clearForm() {
    const modal = document.getElementById('clearConfirmModal');
    if (modal) {
        modal.classList.add('show');
    }
}

// Función para confirmar limpiar desde el modal
function confirmClear() {
    const modal = document.getElementById('clearConfirmModal');
    document.getElementById('productForm').reset();
    document.getElementById('packOptions').classList.remove('show');
    document.getElementById('successMessage').classList.remove('show');
    document.getElementById('packQuantityPreview').textContent = '6';
    
    if (modal) {
        modal.classList.remove('show');
    }
    document.getElementById('sku').focus();
}

// Función para cancelar limpiar
function cancelClear() {
    const modal = document.getElementById('clearConfirmModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// Función para mostrar errores
function showErrorMsg(message) {
    showError('Error', message);
}

// Función para mostrar éxito
function showSuccessMsg(message) {
    showSuccess('¡Producto guardado!', message);
}

function saveProduct() {
    // Obtener valores
    const sku = document.getElementById('sku').value.trim();
    const name = document.getElementById('name').value.trim();
    const stock = parseInt(document.getElementById('stock').value) || 0;
    const priceUnit = parseFloat(document.getElementById('priceUnit').value);
    const stockMinimo = parseInt(document.getElementById('stockMinimo').value);
    const categoria = document.getElementById('categoria').value;
    const sellsByPack = document.getElementById('sellsByPack').checked;
    const packQuantity = sellsByPack ? parseInt(document.getElementById('packQuantity').value) : null;
    const pricePack = sellsByPack ? parseFloat(document.getElementById('pricePack').value) : null;

    // Validaciones básicas
    if (!sku || !name || !priceUnit || !categoria) {
        showErrorMsg('Por favor completa los campos obligatorios: SKU, Nombre, Precio por unidad y Categoría');
        return;
    }

    // Validar Stock Mínimo
    if (isNaN(stockMinimo) || stockMinimo < 0) {
        showErrorMsg('⚠️ Por favor ingresa un Stock mínimo VÁLIDO (número mayor o igual a 0).\n\nEste valor es importante para las alertas de bajo stock.');
        document.getElementById('stockMinimo').focus();
        return;
    }

    console.log('✅ Stock mínimo capturado:', stockMinimo);

    // Validar SKU
    if (sku.length < 3) {
        showErrorMsg('El código SKU debe tener al menos 3 caracteres');
        return;
    }

    // Validar paquete
    if (sellsByPack) {
        if (!packQuantity || packQuantity < 2) {
            showErrorMsg('La cantidad por paquete debe ser al menos 2');
            return;
        }
        if (!pricePack || pricePack <= 0) {
            showErrorMsg('El precio del paquete es obligatorio');
            return;
        }
    }

    // Preparar datos para enviar al backend
    const productData = {
        sku: sku,
        nombre: name,
        precio_pieza: parseFloat(priceUnit),
        categoria_id: parseInt(categoria),
        stock: stock,
        stock_minimo: stockMinimo,
        precio_paquete: sellsByPack ? parseFloat(pricePack) : null,
        cantidad_paquete: sellsByPack ? parseInt(packQuantity) : 1,
    };

    // Enviar al backend
    fetch('/productos/crear/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(productData)
    })
    .then(response => response.json().then(data => ({ status: response.status, data: data })))
    .then(({ status, data }) => {
        if (status === 200 && data.exito) {
            // Éxito: mostrar mensaje y limpiar formulario
            let packInfo = '';
            if (sellsByPack) {
                packInfo = ` | Paquete: $${pricePack.toFixed(2)} (${packQuantity} pz)`;
            }
            
            const message = `SKU: ${escapeHtml(sku)} | Unidad: $${priceUnit.toFixed(2)}${packInfo} | Stock: ${stock} unidades | Mín. Alerta: ${stockMinimo}`;
            
            showSuccessMsg(message);
            resetFormClean();
        } else if (!data.exito) {
            // Error del servidor con mensaje específico
            showErrorMsg(data.error || 'No se pudo guardar el producto');
        } else {
            // Otro tipo de error
            showErrorMsg('Error inesperado. Intenta de nuevo.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showErrorMsg(`Error de conexión: ${error.message}`);
    });
}

// Función para obtener el CSRF token de las cookies
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

// Inicializar eventos cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Evento para actualizar preview cuando cambia la cantidad
    const packQuantityInput = document.getElementById('packQuantity');
    if (packQuantityInput) {
        packQuantityInput.addEventListener('input', updatePackPreview);
    }

    // Permitir solo números en SKU
    const skuInput = document.getElementById('sku');
    if (skuInput) {
        skuInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
        });
        
        // Manejar Enter en campo SKU: mover a siguiente campo en lugar de enviar formulario
        // Esto previene que el scanner (que envía Enter) dispare un submit accidental
        skuInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                // Mover al siguiente campo (Nombre)
                const nameInput = document.getElementById('name');
                if (nameInput) {
                    nameInput.focus();
                }
            }
        });
        
        skuInput.focus();
    }

    // Atajo de teclado: F2 para limpiar
    document.addEventListener('keydown', (e) => {
        if (e.key === 'F2') {
            e.preventDefault();
            clearForm();
        }
    });
});
