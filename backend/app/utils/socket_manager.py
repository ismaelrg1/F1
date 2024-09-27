from flask_socketio import SocketIO

# Inicializamos socketio sin asociarlo a la app todavía
socketio = SocketIO()
# Función para enviar actualizaciones a todos los usuarios conectados
def send_update_to_all(message, races):
    socketio.emit('update_schedule', {'message': message, 'races': races}, broadcast=True)