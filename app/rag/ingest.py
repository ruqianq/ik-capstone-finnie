import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

DATA_PATH = "data/knowledge_base"
DB_FAISS_PATH = "data/vector_store/index"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")


def create_vector_db():
    if not os.path.exists(DATA_PATH):
        print(f"No data directory found at {DATA_PATH}")
        return

    # Load documents
    loader = DirectoryLoader(DATA_PATH, glob='*.md', loader_cls=TextLoader)
    documents = loader.load()

    if not documents:
        print("No documents found to ingest.")
        return

    print(f"Loaded {len(documents)} documents from {DATA_PATH}")

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)
    print(f"Split into {len(texts)} chunks")

    # Create embeddings using Ollama
    print(f"Using Ollama embeddings: {EMBEDDING_MODEL} at {OLLAMA_BASE_URL}")
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL
    )

    # Create vector database
    print("Creating FAISS vector store...")
    db = FAISS.from_documents(texts, embeddings)
    db.save_local(DB_FAISS_PATH)
    print(f"Vector store saved to {DB_FAISS_PATH}")


if __name__ == "__main__":
    create_vector_db()
