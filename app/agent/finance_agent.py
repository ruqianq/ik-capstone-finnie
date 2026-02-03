# import google.generativeai as genai # Will add in next step
import os
from app.rag.retriever import FinanceRetriever

# tracer = trace.get_tracer(__name__)

class FinanceAgent:
    def __init__(self):
        self.retriever = FinanceRetriever()
        
    def process_query(self, query: str) -> str:
        # 1. Retrieve relevant context
        docs = self.retriever.get_relevant_documents(query)
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        # 2. Construct Prompt (Stub for now, will connect to LLM later)
        prompt = f"""
        You are a helpful financial advisor. Use the following context to answer the user's question.
        
        Context:
        {context_text}
        
        Question: {query}
        
        Answer:
        """
        
        # TODO: Call actual LLM (Google ADK / GenAI)
        # For now, we return a mock response that proves RAG worked
        if context_text:
            response = f"Based on my knowledge base:\n\n{context_text[:200]}...\n\n(This is a RAG-retrieved snippet)"
        else:
            response = "I couldn't find any information about that in my knowledge base."
            
        return response
