// ========================================
// CORTE DE CAJA - Cierre Diario
// ========================================

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

// Imprimir corte
function imprimirCorte() {
    const corteContent = document.querySelector('.cut-card').innerHTML;
    const printWindow = window.open('', '', 'width=800,height=600');
    
    const style = `
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .cut-card { max-width: 600px; }
            .summary-box, .payment-detail, .final-totals { margin: 1rem 0; }
            .cut-actions { display: none; }
        </style>
    `;
    
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Corte de Caja</title>
            ${style}
        </head>
        <body>
            <h1>📋 REPORTE DE CORTE DE CAJA</h1>
            <p>Papelería Yessy - ${new Date().toLocaleString('es-ES')}</p>
            ${corteContent}
        </body>
        </html>
    `);
    printWindow.document.close();
    
    setTimeout(() => {
        printWindow.print();
        printWindow.close();
    }, 250);
}

// Confirmar corte (abre modal)
function confirmarCorte() {
    const totalEl = document.querySelector('.total-row.grand strong');
    const total = totalEl ? totalEl.textContent : '$0.00';
    
    document.getElementById('confirmTotal').textContent = total;
    document.getElementById('confirmModal').style.display = 'flex';
}

// Cerrar modal
function cerrarModal() {
    document.getElementById('confirmModal').style.display = 'none';
}

// Realizar corte (POST al backend)
async function realizarCorte() {
    const confirmBtn = event.target;
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Procesando...';
    
    try {
        const response = await fetch('/caja/realizar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                notas: document.getElementById('cortesNotes').value || ''
            })
        });
        
        const resultado = await response.json();
        
        if (!response.ok || !resultado.exito) {
            alert(`❌ Error: ${resultado.error || 'Error desconocido'}`);
            confirmBtn.disabled = false;
            confirmBtn.textContent = 'Confirmar';
            return;
        }
        
        // Corte realizado exitosamente
        cerrarModal();
        
        const turnoTexto = resultado.turno === 1 ? 'Turno 1 (1 PM)' : 'Turno 2 (9 PM)';
        let turnoMensaje = '';
        
        if (resultado.turno === 1) {
            turnoMensaje = '¡Este fue automático! Seguí trabajando 💼';
        } else {
            turnoMensaje = '¡Gracias por tu trabajo! Vuelve mañana 💪';
        }
        
        const mensaje = `
✅ ¡${turnoTexto} REALIZADO CON ÉXITO!

📊 Resumen del cierre:
   • Total vendido: $${resultado.total_ventas.toFixed(2)}
   • Efectivo: $${resultado.total_efectivo.toFixed(2)}
   • Transferencias: $${resultado.total_transferencias.toFixed(2)}
   • ID Corte: #${resultado.corte_id}

⏰ ${new Date().toLocaleString('es-ES')}

${turnoMensaje}
        `;
        
        alert(mensaje);
        
        // Recargar página después de 2 segundos
        setTimeout(() => {
            window.location.reload();
        }, 2000);
        
    } catch (error) {
        console.error('Error:', error);
        alert(`❌ Error al procesar corte: ${error.message}`);
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Confirmar';
    }
}

// Ver detalle de un corte anterior
function verCorte(corteId) {
    window.location.href = `/caja/detalle/${corteId}/`;
}

// Cerrar modal con Escape
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            cerrarModal();
        }
    });
});
