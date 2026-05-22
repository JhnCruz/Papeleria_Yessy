/**
 * Sistema de Notificaciones Global
 * Proporciona funciones para mostrar notificaciones bonitas en toda la aplicación
 */

// Estilos de notificación (se inyectan en el documento)
const notificationStyles = `
    <style>
        .notification-toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            min-width: 320px;
            max-width: 400px;
            padding: 1.2rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            z-index: 10000;
            animation: slideInRight 0.3s ease-out;
            font-family: 'Quicksand', sans-serif;
        }

        .notification-toast.success {
            background: #c9e4de;
            border-left: 4px solid #2d6a4f;
        }

        .notification-toast.error {
            background: white;
            border-left: 4px solid #f8acb4;
        }

        .notification-toast.warning {
            background: #fff5e6;
            border-left: 4px solid #e8a87c;
        }

        .notification-toast.info {
            background: #e8f4f8;
            border-left: 4px solid #4a7c8a;
        }

        .notification-toast i {
            font-size: 1.3rem;
            flex-shrink: 0;
            margin-top: 0.2rem;
        }

        .notification-toast.success i {
            color: #2d6a4f;
        }

        .notification-toast.error i {
            color: #f8acb4;
        }

        .notification-toast.warning i {
            color: #e8a87c;
        }

        .notification-toast.info i {
            color: #4a7c8a;
        }

        .notification-content {
            display: flex;
            flex-direction: column;
            gap: 0.3rem;
            flex: 1;
        }

        .notification-title {
            font-weight: 600;
            font-size: 0.95rem;
        }

        .notification-toast.success .notification-title {
            color: #2d6a4f;
        }

        .notification-toast.error .notification-title {
            color: #d46a6a;
        }

        .notification-toast.warning .notification-title {
            color: #9d6b53;
        }

        .notification-toast.info .notification-title {
            color: #4a7c8a;
        }

        .notification-message {
            font-size: 0.85rem;
            line-height: 1.4;
        }

        .notification-toast.success .notification-message {
            color: #1d4a3f;
        }

        .notification-toast.error .notification-message {
            color: #8b5a5a;
        }

        .notification-toast.warning .notification-message {
            color: #8b6b4f;
        }

        .notification-toast.info .notification-message {
            color: #3a5a6a;
        }

        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes fadeOut {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100px);
            }
        }

        .notification-toast.hide {
            animation: fadeOut 0.3s ease-out forwards;
        }

        @media (max-width: 640px) {
            .notification-toast {
                bottom: 1rem;
                right: 1rem;
                left: 1rem;
                max-width: none;
            }
        }
    </style>
`;

// Inyectar estilos en el documento
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectStyles);
    } else {
        injectStyles();
    }
    
    function injectStyles() {
        if (!document.querySelector('[data-notification-styles]')) {
            const styleContainer = document.createElement('div');
            styleContainer.setAttribute('data-notification-styles', 'true');
            styleContainer.innerHTML = notificationStyles;
            document.head.appendChild(styleContainer);
        }
    }
})();

/**
 * Mostrar notificación de éxito
 * @param {string} title - Título de la notificación
 * @param {string} message - Mensaje de la notificación
 * @param {number} duration - Duración en ms (default 4000)
 */
window.showSuccess = function(title, message = '', duration = 4000) {
    showNotification('success', '✓', title, message, duration);
};

/**
 * Mostrar notificación de error
 * @param {string} title - Título de la notificación
 * @param {string} message - Mensaje de la notificación
 * @param {number} duration - Duración en ms (default 5000)
 */
window.showError = function(title, message = '', duration = 5000) {
    showNotification('error', '⚠', title, message, duration);
};

/**
 * Mostrar notificación de advertencia
 * @param {string} title - Título de la notificación
 * @param {string} message - Mensaje de la notificación
 * @param {number} duration - Duración en ms (default 4000)
 */
window.showWarning = function(title, message = '', duration = 4000) {
    showNotification('warning', '!', title, message, duration);
};

/**
 * Mostrar notificación de información
 * @param {string} title - Título de la notificación
 * @param {string} message - Mensaje de la notificación
 * @param {number} duration - Duración en ms (default 3000)
 */
window.showInfo = function(title, message = '', duration = 3000) {
    showNotification('info', 'i', title, message, duration);
};

/**
 * Función interna para crear la notificación
 */
function showNotification(type, icon, title, message = '', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `notification-toast ${type}`;
    
    const iconMap = {
        'success': '<i class="fas fa-check-circle"></i>',
        'error': '<i class="fas fa-exclamation-circle"></i>',
        'warning': '<i class="fas fa-exclamation-triangle"></i>',
        'info': '<i class="fas fa-info-circle"></i>'
    };
    
    toast.innerHTML = `
        ${iconMap[type]}
        <div class="notification-content">
            <div class="notification-title">${escapeHtml(title)}</div>
            ${message ? `<div class="notification-message">${escapeHtml(message)}</div>` : ''}
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove después de la duración especificada
    if (duration > 0) {
        setTimeout(() => {
            toast.classList.add('hide');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, duration);
    }
    
    return toast;
}

/**
 * Escapar HTML para prevenir XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
