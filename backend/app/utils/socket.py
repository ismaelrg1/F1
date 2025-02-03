from backend.app.utils.socket_manager import socketio  # Importa solo socketio, sin app

# Emitir un evento a todos los usuarios conectados cuando se conecten
@socketio.on('connect')
def handle_connect():
    print("Cliente conectado")

@socketio.on('disconnect')
def handle_disconnect():
    print("Cliente desconectado")