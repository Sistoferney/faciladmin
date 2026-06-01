// JavaScript principal de FacilAdmin

document.addEventListener('DOMContentLoaded', function() {
    console.log('FacilAdmin cargado');
});

// Utilidades
const Utils = {
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP'
        }).format(amount);
    },

    formatDate: function(date) {
        return new Intl.DateTimeFormat('es-CO').format(new Date(date));
    },

    formatPhone: function(phone) {
        // Formatear número de teléfono
        return phone.replace(/(\d{2})(\d{4})(\d{4})/, '$1 $2 $3');
    }
};
