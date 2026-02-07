"""
Evaluation Dashboard Page
View and run evaluations on FinnIE agent performance.
"""

import streamlit as st
import sys
import os
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Page configuration
st.set_page_config(
    page_title="Evaluation - FinnIE",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 Evaluation Dashboard")
st.markdown("Evaluate and monitor FinnIE agent performance")

# Sidebar
with st.sidebar:
    st.markdown("## 💰 FinnIE")
    st.markdown("*Evaluation Engine*")
    st.divider()

    st.markdown("### Evaluation Types")
    st.markdown("""
    - **RAG Quality**: Retrieval relevance & groundedness
    - **Routing**: Intent classification accuracy
    - **Response**: Helpfulness, accuracy, coherence
    - **Hallucination**: Fact-checking responses
    """)

    st.divider()

    st.markdown("### Quick Links")
    phoenix_url = os.getenv("PHOENIX_URL", "http://localhost:6007")
    st.markdown(f"[Open Phoenix UI]({phoenix_url})")


# Tab layout
tab1, tab2, tab3 = st.tabs(["📊 Results", "🚀 Run Evaluation", "📝 Manual Test"])


with tab1:
    st.markdown("### Evaluation Results")

    # Load results if available
    results_path = "eval_results.json"

    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            results = json.load(f)

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Evaluations", results.get("total_evaluations", 0))

        with col2:
            avg_score = results.get("average_score", 0)
            st.metric("Average Score", f"{avg_score}/5.0")

        with col3:
            st.metric("Evaluation Date", results.get("evaluation_date", "N/A")[:10])

        with col4:
            excellent = sum(1 for r in results.get("reports", []) if r.get("overall_score", 0) >= 4.5)
            st.metric("Excellent (≥4.5)", excellent)

        st.divider()

        # Score distribution chart
        reports = results.get("reports", [])
        if reports:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Score Distribution")
                scores = [r.get("overall_score", 0) for r in reports]
                score_df = pd.DataFrame({"Score": scores})

                fig_hist = px.histogram(
                    score_df,
                    x="Score",
                    nbins=10,
                    title="Overall Score Distribution",
                    color_discrete_sequence=['#2196F3']
                )
                fig_hist.update_layout(
                    xaxis_title="Score",
                    yaxis_title="Count",
                    height=350
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            with col2:
                st.markdown("#### Scores by Evaluation Type")

                # Aggregate scores by type
                type_scores = {}
                for report in reports:
                    for eval_type, eval_data in report.get("evaluations", {}).items():
                        if eval_type not in type_scores:
                            type_scores[eval_type] = []
                        if eval_data.get("score", 0) > 0:
                            type_scores[eval_type].append(eval_data["score"])

                type_avgs = {k: sum(v)/len(v) for k, v in type_scores.items() if v}

                if type_avgs:
                    fig_bar = go.Figure(data=[
                        go.Bar(
                            x=list(type_avgs.keys()),
                            y=list(type_avgs.values()),
                            marker_color=['#4CAF50' if v >= 4 else '#FF9800' if v >= 3 else '#F44336'
                                          for v in type_avgs.values()],
                            text=[f"{v:.2f}" for v in type_avgs.values()],
                            textposition='outside'
                        )
                    ])
                    fig_bar.update_layout(
                        title="Average Score by Evaluation Type",
                        yaxis_title="Average Score",
                        yaxis_range=[0, 5.5],
                        height=350
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

            st.divider()

            # Detailed results table
            st.markdown("#### Detailed Results")

            # Create summary dataframe
            summary_data = []
            for report in reports:
                row = {
                    "Query": report.get("query", "")[:50] + "..." if len(report.get("query", "")) > 50 else report.get("query", ""),
                    "Overall": report.get("overall_score", 0),
                }
                for eval_type, eval_data in report.get("evaluations", {}).items():
                    row[eval_type.replace("_", " ").title()] = eval_data.get("score", "-")
                summary_data.append(row)

            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            # Expandable detailed view
            st.markdown("#### Detailed Explanations")
            for i, report in enumerate(reports[:10]):  # Show first 10
                with st.expander(f"Query: {report.get('query', '')[:60]}..."):
                    st.markdown(f"**Overall Score:** {report.get('overall_score', 0)}/5.0")
                    st.markdown(f"**Response:** {report.get('response', '')[:300]}...")

                    for eval_type, eval_data in report.get("evaluations", {}).items():
                        st.markdown(f"**{eval_type.replace('_', ' ').title()}:**")
                        st.markdown(f"- Score: {eval_data.get('score', 'N/A')}/5.0 ({eval_data.get('label', 'N/A')})")
                        st.markdown(f"- {eval_data.get('explanation', 'No explanation')}")
    else:
        st.info("No evaluation results found. Run an evaluation first!")
        st.markdown("""
        To run evaluations from the command line:
        ```bash
        # Inside Docker container:
        docker-compose exec finnie-app python -m app.evaluation.runner --limit 50 --phoenix-url http://phoenix:6006

        # Or use make command:
        make evaluate
        ```
        """)


with tab2:
    st.markdown("### Run Evaluation from Traces")
    st.markdown("Pull traces from Phoenix and evaluate agent performance automatically.")

    # Show current Phoenix URL for diagnostics
    current_phoenix_url = os.getenv("PHOENIX_URL", "http://localhost:6007")
    st.caption(f"Phoenix endpoint: `{current_phoenix_url}`")

    col1, col2 = st.columns(2)
    with col1:
        trace_limit = st.number_input("Max traces to evaluate", min_value=1, max_value=500, value=50)
    with col2:
        upload_to_phoenix = st.checkbox("Upload results to Phoenix UI", value=True)

    output_file = st.text_input("Output file", value="eval_results.json")

    bcol1, bcol2 = st.columns(2)
    run_eval = bcol1.button("🚀 Run Evaluation", type="primary")
    test_conn = bcol2.button("🔌 Test Connection")

    if test_conn:
        try:
            from app.evaluation.runner import EvaluationRunner
            runner = EvaluationRunner()
            with st.spinner(f"Testing connection to `{runner.phoenix_url}`..."):
                ok, msg = runner.test_connection()
            if ok:
                st.success(msg)
            else:
                st.error(msg)
        except Exception as e:
            st.error(f"Could not initialize runner: {e}")

    if run_eval:
        try:
            from app.evaluation.runner import EvaluationRunner

            runner = EvaluationRunner()
            st.info(f"Connecting to Phoenix at `{runner.phoenix_url}`...")

            # Test connection first
            with st.spinner("Testing Phoenix connection..."):
                ok, msg = runner.test_connection()

            if not ok:
                st.error(f"Cannot reach Phoenix: {msg}")
                st.markdown("""
                **Troubleshooting:**
                - Make sure Phoenix is running: `docker-compose up -d`
                - Inside Docker, the URL should be `http://phoenix:6006`
                - Outside Docker, use `http://localhost:6007`
                """)
            else:
                st.success("Phoenix connection OK")

                with st.spinner(f"Fetching up to {trace_limit} traces..."):
                    try:
                        spans_df = runner.get_traces(limit=trace_limit)
                    except ConnectionError as e:
                        st.error(str(e))
                        spans_df = pd.DataFrame()

                if spans_df.empty:
                    st.warning("No traces found in Phoenix. Chat with the agent first to generate traces, then try again.")
                else:
                    st.success(f"Found {len(spans_df)} spans")

                    with st.spinner("Extracting trace data..."):
                        traces = runner.extract_trace_data(spans_df)

                    if not traces:
                        st.warning("No evaluable traces found (spans missing input/output data).")
                    else:
                        st.info(f"Extracted {len(traces)} evaluable traces. Running evaluations...")

                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        reports = []
                        evaluated_traces = []
                        for i, trace_item in enumerate(traces):
                            status_text.text(f"Evaluating trace {i+1}/{len(traces)}...")
                            progress_bar.progress((i + 1) / len(traces))
                            try:
                                report = runner.evaluate_trace(trace_item)
                                reports.append(report)
                                evaluated_traces.append(trace_item)
                            except Exception as e:
                                st.warning(f"Error evaluating trace {trace_item.trace_id}: {e}")

                        progress_bar.empty()
                        status_text.empty()

                        if reports:
                            # Upload to Phoenix
                            if upload_to_phoenix:
                                with st.spinner("Uploading evaluations to Phoenix..."):
                                    runner.upload_to_phoenix(evaluated_traces, reports)

                            # Save results
                            runner.save_results(reports, output_file)

                            # Show summary
                            summary = runner.get_summary_metrics(reports)
                            st.success(f"Completed {len(reports)} evaluations! Results saved to `{output_file}`.")

                            mcol1, mcol2, mcol3 = st.columns(3)
                            with mcol1:
                                st.metric("Total Evaluated", summary["total_evaluations"])
                            with mcol2:
                                st.metric("Average Score", f"{summary['overall_average']}/5.0")
                            with mcol3:
                                dist = summary.get("score_distribution", {})
                                st.metric("Excellent (≥4.5)", dist.get("excellent (5)", 0))

                            st.markdown("**Scores by Type:**")
                            for eval_type, metrics in summary.get("by_evaluation_type", {}).items():
                                st.markdown(f"- **{eval_type.replace('_', ' ').title()}**: {metrics['average']}/5.0 (n={metrics['count']})")

                            st.info("Refresh the **Results** tab to see full charts and details.")
                        else:
                            st.error("All evaluations failed.")

        except Exception as e:
            st.error(f"Error: {e}")


with tab3:
    st.markdown("### Manual Evaluation Test")
    st.markdown("Test the evaluation system with a custom query/response pair.")

    query = st.text_area(
        "Query",
        value="What is a 401k and how much can I contribute?",
        height=80
    )

    response = st.text_area(
        "Response to Evaluate",
        value="""A 401(k) is a tax-advantaged retirement savings plan offered by employers.

Key points:
- Contributions are made pre-tax, reducing your taxable income
- Investments grow tax-deferred until withdrawal
- 2024 contribution limit is $23,000 ($30,500 if 50+)
- Many employers offer matching contributions

It's one of the best ways to save for retirement due to tax benefits and potential employer matches.""",
        height=200
    )

    intent = st.selectbox(
        "Classified Intent (optional)",
        options=["", "finance_qa", "portfolio", "market_analysis", "goal_planning", "news", "tax_education"]
    )

    documents = st.text_area(
        "Retrieved Documents / Context (one per line)",
        placeholder="Paste retrieved document content here to enable RAG relevance, groundedness, and hallucination evaluations...",
        height=100
    )
    st.caption("Required for: RAG Relevance, Groundedness, Hallucination. Without documents, only Response Quality runs.")

    if st.button("🔍 Evaluate", type="primary"):
        try:
            from app.evaluation.runner import EvaluationRunner

            with st.spinner("Running evaluation..."):
                runner = EvaluationRunner()

                sample = {
                    "query": query,
                    "response": response,
                    "intent": intent if intent else None,
                    "documents": documents.split("\n") if documents.strip() else None
                }

                reports = runner.run_evaluation_on_samples([sample])

                if reports:
                    report = reports[0]

                    st.success(f"Overall Score: {report.overall_score}/5.0")

                    for eval_type, eval_data in report.evaluations.items():
                        score = eval_data.get("score", 0)
                        if score >= 4:
                            color = "🟢"
                        elif score >= 3:
                            color = "🟡"
                        else:
                            color = "🔴"

                        with st.expander(f"{color} {eval_type.replace('_', ' ').title()}: {score}/5.0"):
                            st.markdown(f"**Label:** {eval_data.get('label', 'N/A')}")
                            st.markdown(f"**Explanation:** {eval_data.get('explanation', 'N/A')}")

                            if eval_data.get("metadata", {}).get("dimensions"):
                                st.markdown("**Dimensions:**")
                                for dim, data in eval_data["metadata"]["dimensions"].items():
                                    st.markdown(f"- {dim}: {data.get('score', 'N/A')}/5 - {data.get('note', '')}")

                            if eval_data.get("metadata", {}).get("hallucinations_found"):
                                st.markdown("**Potential Hallucinations:**")
                                for h in eval_data["metadata"]["hallucinations_found"]:
                                    st.markdown(f"- {h}")
                else:
                    st.error("Evaluation failed")

        except Exception as e:
            st.error(f"Error: {e}")


# Footer
st.divider()
st.markdown("### About Evaluations")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Scoring Guide")
    st.markdown("""
    - **5 (Excellent)**: Perfect performance
    - **4 (Good)**: Minor issues only
    - **3 (Acceptable)**: Room for improvement
    - **2 (Poor)**: Significant problems
    - **1 (Fail)**: Unacceptable
    """)

with col2:
    st.markdown("#### Evaluation Types")
    st.markdown("""
    - **RAG Relevance**: Document retrieval quality
    - **Groundedness**: Response based on sources
    - **Routing**: Correct agent selection
    - **Response Quality**: Overall helpfulness
    - **Hallucination**: Fact accuracy check
    """)

with col3:
    st.markdown("#### Best Practices")
    st.markdown("""
    - Run evaluations regularly
    - Review low-scoring responses
    - Use results to improve prompts
    - Track metrics over time
    """)
