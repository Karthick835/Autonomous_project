"""
FalsificationAgent (Agent 6) — Karl Popper-inspired adversarial challenger.
Attempts to disprove or uncover critical vulnerabilities in every confirmed hypothesis.
Enforces empirical data citations (column names, sample sizes, distribution shifts, confounding).
"""

import json
from typing import Dict, Any, List, Optional
from llm.provider import LLMProvider, LLMConfigurationError


SYSTEM_PROMPT = """You are a ruthless senior adversarial peer reviewer and statistician operating strictly under Karl Popper's falsifiability principle.
Your sole mission is to find vulnerabilities, confounds, sample biases, and alternative explanations in proposed scientific findings.
You must adopt a purely critical stance — you NEVER validate, praise, or accept a finding as sound.
You must always cite real dataset values, column names, sample sizes, and statistics provided in the prompt.
Always respond with valid JSON only — no markdown backticks, no markdown formatting outside JSON strings."""


class FalsificationAgent:
    """
    Agent 6: Challenges findings using real statistical reasoning,
    confounder detection, outlier sensitivity, and causation vs correlation checks.
    """

    def challenge_finding(
        self,
        hypothesis: Dict[str, Any],
        statistical_result: Dict[str, Any],
        profile: Dict[str, Any],
        llm_provider: Optional[LLMProvider] = None,
    ) -> Dict[str, Any]:
        """
        Generate at least 2 rigorous, evidence-based challenges against the hypothesis.
        """
        dataset_rows = profile.get("num_rows", 0)
        num_cols = profile.get("numerical_columns", [])
        cat_cols = profile.get("categorical_columns", [])
        all_cols = list(profile.get("column_profiles", {}).keys())

        # Collect potential confounders (other columns excluding tested variables)
        tested_vars = [hypothesis.get("independent_var", ""), hypothesis.get("dependent_var", "")]
        potential_confounders = [c for c in all_cols if c not in tested_vars and c != "id"][:8]

        parsed = statistical_result.get("parsed_result", {})
        p_val = parsed.get("p_value", 1.0)
        effect_size = parsed.get("effect_size", 0.0)
        effect_metric = parsed.get("effect_size_metric", "Effect Size")
        test_type = hypothesis.get("test_type", "")

        if llm_provider is not None:
            try:
                return self._challenge_with_llm(
                    hypothesis=hypothesis,
                    p_val=p_val,
                    effect_size=effect_size,
                    effect_metric=effect_metric,
                    test_type=test_type,
                    dataset_rows=dataset_rows,
                    num_cols=num_cols,
                    cat_cols=cat_cols,
                    potential_confounders=potential_confounders,
                    profile=profile,
                    llm_provider=llm_provider,
                )
            except LLMConfigurationError:
                raise
            except Exception as e:
                print(f"[FalsificationAgent] LLM challenge failed ({e}). Using heuristic falsifier.")

        return self._challenge_heuristics(
            hypothesis=hypothesis,
            p_val=p_val,
            effect_size=effect_size,
            effect_metric=effect_metric,
            dataset_rows=dataset_rows,
            potential_confounders=potential_confounders,
        )

    def _challenge_with_llm(
        self,
        hypothesis: Dict[str, Any],
        p_val: float,
        effect_size: float,
        effect_metric: str,
        test_type: str,
        dataset_rows: int,
        num_cols: List[str],
        cat_cols: List[str],
        potential_confounders: List[str],
        profile: Dict[str, Any],
        llm_provider: LLMProvider,
    ) -> Dict[str, Any]:
        prompt = f"""Target Hypothesis:
- ID: {hypothesis.get('id')}
- Title: {hypothesis.get('title')}
- Statement: {hypothesis.get('statement')}
- Independent Variable: {hypothesis.get('independent_var')}
- Dependent Variable: {hypothesis.get('dependent_var')}
- Test Type: {test_type}

Empirical Statistical Results:
- Observed P-Value: {p_val:.5f}
- Observed {effect_metric}: {effect_size:.4f}
- Total Sample Observations (N): {dataset_rows}

Dataset Context:
- Available Columns: {list(profile.get('column_profiles', {}).keys())}
- Potential Uncontrolled Confounders: {potential_confounders}
- High Correlations in Dataset: {profile.get('high_correlations', [])[:3]}

Task:
Produce minimum 2 specific, evidence-backed scientific challenges trying to disprove or weaken this finding.
Angles to evaluate:
1. Causation vs Correlation (observational study risks).
2. Uncontrolled Confounding (e.g. how a third variable like {potential_confounders[:2] if potential_confounders else 'another feature'} could explain this effect).
3. Sample Size / Generalizability / Subgroup Sensitivity (e.g. with N={dataset_rows}, is this robust across segments?).
4. Outlier / Distribution Sensitivity.

Return ONLY a JSON object with this exact schema:
{{
  "hypothesis_id": "{hypothesis.get('id')}",
  "falsification_stance": "CRITICAL_CHALLENGE",
  "challenges": [
    {{
      "id": "C1",
      "category": "Confounding / Causation / Outlier / Sample Size",
      "challenge_text": "Precise critique citing statistical mechanism...",
      "data_reference": "Specific column names, sample size (N={dataset_rows}), or metric values cited..."
    }},
    {{
      "id": "C2",
      "category": "Confounding / Causation / Outlier / Sample Size",
      "challenge_text": "Second distinct critique...",
      "data_reference": "Specific data reference..."
    }}
  ],
  "falsification_summary": "1-2 sentence executive summary of key vulnerabilities."
}}

No markdown code fences. No explanation outside JSON."""

        return llm_provider.generate_json(prompt, system_prompt=SYSTEM_PROMPT)

    def _challenge_heuristics(
        self,
        hypothesis: Dict[str, Any],
        p_val: float,
        effect_size: float,
        effect_metric: str,
        dataset_rows: int,
        potential_confounders: List[str],
    ) -> Dict[str, Any]:
        confounder = potential_confounders[0] if potential_confounders else "unmeasured demographic factors"
        challenges = [
            {
                "id": "C1",
                "category": "Correlation vs Causation",
                "challenge_text": f"The statistical relationship between '{hypothesis.get('independent_var')}' and '{hypothesis.get('dependent_var')}' is strictly observational. An uncontrolled latent covariate such as '{confounder}' could mediate this variance.",
                "data_reference": f"Variables: {hypothesis.get('independent_var')} → {hypothesis.get('dependent_var')} (N={dataset_rows})",
            },
            {
                "id": "C2",
                "category": "Effect Size & Distributional Sensitivity",
                "challenge_text": f"While p={p_val:.4f} satisfies significance thresholds, the observed {effect_metric} of {effect_size:.3f} may be susceptible to heavy-tailed outliers or non-linear subgroups across the {dataset_rows} samples.",
                "data_reference": f"{effect_metric}={effect_size:.3f}, sample size N={dataset_rows}",
            },
        ]
        return {
            "hypothesis_id": hypothesis.get("id"),
            "falsification_stance": "CRITICAL_CHALLENGE",
            "challenges": challenges,
            "falsification_summary": f"Challenged based on observational confounding risks and outlier sensitivity in N={dataset_rows} sample.",
        }
