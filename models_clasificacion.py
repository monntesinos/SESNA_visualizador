"""

- Eje temático (carpeta ejes/): Eje 1-4 de la Política Nacional Anticorrupción.
- Proceso (carpeta Procesos/): las 4 etapas del combate a la corrupción -
- Prevención, Detección, Sanción y Fiscalización y control de recursos públicos.
Entrada: dos listas paralelas (nombres de variable, descripciones) 
Salida: una tabla (DataFrame) con cuatro columnas - Variable, Descripcion,
Eje, Proceso - no se exporta a Excel/CSV.
"""

import os
import re
import unicodedata
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

NOMBRE_MODELO = "paraphrase-multilingual-MiniLM-L12-v2"

# Pesos del score combinado (deben sumar 1.0). Se usan igual para el índice
# de ejes y para el de procesos.
PESOS_SENALES = {
    "centroide": 0.25,  # visión global de la categoría (robusta, poco discriminativa)
    "top_k": 0.35,      # evidencia local densa (chunks más parecidos)
    "tfidf": 0.20,       # solapamiento léxico con el documento completo de la categoría
    "bm25": 0.20,        # solapamiento con vocabulario controlado (conceptos/sinónimos/acciones)
}

TOP_K_CHUNKS = 3          # nº de chunks densos que se promedian por categoría
BM25_TOP_K = 5             # nº de frases clave que se promedian por categoría

MIN_PALABRAS_FUSION = 6     # párrafos más cortos que esto se fusionan con el siguiente
MAX_PALABRAS_CHUNK = 90      # tamaño máximo de un chunk antes de subdividirlo
################################################################################################################
# funciones que preparan los textos quitando palabras que no sirven
##################################
STOPWORDS_ES = {
    "a", "al", "algo", "algunas", "algunos", "ante", "asi", "aun", "cada",
    "como", "con", "cual", "cuales", "cuando", "de", "del", "donde", "dos",
    "durante", "e", "el", "ella", "ellas", "ellos", "en", "entre", "era",
    "es", "esa", "esas", "ese", "esos", "esta", "estas", "este", "esto",
    "estos", "fue", "ha", "hay", "la", "las", "le", "les", "lo", "los",
    "mas", "mediante", "mi", "mis", "muy", "no", "nos", "nosotros", "o",
    "otra", "otras", "otro", "otros", "para", "pero", "por", "porque",
    "que", "quien", "quienes", "se", "segun", "ser", "si", "sin", "sobre",
    "solo", "su", "sus", "tambien", "tan", "tanto", "te", "tiene", "traves",
    "tu", "u", "un", "una", "unas", "uno", "unos", "y", "ya",
}

ENCABEZADOS_SECCION = {
    "conceptos relacionados",
    "sinonimos y terminos relacionados",
    "instituciones relacionadas",
    "acciones relacionadas",
    "ejemplos",
}

SECCIONES_VOCABULARIO_CONTROLADO = {
    "conceptos relacionados",
    "sinonimos y terminos relacionados",
    "acciones relacionadas",
}

DISAGREGACIONES_GENERICAS = {
    "hombres",
    "mujeres",
    "subtotal",
    "total",
    "no identificado",
    "no especificado",
    "no aplica",
}

def quitar_acentos(texto):
    forma = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in forma if not unicodedata.combining(c))

def normalizar_espacios(texto):
    return re.sub(r"\s+", " ", texto).strip()

_PATRON_TOKEN = re.compile(r"[a-zA-Z]+")

def tokenizar(texto):
    texto_normalizado = quitar_acentos(str(texto).lower())
    tokens = _PATRON_TOKEN.findall(texto_normalizado)
    return [t for t in tokens if len(t) > 2 and t not in STOPWORDS_ES]


_PATRON_SEPARADOR_SUFIJO = re.compile(r"\s+-\s+")


def limpiar_sufijos_desagregacion(variable, genericos=DISAGREGACIONES_GENERICAS):
    """Recorta del final del nombre de la variable las categorías de
    desagregación genéricas (Hombres, Mujeres, Subtotal, Total, No
    identificado, No especificado), que no aportan señal temática propia.
    """
    segmentos = _PATRON_SEPARADOR_SUFIJO.split(str(variable).strip())
    while len(segmentos) > 1:
        clave = quitar_acentos(segmentos[-1].strip().lower())
        if clave in genericos:
            segmentos.pop()
        else:
            break
    return " - ".join(segmentos)


def construir_texto_consulta(variable, descripcion=None):
    """
    El nombre de la variable (ya sin sufijos de desagregación genéricos) se
    repite para que pese más que la descripción -normalmente más larga- 
    """
    variable_nucleo = normalizar_espacios(limpiar_sufijos_desagregacion(variable))
    if not descripcion or (isinstance(descripcion, float) and pd.isna(descripcion)):
        return variable_nucleo

    descripcion_limpia = normalizar_espacios(str(descripcion))
    return f"{variable_nucleo}. {variable_nucleo}. {descripcion_limpia}"

# Preparacion y division de los textos de referencia 

def dividir_texto_semantico(texto, min_palabras=MIN_PALABRAS_FUSION, max_palabras=MAX_PALABRAS_CHUNK):
    """Divide el texto de una categoría en unidades semánticamente
    coherentes
    """
    bloques = [normalizar_espacios(b) for b in re.split(r"\n\s*\n", texto.strip())]
    bloques = [b for b in bloques if b]

    fusionados = []
    pendiente = ""
    for bloque in bloques:
        actual = f"{pendiente} {bloque}".strip() if pendiente else bloque
        if len(actual.split()) < min_palabras:
            pendiente = actual
            continue
        fusionados.append(actual)
        pendiente = ""

    if pendiente:
        if fusionados:
            fusionados[-1] = f"{fusionados[-1]} {pendiente}".strip()
        else:
            fusionados.append(pendiente)

    chunks = []
    for bloque in fusionados:
        palabras = bloque.split()
        if len(palabras) <= max_palabras:
            chunks.append(bloque)
        else:
            for i in range(0, len(palabras), max_palabras):
                chunks.append(" ".join(palabras[i:i + max_palabras]))

    return chunks


def extraer_vocabulario_controlado(texto):
    """Extrae las frases de las secciones curadas (conceptos, sinónimos y
    acciones relacionadas), una por línea, para el score léxico BM25.
    """
    frases = []
    seccion_activa = None

    for linea in texto.splitlines():
        linea = linea.strip()
        clave = quitar_acentos(linea.lower()).rstrip(":").strip()

        if clave in ENCABEZADOS_SECCION:
            seccion_activa = clave
            continue

        if seccion_activa in SECCIONES_VOCABULARIO_CONTROLADO and linea:
            frases.append(linea)

    return frases


# ---------------------------------------------------------------------------
# Índice genérico de categorías (sirve tanto para ejes como para procesos)
# ---------------------------------------------------------------------------

@dataclass
class IndiceCategoria:
    nombre: str
    texto_completo: str
    chunks: list
    embeddings_chunks: np.ndarray
    centroide: np.ndarray
    vocabulario_controlado: list = field(default_factory=list)


@dataclass
class IndiceCategorias:
    categorias: dict
    orden_categorias: list
    vectorizador_tfidf: TfidfVectorizer
    matriz_tfidf_categorias: object
    bm25: BM25Okapi
    bm25_origen_categoria: list


_modelo_cache = {}


def cargar_modelo(nombre_modelo=NOMBRE_MODELO):
    if nombre_modelo not in _modelo_cache:
        _modelo_cache[nombre_modelo] = SentenceTransformer(nombre_modelo)
    return _modelo_cache[nombre_modelo]


def _leer_textos_categoria(ruta_carpeta, codificacion="utf-8"):
    textos = {}
    for archivo in sorted(os.listdir(ruta_carpeta)):
        if not archivo.lower().endswith(".txt"):
            continue
        ruta_archivo = os.path.join(ruta_carpeta, archivo)
        with open(ruta_archivo, "r", encoding=codificacion, errors="replace") as f:
            textos[archivo] = f.read()
    return textos


def preparar_indice_categorias(ruta_carpeta, modelo=None, codificacion="utf-8"):
    """Construye el índice de una carpeta de categorías (ejes/ o Procesos/):
    chunks + embeddings + centroide + TF-IDF + BM25 sobre vocabulario
    controlado. 
    """
    modelo = modelo or cargar_modelo()
    textos = _leer_textos_categoria(ruta_carpeta, codificacion)

    if not textos:
        raise ValueError(f"No se encontraron archivos .txt en '{ruta_carpeta}'.")

    categorias = {}
    for nombre, texto in textos.items():
        chunks = dividir_texto_semantico(texto)
        if not chunks:
            continue

        embeddings_chunks = modelo.encode(
            chunks, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
        )
        centroide = embeddings_chunks.mean(axis=0)
        centroide = centroide / (np.linalg.norm(centroide) + 1e-12)

        categorias[nombre] = IndiceCategoria(
            nombre=nombre,
            texto_completo=normalizar_espacios(texto),
            chunks=chunks,
            embeddings_chunks=embeddings_chunks,
            centroide=centroide,
            vocabulario_controlado=extraer_vocabulario_controlado(texto),
        )

    orden_categorias = list(categorias.keys())

    vectorizador_tfidf = TfidfVectorizer(tokenizer=tokenizar, token_pattern=None, lowercase=False)
    matriz_tfidf_categorias = vectorizador_tfidf.fit_transform(
        [categorias[nombre].texto_completo for nombre in orden_categorias]
    )

    documentos_bm25 = []
    origen_bm25 = []
    for nombre in orden_categorias:
        for frase in categorias[nombre].vocabulario_controlado:
            tokens = tokenizar(frase)
            if tokens:
                documentos_bm25.append(tokens)
                origen_bm25.append(nombre)

    if not documentos_bm25:
        
        documentos_bm25 = [tokenizar(categorias[nombre].texto_completo) for nombre in orden_categorias]
        origen_bm25 = list(orden_categorias)

    bm25 = BM25Okapi(documentos_bm25)

    return IndiceCategorias(
        categorias=categorias,
        orden_categorias=orden_categorias,
        vectorizador_tfidf=vectorizador_tfidf,
        matriz_tfidf_categorias=matriz_tfidf_categorias,
        bm25=bm25,
        bm25_origen_categoria=origen_bm25,
    )


############### Cálculo de señales########################################## 

def _normalizar_filas(matriz):
    """Reescala cada fila (variable) a [0, 1] para que las cuatro señales
    -de escalas muy distintas- pesen de forma comparable en el score
    combinado.
    """
    minimo = matriz.min(axis=1, keepdims=True)
    maximo = matriz.max(axis=1, keepdims=True)
    rango = maximo - minimo
    rango[rango < 1e-9] = 1.0
    return (matriz - minimo) / rango


def _calcular_senales(embeddings_consulta, textos_consulta, indice, top_k=TOP_K_CHUNKS, bm25_top_k=BM25_TOP_K):
    """Calcula las cuatro señales de una lista de textos de consulta contra
    un índice de categorías. Recibe los embeddings ya calculados para poder reutilizarlos contra el índice de
    ejes y el de procesos sin volver a llamar al modelo dos veces.
    """
    orden_categorias = indice.orden_categorias
    n_vars = embeddings_consulta.shape[0]
    n_categorias = len(orden_categorias)

    matriz_centroide = np.zeros((n_vars, n_categorias))
    matriz_topk = np.zeros((n_vars, n_categorias))

    for j, nombre_categoria in enumerate(orden_categorias):
        categoria = indice.categorias[nombre_categoria]
        matriz_centroide[:, j] = embeddings_consulta @ categoria.centroide

        similitudes_chunks = embeddings_consulta @ categoria.embeddings_chunks.T
        k = min(top_k, similitudes_chunks.shape[1])
        top_valores = np.sort(similitudes_chunks, axis=1)[:, -k:]
        matriz_topk[:, j] = top_valores.mean(axis=1)

    matriz_tfidf_consulta = indice.vectorizador_tfidf.transform(textos_consulta)
    matriz_tfidf = cosine_similarity(matriz_tfidf_consulta, indice.matriz_tfidf_categorias)

    matriz_bm25 = np.zeros((n_vars, n_categorias))
    columna_por_categoria = {nombre: j for j, nombre in enumerate(orden_categorias)}
    origen_bm25 = np.array(indice.bm25_origen_categoria)

    for i, texto in enumerate(textos_consulta):
        tokens = tokenizar(texto)
        if not tokens:
            continue

        puntuaciones = indice.bm25.get_scores(tokens)
        for nombre_categoria in orden_categorias:
            mascara = origen_bm25 == nombre_categoria
            if not mascara.any():
                continue
            valores_categoria = puntuaciones[mascara]
            k = min(bm25_top_k, valores_categoria.shape[0])
            mejores = np.sort(valores_categoria)[-k:]
            matriz_bm25[i, columna_por_categoria[nombre_categoria]] = mejores.mean()

    return {
        "centroide": matriz_centroide,
        "top_k": matriz_topk,
        "tfidf": matriz_tfidf,
        "bm25": matriz_bm25,
    }


def _elegir_ganador(textos_consulta, embeddings_consulta, indice, pesos, top_k):
    """Combina las cuatro señales en un score de ranking y devuelve, para
    cada consulta, el nombre de la categoría con el score más alto. No hay
    umbral de confianza ni margen mínimo: siempre se elige la mejor opción.
    """
    senales = _calcular_senales(embeddings_consulta, textos_consulta, indice, top_k=top_k)
    senales_normalizadas = {nombre: _normalizar_filas(matriz) for nombre, matriz in senales.items()}
    score_ranking = sum(pesos[nombre] * senales_normalizadas[nombre] for nombre in senales_normalizadas)

    idx_ganadores = np.argmax(score_ranking, axis=1)
    return [indice.orden_categorias[idx] for idx in idx_ganadores]

def _nombre_legible(nombre_archivo):
    """Convierte el nombre de archivo de una categoría (p.ej. 'Eje 1 -
    Prevención.txt') en la etiqueta a mostrar en la tabla de resultados."""
    return normalizar_espacios(os.path.splitext(nombre_archivo)[0])


#########################################################################################3
# función final de clasificación
######################################

def clasificar_variables(
    nombres,
    descripciones,
    indice_ejes,
    indice_procesos,
    modelo=None,
    pesos=PESOS_SENALES,
    top_k=TOP_K_CHUNKS,
):
    """Clasifica variables contra el índice de ejes y el de procesos a la
    vez, eligiendo forzosamente un eje y un proceso para cada una 
    Entrada: dos listas paralelas -nombres de variable y descripciones-.
    Salida: DataFrame con columnas Variable, Descripcion, Eje, Proceso.
    """
    if len(nombres) != len(descripciones):
        raise ValueError("'nombres' y 'descripciones' deben tener la misma longitud.")

    modelo = modelo or cargar_modelo()

    textos_consulta = [
        construir_texto_consulta(nombre, descripcion)
        for nombre, descripcion in zip(nombres, descripciones)
    ]

    embeddings_consulta = modelo.encode(
        textos_consulta, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
    )

    ejes_ganadores = _elegir_ganador(textos_consulta, embeddings_consulta, indice_ejes, pesos, top_k)
    procesos_ganadores = _elegir_ganador(textos_consulta, embeddings_consulta, indice_procesos, pesos, top_k)

    return pd.DataFrame({
        "Variable": list(nombres),
        "Descripcion": list(descripciones),
        "Eje": [_nombre_legible(nombre) for nombre in ejes_ganadores],
        "Proceso": [_nombre_legible(nombre) for nombre in procesos_ganadores],
    })




#########################################################################3
# Como se usa? Ejemplo : clasificar_variables() sólo
# necesita dos listas paralelas -nombres y descripciones-, el elemento i de
# 'nombres' se empareja con el elemento i de 'descripciones'; ambas listas
# deben tener la misma longitud (si no, clasificar_variables() lanza
# ValueError antes de calcular nada).

#aqui pueden correrlo como ejemplo
# #################################################3

if __name__ == "__main__":

    ruta_proyecto = os.path.dirname(os.path.abspath(__file__))
    ruta_ejes = os.path.join(ruta_proyecto, "ejes")
    ruta_procesos = os.path.join(ruta_proyecto, "Procesos")

    print("Cargando modelo de embeddings...")
    modelo = cargar_modelo()

    print("Construyendo índice de ejes temáticos...")
    indice_ejes = preparar_indice_categorias(ruta_ejes, modelo=modelo, codificacion="cp1252")

    print("Construyendo índice de procesos...")
    indice_procesos = preparar_indice_categorias(ruta_procesos, modelo=modelo, codificacion="utf-8")

    ####### nombres[i] es el nombre de la variable i-ésima; descripciones[i] es su
    # descripción. Cada variable puede repetir descripción (p. ej. va1 y va2
    # comparten la misma) sin que eso afecte la clasificación de las demás.
    nombres = ["va1", "va2", "va3", "va4"]
    descripciones = [
        "Abstención de imposición de sanción",
        "Abstención de imposición de sanción",
        "Abuso de funciones y actos de violencia política contra las mujeres- Mujeres",
        "Acciones sistemáticas alineadas a los objetivos de las políticas anticorrupción",
    ]

    print(f"Clasificando {len(nombres)} variables (eje + proceso)...")
    resultados = clasificar_variables(
        nombres=nombres,
        descripciones=descripciones,
        indice_ejes=indice_ejes,
        indice_procesos=indice_procesos,
        modelo=modelo,
    )

    vista_previa = resultados.head(20).copy()
    vista_previa["Descripcion"] = vista_previa["Descripcion"].str.slice(0, 60)
    print(vista_previa.to_string(index=False))
    print()
    print("Distribución por eje:")
    print(resultados["Eje"].value_counts())
    print()
    print("Distribución por proceso:")
    print(resultados["Proceso"].value_counts())
##### no tengo aun unos textos de procesos de la ley bien estructurados