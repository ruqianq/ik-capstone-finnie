from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class GoalPlanningAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
    def process_query(self, query: str) -> str:
        """
        Analyzes the goal query and provides a savings plan.
        """
        # Simple extraction prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a financial planner. Extract the financial goal (amount, time horizon) from the user's query and calculate the monthly savings required. Provide a breakdown. Assume no interest for simplicity unless specified."),
            ("user", "{query}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            return chain.invoke({"query": query})
        except Exception as e:
            return f"Error processing goal: {e}. (Make sure OPENAI_API_KEY is set)"
