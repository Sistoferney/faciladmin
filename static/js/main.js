// JavaScript principal de FacilAdmin

document.addEventListener('DOMContentLoaded', function() {
    console.log('FacilAdmin cargado');
});

// Utilidades
const Utils = {
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('es-MX', {
            style: 'currency',
            currency: 'MXN'
        }).format(amount);
    },

    formatDate: function(date) {
        return new Intl.DateTimeFormat('es-MX').format(new Date(date));
    },

    formatPhone: function(phone) {
        // Formatear número de teléfono
        return phone.replace(/(\d{2})(\d{4})(\d{4})/, '$1 $2 $3');
    }
};
