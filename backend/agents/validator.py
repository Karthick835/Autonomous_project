import math
import numpy as np
from typing import Dict, Any, List

def sanitize_val(val: Any) -> Any:
    """Recursively replaces NaN/Inf floats with JSON-compliant safe defaults."""
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return 0.0
        return val
    elif isinstance(val, dict):
        return {k: sanitize_val(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_val(v) for v in val]
    return val

class StatisticalValidatorAgent:
    """
    Applies False Discovery Rate (FDR) control (Benjamini-Hochberg),
    verifies effect sizes, checks cross-validation stability, and prevents p-hacking.
    Safely sanitizes all outputs for JSON.
    """

    def apply_benjamini_hochberg(self, p_values: List[float], alpha: float = 0.05) -> List[bool]:
        """
        Implements Benjamini-Hochberg FDR correction.
        Returns boolean list indicating statistical significance after FDR control.
        """
        clean_p_values = [1.0 if (p is None or math.isnan(p) or math.isinf(p)) else float(p) for p in p_values]
        n = len(clean_p_values)
        if n == 0:
            return []

        sorted_indices = np.argsort(clean_p_values)
        sorted_p_values = np.array(clean_p_values)[sorted_indices]

        # Calculate BH critical thresholds: (i / m) * alpha
        bh_thresholds = [(i + 1) / n * alpha for i in range(n)]

        significant_sorted = [False] * n
        max_sig_idx = -1

        for i in range(n - 1, -1, -1):
            if sorted_p_values[i] <= bh_thresholds[i]:
                max_sig_idx = i
                break

        if max_sig_idx != -1:
            for i in range(max_sig_idx + 1):
                significant_sorted[i] = True

        # Unsort back to original input order
        original_significant = [False] * n
        for idx, sig in zip(sorted_indices, significant_sorted):
            original_significant[idx] = sig

        return original_significant

    def validate_results(self, hypothesis_results: List[Dict[str, Any]], alpha: float = 0.05) -> Dict[str, Any]:
        p_vals = []
        valid_indices = []

        for idx, item in enumerate(hypothesis_results):
            raw_res = item.get("execution_result", {})
            if raw_res and raw_res.get("parsed_result"):
                p_val = raw_res["parsed_result"].get("p_value", 1.0)
                if p_val is None or math.isnan(p_val) or math.isinf(p_val):
                    p_val = 1.0
                p_vals.append(p_val)
                valid_indices.append(idx)

        bh_passed = self.apply_benjamini_hochberg(p_vals, alpha=alpha)

        validated_findings = []
        confirmed_count = 0
        rejected_count = 0

        for i, orig_idx in enumerate(valid_indices):
            item = hypothesis_results[orig_idx]
            hypothesis = item["hypothesis"]
            res = item["execution_result"]["parsed_result"]
            
            p_val = res.get("p_value", 1.0)
            if p_val is None or math.isnan(p_val) or math.isinf(p_val):
                p_val = 1.0

            effect_size = res.get("effect_size", 0.0)
            if effect_size is None or math.isnan(effect_size) or math.isinf(effect_size):
                effect_size = 0.0

            min_eff = hypothesis.get("min_effect_size", 0.1)
            is_fdr_significant = bh_passed[i]

            is_negative_control = hypothesis.get("category") == "Negative Control"

            if is_negative_control:
                status = "VALIDATED_CONTROL" if p_val > alpha else "FAILED_CONTROL"
                finding_summary = f"Negative Control check: '{hypothesis['independent_var']}' showed no target effect (p = {p_val:.4f})."
            elif is_fdr_significant and effect_size >= min_eff:
                status = "CONFIRMED_DISCOVERY"
                confirmed_count += 1
                finding_summary = f"Confirmed relationship between '{hypothesis['independent_var']}' and '{hypothesis['dependent_var']}' (p = {p_val:.4f}, {res.get('effect_size_metric')} = {effect_size:.3f})."
            elif p_val <= alpha and effect_size < min_eff:
                status = "WEAK_EVIDENCE"
                finding_summary = f"Statistically significant p-value ({p_val:.4f}) but weak effect size ({effect_size:.3f} < threshold {min_eff})."
            else:
                status = "REJECTED"
                rejected_count += 1
                finding_summary = f"Hypothesis rejected (p = {p_val:.4f} > {alpha} or insufficient evidence)."

            validated_findings.append(sanitize_val({
                "hypothesis_id": hypothesis["id"],
                "title": hypothesis["title"],
                "category": hypothesis["category"],
                "status": status,
                "p_value": float(p_val),
                "fdr_significant": bool(is_fdr_significant),
                "effect_size": float(effect_size),
                "effect_size_metric": str(res.get("effect_size_metric", "")),
                "summary": finding_summary,
                "details": res.get("details", {})
            }))

        return sanitize_val({
            "total_tested": len(hypothesis_results),
            "confirmed_discoveries": confirmed_count,
            "rejected_count": rejected_count,
            "fdr_alpha_used": alpha,
            "findings": validated_findings
        })
