
// Función para alternar entre el formulario y la tabla
function toggleContent(sectionId, showForm) {
    var form = document.querySelector(`#${sectionId}-form`);
    var results = document.querySelector(`#${sectionId}-results`);

    if (showForm) {
        form.style.display = 'block';
        results.style.display = 'none';
    } else {
        form.style.display = 'none';
        results.style.display = 'table';
    }
}

// Ejemplo de cómo llamar a la función
// Puedes usar lógica condicional según el estado real
document.addEventListener('DOMContentLoaded', function() {
    toggleContent('qualy', false); // Muestra el formulario de qualy
    toggleContent('race', true); // Muestra la tabla de carrera
});
