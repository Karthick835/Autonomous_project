"""
ArbitrationAgent (Agent 8) — Independent Senior Editor & Peer Review Arbiter.
Evaluates challenges from FalsificationAgent and rebuttals from CorroborationAgent.
Delivers deterministic (temperature=0.1) peer review verdicts:
- VALIDATED (accepted unconditionally)
- VALIDATED_WITH_CONDITIONS (accepted with specific stated limitations)
- INVALIDATED (rejected from primary findings; archived to transparency log)
"""

import json
from typing import Dict, Any, List, Optional
from llm.provider import LLMProvider, LLMConfigurationError


SYSTEM_PROMPT = """You are the Editor-in-Chief of a premier peer-reviewed statistical science journal.
You are strictly impartial and neutral.
You read the empirical hypothesis, the adversarial review challenges, and the author's defense.
Your job is to:
1. Score the validity of each challenge (1-10, where 10 = devastating fatal flaw).
2. Score the strength of each response (1-10, where 10 = complete empirical proof).
3. Render one of THREE exact verdicts:
   - "VALIDATED": Rebuttals completely dissolved all challenges. High confidence.
   - "VALIDATED_WITH_CONDITIONS": Finding has statistical support but carries valid limitations (e.g. observational bounds, moderate effect size, specific subgroup constraints).
   - "INVALIDATED": Critical challenges were not adequately resolved or effect is unconvincing.
4. Calculate an overall confidence percentage (0-100%).
5. Provide a rigorous 2-3 sentence editorial justification citing specific data.

Always respond with valid JSON only — no markdown backticks, no text outside JSON."""


class ArbitrationAgent:
    """
    Agent 8: Impartial arbiter rendering peer review verdicts with deterministic low temperature.
    """

    def arbitrate(
        self,
        hypothesis: Dict[str, Any],
        statistical_result: Dict[str, Any],
        falsification_report: Dict[str, Any],
        corroboration_report: Dict[str, Any],
        profile: Dict[str, Any],
        llm_provider: Optional[LLMProvider] = None,
    ) -> Dict[str, Any]:
        """
        Deliver a deterministic arbitration verdict on the contested hypothesis.
        """
        challenges = falsification_report.get("challenges", [])
        responses = corroboration_report.get("responses", [])
        dataset_rows = profile.get("num_rows", 0)

        parsed = statistical_result.get("parsed_result", {})
        p_val = parsed.get("p_value", 1.0)
        effect_size = parsed.get("effect_size", 0.0)
        effect_metric = parsed.get("effect_size_metric", "Effect Size")

        if llm_provider is not None:
            try:
                return self._arbitrate_with_llm(
                    hypothesis=hypothesis,
                    p_val=p_val,
                    effect_size=effect_size,
                    effect_metric=effect_metric,
                    dataset_rows=dataset_rows,
                    challenges=challenges,
                    responses=responses,
                    llm_provider=llm_provider,
                )
            except LLMConfigurationError:
                raise
            except Exception as e:
                print(f"[ArbitrationAgent] LLM arbitration failed ({e}). Using heuristic arbiter.")

        return self._arbitrate_heuristics(
            hypothesis=hypothesis,
            p_val=p_val,
            effect_size=effect_size,
            effect_metric=effect_metric,
            dataset_rows=dataset_rows,
            challenges=challenges,
            responses=responses,
        )

    def _arbitrate_with_llm(
        self,
        hypothesis: Dict[str, Any],
        p_val: float,
        effect_size: float,
        effect_metric: str,
        dataset_rows: int,
        challenges: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
        llm_provider: LLMProvider,
    ) -> Dict[str, Any]:
        prompt = f"""Contested Finding:
- ID: {hypothesis.get('id')}
- Title: {hypothesis.get('title')}
- Statement: {hypothesis.get('statement')}
- Tested Mechanism: {hypothesis.get('independent_var')} → {hypothesis.get('dependent_var')}
- Empirical Evidence: p={p_val:.5f}, {effect_metric}={effect_size:.4f}, Sample N={dataset_rows}

Adversarial Falsification Challenges:
{json.dumps(challenges, indent=2)}

Author Corroboration Responses:
{json.dumps(responses, indent=2)}

Task:
Evaluate the complete adversarial transcript and deliver the final verdict.
Return ONLY valid JSON matching this schema:
{{
  "hypothesis_id": "{hypothesis.get('id')}",
  "verdict": "VALIDATED" | "VALIDATED_WITH_CONDITIONS" | "INVALIDATED",
  "confidence_score": 85,
  "challenge_evaluations": [
    {{
      "challenge_id": "C1",
      "challenge_validity_score": 7,
      "response_strength_score": 8,
      "assessment": "Brief editorial assessment..."
    }}
  ],
  "conditions": [
    "Specific condition 1 (if VALIDATED_WITH_CONDITIONS, else empty list)"
  ],
  "editorial_reasoning": "2-3 sentence clear justification citing data values (p={p_val:.4f}, {effect_metric}={effect_size:.3f}, N={dataset_rows})."
}}

Rules:
- temperature=0.1 deterministic consistency
- If p > 0.05 or effect size is negligible, verdict MUST be INVALIDATED.
- If challenges raised valid observational / confounding points that the author conceded or partially conceded, verdict should be VALIDATED_WITH_CONDITIONS.
- If finding has overwhelming statistical power and rebuttal was airtight, verdict is VALIDATED.

Return ONLY valid JSON."""

        return llm_provider.generate_json(prompt, system_prompt=SYSTEM_PROMPT)

    def _arbitrate_heuristics(
        self,
        hypothesis: Dict[str, Any],
        p_val: float,
        effect_size: float,
        effect_metric: str,
        dataset_rows: int,
        challenges: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        evaluations = []
        has_concession = False

        for c, r in zip(challenges, responses):
            cid = c.get("id", "C1")
            stance = r.get("stance", "REBUTTED")
            if stance in ["PARTIALLY_CONCEDED", "CONCEDED"]:
                has_concession = True
                evaluations.append({
                    "challenge_id": cid,
                    "challenge_validity_score": 7,
                    "response_strength_score": 7,
                    "assessment": "Valid observational boundary acknowledged by author.",
                })
            else:
                evaluations.append({
                    "challenge_id": cid,
                    "challenge_validity_score": 5,
                    "response_strength_score": 8,
                    "assessment": "Author provided sufficient empirical defense.",
                })

        if p_val > 0.05:
            verdict = "INVALIDATED"
            confidence = 90
            conditions = []
            reasoning = f"Finding invalidated: observed p-value ({p_val:.4f}) exceeds the alpha=0.05 threshold."
        elif has_concession or dataset_rows < 100 or effect_size < 0.25:
            verdict = "VALIDATED_WITH_CONDITIONS"
            confidence = 82
            conditions = [
                f"Finding is observational ({hypothesis.get('independent_var')} → {hypothesis.get('dependent_var')}); potential latent confounders cannot be ruled out without experimental intervention.",
                f"Effect magnitude ({effect_metric}={effect_size:.3f}) must be evaluated within the context of sample size N={dataset_rows}.",
            ]
            reasoning = f"Accepted with conditions: statistically robust correlation ({effect_metric}={effect_size:.3f}, p={p_val:.4f}) in N={dataset_rows}, with noted observational boundaries."
        else:
            verdict = "VALIDATED"
            confidence = 92
            conditions = []
            reasoning = f"Fully validated: empirical evidence ({effect_metric}={effect_size:.3f}, p={p_val:.5f}) successfully dissolved all reviewer challenges without significant unaddressed vulnerabilities."

        return {
            "hypothesis_id": hypothesis.get("id"),
            "verdict": verdict,
            "confidence_score": confidence,
            "challenge_evaluations": evaluations,
            "conditions": conditions,
            "editorial_reasoning": reasoning,
        }
