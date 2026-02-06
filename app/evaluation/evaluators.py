"""
Evaluators for FinnIE agent system.

Uses LLM-as-judge pattern with Phoenix evaluation framework.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class EvalScore(Enum):
    """Evaluation score levels."""
    EXCELLENT = 5
    GOOD = 4
    ACCEPTABLE = 3
    POOR = 2
    FAIL = 1


@dataclass
class EvalResult:
    """Result of an evaluation."""
    score: float
    label: str
    explanation: str
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict:
        return {
            "score": self.score,
            "label": self.label,
            "explanation": self.explanation,
            "metadata": self.metadata or {}
        }


class BaseEvaluator:
    """Base class for all evaluators."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model, temperature=0)

    def evaluate(self, **kwargs) -> EvalResult:
        raise NotImplementedError


class RAGEvaluator(BaseEvaluator):
    """
    Evaluates RAG (Retrieval-Augmented Generation) quality.

    Assesses:
    - Retrieval Relevance: Are retrieved documents relevant to the query?
    - Groundedness: Is the response grounded in retrieved documents?
    - Answer Completeness: Does the answer fully address the query?
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(model)

        self.relevance_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert evaluator assessing retrieval relevance.

Given a user query and retrieved documents, evaluate how relevant the documents are to answering the query.

Scoring:
- 5 (Excellent): Documents directly answer the query with comprehensive information
- 4 (Good): Documents are highly relevant with most needed information
- 3 (Acceptable): Documents are somewhat relevant but missing key details
- 2 (Poor): Documents are marginally relevant, mostly off-topic
- 1 (Fail): Documents are completely irrelevant

Respond in JSON format:
{{"score": <1-5>, "label": "<label>", "explanation": "<brief explanation>"}}"""),
            ("user", """Query: {query}

Retrieved Documents:
{documents}

Evaluate the relevance of these documents to the query.""")
        ])

        self.groundedness_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert evaluator assessing answer groundedness.

Given retrieved documents and a generated response, evaluate whether the response is grounded in (supported by) the documents.

Scoring:
- 5 (Excellent): Response is fully grounded, all claims supported by documents
- 4 (Good): Response is mostly grounded, minor unsupported details
- 3 (Acceptable): Response is partially grounded, some claims lack support
- 2 (Poor): Response has significant unsupported claims
- 1 (Fail): Response contradicts documents or is entirely hallucinated

Respond in JSON format:
{{"score": <1-5>, "label": "<label>", "explanation": "<brief explanation>"}}"""),
            ("user", """Retrieved Documents:
{documents}

Generated Response:
{response}

Evaluate the groundedness of the response.""")
        ])

    def evaluate_relevance(self, query: str, documents: List[str]) -> EvalResult:
        """Evaluate retrieval relevance."""
        docs_text = "\n\n".join([f"Document {i+1}:\n{doc}" for i, doc in enumerate(documents)])

        chain = self.relevance_prompt | self.llm | StrOutputParser()

        try:
            result = chain.invoke({"query": query, "documents": docs_text})
            parsed = json.loads(result)
            return EvalResult(
                score=parsed["score"],
                label=parsed["label"],
                explanation=parsed["explanation"],
                metadata={"eval_type": "relevance", "query": query}
            )
        except Exception as e:
            return EvalResult(
                score=0,
                label="Error",
                explanation=f"Evaluation failed: {str(e)}",
                metadata={"eval_type": "relevance", "error": str(e)}
            )

    def evaluate_groundedness(self, documents: List[str], response: str) -> EvalResult:
        """Evaluate response groundedness."""
        docs_text = "\n\n".join([f"Document {i+1}:\n{doc}" for i, doc in enumerate(documents)])

        chain = self.groundedness_prompt | self.llm | StrOutputParser()

        try:
            result = chain.invoke({"documents": docs_text, "response": response})
            parsed = json.loads(result)
            return EvalResult(
                score=parsed["score"],
                label=parsed["label"],
                explanation=parsed["explanation"],
                metadata={"eval_type": "groundedness"}
            )
        except Exception as e:
            return EvalResult(
                score=0,
                label="Error",
                explanation=f"Evaluation failed: {str(e)}",
                metadata={"eval_type": "groundedness", "error": str(e)}
            )

    def evaluate(self, query: str, documents: List[str], response: str) -> Dict[str, EvalResult]:
        """Run full RAG evaluation."""
        return {
            "relevance": self.evaluate_relevance(query, documents),
            "groundedness": self.evaluate_groundedness(documents, response)
        }


class RoutingEvaluator(BaseEvaluator):
    """
    Evaluates agent routing accuracy.

    Assesses whether queries are routed to the correct specialized agent.
    """

    VALID_INTENTS = [
        "finance_qa",
        "portfolio",
        "market_analysis",
        "goal_planning",
        "news",
        "tax_education"
    ]

    INTENT_DESCRIPTIONS = {
        "finance_qa": "General financial education questions (what is a stock, how does compound interest work)",
        "portfolio": "Portfolio management, stock prices, adding/removing holdings",
        "market_analysis": "Market overview, indices, sector performance, technical analysis",
        "goal_planning": "Savings goals, retirement planning, financial planning",
        "news": "Market news, headlines, current events in finance",
        "tax_education": "Tax questions, 401k, IRA, HSA, tax strategies"
    }

    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(model)

        intent_desc = "\n".join([f"- {k}: {v}" for k, v in self.INTENT_DESCRIPTIONS.items()])

        self.routing_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert evaluator assessing intent classification accuracy.

Given a user query and the classified intent, evaluate whether the classification is correct.

Available intents:
{intent_desc}

Scoring:
- 5 (Excellent): Perfect classification, clearly the right intent
- 4 (Good): Correct classification, though another could also work
- 3 (Acceptable): Classification is reasonable but not optimal
- 2 (Poor): Classification is questionable, likely wrong
- 1 (Fail): Classification is clearly wrong

Also provide the correct intent if the classification is wrong.

Respond in JSON format:
{{"score": <1-5>, "label": "<label>", "explanation": "<brief explanation>", "correct_intent": "<intent or null if correct>"}}"""),
            ("user", """Query: {query}

Classified Intent: {classified_intent}

Evaluate the routing accuracy.""")
        ])

    def evaluate(self, query: str, classified_intent: str) -> EvalResult:
        """Evaluate routing accuracy for a query."""
        chain = self.routing_prompt | self.llm | StrOutputParser()

        try:
            result = chain.invoke({
                "query": query,
                "classified_intent": classified_intent
            })
            parsed = json.loads(result)
            return EvalResult(
                score=parsed["score"],
                label=parsed["label"],
                explanation=parsed["explanation"],
                metadata={
                    "eval_type": "routing",
                    "query": query,
                    "classified_intent": classified_intent,
                    "correct_intent": parsed.get("correct_intent")
                }
            )
        except Exception as e:
            return EvalResult(
                score=0,
                label="Error",
                explanation=f"Evaluation failed: {str(e)}",
                metadata={"eval_type": "routing", "error": str(e)}
            )


class ResponseQualityEvaluator(BaseEvaluator):
    """
    Evaluates overall response quality.

    Assesses:
    - Helpfulness: Does the response help the user?
    - Accuracy: Is the information correct?
    - Coherence: Is the response well-structured and clear?
    - Completeness: Does it fully address the query?
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(model)

        self.quality_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert evaluator assessing response quality for a financial advisor chatbot.

Evaluate the response on these dimensions:
1. Helpfulness: Does it help the user achieve their goal?
2. Accuracy: Is the financial information correct? (Be careful with numbers, rates, limits)
3. Coherence: Is it well-organized and easy to understand?
4. Completeness: Does it fully address what the user asked?

Provide an overall score and individual dimension scores.

Respond in JSON format:
{{
    "overall_score": <1-5>,
    "overall_label": "<label>",
    "dimensions": {{
        "helpfulness": {{"score": <1-5>, "note": "<brief note>"}},
        "accuracy": {{"score": <1-5>, "note": "<brief note>"}},
        "coherence": {{"score": <1-5>, "note": "<brief note>"}},
        "completeness": {{"score": <1-5>, "note": "<brief note>"}}
    }},
    "explanation": "<overall assessment>"
}}"""),
            ("user", """User Query: {query}

Agent Response: {response}

Evaluate the quality of this response.""")
        ])

    def evaluate(self, query: str, response: str) -> EvalResult:
        """Evaluate response quality."""
        chain = self.quality_prompt | self.llm | StrOutputParser()

        try:
            result = chain.invoke({"query": query, "response": response})
            parsed = json.loads(result)
            return EvalResult(
                score=parsed["overall_score"],
                label=parsed["overall_label"],
                explanation=parsed["explanation"],
                metadata={
                    "eval_type": "response_quality",
                    "dimensions": parsed["dimensions"],
                    "query": query
                }
            )
        except Exception as e:
            return EvalResult(
                score=0,
                label="Error",
                explanation=f"Evaluation failed: {str(e)}",
                metadata={"eval_type": "response_quality", "error": str(e)}
            )


class HallucinationEvaluator(BaseEvaluator):
    """
    Evaluates whether a response contains hallucinations.

    Specifically checks for:
    - Made-up statistics or numbers
    - Incorrect financial facts
    - Claims not supported by context
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(model)

        self.hallucination_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert evaluator detecting hallucinations in financial advice responses.

Hallucinations include:
- Made-up statistics, percentages, or dollar amounts
- Incorrect financial facts (wrong contribution limits, rates, etc.)
- Claims about specific companies/stocks that may be fabricated
- Confident statements about uncertain or changing information

Scoring:
- 5 (Excellent): No hallucinations detected, all claims verifiable or properly hedged
- 4 (Good): Minor potential issues but generally accurate
- 3 (Acceptable): Some questionable claims but core info is correct
- 2 (Poor): Contains likely hallucinations that could mislead users
- 1 (Fail): Significant hallucinations, dangerous misinformation

Respond in JSON format:
{{
    "score": <1-5>,
    "label": "<label>",
    "hallucinations_found": ["<list of potential hallucinations if any>"],
    "explanation": "<brief explanation>"
}}"""),
            ("user", """Query: {query}

Response to evaluate:
{response}

Context provided (if any):
{context}

Check for hallucinations.""")
        ])

    def evaluate(self, query: str, response: str, context: str = "") -> EvalResult:
        """Evaluate for hallucinations."""
        chain = self.hallucination_prompt | self.llm | StrOutputParser()

        try:
            result = chain.invoke({
                "query": query,
                "response": response,
                "context": context or "No additional context provided"
            })
            parsed = json.loads(result)
            return EvalResult(
                score=parsed["score"],
                label=parsed["label"],
                explanation=parsed["explanation"],
                metadata={
                    "eval_type": "hallucination",
                    "hallucinations_found": parsed.get("hallucinations_found", []),
                    "query": query
                }
            )
        except Exception as e:
            return EvalResult(
                score=0,
                label="Error",
                explanation=f"Evaluation failed: {str(e)}",
                metadata={"eval_type": "hallucination", "error": str(e)}
            )
