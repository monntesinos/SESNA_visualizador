"""
CICM - Catálogo de Información sobre la Corrupción en México
Punto de entrada de la aplicación Flask.
"""

from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def inicio():
    """Página de inicio (incluye la sección 'Acerca del CICM' fusionada)."""
    return render_template("inicio.html")


@app.route("/buscador-ciudadano")
def buscador_ciudadano():
    return render_template("buscador-ciudadano.html")


@app.route("/busqueda-avanzada")
def busqueda_avanzada():
    return render_template("busqueda-avanzada.html")


@app.route("/contacto")
def contacto():
    return render_template("contacto.html")


@app.route("/preguntas-frecuentes")
def preguntas_frecuentes():
    return render_template("preguntas-frecuentes.html")


if __name__ == "__main__":
    app.run(debug=True)
