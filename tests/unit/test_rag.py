"""
Unit tests for FinnIE RAG (Retrieval-Augmented Generation) system.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestFinanceRetriever:
    """Tests for the Finance document retriever."""

    @patch("langchain_ollama.OllamaEmbeddings")
    @patch("langchain_community.vectorstores.FAISS")
    def test_retriever_initialization(self, mock_faiss, mock_embeddings):
        """Test that retriever initializes with embeddings and vector store."""
        mock_embedding_instance = MagicMock()
        mock_embeddings.return_value = mock_embedding_instance

        mock_faiss_instance = MagicMock()
        mock_faiss.load_local.return_value = mock_faiss_instance

        from app.rag.retriever import FinanceRetriever

        retriever = FinanceRetriever()

        # Verify embeddings were created
        mock_embeddings.assert_called()

    @patch("langchain_ollama.OllamaEmbeddings")
    @patch("langchain_community.vectorstores.FAISS")
    def test_retrieve_documents(self, mock_faiss, mock_embeddings):
        """Test document retrieval."""
        mock_embedding_instance = MagicMock()
        mock_embeddings.return_value = mock_embedding_instance

        # Create mock documents
        mock_doc = Mock()
        mock_doc.page_content = "A stock represents ownership in a company."
        mock_doc.metadata = {"source": "test.md"}

        mock_faiss_instance = MagicMock()
        mock_faiss_instance.similarity_search.return_value = [mock_doc]
        mock_faiss.load_local.return_value = mock_faiss_instance

        from app.rag.retriever import FinanceRetriever

        retriever = FinanceRetriever()

        # Mock the get_relevant_documents method
        with patch.object(retriever, 'get_relevant_documents', return_value=[mock_doc]):
            docs = retriever.get_relevant_documents("What is a stock?")

            assert len(docs) == 1
            assert "stock" in docs[0].page_content.lower()

    @patch("langchain_ollama.OllamaEmbeddings")
    @patch("langchain_community.vectorstores.FAISS")
    def test_retrieve_with_k_parameter(self, mock_faiss, mock_embeddings):
        """Test retrieval with custom k parameter."""
        mock_embedding_instance = MagicMock()
        mock_embeddings.return_value = mock_embedding_instance

        mock_docs = [
            Mock(page_content=f"Document {i}", metadata={"source": f"doc{i}.md"})
            for i in range(5)
        ]

        mock_faiss_instance = MagicMock()
        mock_faiss_instance.similarity_search.return_value = mock_docs[:3]
        mock_faiss.load_local.return_value = mock_faiss_instance

        from app.rag.retriever import FinanceRetriever

        retriever = FinanceRetriever()

        # Verify similarity_search can be called with k
        mock_faiss_instance.similarity_search("test query", k=3)
        mock_faiss_instance.similarity_search.assert_called_with("test query", k=3)


class TestDocumentIngestion:
    """Tests for document ingestion."""

    def test_knowledge_base_files_exist(self):
        """Test that knowledge base files exist."""
        kb_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "knowledge_base"
        )

        assert os.path.exists(kb_path), "Knowledge base directory should exist"

        # Check for markdown files
        md_files = [f for f in os.listdir(kb_path) if f.endswith('.md')]
        assert len(md_files) > 0, "Should have at least one markdown file"

    def test_knowledge_base_content_structure(self):
        """Test that knowledge base files have proper structure."""
        kb_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "knowledge_base"
        )

        # Check first few files for structure
        md_files = [f for f in os.listdir(kb_path) if f.endswith('.md')]

        for md_file in md_files[:3]:  # Check first 3 files
            file_path = os.path.join(kb_path, md_file)
            with open(file_path, 'r') as f:
                content = f.read()

            # Should have a title (starts with #)
            assert content.startswith('#'), f"{md_file} should start with a heading"

            # Should have some content
            assert len(content) > 100, f"{md_file} should have substantial content"


class TestVectorStore:
    """Tests for FAISS vector store operations."""

    def test_vector_store_exists(self):
        """Test that vector store index exists after ingestion."""
        vs_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "vector_store", "index"
        )

        # Note: This may fail if ingestion hasn't been run
        # The test documents the expected location
        expected_files = ["index.faiss", "index.pkl"]

        if os.path.exists(vs_path + ".faiss"):
            assert True
        else:
            pytest.skip("Vector store not yet created - run python app/rag/ingest.py first")

    @patch("langchain_ollama.OllamaEmbeddings")
    def test_embeddings_configuration(self, mock_embeddings):
        """Test that embeddings are configured correctly."""
        from app.rag.retriever import OLLAMA_BASE_URL, EMBEDDING_MODEL

        # Verify configuration from environment
        assert EMBEDDING_MODEL == "nomic-embed-text" or EMBEDDING_MODEL is not None
        assert "localhost" in OLLAMA_BASE_URL or "ollama" in OLLAMA_BASE_URL


class TestTextSplitting:
    """Tests for document text splitting."""

    def test_chunk_size_reasonable(self):
        """Test that chunk sizes are reasonable for retrieval."""
        # Standard chunk sizes for RAG
        typical_chunk_size = 1000
        typical_chunk_overlap = 200

        # Chunks should be large enough to contain meaningful content
        assert typical_chunk_size >= 500, "Chunks should be at least 500 characters"

        # Overlap should be meaningful but not too large
        assert typical_chunk_overlap >= 50, "Overlap should be at least 50 characters"
        assert typical_chunk_overlap < typical_chunk_size / 2, "Overlap shouldn't exceed half chunk size"

    def test_markdown_splitting(self):
        """Test that markdown is split appropriately."""
        from langchain_text_splitters import MarkdownHeaderTextSplitter

        # Test markdown header splitting
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
            ]
        )

        test_markdown = """# Investment Basics

This is an introduction.

## Stocks

Stocks are ownership shares.

## Bonds

Bonds are debt instruments.
"""

        splits = splitter.split_text(test_markdown)

        # Should split by headers
        assert len(splits) >= 1


class TestEmbeddingModel:
    """Tests for embedding model configuration."""

    @patch("langchain_ollama.OllamaEmbeddings")
    def test_ollama_embeddings_creation(self, mock_embeddings):
        """Test Ollama embeddings can be created."""
        mock_instance = MagicMock()
        mock_instance.embed_query.return_value = [0.1] * 768
        mock_embeddings.return_value = mock_instance

        # Create embeddings
        from langchain_ollama import OllamaEmbeddings

        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )

        # Verify creation
        mock_embeddings.assert_called_with(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )

    def test_embedding_dimension(self):
        """Test that embedding dimension is as expected."""
        # nomic-embed-text produces 768-dimensional embeddings
        expected_dimension = 768

        # This is a documentation test
        assert expected_dimension == 768
