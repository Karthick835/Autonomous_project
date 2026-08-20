"""
Test suite for Level 3 Active Data Acquisition System.
Tests DataGapAnalysisAgent, DataMergeEngine, validation, and full Orchestration.
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.profiler import DataProfilerAgent
from agents.data_gap_analysis_agent import DataGapAnalysisAgent
from engine.merger import DataMergeEngine
from engine.orchestrator import ResearchOrchestrator


def test_data_gap_analysis():
    print("\n--- [TEST 1] Unit Test: DataGapAnalysisAgent ---", flush=True)
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_churn.csv"))
    profiler = DataProfilerAgent()
    profile = profiler.profile_csv(data_path)

    sample_hypotheses = [
        {
            "id": "H001",
            "title": "MonthlyCharges vs Churn Distribution Shift",
            "statement": "Higher values of 'monthly_charges' significantly differentiate churn outcome.",
            "independent_var": "monthly_charges",
            "dependent_var": "churn",
        },
        {
            "id": "H002",
            "title": "Tenure Longitudinal Trend on Churn",
            "statement": "Longer customer tenure trends decrease churn risk over time.",
            "independent_var": "tenure",
            "dependent_var": "churn",
        }
    ]

    agent = DataGapAnalysisAgent()
    gap_rep = agent.analyze_gaps(profile, sample_hypotheses, domain_context="Customer churn risk modeling")

    print(f"[Gap Analysis] Total gaps identified: {len(gap_rep.get('gaps', []))}", flush=True)
    print(f"   Critical: {gap_rep.get('critical_count', 0)} | Important: {gap_rep.get('important_count', 0)} | Optional: {gap_rep.get('optional_count', 0)}", flush=True)
    print(f"   Pipeline Action: {gap_rep.get('pipeline_action')}", flush=True)
    print(f"   Assessment: {gap_rep.get('overall_assessment')[:90]}...", flush=True)

    assert "gaps" in gap_rep
    assert gap_rep.get("pipeline_action") in ["PAUSE", "WARN", "CONTINUE"]
    print("SUCCESS: DataGapAnalysisAgent test passed!\n", flush=True)


def test_data_merge_engine():
    print("\n--- [TEST 2] Unit Test: DataMergeEngine ---", flush=True)
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_path = os.path.join(workspace, "data", "sample_churn.csv")

    # Create a small synthetic supplemental dataset with matching customerID
    df_orig = pd.read_csv(data_path)
    # Check if there is an id column or create one
    first_col = df_orig.columns[0]
    supp_data = pd.DataFrame({
        first_col: df_orig[first_col].iloc[:30],
        "competitor_discount_offered": [True, False] * 15,
        "customer_satisfaction_score": [7.5 + (i % 3) * 0.8 for i in range(30)],
    })

    supp_path = os.path.join(workspace, "uploads", "test_supplemental.csv")
    os.makedirs(os.path.dirname(supp_path), exist_ok=True)
    supp_data.to_csv(supp_path, index=False)

    merger = DataMergeEngine(working_dir=workspace)
    merge_result = merger.merge(data_path, supp_path)

    print(f"[MergeEngine] Strategy: {merge_result.get('strategy')}", flush=True)
    print(f"   Keys used: {merge_result.get('merge_keys')}", flush=True)
    print(f"   Original shape: {merge_result.get('original_shape')} -> Enriched shape: {merge_result.get('enriched_shape')}", flush=True)
    print(f"   New columns: {merge_result.get('new_columns')}", flush=True)
    print(f"   Message: {merge_result.get('message')}", flush=True)

    assert merge_result.get("success") is True
    assert len(merge_result.get("new_columns", [])) > 0
    assert os.path.exists(merge_result.get("enriched_csv_path"))
    print("SUCCESS: DataMergeEngine test passed!\n", flush=True)


def test_full_level3_pipeline():
    print("\n--- [TEST 3] End-to-End 9-Agent Level 3 Pipeline ---", flush=True)
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_path = os.path.join(workspace, "data", "sample_churn.csv")

    events = []
    def event_cb(e):
        events.append(e)
        if e.get("stage") in ["DATA_GAP_ANALYSIS", "DATA_REQUEST", "ADVERSARIAL_REVIEW"]:
            safe_msg = e['message'][:75].encode('ascii', 'replace').decode('ascii')
            print(f"   [SSE Event] [{e['stage']}] {e['agent']} -> {safe_msg}...", flush=True)

    orchestrator = ResearchOrchestrator(working_dir=workspace)
    results = orchestrator.run_investigation(
        csv_path=data_path,
        domain_context="Customer churn analysis",
        event_callback=event_cb,
    )

    print(f"\nResults Summary (Level 3):", flush=True)
    print(f"   Total Tested: {len(results['hypotheses'])}", flush=True)
    print(f"   Tier 1 (Validated): {len(results.get('tier1_findings', []))}", flush=True)
    print(f"   Tier 2 (Conditional): {len(results.get('tier2_findings', []))}", flush=True)
    print(f"   Tier 3 (Invalidated): {len(results.get('tier3_findings', []))}", flush=True)
    print(f"   Gap Report Gaps: {len(results.get('gap_report', {}).get('gaps', []))}", flush=True)
    print(f"   Notebook saved at: {results['notebook_path']}", flush=True)
    print(f"   Transcript saved at: {results['transcript_path']}", flush=True)

    assert os.path.exists(results['notebook_path'])
    assert os.path.exists(results['transcript_path'])
    assert "gap_report" in results
    print("SUCCESS: Full Level 3 Pipeline test passed!\n", flush=True)


if __name__ == "__main__":
    test_data_gap_analysis()
    test_data_merge_engine()
    test_full_level3_pipeline()
