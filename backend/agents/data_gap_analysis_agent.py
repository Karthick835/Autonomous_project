"""
DataGapAnalysisAgent (Agent 9) — Active Data Acquisition System.
Runs immediately after the Profiler. Examines the dataset structure and proposed
hypotheses to identify missing variables, incomplete time ranges, or absent contextual
data that would materially affect the validity or strength of the findings.

Modeled after the data sufficiency review step in academic research design.
"""

import json
from typing import Dict, Any, List, Optional
from llm.provider import LLMProvider, LLMConfigurationError


SYSTEM_PROMPT = """You are a rigorous research methodologist and data sufficiency expert.
Your role is to examine a dataset profile and identify what data is MISSING that would
materially affect the scientific validity of the proposed hypotheses.

You must be specific — never say "more data would help". Say exactly what column,
what time range, what demographic group, or what contextual variable is absent and why
its absence matters for these specific hypotheses.

Always cite actual column names from the dataset profile provided.
Always respond with valid JSON only — no markdown, no prose outside JSON."""


class DataGapAnalysisAgent:
    """
    Agent 9: Identifies missing variables, incomplete time coverage,
    absent comparison groups, and potential confounders not present in the dataset.
    Classifies each gap as CRITICAL / IMPORTANT / OPTIONAL.
    """

    def analyze_gaps(
        self,
        profile: Dict[str, Any],
        hypotheses: List[Dict[str, Any]],
        domain_context: str = "",
        llm_provider: Optional[LLMProvider] = None,
    ) -> Dict[str, Any]:
        """
        Identify data gaps relative to the hypotheses and dataset structure.

        Returns:
            {
              "gaps": [...],                # list of gap dicts
              "critical_count": N,
              "important_count": N,
              "optional_count": N,
              "overall_assessment": "...",
              "pipeline_action": "PAUSE" | "WARN" | "CONTINUE"
            }
        """
        if llm_provider is not None:
            try:
                return self._analyze_with_llm(profile, hypotheses, domain_context, llm_provider)
            except LLMConfigurationError:
                raise
            except Exception as e:
                print(f"[DataGapAnalysisAgent] LLM analysis failed ({e}). Using heuristic fallback.")

        return self._analyze_heuristic(profile, hypotheses, domain_context)

    def _analyze_with_llm(
        self,
        profile: Dict[str, Any],
        hypotheses: List[Dict[str, Any]],
        domain_context: str,
        llm_provider: LLMProvider,
    ) -> Dict[str, Any]:
        columns = list(profile.get("column_profiles", {}).keys())
        num_rows = profile.get("num_rows", 0)
        num_cols = profile.get("num_cols", 0)
        target = profile.get("active_target", "")
        task = profile.get("active_task", "")
        high_corr = profile.get("high_correlations", [])[:5]

        hyp_summaries = [
            f"  [{h.get('id')}] {h.get('title')}: {h.get('statement', '')} "
            f"(tests {h.get('independent_var', '?')} → {h.get('dependent_var', '?')})"
            for h in hypotheses[:8]
        ]

        prompt = f"""Dataset Profile:
- Rows: {num_rows}, Columns: {num_cols}
- Target Variable: {target} ({task})
- All Columns: {columns}
- High Correlations: {high_corr}
- Domain Context: {domain_context or "Not specified"}

Proposed Hypotheses to be tested:
{chr(10).join(hyp_summaries)}

Task:
Identify data that is MISSING from this dataset that would materially affect the validity
or strength of the proposed hypotheses. Focus on:

1. MISSING CONTEXTUAL VARIABLES — e.g. if sales data lacks marketing spend, crime data
   lacks population for per-capita normalization, patient data lacks age/comorbidities.

2. INCOMPLETE TIME COVERAGE — gaps in time ranges, missing years, truncated periods that
   affect trend or longitudinal hypotheses.

3. MISSING COMPARISON GROUPS — single region/demographic when hypothesis implies universality,
   no control group when treatment effect is claimed.

4. POTENTIAL CONFOUNDING VARIABLES — known domain-specific confounders not present in the
   columns list above.

For each gap, classify as:
- CRITICAL: findings will be scientifically invalid without this data
- IMPORTANT: findings will be materially weakened without this data
- OPTIONAL: findings would be enhanced but remain valid without this data

Return ONLY a JSON object with this exact schema:
{{
  "gaps": [
    {{
      "id": "G1",
      "priority": "CRITICAL" | "IMPORTANT" | "OPTIONAL",
      "title": "One line: what is missing",
      "what_is_missing": "Exact variable/dataset description (cite column names where relevant)",
      "why_it_matters": "How absence of this data specifically affects hypotheses H001, H002...",
      "impact_if_absent": "Findings will be: invalid/weakened/less precise",
      "affected_hypotheses": ["H001", "H002"],
      "example_csv_columns": ["col1", "col2", "col3"],
      "example_description": "A CSV with these columns would satisfy this gap"
    }}
  ],
  "overall_assessment": "2-3 sentence executive summary of data sufficiency",
  "pipeline_action": "PAUSE" | "WARN" | "CONTINUE"
}}

Rules:
- pipeline_action = "PAUSE" if any CRITICAL gaps exist
- pipeline_action = "WARN" if IMPORTANT gaps exist but no CRITICAL
- pipeline_action = "CONTINUE" if only OPTIONAL gaps
- If data is genuinely sufficient, return empty gaps array and CONTINUE
- Do not invent gaps that don't logically apply to these hypotheses
- Maximum 5 gaps total — focus on the most impactful

No markdown code fences. No explanation outside JSON."""

        result = llm_provider.generate_json(prompt, system_prompt=SYSTEM_PROMPT)
        return self._enrich_result(result)

    def _analyze_heuristic(
        self,
        profile: Dict[str, Any],
        hypotheses: List[Dict[str, Any]],
        domain_context: str,
    ) -> Dict[str, Any]:
        """Heuristic fallback: identify obvious structural gaps without LLM."""
        columns = list(profile.get("column_profiles", {}).keys())
        num_rows = profile.get("num_rows", 0)
        target = profile.get("active_target", "")
        gaps = []

        col_str = " ".join(c.lower() for c in columns)

        # Check for population normalization gap in crime/count data
        has_count_cols = any(w in col_str for w in ["crime", "count", "incident", "case", "arrest"])
        has_pop_col = any(w in col_str for w in ["population", "pop", "capita", "density"])
        if has_count_cols and not has_pop_col:
            gaps.append({
                "id": "G1",
                "priority": "IMPORTANT",
                "title": "Missing population data for per-capita normalization",
                "what_is_missing": "Population count per geographic/time unit to normalize absolute counts",
                "why_it_matters": "Without population denominators, count-based findings cannot be interpreted as rates and may reflect population growth rather than true trends.",
                "impact_if_absent": "Findings about counts will be weakened — rates cannot be computed",
                "affected_hypotheses": [h.get("id") for h in hypotheses[:3]],
                "example_csv_columns": ["state", "year", "population"],
                "example_description": "A CSV with state, year, and population columns matching your dataset's geographic/time granularity",
            })

        # Check for time-series data without date column
        has_year = any(w in col_str for w in ["year", "date", "month", "period", "time"])
        hyp_texts = " ".join(h.get("statement", "") + " " + h.get("title", "") for h in hypotheses).lower()
        mentions_trend = any(w in hyp_texts for w in ["trend", "over time", "increase", "decrease", "growth", "change"])
        if mentions_trend and not has_year:
            gaps.append({
                "id": f"G{len(gaps)+1}",
                "priority": "IMPORTANT",
                "title": "Missing time dimension for trend hypotheses",
                "what_is_missing": "A date or year column to enable longitudinal/temporal analysis",
                "why_it_matters": "One or more hypotheses concern temporal trends but the dataset has no time dimension to test these claims.",
                "impact_if_absent": "Trend-based findings will be weakened — no temporal ordering available",
                "affected_hypotheses": [h.get("id") for h in hypotheses if any(w in (h.get("statement","") + h.get("title","")).lower() for w in ["trend","change","increase","decrease"])],
                "example_csv_columns": ["year", "date"],
                "example_description": "A column indicating the time period for each observation",
            })

        # Small sample warning
        if num_rows < 100:
            gaps.append({
                "id": f"G{len(gaps)+1}",
                "priority": "IMPORTANT",
                "title": f"Small sample size (N={num_rows}) limits statistical generalizability",
                "what_is_missing": "Additional observations to achieve adequate statistical power",
                "why_it_matters": f"With only {num_rows} rows, effect size estimates have wide confidence intervals and findings cannot be generalized to broader populations.",
                "impact_if_absent": "All findings will carry a small-sample caveat limiting generalizability",
                "affected_hypotheses": [h.get("id") for h in hypotheses],
                "example_csv_columns": columns[:3],
                "example_description": f"Additional rows following the same column structure as the uploaded file",
            })

        pipeline_action = "CONTINUE"
        if any(g["priority"] == "CRITICAL" for g in gaps):
            pipeline_action = "PAUSE"
        elif any(g["priority"] == "IMPORTANT" for g in gaps):
            pipeline_action = "WARN"

        return self._enrich_result({
            "gaps": gaps,
            "overall_assessment": (
                f"Heuristic scan identified {len(gaps)} data gap(s) in the {profile.get('num_rows',0)}-row dataset. "
                f"{'Pipeline will pause for critical gaps.' if pipeline_action == 'PAUSE' else 'Investigation continues with noted limitations.' if gaps else 'Dataset appears sufficient for the proposed hypotheses.'}"
            ),
            "pipeline_action": pipeline_action,
        })

    def _enrich_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Compute summary counts and ensure required fields."""
        gaps = result.get("gaps", [])
        critical = [g for g in gaps if g.get("priority") == "CRITICAL"]
        important = [g for g in gaps if g.get("priority") == "IMPORTANT"]
        optional = [g for g in gaps if g.get("priority") == "OPTIONAL"]

        result["critical_count"] = len(critical)
        result["important_count"] = len(important)
        result["optional_count"] = len(optional)

        # Ensure pipeline_action is correct
        if critical:
            result["pipeline_action"] = "PAUSE"
        elif important:
            result["pipeline_action"] = "WARN"
        else:
            result["pipeline_action"] = "CONTINUE"

        return result

    def validate_supplemental_csv(
        self,
        gap: Dict[str, Any],
        supplemental_columns: List[str],
    ) -> Dict[str, Any]:
        """
        Validate that a supplemental CSV actually contains what was requested for a gap.
        Returns: {valid: bool, message: str, matched_columns: [...], missing_columns: [...]}
        """
        requested = [c.lower() for c in gap.get("example_csv_columns", [])]
        provided = [c.lower() for c in supplemental_columns]

        if not requested:
            return {"valid": True, "message": "No specific columns required for this gap.", "matched_columns": provided, "missing_columns": []}

        matched = [r for r in requested if any(r in p or p in r for p in provided)]
        missing = [r for r in requested if r not in matched]

        # Require at least 50% of requested columns
        match_ratio = len(matched) / len(requested)
        if match_ratio >= 0.5:
            return {
                "valid": True,
                "message": f"Supplemental data validated: {len(matched)}/{len(requested)} expected columns found.",
                "matched_columns": matched,
                "missing_columns": missing,
            }
        else:
            return {
                "valid": False,
                "message": (
                    f"Supplemental CSV is missing key columns. "
                    f"Expected: {gap.get('example_csv_columns', [])}. "
                    f"Found: {supplemental_columns}. "
                    f"Please provide a CSV with at least: {missing[:3]}."
                ),
                "matched_columns": matched,
                "missing_columns": missing,
            }
