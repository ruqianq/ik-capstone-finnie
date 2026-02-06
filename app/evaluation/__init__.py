"""
FinnIE Evaluation Module

Provides evaluation capabilities for:
- RAG retrieval relevance and groundedness
- Agent routing accuracy
- Response quality assessment
- Hallucination detection
"""

from app.evaluation.evaluators import (
    RAGEvaluator,
    RoutingEvaluator,
    ResponseQualityEvaluator,
    HallucinationEvaluator,
    EvalResult,
)
from app.evaluation.runner import EvaluationRunner, TraceData, EvaluationReport

__all__ = [
    "RAGEvaluator",
    "RoutingEvaluator",
    "ResponseQualityEvaluator",
    "HallucinationEvaluator",
    "EvalResult",
    "EvaluationRunner",
    "TraceData",
    "EvaluationReport",
]
