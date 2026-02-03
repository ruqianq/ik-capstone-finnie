import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

DATA_PATH = "data/knowledge_base"
DB_FAISS_PATH = "data/vector_store/index"

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

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)

    # Create embeddings
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2',
                                     model_kwargs={'device': 'cpu'})

    # Create vector database
    db = FAISS.from_documents(texts, embeddings)
    db.save_local(DB_FAISS_PATH)
    print(f"Vector store saved to {DB_FAISS_PATH}")

if __name__ == "__main__":
    create_vector_db()
