from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os

DB_FAISS_PATH = "data/vector_store/index"

class FinanceRetriever:
    def __init__(self):
        self.db = None
        self._load_db()

    def _load_db(self):
        if os.path.exists(DB_FAISS_PATH):
            embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2',
                                             model_kwargs={'device': 'cpu'})
            self.db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
            print("FAISS index loaded successfully.")
        else:
            print("FAISS index not found. Run ingest.py first.")

    def get_relevant_documents(self, query: str, k: int = 3):
        if not self.db:
            return []
        return self.db.similarity_search(query, k=k)
