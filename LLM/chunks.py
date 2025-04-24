import os
import markdown
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

def extract_text_from_markdown(md_file):
    """ Leer archivo Markdown y extraer el texto plano """
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # Convertir a HTML y eliminar el formato
    html_content = markdown.markdown(md_content)
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

def load_markdown_files(folder):
    """ Leer recursivamente todos los archivos Markdown en la carpeta y subcarpetas """
    all_texts = []
    
    for root, _, files in os.walk(folder):  # Usar os.walk para recorrer todas las subcarpetas
        for filename in files:
            if filename.endswith(".md"):
                file_path = os.path.join(root, filename)
                text = extract_text_from_markdown(file_path)
                all_texts.append(text)
                
    return all_texts

def chunk_texts(texts, chunk_size=500, chunk_overlap=50):
    """ Dividir el texto en fragmentos """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = []
    for text in texts:
        chunks.extend(text_splitter.split_text(text))
    return chunks

def compute_embeddings(chunks):
    """ Calcular las incrustaciones usando un modelo local """
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(chunks, convert_to_numpy=True)
    return embeddings, model

def store_in_chromadb(chunks, embeddings):
    """ Almacenar en ChromaDB """
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(name="markdown_docs")
    
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        collection.add(
            ids=[str(i)],
            embeddings=[embedding.tolist()],
            metadatas=[{"source": f"Fragmento Markdown {i}"}],
            documents=[chunk]
        )
    print("¡Datos almacenados en ChromaDB con éxito!")

def query_chromadb(query_text, model, top_n=3):
    """ Realizar búsqueda de similitud en ChromaDB """
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_collection(name="markdown_docs")
    query_embedding = model.encode([query_text])[0].tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=top_n)
    
    for doc, score in zip(results["documents"][0], results["distances"][0]):
        print(f"Fragmento relacionado: {doc} (Similitud: {score})")

if __name__ == "__main__":
    folder_path = "./markdown_pages"  # Ruta de tu carpeta Markdown
    texts = load_markdown_files(folder_path)
    chunks = chunk_texts(texts)
    embeddings, model = compute_embeddings(chunks)
    store_in_chromadb(chunks, embeddings)
    
    # Prueba de búsqueda
    query_text = "Secretaria"
    print("\n🔍 Resultados de la búsqueda:")
    query_chromadb(query_text, model)
