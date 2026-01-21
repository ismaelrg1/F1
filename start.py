from backend.app.utils.socket import socketio
from backend.application import create_app
import eventlet
import eventlet.wsgi
import ssl
import os

app = create_app()

def main():
    app_env = os.getenv('APP_ENV', 'development').lower()

    if app_env != 'production':
        print("🚀 Servidor Flask-SocketIO corriendo en HTTP (modo desarrollo) en el puerto 5000")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
        return

    # Configurar SSL manualmente (produccion)
    cert = "fullchain.pem"
    key = "privkey.pem"

    if not (os.path.exists(cert) and os.path.exists(key)):
        print("⚠️  No se encontraron certificados SSL, arrancando en HTTP")
        socketio.run(app, host='0.0.0.0', port=5000)
        return

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
