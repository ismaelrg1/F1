var socket;

// Espera a que el DOM se cargue
document.addEventListener("DOMContentLoaded",function(){
    // Conectar a Socket.IO
    socket = io('/calendario', {
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 3000
    });

    socket.on('connect', function() {
        console.log('Conectado al servidor');

        socket.emit('list_clients');
        socket.on('client_list', function(data) {
            console.log("📡 Clientes en la sala:", data.clients);
        });

        // Escuchar el evento 'update_schedule'
        socket.on('update_schedule', function(data) {
            console.log("📡 Recibidos nuevos datos de la carrera:", data);
            actualizarCalendario(data.races);
        });
    });

    socket.on('disconnect', function() {
        console.log("⚠️ Desconectado. Intentando reconectar...");
    });


});

// Función para actualizar el DOM con las nuevas carreras
function actualizarCalendario(races) {
    // Selecciona el contenedor que contiene las carreras.
    // En tu plantilla, este contenedor es el div con clase "container".
    var container = document.querySelector('.container');
    if (!container) return; // Si no se encuentra el contenedor, salir

    // Limpiar el contenido existente
    container.innerHTML = '';

    // Recorrer cada carrera y crear el HTML correspondiente
    races.forEach(function(race) {
        // Suponiendo que race.date es una cadena con espacio separando fecha y hora.
        var fechaPartes = race.date.split(' ');
        var raceElement = `
            <a href="/race/${race.round}">
                <div class="race-card">
                    <div class="race-header">
                        <span class="round">ROUND ${race.round}</span>
                        <div class="date">
                            <span>${fechaPartes[0]}</span>
                            <span>${fechaPartes[1] ? fechaPartes[1] : ''}</span>
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