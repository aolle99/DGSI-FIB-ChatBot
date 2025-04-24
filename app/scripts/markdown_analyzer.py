# Diccionario Semántico y Diagrama de Conocimiento
# Importación de bibliotecas
import os
import re
import json
import glob
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag

# Configuración e instalación de dependencias
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('taggers/averaged_perceptron_tagger')
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Descargando recursos de NLTK...")
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('wordnet')


# Función para leer archivos markdown
def leer_archivos_markdown(directorio="markdown_pages"):
    """Lee todos los archivos markdown en el directorio especificado."""
    archivos = {}

    if not os.path.exists(directorio):
        print(f"El directorio {directorio} no existe.")
        return archivos

    patron = os.path.join(directorio, "**", "*.md")
    rutas = glob.glob(patron, recursive=True)

    for ruta in rutas:
        try:
            with open(ruta, 'r', encoding='utf-8') as archivo:
                contenido = archivo.read()
                nombre_archivo = os.path.relpath(ruta, directorio)
                archivos[nombre_archivo] = contenido
        except Exception as e:
            print(f"Error al leer {ruta}: {e}")

    print(f"Se leyeron {len(archivos)} archivos markdown.")
    return archivos


# Función para extraer acrónimos y definiciones
def extraer_acronimos(contenido_archivos):
    """Extrae acrónimos y sus posibles definiciones de los archivos."""
    acronimos = {}

    # Patrones para encontrar acrónimos
    patron_acronimo = r'\b([A-Z]{2,})\b'

    for archivo, contenido in contenido_archivos.items():
        # Encontrar todos los acrónimos en el texto
        encontrados = re.findall(patron_acronimo, contenido)

        for acronimo in encontrados:
            if len(acronimo) >= 2:  # Solo considerar acrónimos de al menos 2 letras
                # Buscar posibles definiciones
                # Patrón 1: "ACRONIMO (definición)"
                patron1 = rf'{acronimo}\s*\(([^)]+)\)'
                # Patrón 2: "definición (ACRONIMO)"
                patron2 = r'([^(]+)\s*\(\s*' + acronimo + r'\s*\)'

                definicion = None
                match1 = re.search(patron1, contenido)
                if match1:
                    definicion = match1.group(1).strip()
                else:
                    match2 = re.search(patron2, contenido)
                    if match2:
                        definicion = match2.group(1).strip()

                if acronimo not in acronimos:
                    acronimos[acronimo] = {"definicion": definicion, "archivos": []}

                # Añadir archivo a la lista de archivos donde aparece
                if archivo not in acronimos[acronimo]["archivos"]:
                    acronimos[acronimo]["archivos"].append(archivo)

    print(f"Se encontraron {len(acronimos)} acrónimos únicos.")
    return acronimos


# Función para extraer términos importantes
def extraer_terminos(contenido_archivos):
    """Extrae términos y conceptos importantes de los documentos."""
    terminos = defaultdict(lambda: {"ocurrencias": 0, "archivos": []})
    stop_words = set(stopwords.words('spanish'))
    lemmatizer = WordNetLemmatizer()

    for archivo, contenido in contenido_archivos.items():
        # Tokenizar por oraciones y luego por palabras
        sentencias = sent_tokenize(contenido)
        for sentencia in sentencias:
            palabras = word_tokenize(sentencia)
            # Filtrar stopwords y etiquetas POS
            palabras_filtradas = [palabra.lower() for palabra in palabras
                                  if palabra.isalpha() and palabra.lower() not in stop_words]

            # Etiquetar partes del discurso
            etiquetadas = pos_tag(palabras_filtradas)

            # Extraer sustantivos y frases nominales
            i = 0
            while i < len(etiquetadas):
                palabra, etiqueta = etiquetadas[i]

                # Si es un sustantivo, verificar si forma parte de una frase nominal
                if etiqueta.startswith('NN'):
                    # Intentar formar una frase nominal (sustantivo + sustantivo)
                    frase = palabra
                    j = i + 1
                    while j < len(etiquetadas) and etiquetadas[j][1].startswith('NN'):
                        frase += " " + etiquetadas[j][0]
                        j += 1

                    if j > i + 1:  # Si se encontró una frase nominal
                        termino = frase
                        i = j - 1  # Avanzar el índice
                    else:
                        # Usar solo el sustantivo individual
                        termino = lemmatizer.lemmatize(palabra)

                    # Registrar el término
                    terminos[termino]["ocurrencias"] += 1
                    if archivo not in terminos[termino]["archivos"]:
                        terminos[termino]["archivos"].append(archivo)
                i += 1

    # Filtrar términos con pocas ocurrencias
    terminos_filtrados = {k: v for k, v in terminos.items() if v["ocurrencias"] > 1}
    print(f"Se extrajeron {len(terminos_filtrados)} términos relevantes.")
    return terminos_filtrados


# Función para crear relaciones entre términos
def crear_relaciones(acronimos, terminos, contenido_archivos):
    """Crea relaciones entre términos y acrónimos basados en co-ocurrencia."""
    relaciones = []

    # Combinar acrónimos y términos para el análisis
    todos_los_elementos = list(acronimos.keys()) + list(terminos.keys())

    # Crear matriz de co-ocurrencia
    for archivo, contenido in contenido_archivos.items():
        # Verificar qué elementos aparecen en este archivo
        elementos_presentes = []
        for elemento in todos_los_elementos:
            if elemento.lower() in contenido.lower():
                elementos_presentes.append(elemento)

        # Crear relaciones basadas en co-ocurrencia en el mismo archivo
        for i in range(len(elementos_presentes)):
            for j in range(i + 1, len(elementos_presentes)):
                elemento1 = elementos_presentes[i]
                elemento2 = elementos_presentes[j]

                # Verificar si están cerca uno del otro en el texto (dentro de la misma sección)
                contenido_lower = contenido.lower()
                pos1 = contenido_lower.find(elemento1.lower())
                pos2 = contenido_lower.find(elemento2.lower())

                if pos1 >= 0 and pos2 >= 0:
                    # Calcular la distancia de texto entre ellos
                    distancia = abs(pos1 - pos2)

                    # Si están relativamente cerca (en el mismo párrafo aproximadamente)
                    if distancia < 500:  # Un párrafo suele tener menos de 500 caracteres
                        relaciones.append((elemento1, elemento2, {'archivo': archivo, 'distancia': distancia}))

    print(f"Se crearon {len(relaciones)} relaciones entre términos.")
    return relaciones


# Función para crear grafo de conocimiento
def crear_grafo(acronimos, terminos, relaciones):
    """Crea un grafo de conocimiento con los términos y sus relaciones."""
    G = nx.Graph()

    # Añadir nodos para acrónimos
    for acronimo, info in acronimos.items():
        G.add_node(acronimo, tipo='acronimo', definicion=info["definicion"])

    # Añadir nodos para términos
    for termino, info in terminos.items():
        G.add_node(termino, tipo='termino', ocurrencias=info["ocurrencias"])

    # Añadir aristas para las relaciones
    for origen, destino, atributos in relaciones:
        # Comprobar si ambos nodos existen en el grafo
        if G.has_node(origen) and G.has_node(destino):
            if G.has_edge(origen, destino):
                # Si la arista ya existe, actualizar el peso
                G[origen][destino]['weight'] = G[origen][destino].get('weight', 0) + 1
            else:
                # Si no existe, crear la arista con peso inicial
                G.add_edge(origen, destino, weight=1)

    print(f"Grafo creado con {G.number_of_nodes()} nodos y {G.number_of_edges()} aristas.")
    return G


# Función para visualizar el grafo
def visualizar_grafo(G, nombre_archivo="grafo_conocimiento.png"):
    """Visualiza y guarda el grafo de conocimiento como imagen."""
    plt.figure(figsize=(12, 12))

    # Determinar tamaño de nodos según su importancia
    tamanos = []
    colores = []

    for nodo in G.nodes():
        if G.nodes[nodo].get('tipo') == 'acronimo':
            colores.append('red')
            tamanos.append(300)  # Acrónimos más grandes
        else:
            colores.append('skyblue')
            tamanos.append(100 + G.nodes[nodo].get('ocurrencias', 0) * 10)

    # Determinar grosor de las aristas según el peso
    pesos = [G[u][v].get('weight', 1) * 0.5 for u, v in G.edges()]

    # Usar layout basado en fuerza
    pos = nx.spring_layout(G, k=0.30, iterations=50)

    # Dibujar el grafo
    nx.draw_networkx(
        G, pos=pos,
        with_labels=True,
        node_color=colores,
        node_size=tamanos,
        edge_color='gray',
        width=pesos,
        alpha=0.8,
        font_size=8,
        font_weight='bold'
    )

    plt.title("Grafo de Conocimiento")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(nombre_archivo, format='png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Grafo guardado como {nombre_archivo}")


# Función para generar diccionario semántico
def generar_diccionario_semantico(acronimos, terminos, relaciones, G):
    """Genera el diccionario semántico completo."""
    diccionario = {
        "acronimos": {},
        "terminos": {},
        "relaciones": []
    }

    # Añadir acrónimos
    for acronimo, info in acronimos.items():
        diccionario["acronimos"][acronimo] = {
            "definicion": info["definicion"],
            "archivos": info["archivos"],
            "conexiones": []
        }

    # Añadir términos
    for termino, info in terminos.items():
        diccionario["terminos"][termino] = {
            "ocurrencias": info["ocurrencias"],
            "archivos": info["archivos"],
            "conexiones": []
        }

    # Añadir relaciones y actualizar conexiones
    for origen, destino, atributos in relaciones:
        diccionario["relaciones"].append({
            "origen": origen,
            "destino": destino,
            "archivo": atributos["archivo"],
            "distancia": atributos["distancia"]
        })

        # Actualizar conexiones en acrónimos
        if origen in diccionario["acronimos"]:
            diccionario["acronimos"][origen]["conexiones"].append(destino)

        if destino in diccionario["acronimos"]:
            diccionario["acronimos"][destino]["conexiones"].append(origen)

        # Actualizar conexiones en términos
        if origen in diccionario["terminos"]:
            diccionario["terminos"][origen]["conexiones"].append(destino)

        if destino in diccionario["terminos"]:
            diccionario["terminos"][destino]["conexiones"].append(origen)

    # Añadir métricas de centralidad del grafo
    if G.number_of_nodes() > 0:
        centralidad = nx.degree_centrality(G)
        for nodo, valor in centralidad.items():
            if nodo in diccionario["acronimos"]:
                diccionario["acronimos"][nodo]["centralidad"] = valor
            elif nodo in diccionario["terminos"]:
                diccionario["terminos"][nodo]["centralidad"] = valor

    print("Diccionario semántico generado correctamente.")
    return diccionario


# Guardar resultados
def guardar_resultados(diccionario, G, prefijo="resultados"):
    """Guarda el diccionario semántico y el grafo en archivos."""
    # Guardar diccionario como JSON
    with open(f"{prefijo}_diccionario.json", 'w', encoding='utf-8') as f:
        json.dump(diccionario, f, ensure_ascii=False, indent=2)

    # Guardar grafo como GraphML
    nx.write_graphml(G, f"{prefijo}_grafo.graphml")

    print(f"Resultados guardados con prefijo '{prefijo}'")


# Ejecución principal
def main():
    # Leer archivos markdown
    contenido_archivos = leer_archivos_markdown()

    if not contenido_archivos:
        print("No se encontraron archivos para procesar.")
        return

    # Extraer acrónimos y términos
    acronimos = extraer_acronimos(contenido_archivos)
    terminos = extraer_terminos(contenido_archivos)

    # Crear relaciones
    relaciones = crear_relaciones(acronimos, terminos, contenido_archivos)

    # Crear grafo de conocimiento
    G = crear_grafo(acronimos, terminos, relaciones)

    # Visualizar grafo
    visualizar_grafo(G)

    # Generar diccionario semántico
    diccionario = generar_diccionario_semantico(acronimos, terminos, relaciones, G)

    # Guardar resultados
    guardar_resultados(diccionario, G)

    # Mostrar estadísticas
    print("\n=== Estadísticas ===")
    print(f"Acrónimos encontrados: {len(acronimos)}")
    print(f"Términos importantes: {len(terminos)}")
    print(f"Relaciones identificadas: {len(relaciones)}")
    print(f"Nodos en el grafo: {G.number_of_nodes()}")
    print(f"Aristas en el grafo: {G.number_of_edges()}")


# Ejecutar
main()