import os
import markdown
import requests
import json
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

# ==============================
# 1️⃣ Extraer texto de archivos Markdown
# ==============================
def extract_text_from_markdown(md_file):
    """ Leer archivo Markdown y convertirlo en texto plano """
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    html_content = markdown.markdown(md_content)
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

def load_markdown_files(folder):
    """ Leer recursivamente todos los archivos Markdown """
    all_texts = []
    file_sources = []  # Lista para guardar las fuentes de origen
    
    for root, _, files in os.walk(folder):
        for filename in files:
            if filename.endswith(".md"):
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, folder)
                text = extract_text_from_markdown(file_path)
                all_texts.append(text)
                file_sources.append(f"Archivo: {relative_path}")
    
    return all_texts, file_sources

# ==============================
# 2️⃣ Dividir textos y calcular embeddings
# ==============================
def chunk_texts(texts, chunk_size=500, chunk_overlap=50):
    """ Dividir texto en fragmentos pequeños """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = []
    for text in texts:
        chunks.extend(text_splitter.split_text(text))
    return chunks

def compute_embeddings(chunks):
    """ Calcular embeddings """
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(chunks, convert_to_numpy=True)
    return embeddings, model

# ==============================
# 3️⃣ Almacenar en ChromaDB
# ==============================
def store_in_chromadb(chunks, embeddings, sources=None):
    """ Almacenar texto y embeddings en ChromaDB """
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(name="markdown_docs")
    
    # Eliminar datos existentes para evitar duplicados
    collection.delete(where={})
    print("🧹 Datos antiguos eliminados de ChromaDB")
    
    # Lista para almacenar metadatos
    metadatas = []
    
    # Generar metadatos para cada chunk
    for i, chunk in enumerate(chunks):
        if sources and i < len(sources):
            metadata = {"source": sources[i], "chunk_id": str(i)}
        else:
            metadata = {"source": f"Fragmento Markdown {i}", "chunk_id": str(i)}
        metadatas.append(metadata)
    
    # Añadir todos los chunks a ChromaDB de una vez (más eficiente)
    collection.add(
        ids=[str(i) for i in range(len(chunks))],
        embeddings=[emb.tolist() for emb in embeddings],
        metadatas=metadatas,
        documents=chunks
    )
    print(f"✅ {len(chunks)} fragmentos Markdown almacenados en ChromaDB")

# ==============================
# 4️⃣ Consultar ChromaDB
# ==============================
def query_chromadb(query_text, model, top_n=5):
    """ Consultar ChromaDB para encontrar los fragmentos más relevantes """
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_collection(name="markdown_docs")
    query_embedding = model.encode([query_text])[0].tolist()
    
    # Aumentar el número de resultados para obtener más contexto
    results = collection.query(
        query_embeddings=[query_embedding], 
        n_results=top_n,
        include=["documents", "metadatas", "distances"]
    )
    
    if not results["documents"] or len(results["documents"][0]) == 0:
        return "No se encontró información relevante"
    
    # Construir un contexto más rico con los fragmentos encontrados
    context_parts = []
    for i, (doc, metadata, distance) in enumerate(zip(results["documents"][0], results["metadatas"][0], results["distances"][0])):
        # Solo incluir fragmentos con una distancia razonable (menor es mejor)
        if distance < 1.5:  # Umbral ajustable según necesidad
            source = metadata.get("source", "Desconocido")
            context_parts.append(f"[Fragmento {i+1} - Fuente: {source}]\n{doc}")
    
    if context_parts:
        return "\n\n".join(context_parts)
    else:
        return "No se encontró información suficientemente relevante para tu pregunta."

# ==============================
# 5️⃣ Inicializar el modelo LMStudio y generar respuesta
# ==============================
# Configurar la URL de la API de LMStudio
LMSTUDIO_API_URL = "http://127.0.0.1:1234/v1/chat/completions"

def ask_ai_with_context(question, model):
    """ Consultar ChromaDB para obtener fragmentos Markdown y generar respuesta con el modelo local LMStudio """
    context = query_chromadb(question, model)  
    
    # Prompt más estructurado para guiar mejor al modelo
    prompt = f"""Eres un asistente experto en la UPC (Universitat Politècnica de Catalunya).
Tu tarea es responder preguntas utilizando ÚNICAMENTE la información proporcionada en el contexto.
Si la información no está en el contexto, indica que no tienes esa información.
No inventes ni añadas información que no esté en el contexto proporcionado.

CONTEXTO:
{context}

PREGUNTA:
{question}

INSTRUCCIONES:
1. Proporciona una respuesta clara y concisa basada ÚNICAMENTE en el contexto dado.
2. Cita las fuentes específicas del contexto que utilizaste para tu respuesta.
3. Si la información en el contexto es insuficiente, indícalo claramente.
"""
    
    try:
        # Preparar el payload para la API de LMStudio (compatible con OpenAI)
        payload = {
            "model": "local-model",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,  # Aumentado para permitir respuestas más completas
            "temperature": 0.5  # Reducido para obtener respuestas más deterministas
        }
        
        # Realizar la solicitud HTTP directamente a la API de LMStudio
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            LMSTUDIO_API_URL,
            headers=headers,
            data=json.dumps(payload)
        )
        
        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
        else:
            print(f"Error en la API de LMStudio: {response.status_code} - {response.text}")
            return f"Error al procesar la consulta: {response.reason}"
    except Exception as e:
        print(f"Error al llamar a la API local de LMStudio: {e}")
        return "Lo siento, hubo un error al procesar tu pregunta con el modelo local."

# ==============================
# 6️⃣ Ejecutar el flujo
# ==============================
def main():
    # Ruta a la carpeta con archivos Markdown
    markdown_folder = "./markdown_pages"
    
    # Procesamiento inicial (solo es necesario una vez)
    # Descomentar si necesita crear/actualizar la base de datos
    """
    # Cargar los archivos Markdown con sus fuentes
    texts, sources = load_markdown_files(markdown_folder)
    
    # Dividir los textos en chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = []
    chunk_sources = []
    
    # Procesar cada texto y mantener registro de su origen
    for i, text in enumerate(texts):
        # Dividir este texto específico en chunks
        text_chunks = text_splitter.split_text(text)
        chunks.extend(text_chunks)
        
        # Asociar la fuente a cada chunk generado
        for _ in text_chunks:
            chunk_sources.append(sources[i])
    
    # Calcular embeddings para todos los chunks
    embeddings, model = compute_embeddings(chunks)
    
    # Almacenar chunks con sus metadatos en ChromaDB
    store_in_chromadb(chunks, embeddings, chunk_sources)
    """
    
    # Cargar el modelo para consultas
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Bucle de preguntas interactivo
    print("✨ Asistente DeepSeek UPC listo para responder preguntas sobre la UPC ✨")
    print("📝 Escribe 'salir' para terminar.")
    
    while True:
        question = input("\n❓ Pregunta: ")
        if question.lower() == "salir":
            break
            
        answer = ask_ai_with_context(question, model)
        print(f"\n🤖 Respuesta: {answer}")

if __name__ == "__main__":
    main()
