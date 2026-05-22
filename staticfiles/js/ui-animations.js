/**
 * Papelería Yessy · Utilidades de UI y Animaciones
 */

// ==================
// Loading Indicators
// ==================

/**
 * Muestra un indicador de carga global
 */
function mostrarCargando(mensaje = 'Cargando...') {
    // Crear overlay si no existe
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            animation: fadeIn 0.3s ease;
        `;
        document.body.appendChild(overlay);
    }
    
    // Crear spinner
    overlay.innerHTML = `
        <div style="text-align: center; background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);">
            <div class="loading-spinner" style="width: 40px; height: 40px; margin: 0 auto 1rem;"></div>
            <p style="color: #2d3e50; margin: 0;">${mensaje}</p>
        </div>
    `;
    
    overlay.style.display = 'flex';
}

/**
 * Oculta el indicador de carga global
 */
function ocultarCargando() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// ==================
// Botones con loading
// ==================

/**
 * Activa estado de carga en un botón
 * @param {HTMLElement|string} btnElement - El elemento botón o su ID
 */
function activarCargandoBoton(btnElement) {
    if (typeof btnElement === 'string') {
        btnElement = document.getElementById(btnElement);
    }
    
    if (!btnElement) return;
    
    const textoOriginal = btnElement.innerHTML;
    btnElement.disabled = true;
    btnElement.dataset.textoOriginal = textoOriginal;
    btnElement.innerHTML = `
        <span class="loading-spinner" style="width: 16px; height: 16px; margin-right: 0.5rem; display: inline-block;"></span>
        Procesando...
    `;
}

/**
 * Desactiva estado de carga en un botón
 * @param {HTMLElement|string} btnElement - El elemento botón o su ID
 */
function desactivarCargandoBoton(btnElement) {
    if (typeof btnElement === 'string') {
        btnElement = document.getElementById(btnElement);
    }
    
    if (!btnElement) return;
    
    const textoOriginal = btnElement.dataset.textoOriginal || btnElement.innerHTML;
    btnElement.disabled = false;
    btnElement.innerHTML = textoOriginal;
}

// ==================
// Transiciones de Página
// ==================

/**
 * Transición suave entre páginas
 */
function transicionPagina(url, duracion = 300) {
    mostrarCargando();
    setTimeout(() => {
        window.location.href = url;
    }, duracion);
}

// ==================
// Toast Notifications
// ==================

/**
 * Muestra una notificación toast
 * @param {string} mensaje - El mensaje a mostrar
 * @param {string} tipo - 'success', 'error', 'warning', 'info'
 * @param {number} duracion - Duracion en ms (0 = manual)
 */
function mostrarToast(mensaje, tipo = 'info', duracion = 3000) {
    const container = document.getElementById('toast-container') || crearToastContainer();
    
    const toast = document.createElement('div');
    
    const iconos = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-warning',
        info: 'fa-info-circle'
    };
    
    const colores = {
        success: '#27ae60',
        error: '#e74c3c',
        warning: '#f39c12',
        info: '#3498db'
    };
    
    toast.innerHTML = `
        <div style="
            background: white;
            border-left: 4px solid ${colores[tipo]};
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            gap: 1rem;
            animation: slideInRight 0.4s ease-out;
            margin-bottom: 0.8rem;
        ">
            <i class="fas ${iconos[tipo]}" style="color: ${colores[tipo]}; font-size: 1.2rem;"></i>
            <span style="color: #2d3e50;">${mensaje}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="
                background: none;
                border: none;
                color: #999;
                cursor: pointer;
                font-size: 1.2rem;
                margin-left: auto;
            ">×</button>
        </div>
    `;
    
    container.appendChild(toast);
    
    if (duracion > 0) {
        setTimeout(() => {
            toast.remove();
        }, duracion);
    }
}

/**
 * Crea el contenedor de toasts si no existe
 */
function crearToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
        position: fixed;
        top: 2rem;
        right: 2rem;
        z-index: 9000;
        width: 350px;
        max-width: 100%;
    `;
    document.body.appendChild(container);
    return container;
}

// ==================
// Confirmación con Modal
// ==================

/**
 * Muestra un modal de confirmación
 * @param {string} titulo - Título del modal
 * @param {string} mensaje - Mensaje a mostrar
 * @param {Function} onConfirm - Callback al confirmar
 * @param {Function} onCancel - Callback al cancelar
 */
function confirmar(titulo, mensaje, onConfirm, onCancel = null) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9998;
        animation: fadeIn 0.3s ease;
    `;
    
    modal.innerHTML = `
        <div style="
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            max-width: 400px;
            animation: scalePop 0.3s ease;
        ">
            <h3 style="color: #e8a87c; margin-bottom: 1rem;">${titulo}</h3>
            <p style="color: #2d3e50; margin-bottom: 2rem;">${mensaje}</p>
            <div style="display: flex; gap: 1rem; justify-content: flex-end;">
                <button onclick="this.closest('div').parentElement.remove()" style="
                    padding: 0.6rem 1.2rem;
                    background: #ecf0f1;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: background 0.2s;
                ">Cancelar</button>
                <button onclick="
                    this.closest('div').parentElement.remove();
                    onConfirm();
                " style="
                    padding: 0.6rem 1.2rem;
                    background: #e8a87c;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: background 0.2s;
                ">Confirmar</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Cerrar al hacer click afuera
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
            if (onCancel) onCancel();
        }
    });
}

// ==================
// Smooth Scroll
// ==================

/**
 * Scroll suave a un elemento
 * @param {string|HTMLElement} target - Selector CSS o elemento
 */
function smoothScroll(target) {
    if (typeof target === 'string') {
        target = document.querySelector(target);
    }
    
    if (target) {
        target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// ==================
// Inicialización en Carga
// ==================

document.addEventListener('DOMContentLoaded', () => {
    // Agregar clase para animación en carga
    document.body.style.opacity = '1';
    
    // Setup de eventos globales
    setupGlobalListeners();
});

/**
 * Setup de listeners globales
 */
function setupGlobalListeners() {
    // Links que abren modales
    document.querySelectorAll('a.modal-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            mostrarCargando('Abriendo...');
            setTimeout(() => {
                window.location.href = link.href;
            }, 200);
        });
    });
    
    // Formularios con loading automático
    document.querySelectorAll('form.auto-load').forEach(form => {
        form.addEventListener('submit', () => {
            mostrarCargando('Enviando...');
        });
    });
}

// Exportar para uso global
window.UI = {
    mostrarCargando,
    ocultarCargando,
    activarCargandoBoton,
    desactivarCargandoBoton,
    transicionPagina,
    mostrarToast,
    confirmar,
    smoothScroll
};
