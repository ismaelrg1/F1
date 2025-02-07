from backend.app.utils.socket_manager import socketio  # Importa solo socketio, sin app
from flask_socketio import join_room, leave_room
from flask import request

# Emitir un evento a todos los usuarios conectados cuando se conecten
@socketio.on('connect', namespace='/calendario')
def handle_connect():
    join_room('room')
    print(f"Cliente conectado -> {request.sid}")

@socketio.on('disconnect', namespace='/calendario')
def handle_disconnect():
    leave_room('room')
    print("Cliente desconectado")

# @socketio.on('update_schedule', namespace='/calendario')
# def handle_update_schedule(data):
#     print(f"Cliente actualizado -> {data}")
