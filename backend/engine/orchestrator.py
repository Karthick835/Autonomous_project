"""
ResearchOrchestrator — coordinates the full autonomous scientific discovery pipeline.
- Accepts LLMProvider for real multi-LLM support
- Generates real charts via ChartGeneratorAgent
- Stores results in ChromaDB memory
- Supports single-dataset investigation and dual-dataset comparison
- Emits real-time SSE events for live UI streaming
"""

import os
import time
import math
import pandas as pd
from typing import Dict, Any, List, Callable, Optional

from agents.profiler import DataProfilerAgent
from agents.hypothesizer import HypothesizerAgent
from agents.code_engineer import CodeEngineerAgent
from agents.validator import StatisticalValidatorAgent, sanitize_val
from agents.reporter import ScienceWriterAgent
from agents.chart_generator import ChartGeneratorAgent
from engine.sandbox import PythonSandbox
from memory.chroma_store import get_memory
from llm.provider import LLMProvider


class ResearchOrchestrator:
    """
    Coordinates the autonomous scientific discovery pipeline.
    Emits real-time event logs for live SSE streaming to the UI.
    Guarantees 100% JSON-serializable outputs.
    """

    def __init__(self, working_dir: Optional[str] = None, charts_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self.charts_dir = charts_dir or os.path.join(self.working_dir, "backend", "charts")

        self.profiler = DataProfilerAgent()
        self.hypothesizer = HypothesizerAgent()
        self.code_engineer = CodeEngineerAgent()
        self.validator = StatisticalValidatorAgent()
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
        """Run the full 5-stage scientific discovery pipeline on a single dataset."""

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

        # Memory stats
        mem_stats = self.memory.get_memory_stats()
        emit("PROFILING", "DataProfilerAgent",
             f"Profile complete: {profile['num_rows']} rows × {profile['num_cols']} cols. "
             f"Target: '{active_target}' ({active_task}). "
             f"Memory: {mem_stats.get('total_records', 0)} prior experiments.",
             payload={"profile_summary": profile, "memory_stats": mem_stats})

        # Generate global charts
        df = pd.read_csv(csv_path)
        global_charts = {}

        heatmap_file = self.chart_generator.generate_correlation_heatmap(df, dataset_name)
        if heatmap_file:
            global_charts["correlation_heatmap"] = heatmap_file
            emit("PROFILING", "DataProfilerAgent", f"Generated correlation heatmap chart.")

        target_dist_file = self.chart_generator.generate_target_distribution(
            df, active_target, active_task, dataset_name
        )
        if target_dist_file:
            global_charts["target_distribution"] = target_dist_file
            emit("PROFILING", "DataProfilerAgent", f"Generated target distribution chart.")

        # ── Stage 2: Hypothesis Generation ──────────────────────────────────
        llm_name = llm_provider.config["display_name"] if llm_provider else "Heuristic Engine"
        emit("HYPOTHESIZING", "HypothesizerAgent",
             f"Querying ChromaDB memory and formulating hypotheses using {llm_name}...")

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
             "Generating deterministic Python scripts and executing in isolated AST sandbox...")

        execution_results = []

        for h in hypotheses:
            emit("EXPERIMENTATION", "CodeEngineerAgent",
                 f"Building test script for [{h['id']}]: {h['title']}...")

            script = self.code_engineer.generate_test_code(h, csv_path, task_type=active_task)
            res = self.sandbox.execute_script(script, csv_path=csv_path)

            if not res["success"]:
                emit("EXPERIMENTATION", "CodeEngineerAgent",
                     f"Script error for [{h['id']}]. Attempting self-healing...",
                     payload={"error": res["error"]})
                healed = self.code_engineer.heal_code(script, res["error"])
                res = self.sandbox.execute_script(healed, csv_path=csv_path)

            sanitized_res = sanitize_val(res)

            # Generate chart for this hypothesis
            chart_file = None
            try:
                chart_file = self.chart_generator.generate_chart_for_hypothesis(
                    df, h, sanitized_res
                )
                if chart_file:
                    emit("EXPERIMENTATION", "ChartGeneratorAgent",
                         f"Generated {h['test_type']} chart for [{h['id']}].")
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
                 f"[{h['id']}] complete (p={p_val:.4f}).")

        # ── Stage 4: Statistical Validation ──────────────────────────────────
        emit("VALIDATION", "StatisticalValidatorAgent",
             "Applying Benjamini-Hochberg FDR procedure and validating effect sizes...")

        validation = sanitize_val(self.validator.validate_results(execution_results))

        # Attach chart_file to each validated finding
        chart_map = {
            er["hypothesis"]["id"]: er.get("chart_file")
            for er in execution_results
        }
        for finding in validation.get("findings", []):
            finding["chart_file"] = chart_map.get(finding["hypothesis_id"])

        emit("VALIDATION", "StatisticalValidatorAgent",
             f"Validation complete: {validation['confirmed_discoveries']} confirmed, "
             f"{validation['rejected_count']} rejected.",
             payload={"validation": validation})

        # ── Stage 5: Memory Storage ───────────────────────────────────────────
        emit("REPORTING", "AgentMemory",
             f"Persisting {len(validation.get('findings', []))} results to ChromaDB...")

        for er in execution_results:
            h = er["hypothesis"]
            finding = next(
                (f for f in validation.get("findings", [])
                 if f["hypothesis_id"] == h["id"]),
                None,
            )
            if finding:
                self.memory.store_result(dataset_name, h, finding)

        emit("REPORTING", "AgentMemory", "Memory persistence complete.")

        # ── Stage 5b: Report Generation ──────────────────────────────────────
        emit("REPORTING", "ScienceWriterAgent",
             "Synthesizing executive markdown report and executable Jupyter notebook...")

        markdown_report = self.reporter.generate_markdown_report(
            profile, validation, dataset_name
        )

        nb_name = f"research_notebook_{dataset_name.replace('.csv', '').replace(' ', '_')}.ipynb"
        output_ipynb_path = os.path.join(self.working_dir, nb_name)
        self.reporter.generate_jupyter_notebook(
            csv_path, profile, validation, output_ipynb_path
        )
        emit("REPORTING", "ScienceWriterAgent",
             f"Notebook saved as '{nb_name}'. Investigation complete!")

        return sanitize_val({
            "dataset_name": dataset_name,
            "profile": profile,
            "hypotheses": hypotheses,
            "execution_results": execution_results,
            "validation": validation,
            "markdown_report": markdown_report,
            "notebook_path": output_ipynb_path,
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
        """
        Run the same hypothesis suite on two datasets and produce a comparison report.
        Finds which findings hold across both (cross-validated discoveries) and which are dataset-specific.
        """

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

        emit("PROFILING", "DataProfilerAgent",
             f"Profiling Dataset A: '{name_a}'...")
        results_a = self.run_investigation(
            csv_path_a,
            domain_context=domain_context,
            llm_provider=llm_provider,
            event_callback=lambda e: event_callback({**e, "dataset": "A"}) if event_callback else None,
        )

        emit("PROFILING", "DataProfilerAgent",
             f"Profiling Dataset B: '{name_b}'...")
        results_b = self.run_investigation(
            csv_path_b,
            domain_context=domain_context,
            llm_provider=llm_provider,
            event_callback=lambda e: event_callback({**e, "dataset": "B"}) if event_callback else None,
        )

        # Cross-validate findings
        confirmed_a = {
            f["title"].lower().strip(): f
            for f in results_a["validation"]["findings"]
            if f["status"] == "CONFIRMED_DISCOVERY"
        }
        confirmed_b = {
            f["title"].lower().strip(): f
            for f in results_b["validation"]["findings"]
            if f["status"] == "CONFIRMED_DISCOVERY"
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
                    "verdict": "REPLICATED",
                })
            else:
                a_only.append({**finding, "verdict": "DATASET_A_ONLY"})

        for title, finding in confirmed_b.items():
            if title not in confirmed_a:
                b_only.append({**finding, "verdict": "DATASET_B_ONLY"})

        emit("REPORTING", "ScienceWriterAgent",
             f"Comparison complete. Cross-validated: {len(cross_validated)}, "
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
