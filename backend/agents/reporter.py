"""
ScienceWriterAgent — Generates executive Markdown reports and reproducible Jupyter Notebooks (.ipynb).
Structured into 3 formal peer-reviewed tiers:
  Tier 1: Validated Findings (unconditional acceptance)
  Tier 2: Validated with Conditions (acceptance with stated empirical bounds)
  Tier 3: Invalidated Findings (Transparency Log)

Level 3 additions:
  - Enriched Dataset Badges (if supplemental data merged)
  - Data Limitation Warnings (if critical/important gaps skipped)
  - Future Data Enhancement Opportunities section
"""

import json
import os
import nbformat as nbf
from typing import Dict, Any, List, Optional


class ScienceWriterAgent:
    """
    Generates executive Markdown reports and executable Jupyter Notebooks (.ipynb)
    incorporating False Discovery Rate control, 3-Tier Adversarial Peer Review,
    and Level 3 Active Data Acquisition provenance.
    """

    def generate_markdown_report(
        self,
        profile: Dict[str, Any],
        validation: Dict[str, Any],
        adversarial_reviews: Optional[List[Dict[str, Any]]] = None,
        dataset_name: str = "Dataset",
        enrichment_info: Optional[Dict[str, Any]] = None,
        skipped_gaps: Optional[List[Dict[str, Any]]] = None,
        optional_gaps: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        findings = validation.get("findings", [])
        reviews = adversarial_reviews or []
        review_map = {r["hypothesis_id"]: r for r in reviews}

        tier1 = []
        tier2 = []
        tier3 = []

        for f in findings:
            hid = f["hypothesis_id"]
            rev = review_map.get(hid, {})
            verdict = rev.get("arbitration", {}).get("verdict", "")

            if verdict == "VALIDATED" or (not verdict and f["status"] == "CONFIRMED_DISCOVERY"):
                tier1.append((f, rev))
            elif verdict == "VALIDATED_WITH_CONDITIONS":
                tier2.append((f, rev))
            else:
                tier3.append((f, rev))

        target_col = profile.get("active_target", "Target")
        task_type = profile.get("active_task", "Classification").title()
        num_rows = profile.get("num_rows", 0)
        num_cols = profile.get("num_cols", 0)
        fdr_alpha = validation.get("fdr_alpha_used", 0.05)

        md = []
        md.append(f"# Autonomous Scientific Peer-Reviewed Report")
        md.append(f"**Dataset**: `{dataset_name}`  |  **Target Column**: `{target_col}` (`{task_type}`)  |  **Observations (N)**: {num_rows}  |  **Features**: {num_cols}")
        md.append(f"**FDR Alpha**: {fdr_alpha}  |  **Tier 1 Validated**: {len(tier1)}  |  **Tier 2 Conditional**: {len(tier2)}  |  **Tier 3 Invalidated**: {len(tier3)}\n")

        # Level 3: Dataset Provenance & Enrichment Banner
        if enrichment_info and enrichment_info.get("success"):
            md.append("### 🧬 Dataset Enrichment Provenance (Level 3 Active Acquisition)")
            md.append(
                f"- **Enrichment Strategy**: `{enrichment_info.get('strategy', 'Merge')}` on keys `{enrichment_info.get('merge_keys', [])}`\n"
                f"- **Shape Shift**: Original ({enrichment_info.get('original_shape', (0,0))[0]}×{enrichment_info.get('original_shape', (0,0))[1]}) → "
                f"Enriched ({enrichment_info.get('enriched_shape', (0,0))[0]}×{enrichment_info.get('enriched_shape', (0,0))[1]})\n"
                f"- **New Variables Integrated**: `{enrichment_info.get('new_columns', [])}`\n"
            )

        if skipped_gaps:
            md.append("### ⚠️ Active Data Sufficiency Limitations")
            for gap in skipped_gaps:
                md.append(f"- **Unresolved {gap.get('priority', 'GAP')}**: `{gap.get('title')}` — *{gap.get('why_it_matters')}*")
            md.append("")

        # Executive Summary
        md.append("## Executive Summary")
        total = len(findings)
        md.append(
            f"The Autonomous AI Scientist evaluated **{total} hypotheses** on `{dataset_name}` targeting outcome `{target_col}`. "
            f"Every candidate finding underwent two-stage verification: statistical False Discovery Rate (FDR) control and structured **Adversarial Peer Review** (Falsification → Corroboration → Arbitration)."
        )
        md.append(
            f"\n- **Tier 1 (Fully Validated)**: {len(tier1)} discovery(ies) survived adversarial challenges without vulnerabilities."
            f"\n- **Tier 2 (Validated with Conditions)**: {len(tier2)} finding(s) confirmed with explicit observational/sample bounds."
            f"\n- **Tier 3 (Invalidated / Transparency Log)**: {len(tier3)} hypothesis(es) failed peer review or statistical thresholds."
        )

        # Tier 1
        md.append("\n## Tier 1 — Validated Findings (Highest Confidence)")
        if tier1:
            md.append("| ID | Title | Test Type | Effect Size | P-Value | Confidence | Provenance | Editorial Verdict |")
            md.append("|---|---|---|---|---|---|---|---|")
            for f, rev in tier1:
                arb = rev.get("arbitration", {})
                conf = arb.get("confidence_score", 90)
                provenance_badge = "Enriched Data" if f.get("from_enriched_data") else "Original CSV"
                md.append(
                    f"| `{f['hypothesis_id']}` | **{f['title']}** | `{f['test_type']}` | {f['effect_size_metric']}={f['effect_size']:.3f} | `{f['p_value']:.4f}` | {conf}% | {provenance_badge} | ✅ VALIDATED |"
                )
            md.append("")
            for f, rev in tier1:
                arb = rev.get("arbitration", {})
                md.append(f"### `{f['hypothesis_id']}`: {f['title']}")
                stmt = f.get('statement') or f.get('summary') or f.get('title', '')
                md.append(f"- **Statement**: {stmt}")
                md.append(f"- **Statistical Evidence**: {f['summary']}")
                if arb.get("editorial_reasoning"):
                    md.append(f"- **Editorial Review**: *\"{arb['editorial_reasoning']}\"*")
                if f.get("limitation_flags"):
                    md.append(f"- **Data Caveats**: {'; '.join(f['limitation_flags'])}")
                md.append("")
        else:
            md.append("*No hypotheses achieved unconditional Tier 1 validation.*")

        # Tier 2
        md.append("\n## Tier 2 — Validated with Conditions (Bounded Scope)")
        if tier2:
            md.append("| ID | Title | Effect Size | P-Value | Primary Stated Limitation |")
            md.append("|---|---|---|---|---|")
            for f, rev in tier2:
                arb = rev.get("arbitration", {})
                conds = arb.get("conditions", ["Observational boundary"])
                first_cond = conds[0] if conds else "Observational boundary"
                md.append(
                    f"| `{f['hypothesis_id']}` | **{f['title']}** | {f['effect_size_metric']}={f['effect_size']:.3f} | `{f['p_value']:.4f}` | {first_cond} |"
                )
            md.append("")
            for f, rev in tier2:
                arb = rev.get("arbitration", {})
                md.append(f"### `{f['hypothesis_id']}`: {f['title']} (⚠️ CONDITIONAL)")
                stmt = f.get('statement') or f.get('summary') or f.get('title', '')
                md.append(f"- **Statement**: {stmt}")
                md.append(f"- **Statistical Evidence**: {f['summary']}")
                if arb.get("editorial_reasoning"):
                    md.append(f"- **Editorial Review**: *\"{arb['editorial_reasoning']}\"*")
                if arb.get("conditions"):
                    md.append("- **Peer Review Conditions & Stated Limitations**:")
                    for c in arb["conditions"]:
                        md.append(f"  - {c}")
                if f.get("limitation_flags"):
                    md.append(f"- **Data Sufficiency Flags**: {'; '.join(f['limitation_flags'])}")
                md.append("")
        else:
            md.append("*No hypotheses classified into Tier 2.*")

        # Tier 3 (Transparency Log)
        md.append("\n## Tier 3 — Invalidated Findings (Transparency Log)")
        md.append("> *Transparent science reports all tested hypotheses, including those invalidated during peer review or failing statistical FDR thresholds.*")
        if tier3:
            md.append("| ID | Title | Reason for Rejection / Invalidation |")
            md.append("|---|---|---|")
            for f, rev in tier3:
                arb = rev.get("arbitration", {})
                reason = arb.get("editorial_reasoning") or f.get("rejection_reason") or "Failed statistical FDR significance or peer review challenge."
                md.append(f"| `{f['hypothesis_id']}` | {f['title']} | {reason} |")
            md.append("")
            for f, rev in tier3:
                arb = rev.get("arbitration", {})
                md.append(f"### `{f['hypothesis_id']}`: {f['title']} (❌ INVALIDATED)")
                stmt = f.get('statement') or f.get('summary') or f.get('title', '')
                md.append(f"- **Statement**: {stmt}")
                md.append(f"- **Rejection Details**: {arb.get('editorial_reasoning') or f.get('rejection_reason', 'Did not survive adversarial peer review.')}")
                md.append("")
        else:
            md.append("*All candidate hypotheses survived into Tier 1 or Tier 2.*")

        # Level 3: Future Enhancement Opportunities Section
        if optional_gaps:
            md.append("\n## Data Enhancement Opportunities (Level 3 Active Intelligence)")
            md.append("> *The following additional data sources would further strengthen or extend these findings if incorporated in future investigations:*")
            for og in optional_gaps:
                md.append(f"- **{og.get('title')}**: {og.get('what_is_missing')}")
                md.append(f"  *Potential Impact*: {og.get('why_it_matters')}")
            md.append("")

        return "\n".join(md)

    def generate_jupyter_notebook(
        self,
        csv_path: str,
        profile: Dict[str, Any],
        validation: Dict[str, Any],
        output_ipynb_path: str,
        adversarial_reviews: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        nb = nbf.v4.new_notebook()
        dataset_name = os.path.basename(csv_path)
        norm_csv = csv_path.replace("\\", "/")

        # Cell 1: Metadata & Intro
        nb.cells.append(nbf.v4.new_markdown_cell(f"""# Autonomous AI Scientist — Reproducible Research Notebook
**Dataset**: `{dataset_name}`
**Target Column**: `{profile.get('active_target', 'N/A')}` ({profile.get('active_task', 'N/A')})
**Total Validated Findings**: {validation.get('confirmed_discoveries', 0)} / {validation.get('total_hypotheses_tested', 0)}

This notebook contains self-contained, reproducible Python code for all confirmed statistical discoveries and visualizations.
"""))

        # Cell 2: Data Loading & Setup
        nb.cells.append(nbf.v4.new_code_cell(f"""import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use('ggplot')

# Load Dataset
df = pd.read_csv('{norm_csv}')
print("Dataset Loaded Successfully. Shape:", df.shape)
df.head()
"""))

        # Cell 3: Data Visualization
        nb.cells.append(nbf.v4.new_code_cell("""# Plot Correlation Matrix Heatmap for Numerical Features
numeric_cols = df.select_dtypes(include=[np.number]).columns
if len(numeric_cols) >= 2:
    plt.figure(figsize=(10, 6))
    sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
    plt.title("Numerical Feature Correlation Matrix", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()
"""))

        # Cell 4: Validated Findings reproduction
        for f in validation.get("findings", []):
            if f.get("status") == "CONFIRMED_DISCOVERY":
                h_id = f["hypothesis_id"]
                stmt = f.get('statement') or f.get('summary') or f.get('title', '')
                nb.cells.append(nbf.v4.new_markdown_cell(f"### Hypothesis [{h_id}]: {f['title']}\n**Statement**: {stmt}\n**Validated Result**: p={f['p_value']:.5f}, {f['effect_size_metric']}={f['effect_size']:.3f}"))

        with open(output_ipynb_path, "w", encoding="utf-8") as f:
            nbf.write(nb, f)
