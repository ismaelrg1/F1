from backend.app.utils.socket import socketio
from backend.application import create_app
import eventlet
import eventlet.wsgi
import ssl

app = create_app()

def main():
    # Configurar SSL manualmente
    cert = "fullchain.pem"
    key = "privkey.pem"

    # Cargar SSL en un socket seguro
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=cert, keyfile=key)

    # Crear el socket seguro
    socket = eventlet.listen(('0.0.0.0', 5000))
    secure_socket = eventlet.wrap_ssl(socket, certfile=cert, keyfile=key, server_side=True)

    print("🚀 Servidor Flask-SocketIO corriendo en HTTPS en el puerto 5000")
    eventlet.wsgi.server(secure_socket, app)

    # socketio.run(app, host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))

# Si se ejecuta directamente, arranca el servidor con soporte para WebSockets
if __name__ == "__main__":
    main()
