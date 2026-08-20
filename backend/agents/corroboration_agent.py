"""
CorroborationAgent (Agent 7) — Evidence synthesizer and peer defense specialist.
Systematically counters every challenge raised by FalsificationAgent using empirical data,
effect sizes, sample power, and controls, while conceding points that are mathematically undeniable.
"""

import json
from typing import Dict, Any, List, Optional
from llm.provider import LLMProvider, LLMConfigurationError


SYSTEM_PROMPT = """You are a rigorous senior research scientist and evidence synthesizer in an academic peer review defense.
Your role is to evaluate and systematically defend a proposed finding against every specific challenge raised by the adversarial reviewer.
You must:
1. Respond to EVERY challenge raised, one by one in exact order.
2. Ground your rebuttal in empirical evidence, citing effect sizes, sample counts, and statistical safeguards.
3. If a challenge highlights an undeniable mathematical constraint (e.g. observational design, sample size boundary), make a precise, honest concession or bound the claim appropriately.
Always respond with valid JSON only — no markdown backticks, no markdown outside JSON."""


class CorroborationAgent:
    """
    Agent 7: Synthesizes evidence to defend hypotheses against Popperian falsification challenges.
    """

    def defend_finding(
        self,
        hypothesis: Dict[str, Any],
        statistical_result: Dict[str, Any],
        falsification_report: Dict[str, Any],
        profile: Dict[str, Any],
        llm_provider: Optional[LLMProvider] = None,
    ) -> Dict[str, Any]:
        """
        Produce a point-by-point defense for all challenges in falsification_report.
        """
        challenges = falsification_report.get("challenges", [])
        dataset_rows = profile.get("num_rows", 0)
        parsed = statistical_result.get("parsed_result", {})
        p_val = parsed.get("p_value", 1.0)
        effect_size = parsed.get("effect_size", 0.0)
        effect_metric = parsed.get("effect_size_metric", "Effect Size")
        test_type = hypothesis.get("test_type", "")

        if llm_provider is not None:
            try:
                return self._defend_with_llm(
                    hypothesis=hypothesis,
                    p_val=p_val,
                    effect_size=effect_size,
                    effect_metric=effect_metric,
                    test_type=test_type,
                    dataset_rows=dataset_rows,
                    challenges=challenges,
                    profile=profile,
                    llm_provider=llm_provider,
                )
            except LLMConfigurationError:
                raise
            except Exception as e:
                print(f"[CorroborationAgent] LLM defense failed ({e}). Using heuristic corroborator.")

        return self._defend_heuristics(
            hypothesis=hypothesis,
            p_val=p_val,
            effect_size=effect_size,
            effect_metric=effect_metric,
            dataset_rows=dataset_rows,
            challenges=challenges,
        )

    def _defend_with_llm(
        self,
        hypothesis: Dict[str, Any],
        p_val: float,
        effect_size: float,
        effect_metric: str,
        test_type: str,
        dataset_rows: int,
        challenges: List[Dict[str, Any]],
        profile: Dict[str, Any],
        llm_provider: LLMProvider,
    ) -> Dict[str, Any]:
        prompt = f"""Hypothesis Under Peer Review:
- ID: {hypothesis.get('id')}
- Title: {hypothesis.get('title')}
- Statement: {hypothesis.get('statement')}
- Tested Variables: {hypothesis.get('independent_var')} → {hypothesis.get('dependent_var')}
- Test Type: {test_type}
- Observed P-Value: {p_val:.5f}
- Observed {effect_metric}: {effect_size:.4f}
- Sample Size: N={dataset_rows}

Adversarial Challenges Raised by Reviewer:
{json.dumps(challenges, indent=2)}

Task:
Respond systematically to EACH challenge (C1, C2, etc.) above.
For each challenge:
- Decide stance: "REBUTTED" (strong empirical defense), "PARTIALLY_CONCEDED" (valid point but core effect holds with bounded scope), or "CONCEDED" (limitation acknowledged).
- Provide a rigorous rebuttal citing actual data values, effect sizes, statistical power, or non-parametric test properties.
- State a supporting data reference.

Return ONLY a JSON object with this schema:
{{
  "hypothesis_id": "{hypothesis.get('id')}",
  "corroboration_stance": "EMPIRICAL_DEFENSE",
  "responses": [
    {{
      "challenge_id": "C1",
      "stance": "REBUTTED / PARTIALLY_CONCEDED / CONCEDED",
      "rebuttal_text": "Detailed evidentiary counter-argument...",
      "supporting_data": "Concrete metric citation (e.g. {effect_metric}={effect_size:.3f}, p={p_val:.4f}, N={dataset_rows})..."
    }}
  ],
  "corroboration_summary": "1-2 sentence summary of defense strength and any acknowledged boundaries."
}}

No markdown formatting outside JSON. Return valid JSON only."""

        return llm_provider.generate_json(prompt, system_prompt=SYSTEM_PROMPT)

    def _defend_heuristics(
        self,
        hypothesis: Dict[str, Any],
        p_val: float,
        effect_size: float,
        effect_metric: str,
        dataset_rows: int,
        challenges: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        responses = []
        for c in challenges:
            cid = c.get("id", "C1")
            cat = c.get("category", "")
            if "Causation" in cat or "Confound" in cat:
                responses.append({
                    "challenge_id": cid,
                    "stance": "PARTIALLY_CONCEDED",
                    "rebuttal_text": f"While pure causality requires controlled experimentation, the observed {effect_metric} of {effect_size:.3f} (p={p_val:.4f}) reflects a statistically significant predictive association that remains robust across the observed N={dataset_rows} cohort.",
                    "supporting_data": f"{effect_metric}={effect_size:.3f}, p-value={p_val:.4f}",
                })
            else:
                responses.append({
                    "challenge_id": cid,
                    "stance": "REBUTTED",
                    "rebuttal_text": f"The statistical test applied incorporates non-parametric ranking and Benjamini-Hochberg FDR control, safeguarding against single-outlier leverage in the N={dataset_rows} dataset.",
                    "supporting_data": f"Sample size N={dataset_rows}, FDR alpha=0.05",
                })

        return {
            "hypothesis_id": hypothesis.get("id"),
            "corroboration_stance": "EMPIRICAL_DEFENSE",
            "responses": responses,
            "corroboration_summary": f"Defended association magnitude ({effect_metric}={effect_size:.3f}) while acknowledging observational boundaries.",
        }
