import os
import sys

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.orchestrator import ResearchOrchestrator

def test_full_pipeline():
    csv_path = os.path.abspath("data/sample_churn.csv")
    orchestrator = ResearchOrchestrator()

    events = []
    def log_event(event):
        events.append(event)
        print(f"[{event['agent']}] ({event['stage']}): {event['message']}")

    results = orchestrator.run_investigation(csv_path, domain_context="Customer Retention Analysis", event_callback=log_event)

    assert results["dataset_name"] == "sample_churn.csv"
    assert len(results["hypotheses"]) > 0
    assert results["validation"]["total_tested"] > 0
    assert len(results["markdown_report"]) > 100
    assert os.path.exists(results["notebook_path"])

    print(f"\n[OK] Full Multi-Agent Pipeline Test Passed!")
    print(f"Total Events Logged: {len(events)}")
    print(f"Confirmed Discoveries: {results['validation']['confirmed_discoveries']}")
    print(f"Jupyter Notebook Generated at: {results['notebook_path']}")

if __name__ == "__main__":
    test_full_pipeline()
