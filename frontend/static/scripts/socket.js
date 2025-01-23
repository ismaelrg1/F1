// Conectar a Socket.IO
var socket = io();

// Escuchar el evento 'update_schedule'
socket.on('update_schedule', function(data) {
    console.log("Nuevo calendario recibido:", data.races);

    // Actualiza la lista de carreras en la página
    updateRaceList(data.races);
});

// Función para actualizar el DOM con las nuevas carreras
function updateRaceList(races) {
    var container = document.querySelector('.container');
    container.innerHTML = '';  // Limpiar el contenido existente

    races.forEach(function(race) {
        var raceElement = `
            <a href="/race/${race.round}">
                <div class="race-card">
                    <div class="race-header">
                        <span class="round">ROUND ${race.round}</span>
                        <div class="date">
                            <span>${race.date.split(' ')[0]}</span>
                            <span>${race.date.split(' ')[1]}</span>
                        </div>
                        <img src="${race.flag_url}" alt="Bandera de ${race.country}" class="flag">
                    </div>
                    <div class="race-body">
                        <h2>${race.country}</h2>
                        <p>${race.race_name}</p>
                        <img src="${race.circuit_image_url}" alt="Circuito de ${race.country}" class="circuit" loading="lazy">
                    </div>
                </div>
            </a>
        `;
        container.innerHTML += raceElement;
    });
}