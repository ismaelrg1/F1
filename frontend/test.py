from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///f1predictions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Participante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    puntos = db.Column(db.Integer, nullable=False)

@app.route('/ranking')
def mostrar_ranking():
    participantes = Participante.query.order_by(Participante.puntos.desc()).all()
    return render_template('race_detail.html', participantes=participantes)


def agregar_participantes_ejemplo():
    # Ejemplos de participantes
    participantes = [
        Participante(nombre='Juan Pérez', puntos=10),
        Participante(nombre='María García', puntos=15),
        Participante(nombre='Carlos Fernández', puntos=8),
        Participante(nombre='Lucía Martínez', puntos=20)
    ]

    # Agregar participantes a la base de datos
    db.session.add_all(participantes)
    db.session.commit()


# Llamar a la función para agregar ejemplos
with app.app_context():
    agregar_participantes_ejemplo()

if __name__ == '__main__':
    app.run(debug=True)