"""
ResearchOrchestrator — Coordinates the full 9-agent Autonomous AI Scientist pipeline:
1.  DataProfilerAgent        (EDA & Leakage audit)
2.  DataGapAnalysisAgent     (Level 3: Active data acquisition — gap detection + pipeline pause)
3.  HypothesizerAgent        (Hypothesis formulation + ChromaDB deduplication)
4.  CodeEngineerAgent        + PythonSandbox (Deterministic AST-verified code execution)
5.  StatisticalValidatorAgent (Benjamini-Hochberg FDR correction & effect sizes)
6.  FalsificationAgent       (Agent 6: Karl Popper empirical challenges with data citations)
7.  CorroborationAgent       (Agent 7: Evidence synthesis & point-by-point rebuttal)
8.  ArbitrationAgent         (Agent 8: Impartial editor verdict: VALIDATED / CONDITIONAL / INVALIDATED)
9.  ScienceWriterAgent       (3-Tier executive report & reproducible Jupyter notebook)

Level 3: Pipeline pauses on CRITICAL data gaps. Resumes after user provides supplemental CSV.
Real-time SSE streaming and disk persistence for adversarial review transcripts.
"""

import os
import json
import time
import threading
import pandas as pd
from typing import Dict, Any, List, Callable, Optional

from agents.profiler import DataProfilerAgent
from agents.data_gap_analysis_agent import DataGapAnalysisAgent
from agents.hypothesizer import HypothesizerAgent
from agents.code_engineer import CodeEngineerAgent
from agents.validator import StatisticalValidatorAgent, sanitize_val
from agents.falsification_agent import FalsificationAgent
from agents.corroboration_agent import CorroborationAgent
from agents.arbitration_agent import ArbitrationAgent
from agents.reporter import ScienceWriterAgent
from agents.chart_generator import ChartGeneratorAgent
from engine.sandbox import PythonSandbox
from engine.merger import DataMergeEngine
from memory.chroma_store import get_memory
from llm.provider import LLMProvider


# Maximum time to wait for user to provide supplemental data (30 minutes)
DATA_REQUEST_TIMEOUT_SECONDS = 1800


class ResearchOrchestrator:
    """
    Coordinates the Level 3 Active Data Acquisition + Level 2 Adversarial Validation pipeline.
    Streams real-time event logs for live UI updates via SSE.
    Supports pipeline pause/resume on critical data gaps.
    """

    def __init__(self, working_dir: Optional[str] = None, charts_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self.charts_dir = charts_dir or os.path.join(self.working_dir, "backend", "charts")

        self.profiler = DataProfilerAgent()
        self.gap_analyzer = DataGapAnalysisAgent()
        self.hypothesizer = HypothesizerAgent()
        self.code_engineer = CodeEngineerAgent()
        self.validator = StatisticalValidatorAgent()
        self.falsifier = FalsificationAgent()
        self.corroborator = CorroborationAgent()
        self.arbiter = ArbitrationAgent()
        self.reporter = ScienceWriterAgent()
        self.chart_generator = ChartGeneratorAgent(charts_dir=self.charts_dir)
        self.sandbox = PythonSandbox(working_dir=self.working_dir)
        self.merger = DataMergeEngine(working_dir=self.working_dir)
        self.memory = get_memory()

    def run_investigation(
        self,
        csv_path: str,
        domain_context: str = "",
        target_override: Optional[str] = None,
        task_type_override: Optional[str] = None,
        llm_provider: Optional[LLMProvider] = None,
        event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        # Level 3 pause/resume control
        pause_event: Optional[threading.Event] = None,
        session_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run the full 9-agent Level 3 scientific discovery pipeline.

        pause_event: threading.Event set by /provide-data or /skip-gap endpoints to resume pipeline.
        session_state: shared dict (from sessions[sid]) used to inject enriched_csv_path and skip flags.
        """

        dataset_name = os.path.basename(csv_path)
        enrichment_info = None   # filled if dataset is enriched
        skipped_gaps = []        # gaps user chose to skip
        limitation_flags = []    # warnings added to findings due to skipped gaps

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
             f"Profile complete: {profile['num_rows']} rows x {profile['num_cols']} cols. "
             f"Target: '{active_target}' ({active_task}). "
             f"Vector memory: {mem_stats.get('total_records', 0)} prior records.",
             payload={"profile_summary": profile, "memory_stats": mem_stats})

        # Generate preliminary hypotheses (needed by gap analyzer for context)
        llm_name = llm_provider.config["display_name"] if llm_provider else "Heuristic Engine"
        emit("HYPOTHESIZING", "HypothesizerAgent",
             f"Generating preliminary hypotheses for gap analysis context using {llm_name}...")

        preliminary_hypotheses = sanitize_val(self.hypothesizer.generate_hypotheses(
            profile,
            domain_context=domain_context,
            llm_provider=llm_provider,
            dataset_name=dataset_name,
        ))

        # ── Stage 2: Data Gap Analysis (Level 3) ─────────────────────────────
        emit("DATA_GAP_ANALYSIS", "DataGapAnalysisAgent",
             "Running data sufficiency review — scanning for missing variables, "
             "incomplete time coverage, and absent comparison groups...")

        gap_report = sanitize_val(self.gap_analyzer.analyze_gaps(
            profile=profile,
            hypotheses=preliminary_hypotheses,
            domain_context=domain_context,
            llm_provider=llm_provider,
        ))

        critical_gaps = [g for g in gap_report.get("gaps", []) if g.get("priority") == "CRITICAL"]
        important_gaps = [g for g in gap_report.get("gaps", []) if g.get("priority") == "IMPORTANT"]
        optional_gaps = [g for g in gap_report.get("gaps", []) if g.get("priority") == "OPTIONAL"]

        emit("DATA_GAP_ANALYSIS", "DataGapAnalysisAgent",
             f"Data sufficiency analysis complete: {len(critical_gaps)} critical, "
             f"{len(important_gaps)} important, {len(optional_gaps)} optional gaps identified. "
             f"Pipeline action: {gap_report.get('pipeline_action', 'CONTINUE')}.",
             payload={"gap_report": gap_report})

        # ── Handle Critical Gaps — PAUSE PIPELINE ────────────────────────────
        if critical_gaps and pause_event is not None and session_state is not None:
            for gap in critical_gaps:
                emit("DATA_REQUEST", "DataGapAnalysisAgent",
                     f"[CRITICAL GAP] Pipeline paused — '{gap['title']}'. "
                     f"Investigation cannot proceed without this data.",
                     payload={
                         "gap": gap,
                         "gap_type": "CRITICAL",
                         "paused": True,
                         "action_required": "Upload supplemental CSV via the Data Request panel",
                     })

                # Store which gap is blocking in shared session state
                session_state["paused_for_gap"] = gap
                session_state["status"] = "paused"

                # Wait for user to provide data or skip
                got_data = pause_event.wait(timeout=DATA_REQUEST_TIMEOUT_SECONDS)
                pause_event.clear()

                if not got_data:
                    emit("DATA_REQUEST", "DataGapAnalysisAgent",
                         f"Timeout waiting for data. Continuing without critical gap data — "
                         f"findings will carry invalidation warnings.")
                    limitation_flags.append(f"CRITICAL gap '{gap['title']}' not resolved — findings may be invalid.")
                    continue

                # Check if user provided enriched CSV
                enriched_path = session_state.get("enriched_csv")
                skipped = session_state.get("last_action") == "skip"

                if skipped:
                    emit("DATA_REQUEST", "DataGapAnalysisAgent",
                         f"User skipped critical gap '{gap['title']}'. "
                         f"All downstream findings will be flagged as potentially invalid.")
                    skipped_gaps.append(gap)
                    limitation_flags.append(
                        f"CRITICAL gap skipped: '{gap['title']}' — {gap.get('why_it_matters', '')}"
                    )
                elif enriched_path and os.path.exists(enriched_path):
                    merge_result = self._apply_enrichment(
                        csv_path, enriched_path, emit, gap
                    )
                    if merge_result["success"]:
                        csv_path = merge_result["enriched_csv_path"]
                        dataset_name = os.path.basename(csv_path)
                        enrichment_info = merge_result

                        # Re-profile enriched dataset
                        emit("PROFILING", "DataProfilerAgent",
                             f"Re-profiling enriched dataset ({merge_result['enriched_shape'][1]} columns)...")
                        profile = sanitize_val(self.profiler.profile_csv(
                            csv_path,
                            target_override=active_target,
                            task_type_override=active_task,
                        ))
                        emit("PROFILING", "DataProfilerAgent",
                             f"Enriched profile complete: {profile['num_rows']} rows x {profile['num_cols']} cols.",
                             payload={"profile_summary": profile, "enrichment_info": enrichment_info})

        # ── Handle Important Gaps — WARN but continue ─────────────────────────
        if important_gaps and pause_event is not None and session_state is not None:
            for gap in important_gaps:
                emit("DATA_REQUEST", "DataGapAnalysisAgent",
                     f"[IMPORTANT GAP] '{gap['title']}' — providing supplemental data will strengthen findings. "
                     f"Investigation continues with limitations.",
                     payload={
                         "gap": gap,
                         "gap_type": "IMPORTANT",
                         "paused": False,
                         "action_required": "Optionally upload supplemental CSV via the Data Request panel",
                     })

                # Short wait (10 seconds) to see if user uploads immediately
                session_state["paused_for_gap"] = gap
                got_data = pause_event.wait(timeout=10)
                pause_event.clear()

                if got_data:
                    enriched_path = session_state.get("enriched_csv")
                    skipped = session_state.get("last_action") == "skip"
                    if not skipped and enriched_path and os.path.exists(enriched_path):
                        merge_result = self._apply_enrichment(csv_path, enriched_path, emit, gap)
                        if merge_result["success"]:
                            csv_path = merge_result["enriched_csv_path"]
                            dataset_name = os.path.basename(csv_path)
                            enrichment_info = merge_result
                            profile = sanitize_val(self.profiler.profile_csv(
                                csv_path,
                                target_override=active_target,
                                task_type_override=active_task,
                            ))
                            emit("PROFILING", "DataProfilerAgent",
                                 f"Enriched dataset active: {profile['num_cols']} cols.",
                                 payload={"profile_summary": profile, "enrichment_info": enrichment_info})
                    else:
                        skipped_gaps.append(gap)
                        limitation_flags.append(
                            f"Important gap skipped: '{gap['title']}' — {gap.get('why_it_matters', '')}"
                        )
                else:
                    # User didn't respond in time — continue with warning
                    skipped_gaps.append(gap)
                    limitation_flags.append(
                        f"Important gap unresolved: '{gap['title']}' — {gap.get('why_it_matters', '')}"
                    )

                session_state["paused_for_gap"] = None

        if optional_gaps:
            emit("DATA_GAP_ANALYSIS", "DataGapAnalysisAgent",
                 f"{len(optional_gaps)} optional data enhancement opportunity(ies) noted in the final report.")

        # ── Stage 3: Final Hypothesis Generation on (enriched) profile ───────
        emit("HYPOTHESIZING", "HypothesizerAgent",
             f"Formulating final testable hypotheses using {llm_name}...")

        # Re-generate on enriched profile if data changed
        if enrichment_info:
            hypotheses = sanitize_val(self.hypothesizer.generate_hypotheses(
                profile,
                domain_context=domain_context,
                llm_provider=llm_provider,
                dataset_name=dataset_name,
            ))
        else:
            hypotheses = preliminary_hypotheses

        emit("HYPOTHESIZING", "HypothesizerAgent",
             f"Generated {len(hypotheses)} novel hypotheses (memory-filtered).",
             payload={"hypotheses": hypotheses})

        # Generate global exploratory charts
        df = pd.read_csv(csv_path)
        global_charts = {}

        heatmap_file = self.chart_generator.generate_correlation_heatmap(df, dataset_name)
        if heatmap_file:
            global_charts["correlation_heatmap"] = heatmap_file
            emit("PROFILING", "DataProfilerAgent", "Generated feature correlation heatmap.")

        target_dist_file = self.chart_generator.generate_target_distribution(
            df, active_target, active_task, dataset_name
        )
        if target_dist_file:
            global_charts["target_distribution"] = target_dist_file
            emit("PROFILING", "DataProfilerAgent", "Generated target distribution chart.")

        # ── Stage 4: Sandbox Execution + Chart Generation ─────────────────────
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
                chart_file = self.chart_generator.generate_chart_for_hypothesis(df, h, sanitized_res)
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
                "from_enriched_data": enrichment_info is not None,
            })

            emit("EXPERIMENTATION", "PythonSandbox",
                 f"[{h['id']}] execution complete (p={p_val:.4f}).")

        # ── Stage 5: Statistical Validation ───────────────────────────────────
        emit("VALIDATION", "StatisticalValidatorAgent",
             "Applying Benjamini-Hochberg FDR correction and verifying effect sizes...")

        validation = sanitize_val(self.validator.validate_results(execution_results))

        chart_map = {
            er["hypothesis"]["id"]: er.get("chart_file")
            for er in execution_results
        }
        for finding in validation.get("findings", []):
            finding["chart_file"] = chart_map.get(finding["hypothesis_id"])
            finding["from_enriched_data"] = enrichment_info is not None
            # Attach limitation flags to every finding if gaps were skipped
            if limitation_flags:
                finding["limitation_flags"] = limitation_flags

        emit("VALIDATION", "StatisticalValidatorAgent",
             f"FDR validation: {validation['confirmed_discoveries']} passed alpha={validation['fdr_alpha_used']}, "
             f"{validation['rejected_count']} rejected.",
             payload={"validation": validation})

        # ── Stage 6: Adversarial Peer Review (Level 2) ────────────────────────
        emit("ADVERSARIAL_REVIEW", "FalsificationAgent",
             "Initiating Level 2 Adversarial Validation System "
             "(Popperian Falsification -> Corroboration -> Arbitration)...")

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

            emit("ADVERSARIAL_FALSIFY", "FalsificationAgent",
                 f"[FalsificationAgent] Stress-testing [{h_id}]: "
                 f"Generating empirical challenges citing dataset values...")

            falsification_report = sanitize_val(self.falsifier.challenge_finding(
                hypothesis=h_obj,
                statistical_result=stat_res,
                profile=profile,
                llm_provider=llm_provider,
            ))

            challenges_count = len(falsification_report.get("challenges", []))
            emit("ADVERSARIAL_FALSIFY", "FalsificationAgent",
                 f"[FalsificationAgent] Raised {challenges_count} empirical challenges against [{h_id}].",
                 payload={
                     "hypothesis_id": h_id,
                     "hypothesis_title": h_obj.get("title"),
                     "falsification": falsification_report,
                 })

            emit("ADVERSARIAL_CORROBORATE", "CorroborationAgent",
                 f"[CorroborationAgent] Defending [{h_id}]: "
                 f"Evaluating effect sizes and constructing point-by-point rebuttal...")

            corroboration_report = sanitize_val(self.corroborator.defend_finding(
                hypothesis=h_obj,
                statistical_result=stat_res,
                falsification_report=falsification_report,
                profile=profile,
                llm_provider=llm_provider,
            ))

            emit("ADVERSARIAL_CORROBORATE", "CorroborationAgent",
                 f"[CorroborationAgent] Completed rebuttal for [{h_id}] "
                 f"({len(corroboration_report.get('responses', []))} responses).",
                 payload={
                     "hypothesis_id": h_id,
                     "corroboration": corroboration_report,
                 })

            emit("ADVERSARIAL_ARBITRATE", "ArbitrationAgent",
                 f"[ArbitrationAgent] Reviewing adversarial record for [{h_id}] "
                 f"with deterministic editor arbitration...")

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
                verdict_str = "VALIDATED (Tier 1)"
            elif verdict == "VALIDATED_WITH_CONDITIONS":
                tier2_findings.append(finding)
                verdict_str = "VALIDATED WITH CONDITIONS (Tier 2)"
            else:
                tier3_findings.append(finding)
                verdict_str = "INVALIDATED (Tier 3)"

            emit("ADVERSARIAL_ARBITRATE", "ArbitrationAgent",
                 f"[ArbitrationAgent] [{h_id}] Verdict: {verdict_str} (Confidence: {confidence}%).",
                 payload={
                     "hypothesis_id": h_id,
                     "verdict": verdict,
                     "confidence_score": confidence,
                     "arbitration": arbitration_report,
                     "full_review_record": review_record,
                 })

        # ── Stage 7: Persistent Vector Memory Storage ──────────────────────
        emit("REPORTING", "AgentMemory",
             f"Persisting {len(adversarial_reviews)} peer-reviewed findings to ChromaDB vector store...")

        for er in execution_results:
            h = er["hypothesis"]
            finding = next((f for f in validation.get("findings", []) if f["hypothesis_id"] == h["id"]), None)
            if finding:
                self.memory.store_result(dataset_name, h, finding)

        # ── Stage 8: Reporting & Disk Artifact Persistence ─────────────────
        emit("REPORTING", "ScienceWriterAgent",
             "Synthesizing 3-Tier Executive Report, reproducible Jupyter Notebook, "
             "and Adversarial Transcript...")

        markdown_report = self.reporter.generate_markdown_report(
            profile=profile,
            validation=validation,
            adversarial_reviews=adversarial_reviews,
            dataset_name=dataset_name,
            enrichment_info=enrichment_info,
            skipped_gaps=skipped_gaps,
            optional_gaps=optional_gaps,
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

        transcript_path = os.path.join(self.working_dir, f"adversarial_transcript_{clean_name}.json")
        try:
            with open(transcript_path, "w", encoding="utf-8") as tf:
                json.dump(adversarial_reviews, tf, indent=2)
            emit("REPORTING", "ScienceWriterAgent",
                 f"Saved adversarial transcript to '{os.path.basename(transcript_path)}'.")
        except Exception as e:
            print(f"[Orchestrator] Could not save transcript: {e}")

        emit("REPORTING", "ScienceWriterAgent",
             f"Investigation complete! "
             f"Tier 1: {len(tier1_findings)} | "
             f"Tier 2: {len(tier2_findings)} | "
             f"Tier 3: {len(tier3_findings)}.")

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
            "gap_report": gap_report,
            "enrichment_info": enrichment_info,
            "skipped_gaps": skipped_gaps,
            "optional_gaps": optional_gaps,
            "limitation_flags": limitation_flags,
        })

    def _apply_enrichment(
        self,
        original_csv: str,
        supplemental_csv: str,
        emit: Callable,
        gap: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run DataMergeEngine and emit progress events."""
        emit("DATA_GAP_ANALYSIS", "DataMergeEngine",
             f"Merging supplemental data for gap '{gap['title']}'...")

        merge_result = self.merger.merge(
            original_csv_path=original_csv,
            supplemental_csv_path=supplemental_csv,
            gap_info=gap,
        )

        if merge_result["success"]:
            emit("DATA_GAP_ANALYSIS", "DataMergeEngine",
                 f"Enrichment successful: {merge_result['message']}",
                 payload={"enrichment_info": merge_result})
        else:
            emit("DATA_GAP_ANALYSIS", "DataMergeEngine",
                 f"Enrichment failed: {merge_result['message']}")

        return merge_result

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
             f"Comparison complete. Replicated: {len(cross_validated)}, "
             f"A-only: {len(a_only)}, B-only: {len(b_only)}.")

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
