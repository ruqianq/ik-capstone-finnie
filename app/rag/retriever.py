from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
import os

DB_FAISS_PATH = "data/vector_store/index"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")


class FinanceRetriever:
    def __init__(self):
        self.db = None
        self.embeddings = None
        self._load_db()

    def _get_embeddings(self):
        """Get Ollama embeddings instance."""
        if self.embeddings is None:
            self.embeddings = OllamaEmbeddings(
                model=EMBEDDING_MODEL,
                base_url=OLLAMA_BASE_URL
            )
        return self.embeddings

    def _load_db(self):
        if os.path.exists(DB_FAISS_PATH):
            try:
                embeddings = self._get_embeddings()
                self.db = FAISS.load_local(
                    DB_FAISS_PATH,
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"FAISS index loaded successfully (using Ollama: {EMBEDDING_MODEL}).")
            except Exception as e:
                print(f"Error loading FAISS index: {e}")
                print("Make sure Ollama is running: ollama serve")
        else:
            print("FAISS index not found. Run ingest.py first.")

    def get_relevant_documents(self, query: str, k: int = 3):
        if not self.db:
            return []
        return self.db.similarity_search(query, k=k)
