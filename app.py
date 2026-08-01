import os
import math
from flask import Flask, render_template, request
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar las variables del archivo .env
load_dotenv()

app = Flask(__name__)

# Configuración del cliente de Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/")
def inicio():
    """Página de inicio."""
    return render_template("inicio.html", pagina_activa="inicio")


@app.route("/buscador-ciudadano")
def buscador_ciudadano():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    start = (page - 1) * per_page
    end = start + per_page - 1

    # 1. Atrapamos todos los posibles valores del panel izquierdo
    filtro_eje = request.args.get('eje')
    filtro_tema = request.args.get('tema')
    filtro_ano = request.args.get('ano')
    filtro_nivel = request.args.get('nivel_gobierno')

    try:
        # 2. Iniciamos la consulta base
        consulta = supabase.table('variables').select('nombre, eje, institucion, valor', count='exact')
        
        # 3. Vamos agregando condiciones dinámicamente solo si tienen un valor
        if filtro_eje:
            consulta = consulta.eq('eje', filtro_eje)
            
        if filtro_tema:
            consulta = consulta.eq('tema', filtro_tema)
            
        if filtro_ano:
            consulta = consulta.eq('ano', filtro_ano)
            
        # Como en tu HTML pusiste "todos" por defecto, lo ignoramos para no romper la consulta
        if filtro_nivel and filtro_nivel != 'todos':
            # OJO: Asegúrate de que la columna en Supabase se llame realmente 'nivel_gobierno'
            consulta = consulta.eq('nivel_gobierno', filtro_nivel) 
            
        # 4. Al final, aplicamos la paginación y ejecutamos todo junto
        respuesta = consulta.range(start, end).execute()
            
        lista_variables = respuesta.data
        total_registros = respuesta.count
        total_pages = math.ceil(total_registros / per_page) if total_registros else 1
        
    except Exception as e:
        print(f"Error de conexión: {e}")
        lista_variables = []
        total_pages = 1
        page = 1

    return render_template(
        "buscador-ciudadano.html", 
        pagina_activa="buscador-ciudadano", 
        variables_supabase=lista_variables,
        page=page,
        total_pages=total_pages
    )


@app.route("/busqueda-avanzada")
def busqueda_avanzada():
    return render_template("busqueda-avanzada.html", pagina_activa="busqueda-avanzada")


@app.route("/contacto")
def contacto():
    return render_template("contacto.html", pagina_activa="contacto")


@app.route("/preguntas-frecuentes")
def preguntas_frecuentes():
    return render_template("preguntas-frecuentes.html", pagina_activa="preguntas-frecuentes")


if __name__ == "__main__":
    app.run(debug=True)