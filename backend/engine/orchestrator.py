import os
import time
import math
from typing import Dict, Any, List, Callable, Optional

from agents.profiler import DataProfilerAgent
from agents.hypothesizer import HypothesizerAgent
from agents.code_engineer import CodeEngineerAgent
from agents.validator import StatisticalValidatorAgent, sanitize_val
from agents.reporter import ScienceWriterAgent
from engine.sandbox import PythonSandbox

class ResearchOrchestrator:
    """
    Coordinates the autonomous scientific discovery pipeline.
    Emits real-time event logs for live streaming to the UI.
    Guarantees 100% JSON-serializable outputs.
    """

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self.profiler = DataProfilerAgent()
        self.hypothesizer = HypothesizerAgent()
        self.code_engineer = CodeEngineerAgent()
        self.validator = StatisticalValidatorAgent()
        self.reporter = ScienceWriterAgent()
        self.sandbox = PythonSandbox(working_dir=self.working_dir)

    def run_investigation(
        self,
        csv_path: str,
        domain_context: str = "",
        target_override: Optional[str] = None,
        task_type_override: Optional[str] = None,
        event_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        dataset_name = os.path.basename(csv_path)

        def emit(stage: str, agent: str, message: str, payload: Optional[Any] = None):
            sanitized_payload = sanitize_val(payload) if payload else None
            event = {
                "timestamp": round(time.time(), 3),
                "stage": stage,
                "agent": agent,
                "message": message,
                "payload": sanitized_payload
            }
            if event_callback:
                event_callback(event)
            return event

        # 1. Data Profiling Stage
        emit("PROFILING", "DataProfilerAgent", f"Initiating automated EDA and leakage audit on '{dataset_name}'...")
        profile = sanitize_val(self.profiler.profile_csv(csv_path, target_override=target_override, task_type_override=task_type_override))
        active_target = profile.get('active_target', 'Target')
        active_task = profile.get('active_task', 'classification')
        emit("PROFILING", "DataProfilerAgent", f"Profile complete: {profile['num_rows']} rows, {profile['num_cols']} columns. Active target: '{active_target}' ({active_task}).", payload={"profile_summary": profile})


        # 2. Hypothesis Generation Stage
        emit("HYPOTHESIZING", "HypothesizerAgent", "Formulating testable scientific hypotheses based on statistical profile...")
        hypotheses = sanitize_val(self.hypothesizer.generate_hypotheses(profile, domain_context=domain_context))
        emit("HYPOTHESIZING", "HypothesizerAgent", f"Generated {len(hypotheses)} testable hypotheses with target effect sizes.", payload={"hypotheses": hypotheses})

        # 3. Execution Stage
        emit("EXPERIMENTATION", "CodeEngineerAgent", "Generating deterministic Python analysis scripts and executing in isolated AST sandbox...")
        execution_results = []

        for h in hypotheses:
            emit("EXPERIMENTATION", "CodeEngineerAgent", f"Building test script for Hypothesis [{h['id']}]: {h['title']}...")
            script = self.code_engineer.generate_test_code(h, csv_path, task_type=active_task)

            res = self.sandbox.execute_script(script, csv_path=csv_path)


            if not res["success"]:
                emit("EXPERIMENTATION", "CodeEngineerAgent", f"Script execution error for [{h['id']}]. Attempting self-healing patch...", payload={"error": res["error"]})
                healed_script = self.code_engineer.heal_code(script, res["error"])
                res = self.sandbox.execute_script(healed_script, csv_path=csv_path)

            sanitized_res = sanitize_val(res)
            execution_results.append({
                "hypothesis": h,
                "generated_code": script,
                "execution_result": sanitized_res
            })

            p_val = sanitized_res['parsed_result'].get('p_value', 1.0) if (sanitized_res['success'] and sanitized_res['parsed_result']) else 1.0
            emit("EXPERIMENTATION", "PythonSandbox", f"Hypothesis [{h['id']}] execution completed (p={p_val:.4f}).")

        # 4. Statistical Validation Stage
        emit("VALIDATION", "StatisticalValidatorAgent", "Applying Benjamini-Hochberg FDR procedure and validating effect sizes...")
        validation = sanitize_val(self.validator.validate_results(execution_results))
        emit("VALIDATION", "StatisticalValidatorAgent", f"Validation complete: {validation['confirmed_discoveries']} Confirmed Discoveries, {validation['rejected_count']} Rejected.", payload={"validation": validation})

        # 5. Report Generation Stage
        emit("REPORTING", "ScienceWriterAgent", "Synthesizing executive markdown report and executable Jupyter notebook...")
        markdown_report = self.reporter.generate_markdown_report(profile, validation, dataset_name)
        
        output_ipynb_path = os.path.join(self.working_dir, f"research_notebook_{dataset_name.split('.')[0]}.ipynb")
        self.reporter.generate_jupyter_notebook(csv_path, profile, validation, output_ipynb_path)
        emit("REPORTING", "ScienceWriterAgent", f"Jupyter notebook saved to '{os.path.basename(output_ipynb_path)}'. Investigation Complete!")

        return sanitize_val({
            "dataset_name": dataset_name,
            "profile": profile,
            "hypotheses": hypotheses,
            "execution_results": execution_results,
            "validation": validation,
            "markdown_report": markdown_report,
            "notebook_path": output_ipynb_path
        })
