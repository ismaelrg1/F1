from application import create_app

# Crea la instancia de la aplicación
app = create_app()

# Si se ejecuta directamente, arranca el servidor
if __name__ == "__main__":
    app.run(debug=True)