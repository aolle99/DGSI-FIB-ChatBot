# Ejemplo de uso con embeddings
import json


def preparar_para_embeddings(diccionario, archivo_salida="embeddings_data.json"):
    """Prepara los datos del diccionario semántico para ser usados con embeddings."""
    datos_embedding = []

    # Procesar acrónimos
    for acronimo, info in diccionario["acronimos"].items():
        # Crear texto enriquecido para cada acrónimo
        texto = f"ACRÓNIMO: {acronimo}"
        if info["definicion"]:
            texto += f"\nDEFINICIÓN: {info['definicion']}"

        texto += f"\nAPARECE EN: {', '.join(info['archivos'])}"

        if info["conexiones"]:
            texto += f"\nRELACIONADO CON: {', '.join(info['conexiones'])}"

        datos_embedding.append({
            "tipo": "acronimo",
            "id": acronimo,
            "texto": texto,
            "metadata": {
                "definicion": info["definicion"],
                "archivos": info["archivos"],
                "centralidad": info.get("centralidad", 0)
            }
        })

    # Procesar términos
    for termino, info in diccionario["terminos"].items():
        # Crear texto enriquecido para cada término
        texto = f"TÉRMINO: {termino}"
        texto += f"\nOCURRENCIAS: {info['ocurrencias']}"
        texto += f"\nAPARECE EN: {', '.join(info['archivos'])}"

        if info["conexiones"]:
            texto += f"\nRELACIONADO CON: {', '.join(info['conexiones'])}"

        datos_embedding.append({
            "tipo": "termino",
            "id": termino,
            "texto": texto,
            "metadata": {
                "ocurrencias": info["ocurrencias"],
                "archivos": info["archivos"],
                "centralidad": info.get("centralidad", 0)
            }
        })

    # Guardar datos para embeddings
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        json.dump(datos_embedding, f, ensure_ascii=False, indent=2)

    print(f"Datos para embeddings guardados en {archivo_salida}")
    print(f"Total de elementos para embeddings: {len(datos_embedding)}")

    return datos_embedding


# Preparar datos para embeddings
with open("resultados_diccionario.json", 'r', encoding='utf-8') as f:
    diccionario_cargado = json.load(f)

datos_para_embeddings = preparar_para_embeddings(diccionario_cargado)

# Ejemplo de cómo podrías usar estos datos con un sistema de embeddings
print("\n=== Ejemplo de uso con embeddings ===")
print("Para utilizar estos datos con un sistema de embeddings, puedes:")
print("1. Cargar el archivo embeddings_data.json")
print("2. Generar embeddings para cada elemento usando su campo 'texto'")
print("3. Almacenar los embeddings junto con los metadatos")
print("4. Usar estos embeddings para búsqueda semántica o recomendaciones")