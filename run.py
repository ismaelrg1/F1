from backend.app.utils.socket import socketio
from backend.application import create_app

app = create_app()

# Si se ejecuta directamente, arranca el servidor con soporte para WebSockets
if __name__ == "__main__":
    socketio.run(app, debug=True)