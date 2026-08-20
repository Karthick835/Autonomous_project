"""
ResearchOrchestrator — Coordinates the full 8-agent Autonomous AI Scientist pipeline:
1. DataProfilerAgent (EDA & Leakage audit)
2. HypothesizerAgent (Hypothesis formulation + ChromaDB deduplication)
3. CodeEngineerAgent + PythonSandbox (Deterministic AST-verified code execution)
4. StatisticalValidatorAgent (Benjamini-Hochberg FDR correction & effect sizes)
5. FalsificationAgent (Agent 6: Karl Popper empirical challenges with data citations)
6. CorroborationAgent (Agent 7: Evidence synthesis & point-by-point rebuttal)
7. ArbitrationAgent (Agent 8: Impartial editor verdict: VALIDATED / CONDITIONAL / INVALIDATED)
8. ScienceWriterAgent (3-Tier executive report & reproducible Jupyter notebook)

Real-time SSE event streaming and disk persistence for adversarial review transcripts.
"""

import os
import json
import time
import math
import pandas as pd
from typing import Dict, Any, List, Callable, Optional

from agents.profiler import DataProfilerAgent
from agents.hypothesizer import HypothesizerAgent
from agents.code_engineer import CodeEngineerAgent
from agents.validator import StatisticalValidatorAgent, sanitize_val
from agents.falsification_agent import FalsificationAgent
from agents.corroboration_agent import CorroborationAgent
from agents.arbitration_agent import ArbitrationAgent
from agents.reporter import ScienceWriterAgent
from agents.chart_generator import ChartGeneratorAgent
from engine.sandbox import PythonSandbox
from memory.chroma_store import get_memory
from llm.provider import LLMProvider


class ResearchOrchestrator:
    """
    Coordinates the Level 2 Adversarial Validation System.
    Streams real-time event logs for live UI updates via SSE.
    """

    def __init__(self, working_dir: Optional[str] = None, charts_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self.charts_dir = charts_dir or os.path.join(self.working_dir, "backend", "charts")

        self.profiler = DataProfilerAgent()
        self.hypothesizer = HypothesizerAgent()
        self.code_engineer = CodeEngineerAgent()
        self.validator = StatisticalValidatorAgent()
        self.falsifier = FalsificationAgent()
        self.corroborator = CorroborationAgent()
        self.arbiter = ArbitrationAgent()
        self.reporter = ScienceWriterAgent()
        self.chart_generator = ChartGeneratorAgent(charts_dir=self.charts_dir)
        self.sandbox = PythonSandbox(working_dir=self.working_dir)
        self.memory = get_memory()

    def run_investigation(
        self,
        csv_path: str,
        domain_context: str = "",
        target_override: Optional[str] = None,
        task_type_override: Optional[str] = None,
        llm_provider: Optional[LLMProvider] = None,
        event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Run the full 8-agent adversarial scientific discovery pipeline on a single dataset."""

        dataset_name = os.path.basename(csv_path)

        def emit(stage: str, agent: str, message: str, payload: Optional[Any] = None):
            sanitized_payload = sanitize_val(payload) if payload else None
            event = {
                "timestamp": round(time.time(), 3),
                "stage": stage,
                "agent": agent,
                "message": message,
                "payload": sanitized_payload,
            }
            if event_callback:
                event_callback(event)
            return event

        # ── Stage 1: Data Profiling ──────────────────────────────────────────
        emit("PROFILING", "DataProfilerAgent",
             f"Initiating automated EDA and leakage audit on '{dataset_name}'...")

        profile = sanitize_val(self.profiler.profile_csv(
            csv_path,
            target_override=target_override,
            task_type_override=task_type_override,
        ))
        active_target = profile.get("active_target", "Target")
        active_task = profile.get("active_task", "classification")

        mem_stats = self.memory.get_memory_stats()
        emit("PROFILING", "DataProfilerAgent",
             f"Profile complete: {profile['num_rows']} rows × {profile['num_cols']} cols. "
             f"Target: '{active_target}' ({active_task}). "
             f"Vector memory: {mem_stats.get('total_records', 0)} prior records.",
             payload={"profile_summary": profile, "memory_stats": mem_stats})

        # Generate global exploratory charts
        df = pd.read_csv(csv_path)
        global_charts = {}

        heatmap_file = self.chart_generator.generate_correlation_heatmap(df, dataset_name)
        if heatmap_file:
            global_charts["correlation_heatmap"] = heatmap_file
            emit("PROFILING", "DataProfilerAgent", "Generated feature correlation heatmap chart.")

        target_dist_file = self.chart_generator.generate_target_distribution(
            df, active_target, active_task, dataset_name
        )
        if target_dist_file:
            global_charts["target_distribution"] = target_dist_file
            emit("PROFILING", "DataProfilerAgent", "Generated target distribution chart.")

        # ── Stage 2: Hypothesis Generation ──────────────────────────────────
        llm_name = llm_provider.config["display_name"] if llm_provider else "Heuristic Engine"
        emit("HYPOTHESIZING", "HypothesizerAgent",
             f"Querying ChromaDB memory and formulating testable hypotheses using {llm_name}...")

        hypotheses = sanitize_val(self.hypothesizer.generate_hypotheses(
            profile,
            domain_context=domain_context,
            llm_provider=llm_provider,
            dataset_name=dataset_name,
        ))
        emit("HYPOTHESIZING", "HypothesizerAgent",
             f"Generated {len(hypotheses)} novel hypotheses (memory-filtered).",
             payload={"hypotheses": hypotheses})

        # ── Stage 3: Sandbox Execution + Chart Generation ────────────────────
        emit("EXPERIMENTATION", "CodeEngineerAgent",
             "Generating Python test scripts and executing in isolated AST sandbox...")

        execution_results = []

        for h in hypotheses:
            emit("EXPERIMENTATION", "CodeEngineerAgent",
                 f"Building test script for [{h['id']}]: {h['title']}...")

            script = self.code_engineer.generate_test_code(h, csv_path, task_type=active_task)
            res = self.sandbox.execute_script(script, csv_path=csv_path)

            if not res["success"]:
                emit("EXPERIMENTATION", "CodeEngineerAgent",
                     f"Script error for [{h['id']}]. Self-healing...",
                     payload={"error": res["error"]})
                healed = self.code_engineer.heal_code(script, res["error"])
                res = self.sandbox.execute_script(healed, csv_path=csv_path)

            sanitized_res = sanitize_val(res)

            chart_file = None
            try:
                chart_file = self.chart_generator.generate_chart_for_hypothesis(
                    df, h, sanitized_res
                )
                if chart_file:
                    emit("EXPERIMENTATION", "ChartGeneratorAgent",
                         f"Rendered statistical chart for [{h['id']}].")
            except Exception as chart_err:
                print(f"[ChartGenerator] Failed for {h['id']}: {chart_err}")

            p_val = (
                sanitized_res["parsed_result"].get("p_value", 1.0)
                if sanitized_res["success"] and sanitized_res["parsed_result"]
                else 1.0
            )

            execution_results.append({
                "hypothesis": h,
                "generated_code": script,
                "execution_result": sanitized_res,
                "chart_file": chart_file,
            })

            emit("EXPERIMENTATION", "PythonSandbox",
                 f"[{h['id']}] execution complete (p={p_val:.4f}).")

        # ── Stage 4: Statistical Validation ──────────────────────────────────
        emit("VALIDATION", "StatisticalValidatorAgent",
             "Applying Benjamini-Hochberg FDR correction and verifying effect sizes...")

        validation = sanitize_val(self.validator.validate_results(execution_results))

        chart_map = {
            er["hypothesis"]["id"]: er.get("chart_file")
            for er in execution_results
        }
        for finding in validation.get("findings", []):
            finding["chart_file"] = chart_map.get(finding["hypothesis_id"])

        emit("VALIDATION", "StatisticalValidatorAgent",
             f"FDR validation: {validation['confirmed_discoveries']} passed alpha={validation['fdr_alpha_used']}, "
             f"{validation['rejected_count']} rejected.",
             payload={"validation": validation})

        # ── Stage 5: Adversarial Peer Review (Level 2) ────────────────────────
        emit("ADVERSARIAL_REVIEW", "FalsificationAgent",
             "Initiating Level 2 Adversarial Validation System (Popperian Falsification → Corroboration → Arbitration)...")

        adversarial_reviews = []
        tier1_findings = []
        tier2_findings = []
        tier3_findings = []

        for finding in validation.get("findings", []):
            h_id = finding["hypothesis_id"]
            h_obj = next((er["hypothesis"] for er in execution_results if er["hypothesis"]["id"] == h_id), None)
            stat_res = next((er["execution_result"] for er in execution_results if er["hypothesis"]["id"] == h_id), None)

            if not h_obj or not stat_res:
                continue

            # 5a: Falsification Agent (Popperian Challenger)
            emit("ADVERSARIAL_FALSIFY", "FalsificationAgent",
                 f"🔴 [FalsificationAgent] Stress-testing [{h_id}]: Generating empirical challenges citing dataset values...")

            falsification_report = sanitize_val(self.falsifier.challenge_finding(
                hypothesis=h_obj,
                statistical_result=stat_res,
                profile=profile,
                llm_provider=llm_provider,
            ))

            challenges_count = len(falsification_report.get("challenges", []))
            emit("ADVERSARIAL_FALSIFY", "FalsificationAgent",
                 f"🔴 [FalsificationAgent] Raised {challenges_count} empirical challenges against [{h_id}].",
                 payload={
                     "hypothesis_id": h_id,
                     "hypothesis_title": h_obj.get("title"),
                     "falsification": falsification_report,
                 })

            # 5b: Corroboration Agent (Evidence Rebuttal)
            emit("ADVERSARIAL_CORROBORATE", "CorroborationAgent",
                 f"🟢 [CorroborationAgent] Defending [{h_id}]: Evaluating effect sizes and constructing point-by-point rebuttal...")

            corroboration_report = sanitize_val(self.corroborator.defend_finding(
                hypothesis=h_obj,
                statistical_result=stat_res,
                falsification_report=falsification_report,
                profile=profile,
                llm_provider=llm_provider,
            ))

            emit("ADVERSARIAL_CORROBORATE", "CorroborationAgent",
                 f"🟢 [CorroborationAgent] Completed rebuttal for [{h_id}] ({len(corroboration_report.get('responses', []))} responses).",
                 payload={
                     "hypothesis_id": h_id,
                     "corroboration": corroboration_report,
                 })

            # 5c: Arbitration Agent (Impartial Senior Editor)
            emit("ADVERSARIAL_ARBITRATE", "ArbitrationAgent",
                 f"🟡 [ArbitrationAgent] Reviewing adversarial record for [{h_id}] with deterministic editor arbitration...")

            arbitration_report = sanitize_val(self.arbiter.arbitrate(
                hypothesis=h_obj,
                statistical_result=stat_res,
                falsification_report=falsification_report,
                corroboration_report=corroboration_report,
                profile=profile,
                llm_provider=llm_provider,
            ))

            verdict = arbitration_report.get("verdict", "VALIDATED_WITH_CONDITIONS")
            confidence = arbitration_report.get("confidence_score", 85)

            finding["verdict"] = verdict
            finding["confidence_score"] = confidence
            finding["arbitration_conditions"] = arbitration_report.get("conditions", [])
            finding["editorial_reasoning"] = arbitration_report.get("editorial_reasoning", "")

            review_record = {
                "hypothesis_id": h_id,
                "hypothesis_title": h_obj.get("title"),
                "hypothesis": h_obj,
                "statistical_finding": finding,
                "falsification": falsification_report,
                "corroboration": corroboration_report,
                "arbitration": arbitration_report,
            }
            adversarial_reviews.append(review_record)

            if verdict == "VALIDATED":
                tier1_findings.append(finding)
                verdict_emoji = "✅ VALIDATED (Tier 1)"
            elif verdict == "VALIDATED_WITH_CONDITIONS":
                tier2_findings.append(finding)
                verdict_emoji = "⚠️ VALIDATED WITH CONDITIONS (Tier 2)"
            else:
                tier3_findings.append(finding)
                verdict_emoji = "❌ INVALIDATED (Tier 3)"

            emit("ADVERSARIAL_ARBITRATE", "ArbitrationAgent",
                 f"🟡 [ArbitrationAgent] [{h_id}] Verdict: {verdict_emoji} (Confidence: {confidence}%).",
                 payload={
                     "hypothesis_id": h_id,
                     "verdict": verdict,
                     "confidence_score": confidence,
                     "arbitration": arbitration_report,
                     "full_review_record": review_record,
                 })

        # ── Stage 6: Persistent Vector Memory Storage ────────────────────────
        emit("REPORTING", "AgentMemory",
             f"Persisting {len(adversarial_reviews)} peer-reviewed findings to ChromaDB vector store...")

        for er in execution_results:
            h = er["hypothesis"]
            finding = next((f for f in validation.get("findings", []) if f["hypothesis_id"] == h["id"]), None)
            if finding:
                self.memory.store_result(dataset_name, h, finding)

        # ── Stage 7: Reporting & Disk Artifact Persistence ────────────────────
        emit("REPORTING", "ScienceWriterAgent",
             "Synthesizing 3-Tier Executive Report, reproducible Jupyter Notebook, and Adversarial Transcript...")

        markdown_report = self.reporter.generate_markdown_report(
            profile=profile,
            validation=validation,
            adversarial_reviews=adversarial_reviews,
            dataset_name=dataset_name,
        )

        clean_name = dataset_name.replace(".csv", "").replace(" ", "_")
        nb_name = f"research_notebook_{clean_name}.ipynb"
        output_ipynb_path = os.path.join(self.working_dir, nb_name)
        self.reporter.generate_jupyter_notebook(
            csv_path=csv_path,
            profile=profile,
            validation=validation,
            output_ipynb_path=output_ipynb_path,
            adversarial_reviews=adversarial_reviews,
        )

        # Save complete adversarial peer review transcript to disk
        transcript_path = os.path.join(self.working_dir, f"adversarial_transcript_{clean_name}.json")
        try:
            with open(transcript_path, "w", encoding="utf-8") as tf:
                json.dump(adversarial_reviews, tf, indent=2)
            emit("REPORTING", "ScienceWriterAgent",
                 f"Saved adversarial transcript to '{os.path.basename(transcript_path)}'.")
        except Exception as e:
            print(f"[Orchestrator] Could not save transcript: {e}")

        emit("REPORTING", "ScienceWriterAgent",
             f"Investigation complete! Tier 1: {len(tier1_findings)} | Tier 2: {len(tier2_findings)} | Tier 3: {len(tier3_findings)}.")

        return sanitize_val({
            "dataset_name": dataset_name,
            "profile": profile,
            "hypotheses": hypotheses,
            "execution_results": execution_results,
            "validation": validation,
            "adversarial_reviews": adversarial_reviews,
            "tier1_findings": tier1_findings,
            "tier2_findings": tier2_findings,
            "tier3_findings": tier3_findings,
            "markdown_report": markdown_report,
            "notebook_path": output_ipynb_path,
            "transcript_path": transcript_path,
            "global_charts": global_charts,
        })

    def run_comparison(
        self,
        csv_path_a: str,
        csv_path_b: str,
        domain_context: str = "",
        llm_provider: Optional[LLMProvider] = None,
        event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Dual-dataset peer-reviewed comparison pipeline."""

        def emit(stage: str, agent: str, message: str, payload: Optional[Any] = None):
            event = {
                "timestamp": round(time.time(), 3),
                "stage": stage,
                "agent": agent,
                "message": message,
                "payload": sanitize_val(payload) if payload else None,
            }
            if event_callback:
                event_callback(event)
            return event

        name_a = os.path.basename(csv_path_a)
        name_b = os.path.basename(csv_path_b)

        emit("PROFILING", "DataProfilerAgent", f"Adversarial analysis on Dataset A: '{name_a}'...")
        results_a = self.run_investigation(
            csv_path_a,
            domain_context=domain_context,
            llm_provider=llm_provider,
            event_callback=lambda e: event_callback({**e, "dataset": "A"}) if event_callback else None,
        )

        emit("PROFILING", "DataProfilerAgent", f"Adversarial analysis on Dataset B: '{name_b}'...")
        results_b = self.run_investigation(
            csv_path_b,
            domain_context=domain_context,
            llm_provider=llm_provider,
            event_callback=lambda e: event_callback({**e, "dataset": "B"}) if event_callback else None,
        )

        # Cross-validation across Tier 1 + Tier 2 findings
        confirmed_a = {
            f["title"].lower().strip(): f
            for f in (results_a.get("tier1_findings", []) + results_a.get("tier2_findings", []))
        }
        confirmed_b = {
            f["title"].lower().strip(): f
            for f in (results_b.get("tier1_findings", []) + results_b.get("tier2_findings", []))
        }

        cross_validated = []
        a_only = []
        b_only = []

        for title, finding in confirmed_a.items():
            if title in confirmed_b:
                cross_validated.append({
                    "title": finding["title"],
                    "dataset_a": finding,
                    "dataset_b": confirmed_b[title],
                    "verdict": "REPLICATED_ACROSS_DATASETS",
                })
            else:
                a_only.append({**finding, "verdict": "DATASET_A_ONLY"})

        for title, finding in confirmed_b.items():
            if title not in confirmed_a:
                b_only.append({**finding, "verdict": "DATASET_B_ONLY"})

        emit("REPORTING", "ScienceWriterAgent",
             f"Comparison complete. Replicated: {len(cross_validated)}, A-only: {len(a_only)}, B-only: {len(b_only)}.")

        return sanitize_val({
            "dataset_a": name_a,
            "dataset_b": name_b,
            "results_a": results_a,
            "results_b": results_b,
            "comparison": {
                "cross_validated": cross_validated,
                "dataset_a_only": a_only,
                "dataset_b_only": b_only,
                "total_replicated": len(cross_validated),
            },
        })
