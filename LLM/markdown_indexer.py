import os
import chromadb
from chromadb.utils import embedding_functions
import glob

# Crear un cliente de ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# Eliminar colección existente si existe
try:
    client.delete_collection("markdown_documents")
except Exception as e:
    print(f"Info: {str(e)}")

# Crear una colección para los documentos markdown
collection = client.create_collection(
    name="markdown_documents",
    metadata={"hnsw:space": "cosine"}
)

def read_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def split_into_chunks(text, chunk_size=500, overlap=50):
    """
    Divide el texto en chunks más pequeños con superposición.
    
    Args:
        text (str): Texto a dividir
        chunk_size (int): Tamaño aproximado de cada chunk en caracteres
        overlap (int): Número de caracteres de superposición entre chunks
        
    Returns:
        list: Lista de chunks de texto
    """
    # Dividir el texto en párrafos
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # Si el párrafo es más grande que chunk_size, dividirlo
        if len(paragraph) > chunk_size:
            words = paragraph.split()
            current_paragraph = []
            current_paragraph_size = 0
            
            for word in words:
                if current_paragraph_size + len(word) + 1 <= chunk_size:
                    current_paragraph.append(word)
                    current_paragraph_size += len(word) + 1
                else:
                    chunks.append(' '.join(current_paragraph))
                    current_paragraph = [word]
                    current_paragraph_size = len(word)
            
            if current_paragraph:
                chunks.append(' '.join(current_paragraph))
        else:
            # Si añadir el párrafo excede chunk_size, crear nuevo chunk
            if current_size + len(paragraph) > chunk_size:
                chunks.append('\n\n'.join(current_chunk))
                # Mantener el último párrafo para overlap
                if current_chunk and overlap > 0:
                    current_chunk = [current_chunk[-1]]
                    current_size = len(current_chunk[-1])
                else:
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(paragraph)
            current_size += len(paragraph)
    
    # Añadir el último chunk si existe
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks

def get_chunk_position(text, chunk):
    """
    Obtiene la posición aproximada del chunk en el texto original.
    
    Returns:
        tuple: (número de línea inicial, número de línea final)
    """
    text_lines = text.split('\n')
    chunk_start = text.find(chunk)
    if chunk_start == -1:
        return (0, 0)
    
    # Contar líneas hasta el inicio del chunk
    start_line = text[:chunk_start].count('\n') + 1
    end_line = start_line + chunk.count('\n')
    
    return (start_line, end_line)

# Obtener todos los archivos markdown
markdown_dir = "markdown_pages"
markdown_files = glob.glob(os.path.join(markdown_dir, "**/*.md"), recursive=True)

# Preparar los documentos para la indexación
documents = []
metadatas = []
ids = []
doc_counter = 0

for file_path in markdown_files:
    content = read_markdown_file(file_path)
    relative_path = os.path.relpath(file_path, markdown_dir)
    
    # Dividir el contenido en chunks
    chunks = split_into_chunks(content)
    
    for i, chunk in enumerate(chunks):
        start_line, end_line = get_chunk_position(content, chunk)
        
        documents.append(chunk)
        metadatas.append({
            "path": relative_path,
            "filename": os.path.basename(file_path),
            "chunk_index": i,
            "total_chunks": len(chunks),
            "start_line": start_line,
            "end_line": end_line
        })
        ids.append(f"doc_{doc_counter}_chunk_{i}")
    
    doc_counter += 1

# Añadir documentos a la colección
if documents:
    # Añadir documentos en lotes de 100
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        end_idx = min(i + batch_size, len(documents))
        collection.add(
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx]
        )
    print(f"Indexed {len(documents)} chunks from {doc_counter} markdown files")
else:
    print("No markdown files found to index")

def search_documents(query, n_results=5):
    """
    Busca documentos relacionados con la consulta.
    
    Args:
        query (str): La consulta de búsqueda
        n_results (int): Número de resultados a devolver
        
    Returns:
        list: Lista de resultados con el contenido y metadata
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    return results

# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de búsqueda
    query = "¿Qué es la FIB?"
    results = search_documents(query)
    
    print(f"\nResultados para la búsqueda: '{query}'")
    print("-" * 50)
    
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        print(f"\nResultado {i+1}:")
        print(f"Archivo: {metadata['filename']}")
        print(f"Ruta: {metadata['path']}")
        print(f"Líneas: {metadata['start_line']} - {metadata['end_line']}")
        print(f"Chunk: {metadata['chunk_index'] + 1} de {metadata['total_chunks']}")
        print(f"Relevancia: {1 - distance:.2%}")
        print("\nContenido del chunk:")
        print(doc)
        print("-" * 50)
