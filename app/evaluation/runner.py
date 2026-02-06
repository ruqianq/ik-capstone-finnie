"""
Evaluation Runner for FinnIE.

Pulls traces from Phoenix and runs evaluations on them.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import pandas as pd

import phoenix as px
from phoenix.trace import SpanEvaluations

from app.evaluation.evaluators import (
    RAGEvaluator,
    RoutingEvaluator,
    ResponseQualityEvaluator,
    HallucinationEvaluator,
    EvalResult
)


@dataclass
class TraceData:
    """Extracted data from a trace for evaluation."""
    trace_id: str
    span_id: str
    query: str
    response: str
    intent: Optional[str] = None
    retrieved_documents: Optional[List[str]] = None
    timestamp: Optional[datetime] = None
    latency_ms: Optional[float] = None


@dataclass
class EvaluationReport:
    """Complete evaluation report for a trace."""
    trace_id: str
    timestamp: datetime
    query: str
    response: str
    evaluations: Dict[str, Dict]
    overall_score: float

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "query": self.query,
            "response": self.response[:200] + "..." if len(self.response) > 200 else self.response,
            "evaluations": self.evaluations,
            "overall_score": self.overall_score
        }


class EvaluationRunner:
    """
    Runs evaluations on traces from Phoenix.

    Usage:
        runner = EvaluationRunner()
        results = runner.run_evaluation(limit=100)
        runner.save_results(results, "eval_results.json")
    """

    def __init__(self, phoenix_url: str = None):
        """
        Initialize the evaluation runner.

        Args:
            phoenix_url: URL of Phoenix server. Defaults to localhost:6007 (Docker mapped port).
        """
        self.phoenix_url = phoenix_url or os.getenv("PHOENIX_URL", "http://localhost:6007")

        # Initialize evaluators
        self.rag_evaluator = RAGEvaluator()
        self.routing_evaluator = RoutingEvaluator()
        self.quality_evaluator = ResponseQualityEvaluator()
        self.hallucination_evaluator = HallucinationEvaluator()

    def get_traces(
        self,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch traces from Phoenix.

        Args:
            limit: Maximum number of traces to fetch
            start_time: Filter traces after this time
            end_time: Filter traces before this time

        Returns:
            DataFrame with trace data
        """
        try:
            # Connect to Phoenix and get traces
            client = px.Client(endpoint=self.phoenix_url)

            # Get spans from Phoenix
            spans_df = client.get_spans_dataframe()

            if spans_df.empty:
                print("No traces found in Phoenix")
                return pd.DataFrame()

            # Filter by time if specified
            if start_time and 'start_time' in spans_df.columns:
                spans_df = spans_df[spans_df['start_time'] >= start_time]
            if end_time and 'start_time' in spans_df.columns:
                spans_df = spans_df[spans_df['start_time'] <= end_time]

            # Limit results
            spans_df = spans_df.head(limit)

            return spans_df

        except Exception as e:
            print(f"Error fetching traces from Phoenix: {e}")
            return pd.DataFrame()

    def _extract_value(self, data: Any, keys: List[str]) -> Optional[str]:
        """Try to extract a string value from various possible locations."""
        if data is None:
            return None

        # If it's already a string
        if isinstance(data, str) and len(data) > 3:
            # Try to parse as JSON if it looks like JSON
            if data.strip().startswith('{') or data.strip().startswith('['):
                try:
                    parsed = json.loads(data)
                    result = self._extract_value(parsed, keys)
                    if result:
                        return result
                except:
                    pass
            return data

        # If it's a dict, try the keys
        if isinstance(data, dict):
            for key in keys:
                val = data.get(key)
                if val:
                    result = self._extract_value(val, keys)
                    if result:
                        return result

        # If it's a list, try first/last element
        if isinstance(data, list) and len(data) > 0:
            for item in [data[0], data[-1]]:
                result = self._extract_value(item, keys)
                if result:
                    return result

        return None

    def extract_trace_data(self, spans_df: pd.DataFrame) -> List[TraceData]:
        """
        Extract relevant data from spans for evaluation.

        Args:
            spans_df: DataFrame of spans from Phoenix

        Returns:
            List of TraceData objects ready for evaluation
        """
        traces = []
        skipped_no_input = 0
        skipped_no_output = 0

        # Keys to look for in nested structures
        value_keys = ['value', 'content', 'text', 'message', 'body']

        for idx, row in spans_df.iterrows():
            try:
                query = None
                response = None

                # Method 1: Check flat Phoenix columns (attributes.input.value, etc.)
                # Phoenix flattens attributes into columns like 'attributes.input.value'
                input_cols = [
                    'attributes.input.value',
                    'attributes.input',
                    'input.value',
                    'input',
                ]
                for col in input_cols:
                    if col in spans_df.columns:
                        val = row.get(col)
                        if val and isinstance(val, str) and len(val) > 3:
                            query = val
                            break

                output_cols = [
                    'attributes.output.value',
                    'attributes.output',
                    'output.value',
                    'output',
                ]
                for col in output_cols:
                    if col in spans_df.columns:
                        val = row.get(col)
                        if val and isinstance(val, str) and len(val) > 3:
                            response = val
                            break

                # Method 2: Check any column containing 'input' or 'output'
                if not query or not response:
                    for col in spans_df.columns:
                        col_lower = col.lower()
                        val = row.get(col)

                        if val is None or (isinstance(val, float) and pd.isna(val)):
                            continue

                        # Input columns
                        if not query and 'input' in col_lower and 'value' in col_lower:
                            query = self._extract_value(val, value_keys)

                        # Output columns
                        if not response and 'output' in col_lower and 'value' in col_lower:
                            response = self._extract_value(val, value_keys)

                # Method 3: Check attributes dict/column (fallback for different Phoenix versions)
                attributes = row.get('attributes', {})
                if isinstance(attributes, str):
                    try:
                        attributes = json.loads(attributes)
                    except:
                        attributes = {}

                if isinstance(attributes, dict):
                    # Input paths
                    if not query:
                        input_paths = [
                            'input.value', 'input', 'openinference.span.input',
                            'llm.input_messages', 'llm.prompts', 'query'
                        ]
                        for path in input_paths:
                            val = attributes.get(path)
                            if val:
                                query = self._extract_value(val, value_keys)
                                if query:
                                    break

                    # Output paths
                    if not response:
                        output_paths = [
                            'output.value', 'output', 'openinference.span.output',
                            'llm.output_messages', 'llm.completions', 'response'
                        ]
                        for path in output_paths:
                            val = attributes.get(path)
                            if val:
                                response = self._extract_value(val, value_keys)
                                if response:
                                    break

                # Skip if no query/response
                if not query:
                    skipped_no_input += 1
                    continue
                if not response:
                    skipped_no_output += 1
                    continue

                # Extract intent if available
                intent = None
                if isinstance(attributes, dict):
                    intent = attributes.get('intent') or attributes.get('classified_intent')

                # Extract retrieved documents if RAG span
                docs = []
                if isinstance(attributes, dict):
                    retrieval_paths = ['retrieval.documents', 'documents', 'context', 'retrieved_documents']
                    for path in retrieval_paths:
                        retrieval_docs = attributes.get(path, [])
                        if retrieval_docs:
                            if isinstance(retrieval_docs, list):
                                for doc in retrieval_docs:
                                    if isinstance(doc, dict):
                                        content = doc.get('content', '') or doc.get('page_content', '') or doc.get('text', '')
                                        if content:
                                            docs.append(content)
                                    elif isinstance(doc, str):
                                        docs.append(doc)
                            break

                # Get span/trace IDs (Phoenix uses 'context.span_id' and 'context.trace_id')
                trace_id = row.get('context.trace_id')
                span_id = row.get('context.span_id')

                # Handle missing IDs
                if trace_id is None or (isinstance(trace_id, float) and pd.isna(trace_id)):
                    trace_id = str(idx)
                else:
                    trace_id = str(trace_id)

                if span_id is None or (isinstance(span_id, float) and pd.isna(span_id)):
                    span_id = str(idx)
                else:
                    span_id = str(span_id)

                trace_data = TraceData(
                    trace_id=trace_id,
                    span_id=span_id,
                    query=str(query),
                    response=str(response),
                    intent=intent,
                    retrieved_documents=docs if docs else None,
                    timestamp=row.get('start_time'),
                    latency_ms=row.get('latency_ms')
                )
                traces.append(trace_data)

            except Exception as e:
                print(f"Error extracting trace data: {e}")
                continue

        if skipped_no_input > 0 or skipped_no_output > 0:
            print(f"  Skipped {skipped_no_input} spans with no input, {skipped_no_output} with no output")

        return traces

    def evaluate_trace(self, trace: TraceData) -> EvaluationReport:
        """
        Run all applicable evaluations on a single trace.

        Args:
            trace: TraceData to evaluate

        Returns:
            EvaluationReport with all evaluation results
        """
        evaluations = {}

        # Always run response quality evaluation
        quality_result = self.quality_evaluator.evaluate(
            query=trace.query,
            response=trace.response
        )
        evaluations["response_quality"] = quality_result.to_dict()

        # Always run hallucination check
        hallucination_result = self.hallucination_evaluator.evaluate(
            query=trace.query,
            response=trace.response,
            context="\n".join(trace.retrieved_documents) if trace.retrieved_documents else ""
        )
        evaluations["hallucination"] = hallucination_result.to_dict()

        # Run routing evaluation if intent is available
        if trace.intent:
            routing_result = self.routing_evaluator.evaluate(
                query=trace.query,
                classified_intent=trace.intent
            )
            evaluations["routing"] = routing_result.to_dict()

        # Run RAG evaluation if documents are available
        if trace.retrieved_documents:
            rag_results = self.rag_evaluator.evaluate(
                query=trace.query,
                documents=trace.retrieved_documents,
                response=trace.response
            )
            evaluations["rag_relevance"] = rag_results["relevance"].to_dict()
            evaluations["rag_groundedness"] = rag_results["groundedness"].to_dict()

        # Calculate overall score (average of all scores)
        scores = [e["score"] for e in evaluations.values() if e.get("score", 0) > 0]
        overall_score = sum(scores) / len(scores) if scores else 0

        return EvaluationReport(
            trace_id=trace.trace_id,
            timestamp=trace.timestamp or datetime.now(),
            query=trace.query,
            response=trace.response,
            evaluations=evaluations,
            overall_score=round(overall_score, 2)
        )

    def run_evaluation(
        self,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        upload_to_phoenix: bool = True
    ) -> List[EvaluationReport]:
        """
        Run evaluations on traces from Phoenix.

        Args:
            limit: Maximum number of traces to evaluate
            start_time: Filter traces after this time
            end_time: Filter traces before this time
            upload_to_phoenix: Whether to upload results back to Phoenix UI

        Returns:
            List of EvaluationReport objects
        """
        print(f"Fetching traces from Phoenix ({self.phoenix_url})...")
        spans_df = self.get_traces(limit=limit, start_time=start_time, end_time=end_time)

        if spans_df.empty:
            print("No traces to evaluate")
            return []

        print(f"Found {len(spans_df)} spans")
        print(f"Columns: {list(spans_df.columns)}")

        # Debug: Show first span's structure
        if len(spans_df) > 0:
            first_row = spans_df.iloc[0]
            print("\nDEBUG - First span structure:")
            for col in spans_df.columns:
                val = first_row.get(col)
                if val is not None and str(val).strip():
                    val_str = str(val)[:100] + "..." if len(str(val)) > 100 else str(val)
                    print(f"  {col}: {val_str}")

        print("\nExtracting trace data...")
        traces = self.extract_trace_data(spans_df)
        print(f"Extracted {len(traces)} evaluable traces")

        if not traces:
            return []

        print("Running evaluations...")
        reports = []
        evaluated_traces = []
        for i, trace in enumerate(traces):
            print(f"  Evaluating trace {i+1}/{len(traces)}...")
            try:
                report = self.evaluate_trace(trace)
                reports.append(report)
                evaluated_traces.append(trace)
            except Exception as e:
                print(f"  Error evaluating trace {trace.trace_id}: {e}")

        print(f"Completed {len(reports)} evaluations")

        # Upload results back to Phoenix
        if upload_to_phoenix and reports:
            print("Uploading evaluations to Phoenix...")
            self.upload_to_phoenix(evaluated_traces, reports)

        return reports

    def run_evaluation_on_samples(self, samples: List[Dict]) -> List[EvaluationReport]:
        """
        Run evaluations on manually provided samples (for testing).

        Args:
            samples: List of dicts with keys: query, response, intent (optional), documents (optional)

        Returns:
            List of EvaluationReport objects
        """
        reports = []

        for i, sample in enumerate(samples):
            trace = TraceData(
                trace_id=f"sample_{i}",
                span_id=f"sample_{i}",
                query=sample["query"],
                response=sample["response"],
                intent=sample.get("intent"),
                retrieved_documents=sample.get("documents"),
                timestamp=datetime.now()
            )

            try:
                report = self.evaluate_trace(trace)
                reports.append(report)
            except Exception as e:
                print(f"Error evaluating sample {i}: {e}")

        return reports

    def save_results(self, reports: List[EvaluationReport], filepath: str):
        """
        Save evaluation results to a JSON file.

        Args:
            reports: List of EvaluationReport objects
            filepath: Path to save the results
        """
        results = {
            "evaluation_date": datetime.now().isoformat(),
            "total_evaluations": len(reports),
            "average_score": round(
                sum(r.overall_score for r in reports) / len(reports), 2
            ) if reports else 0,
            "reports": [r.to_dict() for r in reports]
        }

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"Results saved to {filepath}")

    def upload_to_phoenix(
        self,
        traces: List[TraceData],
        reports: List[EvaluationReport]
    ) -> bool:
        """
        Upload evaluation results back to Phoenix as SpanEvaluations.

        This allows viewing evaluation scores directly in the Phoenix UI
        alongside the original traces.

        Args:
            traces: List of TraceData with span_ids
            reports: List of corresponding EvaluationReport objects

        Returns:
            True if upload successful, False otherwise
        """
        try:
            client = px.Client(endpoint=self.phoenix_url)

            # Create evaluation DataFrames for each evaluation type
            eval_types = set()
            for report in reports:
                eval_types.update(report.evaluations.keys())

            for eval_type in eval_types:
                eval_data = []

                for trace, report in zip(traces, reports):
                    if eval_type in report.evaluations:
                        eval_result = report.evaluations[eval_type]
                        eval_data.append({
                            "context.span_id": trace.span_id,
                            "score": eval_result.get("score", 0),
                            "label": eval_result.get("label", ""),
                            "explanation": eval_result.get("explanation", "")
                        })

                if eval_data:
                    eval_df = pd.DataFrame(eval_data)
                    eval_df = eval_df.set_index("context.span_id")

                    # Log evaluations to Phoenix
                    client.log_evaluations(
                        SpanEvaluations(
                            eval_name=eval_type,
                            dataframe=eval_df
                        )
                    )
                    print(f"  Uploaded {len(eval_data)} {eval_type} evaluations to Phoenix")

            # Also upload overall score
            overall_data = []
            for trace, report in zip(traces, reports):
                overall_data.append({
                    "context.span_id": trace.span_id,
                    "score": report.overall_score,
                    "label": "Excellent" if report.overall_score >= 4.5 else
                             "Good" if report.overall_score >= 4 else
                             "Acceptable" if report.overall_score >= 3 else
                             "Poor" if report.overall_score >= 2 else "Fail",
                    "explanation": f"Overall evaluation score: {report.overall_score}/5.0"
                })

            if overall_data:
                overall_df = pd.DataFrame(overall_data)
                overall_df = overall_df.set_index("context.span_id")

                client.log_evaluations(
                    SpanEvaluations(
                        eval_name="overall_quality",
                        dataframe=overall_df
                    )
                )
                print(f"  Uploaded {len(overall_data)} overall_quality evaluations to Phoenix")

            print(f"Successfully uploaded evaluations to Phoenix!")
            return True

        except Exception as e:
            print(f"Error uploading to Phoenix: {e}")
            return False

    def get_summary_metrics(self, reports: List[EvaluationReport]) -> Dict:
        """
        Calculate summary metrics from evaluation reports.

        Args:
            reports: List of EvaluationReport objects

        Returns:
            Dict with summary metrics
        """
        if not reports:
            return {"error": "No reports to summarize"}

        # Collect scores by evaluation type
        scores_by_type = {}
        for report in reports:
            for eval_type, eval_data in report.evaluations.items():
                if eval_type not in scores_by_type:
                    scores_by_type[eval_type] = []
                if eval_data.get("score", 0) > 0:
                    scores_by_type[eval_type].append(eval_data["score"])

        # Calculate averages
        averages = {}
        for eval_type, scores in scores_by_type.items():
            if scores:
                averages[eval_type] = {
                    "average": round(sum(scores) / len(scores), 2),
                    "min": min(scores),
                    "max": max(scores),
                    "count": len(scores)
                }

        # Overall metrics
        all_scores = [r.overall_score for r in reports if r.overall_score > 0]

        return {
            "total_evaluations": len(reports),
            "overall_average": round(sum(all_scores) / len(all_scores), 2) if all_scores else 0,
            "by_evaluation_type": averages,
            "score_distribution": {
                "excellent (5)": sum(1 for s in all_scores if s >= 4.5),
                "good (4-4.5)": sum(1 for s in all_scores if 4 <= s < 4.5),
                "acceptable (3-4)": sum(1 for s in all_scores if 3 <= s < 4),
                "poor (2-3)": sum(1 for s in all_scores if 2 <= s < 3),
                "fail (<2)": sum(1 for s in all_scores if s < 2)
            }
        }


def main():
    """Run evaluation from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Run FinnIE evaluations")
    parser.add_argument("--limit", type=int, default=50, help="Max traces to evaluate")
    parser.add_argument("--output", type=str, default="eval_results.json", help="Output file")
    parser.add_argument("--phoenix-url", type=str, help="Phoenix server URL")
    parser.add_argument("--no-upload", action="store_true", help="Don't upload results to Phoenix")

    args = parser.parse_args()

    runner = EvaluationRunner(phoenix_url=args.phoenix_url)
    reports = runner.run_evaluation(
        limit=args.limit,
        upload_to_phoenix=not args.no_upload
    )

    if reports:
        runner.save_results(reports, args.output)

        # Print summary
        summary = runner.get_summary_metrics(reports)
        print("\n" + "="*50)
        print("EVALUATION SUMMARY")
        print("="*50)
        print(f"Total Evaluations: {summary['total_evaluations']}")
        print(f"Overall Average Score: {summary['overall_average']}/5.0")
        print("\nScores by Type:")
        for eval_type, metrics in summary.get('by_evaluation_type', {}).items():
            print(f"  {eval_type}: {metrics['average']}/5.0 (n={metrics['count']})")
        print("\nScore Distribution:")
        for label, count in summary.get('score_distribution', {}).items():
            print(f"  {label}: {count}")

        if not args.no_upload:
            print("\nEvaluations uploaded to Phoenix UI - view them alongside your traces!")


if __name__ == "__main__":
    main()
