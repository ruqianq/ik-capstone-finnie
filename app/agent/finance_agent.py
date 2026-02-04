# import google.generativeai as genai # Will add in next step
import os
from app.rag.retriever import FinanceRetriever
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# tracer = trace.get_tracer(__name__)

class FinanceAgent:
    def __init__(self):
        self.retriever = FinanceRetriever()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
    def process_query(self, query: str) -> str:
        # 1. Retrieve relevant context
        docs = self.retriever.get_relevant_documents(query)
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        # 2. Construct Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful financial advisor. Use the following context to answer the user's question. If the answer is not in the context, use your general knowledge but mention that it is general knowledge."),
            ("user", "Context:\n{context}\n\nQuestion: {query}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            response = chain.invoke({"context": context_text, "query": query})
            # Append citations for transparency
            if context_text:
                response += "\n\n*(Source: Internal Knowledge Base)*"
            return response
        except Exception as e:
            return f"Error generating response: {e}. (Check env vars)"
