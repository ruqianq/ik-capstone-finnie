"""Finance Q&A Agent with RAG support."""

from typing import List

from finnie.agents.base import BaseAgent, AgentType, AgentRequest, AgentResponse
from finnie.rag import rag_pipeline
from finnie.observability import log_with_trace


class FinanceQAAgent(BaseAgent):
    """Agent for answering financial questions using RAG."""
    
    def __init__(self):
        super().__init__(AgentType.FINANCE_QA)
        rag_pipeline.initialize()
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process a finance Q&A request.
        
        Args:
            request: The agent request
            
        Returns:
            AgentResponse with answer and citations
        """
        if not self.validate_request(request):
            raise ValueError("Invalid request")
        
        log_with_trace(
            f"Processing finance Q&A: {request.query}",
            trace_id=request.trace_id
        )
        
        # Retrieve relevant documents
        results = rag_pipeline.retrieve(
            request.query,
            trace_id=request.trace_id
        )
        
        # Extract citations
        citations = [f"[{i+1}] {doc.source}" for i, (doc, _) in enumerate(results)]
        
        # Build context from retrieved documents
        context_parts = []
        for i, (doc, similarity) in enumerate(results):
            context_parts.append(
                f"Document {i+1} (similarity: {similarity:.2f}):\n{doc.content}"
            )
        
        context = "\n\n".join(context_parts)
        
        # Generate response (in a real implementation, this would call an LLM)
        # For now, we'll create a simple response based on retrieved documents
        if results:
            response_text = self._generate_response(request.query, results)
        else:
            response_text = "I don't have enough information to answer that question. Please try rephrasing or ask about stocks, bonds, portfolio diversification, or investment strategies."
        
        return AgentResponse(
            response=response_text,
            agent_type=self.agent_type,
            trace_id=request.trace_id,
            metadata={
                "num_documents_retrieved": len(results),
                "query": request.query,
            },
            citations=citations,
            confidence=results[0][1] if results else 0.0,
        )
    
    def _generate_response(self, query: str, results: List) -> str:
        """
        Generate a response based on retrieved documents.
        
        Args:
            query: The user's query
            results: List of (Document, similarity_score) tuples
            
        Returns:
            Generated response text
        """
        # Simple template-based response
        # In production, this would use an LLM
        
        if not results:
            return "I couldn't find relevant information to answer your question."
        
        # Get the most relevant document
        top_doc, similarity = results[0]
        
        response_parts = [
            f"Based on the available information:\n\n{top_doc.content}",
        ]
        
        # Add additional context if available
        if len(results) > 1:
            response_parts.append("\n\nAdditional relevant information:")
            for i, (doc, score) in enumerate(results[1:3], 2):  # Add up to 2 more
                response_parts.append(f"\n• {doc.content}")
        
        return "".join(response_parts)
