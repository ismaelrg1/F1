from backend.app.utils.socket import socketio
from backend.application import create_app
import os

app = create_app()

def main():
    app_env = os.getenv("APP_ENV", "development").lower()
    port = int(os.getenv("PORT", "5000"))

    if app_env == "production":
        # En producción con Tailscale Funnel: NO TLS aquí.
        # Escucha solo en localhost por seguridad.
        host = "127.0.0.1"
        debug = False
        use_reloader = False
        log_msg = f"Servidor Flask-SocketIO en HTTP (production) en {host}:{port}"
    else:
        # Desarrollo: accesible desde la red local, con debug y autoreload
        host = "0.0.0.0"
        debug = True
        use_reloader = True
        log_msg = f"Servidor Flask-SocketIO en HTTP (development) en {host}:{port}"

    print(log_msg)

    # Nota: si usas eventlet en tu proyecto, Flask-SocketIO lo usará si está instalado.
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        use_reloader=use_reloader,
    )

if __name__ == "__main__":
    main()
