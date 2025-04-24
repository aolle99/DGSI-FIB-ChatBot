import os
import markdown
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from llama_cpp import Llama

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
    for root, _, files in os.walk(folder):
        for filename in files:
            if filename.endswith(".md"):
                file_path = os.path.join(root, filename)
                text = extract_text_from_markdown(file_path)
                all_texts.append(text)
    return all_texts

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
def store_in_chromadb(chunks, embeddings):
    """ Almacenar texto y embeddings en ChromaDB """
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(name="markdown_docs")

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        collection.add(
            ids=[str(i)],
            embeddings=[embedding.tolist()],
            metadatas=[{"source": f"Fragmento Markdown {i}"}],
            documents=[chunk]
        )
    print("✅ Datos Markdown almacenados en ChromaDB")

# ==============================
# 4️⃣ Consultar ChromaDB
# ==============================
def query_chromadb(query_text, model, top_n=3):
    """ Consultar ChromaDB para encontrar los fragmentos más relevantes """
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_collection(name="markdown_docs")
    query_embedding = model.encode([query_text])[0].tolist()
    
    results = collection.query(query_embeddings=[query_embedding], n_results=top_n)
    
    if results["documents"]:
        return " ".join(results["documents"][0])  # Devolver fragmentos concatenados
    else:
        return "No se encontró información relevante"

# ==============================
# 5️⃣ Inicializar el modelo Llama y generar respuesta
# ==============================
llm = Llama(model_path="./model/llama/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")

def ask_ai_with_context(question, model):
    """ Consultar ChromaDB para obtener fragmentos Markdown y generar respuesta con Llama """
    context = query_chromadb(question, model)  
    prompt = f"Contexto: {context} , Pregunta: {question}, respuesta simple y corta"
    
    response = llm(prompt, max_tokens=500)["choices"][0]["text"]
    return response

# ==============================
# 6️⃣ Ejecutar el flujo
# ==============================
if __name__ == "__main__":
    folder_path = "./markdown_pages"  # Carpeta con archivos Markdown
    texts = load_markdown_files(folder_path)
    chunks = chunk_texts(texts)
    embeddings, model = compute_embeddings(chunks)
    store_in_chromadb(chunks, embeddings)
    
    # Prueba de consulta
    query_text = "contacto de fib? solo uno"
    print("\n🔍 Fragmento Markdown relevante:")
    context = query_chromadb(query_text, model)
    print(context)

    # Generar respuesta con AI
    print("\n🤖 Respuesta de AI:")
    ai_response = ask_ai_with_context(query_text, model)
    print(ai_response)
