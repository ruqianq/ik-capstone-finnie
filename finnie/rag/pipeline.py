"""RAG (Retrieval-Augmented Generation) module for FinnIE."""

import os
import pickle
from typing import List, Tuple, Optional
import numpy as np

from sentence_transformers import SentenceTransformer
import faiss

from finnie.config import config
from finnie.observability import observability, log_with_trace


class Document:
    """Represents a document in the RAG system."""
    
    def __init__(self, content: str, source: str, metadata: Optional[dict] = None):
        self.content = content
        self.source = source
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"Document(source={self.source}, content={self.content[:50]}...)"


class RAGPipeline:
    """RAG pipeline for document retrieval and augmentation."""
    
    def __init__(self):
        self.embedding_model_name = config.rag.embedding_model
        self.embedding_model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.IndexFlatL2] = None
        self.documents: List[Document] = []
        self.top_k = config.rag.top_k_results
        self._initialized = False
    
    def initialize(self):
        """Initialize the RAG pipeline."""
        if self._initialized:
            return
        
        try:
            # Load embedding model
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            
            # Try to load existing index
            index_path = os.path.join(config.rag.faiss_index_path, "index.faiss")
            docs_path = os.path.join(config.rag.faiss_index_path, "documents.pkl")
            
            if os.path.exists(index_path) and os.path.exists(docs_path):
                self.index = faiss.read_index(index_path)
                with open(docs_path, 'rb') as f:
                    self.documents = pickle.load(f)
                log_with_trace("Loaded existing FAISS index", level="info")
            else:
                # Create new index with sample documents
                self._create_sample_index()
            
            self._initialized = True
            
        except Exception as e:
            log_with_trace(f"Error initializing RAG pipeline: {e}", level="error")
            # Create a minimal working index
            self._create_sample_index()
            self._initialized = True
    
    def _create_sample_index(self):
        """Create a sample FAISS index with financial documents."""
        log_with_trace("Creating sample FAISS index", level="info")
        
        # Sample financial documents
        sample_docs = [
            Document(
                "A stock is a type of investment that represents ownership in a company. When you buy stock, you become a shareholder.",
                "financial_glossary",
                {"category": "stocks"}
            ),
            Document(
                "A bond is a fixed-income instrument representing a loan made by an investor to a borrower. It pays interest over time.",
                "financial_glossary",
                {"category": "bonds"}
            ),
            Document(
                "Portfolio diversification is a risk management strategy that mixes different types of investments to reduce exposure.",
                "investment_guide",
                {"category": "portfolio"}
            ),
            Document(
                "The S&P 500 is a stock market index tracking the stock performance of 500 large companies listed on U.S. exchanges.",
                "market_indices",
                {"category": "indices"}
            ),
            Document(
                "Dollar-cost averaging is an investment strategy where you invest a fixed amount at regular intervals regardless of price.",
                "investment_strategies",
                {"category": "strategies"}
            ),
        ]
        
        self.documents = sample_docs
        
        # Create embeddings
        embeddings = self.embedding_model.encode([doc.content for doc in sample_docs])
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Save index
        self._save_index()
    
    def _save_index(self):
        """Save the FAISS index and documents."""
        try:
            os.makedirs(config.rag.faiss_index_path, exist_ok=True)
            index_path = os.path.join(config.rag.faiss_index_path, "index.faiss")
            docs_path = os.path.join(config.rag.faiss_index_path, "documents.pkl")
            
            faiss.write_index(self.index, index_path)
            with open(docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            log_with_trace("Saved FAISS index", level="info")
        except Exception as e:
            log_with_trace(f"Error saving index: {e}", level="error")
    
    def retrieve(self, query: str, top_k: Optional[int] = None, trace_id: Optional[str] = None) -> List[Tuple[Document, float]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The search query
            top_k: Number of documents to retrieve (default: from config)
            trace_id: Trace ID for observability
            
        Returns:
            List of (Document, similarity_score) tuples
        """
        if not self._initialized:
            self.initialize()
        
        k = top_k or self.top_k
        
        with observability.trace_operation(
            "rag.retrieve",
            attributes={"query": query, "top_k": k, "trace_id": trace_id or ""}
        ) as (span, _):
            try:
                # Encode query
                query_embedding = self.embedding_model.encode([query])
                
                # Search in FAISS index
                distances, indices = self.index.search(
                    np.array(query_embedding).astype('float32'), k
                )
                
                # Retrieve documents
                results = []
                for idx, distance in zip(indices[0], distances[0]):
                    if idx < len(self.documents):
                        doc = self.documents[idx]
                        similarity = 1.0 / (1.0 + distance)  # Convert distance to similarity
                        results.append((doc, similarity))
                
                span.set_attribute("num_results", len(results))
                return results
                
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                log_with_trace(f"Error in RAG retrieval: {e}", trace_id=trace_id, level="error")
                return []
    
    def add_documents(self, documents: List[Document]):
        """
        Add new documents to the index.
        
        Args:
            documents: List of documents to add
        """
        if not self._initialized:
            self.initialize()
        
        if not documents:
            return
        
        # Create embeddings
        embeddings = self.embedding_model.encode([doc.content for doc in documents])
        
        # Add to index
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Add to documents list
        self.documents.extend(documents)
        
        # Save updated index
        self._save_index()
        
        log_with_trace(f"Added {len(documents)} documents to index", level="info")


# Global RAG pipeline instance
rag_pipeline = RAGPipeline()
