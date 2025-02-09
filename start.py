from backend.app.utils.socket import socketio
from backend.application import create_app

app = create_app()

def main():
    socketio.run(app, host='0.0.0.0', port=5000)

# Si se ejecuta directamente, arranca el servidor con soporte para WebSockets
if __name__ == "__main__":
    main()