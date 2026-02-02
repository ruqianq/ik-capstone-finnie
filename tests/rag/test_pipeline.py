"""Tests for RAG pipeline."""

import pytest
from finnie.rag.pipeline import RAGPipeline, Document


def test_document_creation():
    """Test Document creation."""
    doc = Document(
        content="Test content",
        source="test_source",
        metadata={"key": "value"}
    )
    
    assert doc.content == "Test content"
    assert doc.source == "test_source"
    assert doc.metadata["key"] == "value"


def test_rag_pipeline_initialization():
    """Test RAG pipeline initialization."""
    pipeline = RAGPipeline()
    pipeline.initialize()
    
    assert pipeline._initialized is True
    assert pipeline.embedding_model is not None
    assert pipeline.index is not None
    assert len(pipeline.documents) > 0


def test_rag_retrieve():
    """Test document retrieval."""
    pipeline = RAGPipeline()
    pipeline.initialize()
    
    results = pipeline.retrieve("What is a stock?", top_k=3)
    
    assert len(results) > 0
    assert len(results) <= 3
    
    for doc, similarity in results:
        assert isinstance(doc, Document)
        assert 0 <= similarity <= 1


def test_rag_add_documents():
    """Test adding documents to the index."""
    pipeline = RAGPipeline()
    pipeline.initialize()
    
    initial_count = len(pipeline.documents)
    
    new_docs = [
        Document("Test document 1", "test_1"),
        Document("Test document 2", "test_2"),
    ]
    
    pipeline.add_documents(new_docs)
    
    assert len(pipeline.documents) == initial_count + 2


def test_rag_retrieve_with_trace():
    """Test retrieval with trace ID."""
    pipeline = RAGPipeline()
    pipeline.initialize()
    
    results = pipeline.retrieve(
        "portfolio diversification",
        top_k=2,
        trace_id="test-trace-123"
    )
    
    assert len(results) > 0
    assert all(isinstance(doc, Document) for doc, _ in results)
