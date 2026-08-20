"""
Test suite for Level 2 Adversarial Validation System.
Tests FalsificationAgent, CorroborationAgent, ArbitrationAgent, and end-to-end Orchestration.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.profiler import DataProfilerAgent
from agents.falsification_agent import FalsificationAgent
from agents.corroboration_agent import CorroborationAgent
from agents.arbitration_agent import ArbitrationAgent
from engine.orchestrator import ResearchOrchestrator


def test_adversarial_unit():
    print("\n--- [TEST 1] Unit Test: Falsification -> Corroboration -> Arbitration ---", flush=True)
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_churn.csv"))
    profiler = DataProfilerAgent()
    profile = profiler.profile_csv(data_path)

    sample_hypothesis = {
        "id": "H001",
        "title": "MonthlyCharges vs Churn Distribution Shift",
        "statement": "Higher values of 'monthly_charges' significantly differentiate churn outcome.",
        "category": "Group Comparison",
        "independent_var": "monthly_charges",
        "dependent_var": "churn",
        "test_type": "mann_whitney_u",
        "min_effect_size": 0.30,
    }

    sample_stat_result = {
        "success": True,
        "parsed_result": {
            "p_value": 0.00042,
            "effect_size": 0.54,
            "effect_size_metric": "Rank-Biserial Correlation",
            "status": "CONFIRMED_DISCOVERY",
        }
    }

    # Agent 6: Falsification
    falsifier = FalsificationAgent()
    fals_rep = falsifier.challenge_finding(sample_hypothesis, sample_stat_result, profile)
    print(f"[Falsification] Challenges generated: {len(fals_rep.get('challenges', []))}", flush=True)
    assert len(fals_rep.get("challenges", [])) >= 2, "Must produce >= 2 challenges"
    for c in fals_rep["challenges"]:
        print(f"   Challenge [{c['id']}] ({c['category']}): {c['challenge_text'][:80]}...", flush=True)
        assert "data_reference" in c

    # Agent 7: Corroboration
    corroborator = CorroborationAgent()
    corr_rep = corroborator.defend_finding(sample_hypothesis, sample_stat_result, fals_rep, profile)
    print(f"[Corroboration] Defenses generated: {len(corr_rep.get('responses', []))}", flush=True)
    assert len(corr_rep.get("responses", [])) == len(fals_rep.get("challenges", []))
    for r in corr_rep["responses"]:
        print(f"   Defense to [{r['challenge_id']}] ({r['stance']}): {r['rebuttal_text'][:80]}...", flush=True)

    # Agent 8: Arbitration
    arbiter = ArbitrationAgent()
    arb_rep = arbiter.arbitrate(sample_hypothesis, sample_stat_result, fals_rep, corr_rep, profile)
    print(f"[Arbitration] Verdict: {arb_rep.get('verdict')} (Confidence: {arb_rep.get('confidence_score')}%)", flush=True)
    print(f"   Editorial: {arb_rep.get('editorial_reasoning')}", flush=True)
    assert arb_rep.get("verdict") in ["VALIDATED", "VALIDATED_WITH_CONDITIONS", "INVALIDATED"]
    assert 0 <= arb_rep.get("confidence_score", -1) <= 100
    print("SUCCESS: Unit test passed!\n", flush=True)


def test_adversarial_orchestrator():
    print("\n--- [TEST 2] End-to-End Orchestrator Pipeline Test ---", flush=True)
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_churn.csv"))
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    events = []
    def event_cb(e):
        events.append(e)
        if e.get("stage", "").startswith("ADVERSARIAL_"):
            safe_msg = e['message'][:75].encode('ascii', 'replace').decode('ascii')
            print(f"   [SSE Event] [{e['stage']}] {e['agent']} -> {safe_msg}...", flush=True)

    orchestrator = ResearchOrchestrator(working_dir=workspace)
    results = orchestrator.run_investigation(
        csv_path=data_path,
        domain_context="Customer churn analysis",
        event_callback=event_cb,
    )

    print(f"\nResults Summary:", flush=True)
    print(f"   Total Tested: {len(results['hypotheses'])}", flush=True)
    print(f"   Tier 1 (Validated): {len(results.get('tier1_findings', []))}", flush=True)
    print(f"   Tier 2 (Conditional): {len(results.get('tier2_findings', []))}", flush=True)
    print(f"   Tier 3 (Invalidated): {len(results.get('tier3_findings', []))}", flush=True)
    print(f"   Notebook saved at: {results['notebook_path']}", flush=True)
    print(f"   Transcript saved at: {results['transcript_path']}", flush=True)

    assert os.path.exists(results['notebook_path'])
    assert os.path.exists(results['transcript_path'])
    print("SUCCESS: End-to-end Adversarial Pipeline test passed!\n", flush=True)


if __name__ == "__main__":
    test_adversarial_unit()
    test_adversarial_orchestrator()
