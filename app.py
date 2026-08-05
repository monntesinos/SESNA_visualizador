import os
import math
from datetime import datetime
from flask import Flask, render_template, request, jsonify
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
    filtro_estado = request.args.get('estado')
    filtro_texto = request.args.get('q')

    # Lista de años disponible para el filtro: de 2023 al año actual
    anio_actual = datetime.now().year
    anos_disponibles = list(range(anio_actual, 2022, -1))  # ej. [2026, 2025, ..., 2023]

    # Lista de estados para el <select>, generada desde la tabla 'estado' de Supabase
    try:
        respuesta_estados = supabase.table('estado').select('id, name').order('name').execute()
        lista_estados = respuesta_estados.data
    except Exception as e:
        print(f"Error al obtener estados: {e}")
        lista_estados = []

    try:
        # 2. Iniciamos la consulta base
        consulta = supabase.table('variables').select('nombre, eje, institucion, valor', count='exact')
        
        # 3. Vamos agregando condiciones dinámicamente solo si tienen un valor
        if filtro_texto:
            consulta = consulta.ilike('nombre', f'%{filtro_texto}%')

        if filtro_eje:
            consulta = consulta.eq('eje', filtro_eje)
            
        if filtro_tema:
            consulta = consulta.eq('tema', filtro_tema)
            
        if filtro_ano:
            consulta = consulta.eq('ano', filtro_ano)

        # El nivel de gobierno se deriva de la columna 'estado':
        # 'No aplica' = Federal, cualquier otro valor = Estatal/Municipal
        if filtro_nivel == 'federal':
            consulta = consulta.eq('estado', 'No aplica')

        elif filtro_nivel == 'estatal':
            consulta = consulta.neq('estado', 'No aplica')
            if filtro_estado:
                consulta = consulta.eq('estado', filtro_estado)

        # Si filtro_nivel es 'todos' (o no viene), no se aplica condición sobre 'estado'

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
        total_pages=total_pages,
        anos_disponibles=anos_disponibles,
        lista_estados=lista_estados,
        filtro_eje=filtro_eje,
        filtro_tema=filtro_tema,
        filtro_ano=filtro_ano,
        filtro_nivel=filtro_nivel,
        filtro_estado=filtro_estado,
        filtro_texto=filtro_texto
    )


@app.route("/api/sugerencias-variables")
def sugerencias_variables():
    """Devuelve nombres de variables que coinciden con el texto escrito,
    para el autocompletado de la barra de búsqueda."""
    texto = request.args.get('q', '').strip()

    if len(texto) < 2:
        return jsonify([])

    try:
        respuesta = (
            supabase.table('variables')
            .select('nombre')
            .ilike('nombre', f'%{texto}%')
            .limit(20)
            .execute()
        )
        # Quitamos duplicados (puede haber la misma variable repetida por
        # distintos estados/años) conservando el orden de aparición.
        nombres_unicos = list(dict.fromkeys(fila['nombre'] for fila in respuesta.data if fila.get('nombre')))
        return jsonify(nombres_unicos[:8])
    except Exception as e:
        print(f"Error al obtener sugerencias: {e}")
        return jsonify([])


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