"""
Real chart generation agent.
Generates matplotlib/seaborn PNGs from actual data — no mocks.
All charts saved to disk and served via FastAPI static endpoint.
"""

import os
import uuid
import traceback
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — required for server-side
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from typing import Dict, Any, Optional, List

# Dark research theme for all charts
CHART_STYLE = {
    "figure.facecolor": "#0D1117",
    "axes.facecolor": "#161B22",
    "axes.edgecolor": "#30363D",
    "axes.labelcolor": "#C9D1D9",
    "axes.titlecolor": "#F0F6FC",
    "xtick.color": "#8B949E",
    "ytick.color": "#8B949E",
    "grid.color": "#21262D",
    "grid.linewidth": 0.8,
    "text.color": "#C9D1D9",
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
}

ACCENT_VIOLET = "#7C3AED"
ACCENT_CYAN = "#06B6D4"
ACCENT_GREEN = "#10B981"
ACCENT_RED = "#EF4444"
ACCENT_AMBER = "#F59E0B"

CONFIRMED_COLOR = ACCENT_GREEN
REJECTED_COLOR = ACCENT_RED
NEUTRAL_COLOR = ACCENT_CYAN


class ChartGeneratorAgent:
    """
    Generates real matplotlib/seaborn charts from actual dataset data.
    Saves PNGs to the charts directory. Returns filename for serving.
    """

    def __init__(self, charts_dir: str):
        self.charts_dir = charts_dir
        os.makedirs(charts_dir, exist_ok=True)
        plt.rcParams.update(CHART_STYLE)
        sns.set_style("darkgrid")

    def _save_fig(self, fig, prefix: str) -> str:
        """Save figure and return the filename."""
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(self.charts_dir, filename)
        fig.savefig(filepath, dpi=120, bbox_inches="tight",
                    facecolor=CHART_STYLE["figure.facecolor"])
        plt.close(fig)
        return filename

    def generate_distribution_chart(
        self,
        df: pd.DataFrame,
        indep_var: str,
        dep_var: str,
        hypothesis_id: str,
    ) -> Optional[str]:
        """Box plot + violin: distribution of indep_var split by dep_var groups."""
        try:
            if indep_var not in df.columns or dep_var not in df.columns:
                return None

            col_data = pd.to_numeric(df[indep_var], errors="coerce")
            if col_data.isna().all():
                return None

            unique_vals = df[dep_var].dropna().unique()
            if len(unique_vals) < 2 or len(unique_vals) > 20:
                return None

            fig, ax = plt.subplots(figsize=(9, 5))
            palette = sns.color_palette(
                [ACCENT_VIOLET, ACCENT_CYAN, ACCENT_GREEN, ACCENT_AMBER, ACCENT_RED],
                n_colors=len(unique_vals),
            )

            plot_df = df[[indep_var, dep_var]].copy()
            plot_df[indep_var] = pd.to_numeric(plot_df[indep_var], errors="coerce")
            plot_df = plot_df.dropna()
            plot_df[dep_var] = plot_df[dep_var].astype(str)

            sns.boxplot(
                data=plot_df,
                x=dep_var,
                y=indep_var,
                palette=palette,
                linewidth=1.2,
                flierprops=dict(marker="o", markerfacecolor=ACCENT_AMBER, markersize=3, alpha=0.6),
                ax=ax,
            )
            ax.set_title(
                f"Distribution: {indep_var} by {dep_var}",
                fontsize=13, fontweight="bold", pad=14,
            )
            ax.set_xlabel(dep_var, fontsize=11)
            ax.set_ylabel(indep_var, fontsize=11)
            ax.yaxis.grid(True, alpha=0.4)
            ax.set_facecolor(CHART_STYLE["axes.facecolor"])
            fig.patch.set_facecolor(CHART_STYLE["figure.facecolor"])

            return self._save_fig(fig, f"dist_{hypothesis_id}")
        except Exception:
            traceback.print_exc()
            return None

    def generate_correlation_scatter(
        self,
        df: pd.DataFrame,
        indep_var: str,
        dep_var: str,
        hypothesis_id: str,
        correlation: float = 0.0,
    ) -> Optional[str]:
        """Scatter plot with regression line for correlation hypotheses."""
        try:
            if indep_var not in df.columns or dep_var not in df.columns:
                return None

            plot_df = df[[indep_var, dep_var]].copy()
            plot_df[indep_var] = pd.to_numeric(plot_df[indep_var], errors="coerce")
            plot_df[dep_var] = pd.to_numeric(plot_df[dep_var], errors="coerce")
            plot_df = plot_df.dropna()

            if len(plot_df) < 10:
                return None

            # Sample for large datasets
            if len(plot_df) > 2000:
                plot_df = plot_df.sample(2000, random_state=42)

            fig, ax = plt.subplots(figsize=(9, 5))
            ax.scatter(
                plot_df[indep_var],
                plot_df[dep_var],
                alpha=0.4,
                color=ACCENT_CYAN,
                s=18,
                edgecolors="none",
            )
            # Regression line
            try:
                m, b = np.polyfit(plot_df[indep_var], plot_df[dep_var], 1)
                x_line = np.linspace(plot_df[indep_var].min(), plot_df[indep_var].max(), 100)
                ax.plot(x_line, m * x_line + b, color=ACCENT_VIOLET, linewidth=2.2, label=f"r = {correlation:.3f}")
                ax.legend(fontsize=10)
            except Exception:
                pass

            ax.set_title(f"Scatter: {indep_var} vs {dep_var}", fontsize=13, fontweight="bold", pad=14)
            ax.set_xlabel(indep_var, fontsize=11)
            ax.set_ylabel(dep_var, fontsize=11)
            ax.set_facecolor(CHART_STYLE["axes.facecolor"])
            fig.patch.set_facecolor(CHART_STYLE["figure.facecolor"])

            return self._save_fig(fig, f"scatter_{hypothesis_id}")
        except Exception:
            traceback.print_exc()
            return None

    def generate_categorical_bar(
        self,
        df: pd.DataFrame,
        indep_var: str,
        dep_var: str,
        hypothesis_id: str,
    ) -> Optional[str]:
        """Stacked percentage bar chart for chi-square / categorical independence tests."""
        try:
            if indep_var not in df.columns or dep_var not in df.columns:
                return None

            cross_tab = pd.crosstab(df[indep_var], df[dep_var], normalize="index") * 100
            if cross_tab.empty or cross_tab.shape[0] > 25:
                return None

            fig, ax = plt.subplots(figsize=(10, 5))
            palette = sns.color_palette(
                [ACCENT_VIOLET, ACCENT_CYAN, ACCENT_GREEN, ACCENT_AMBER, ACCENT_RED],
                n_colors=cross_tab.shape[1],
            )
            cross_tab.plot(
                kind="bar",
                stacked=True,
                color=palette,
                ax=ax,
                edgecolor="none",
                width=0.7,
            )
            ax.set_title(
                f"Category Distribution: {indep_var} by {dep_var} (%)",
                fontsize=13, fontweight="bold", pad=14,
            )
            ax.set_xlabel(indep_var, fontsize=11)
            ax.set_ylabel("Percentage (%)", fontsize=11)
            ax.legend(title=dep_var, bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=9)
            plt.xticks(rotation=30, ha="right", fontsize=9)
            ax.set_facecolor(CHART_STYLE["axes.facecolor"])
            fig.patch.set_facecolor(CHART_STYLE["figure.facecolor"])

            return self._save_fig(fig, f"catbar_{hypothesis_id}")
        except Exception:
            traceback.print_exc()
            return None

    def generate_feature_importance(
        self,
        top_features: Dict[str, float],
        hypothesis_id: str,
        dep_var: str,
    ) -> Optional[str]:
        """Horizontal bar chart showing Random Forest feature importances."""
        try:
            if not top_features:
                return None

            features = list(top_features.keys())[:10]
            importances = [top_features[f] for f in features]

            # Sort descending
            sorted_pairs = sorted(zip(features, importances), key=lambda x: x[1])
            features = [p[0] for p in sorted_pairs]
            importances = [p[1] for p in sorted_pairs]

            fig, ax = plt.subplots(figsize=(9, max(4, len(features) * 0.45 + 1)))
            colors = [
                ACCENT_VIOLET if imp >= max(importances) * 0.7
                else ACCENT_CYAN if imp >= max(importances) * 0.4
                else "#4B5563"
                for imp in importances
            ]
            bars = ax.barh(features, importances, color=colors, height=0.6, edgecolor="none")

            # Value labels
            for bar, val in zip(bars, importances):
                ax.text(
                    val + max(importances) * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:.3f}",
                    va="center",
                    fontsize=9,
                    color="#C9D1D9",
                )

            ax.set_title(
                f"Feature Importance → {dep_var}",
                fontsize=13, fontweight="bold", pad=14,
            )
            ax.set_xlabel("Importance Score", fontsize=11)
            ax.set_facecolor(CHART_STYLE["axes.facecolor"])
            fig.patch.set_facecolor(CHART_STYLE["figure.facecolor"])
            ax.xaxis.grid(True, alpha=0.4)

            return self._save_fig(fig, f"importance_{hypothesis_id}")
        except Exception:
            traceback.print_exc()
            return None

    def generate_correlation_heatmap(
        self,
        df: pd.DataFrame,
        dataset_name: str,
    ) -> Optional[str]:
        """Correlation heatmap for all numerical features."""
        try:
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(num_cols) < 2:
                return None

            # Cap at 15 columns for readability
            if len(num_cols) > 15:
                num_cols = num_cols[:15]

            corr_matrix = df[num_cols].corr()
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)

            fig, ax = plt.subplots(figsize=(max(7, len(num_cols) * 0.8), max(5, len(num_cols) * 0.7)))
            cmap = sns.diverging_palette(260, 20, s=85, l=40, as_cmap=True)
            sns.heatmap(
                corr_matrix,
                mask=mask,
                cmap=cmap,
                center=0,
                annot=True,
                fmt=".2f",
                annot_kws={"size": 8},
                linewidths=0.4,
                linecolor="#1F2937",
                cbar_kws={"shrink": 0.8},
                ax=ax,
            )
            ax.set_title(
                f"Feature Correlation Matrix — {dataset_name}",
                fontsize=13, fontweight="bold", pad=14,
            )
            ax.set_facecolor(CHART_STYLE["axes.facecolor"])
            fig.patch.set_facecolor(CHART_STYLE["figure.facecolor"])
            plt.xticks(rotation=30, ha="right", fontsize=8)
            plt.yticks(rotation=0, fontsize=8)

            return self._save_fig(fig, "heatmap_global")
        except Exception:
            traceback.print_exc()
            return None

    def generate_target_distribution(
        self,
        df: pd.DataFrame,
        target_col: str,
        task_type: str,
        dataset_name: str,
    ) -> Optional[str]:
        """Distribution plot of the target variable."""
        try:
            if target_col not in df.columns:
                return None

            fig, ax = plt.subplots(figsize=(8, 4.5))
            col = df[target_col].dropna()

            if task_type == "regression" and pd.api.types.is_numeric_dtype(col):
                sns.histplot(col, kde=True, color=ACCENT_VIOLET,
                             edgecolor="none", ax=ax, alpha=0.85)
                ax.set_xlabel(target_col, fontsize=11)
                ax.set_ylabel("Count", fontsize=11)
            else:
                vc = col.value_counts()
                colors = [ACCENT_VIOLET, ACCENT_CYAN, ACCENT_GREEN, ACCENT_AMBER, ACCENT_RED]
                palette = [colors[i % len(colors)] for i in range(len(vc))]
                ax.bar(vc.index.astype(str), vc.values, color=palette, edgecolor="none", width=0.6)
                ax.set_xlabel(target_col, fontsize=11)
                ax.set_ylabel("Count", fontsize=11)
                for i, v in enumerate(vc.values):
                    ax.text(i, v + max(vc.values) * 0.01, str(v),
                            ha="center", va="bottom", fontsize=9, color="#C9D1D9")

            ax.set_title(f"Target Distribution: {target_col}", fontsize=13, fontweight="bold", pad=14)
            ax.set_facecolor(CHART_STYLE["axes.facecolor"])
            fig.patch.set_facecolor(CHART_STYLE["figure.facecolor"])

            return self._save_fig(fig, "target_dist")
        except Exception:
            traceback.print_exc()
            return None

    def generate_chart_for_hypothesis(
        self,
        df: pd.DataFrame,
        hypothesis: Dict[str, Any],
        execution_result: Dict[str, Any],
    ) -> Optional[str]:
        """
        Route to the correct chart type based on hypothesis test_type.
        Returns chart filename or None on failure.
        """
        test_type = hypothesis.get("test_type", "")
        h_id = hypothesis.get("id", "H000")
        indep = hypothesis.get("independent_var", "")
        dep = hypothesis.get("dependent_var", "")
        parsed = execution_result.get("parsed_result") or {}

        if test_type == "mann_whitney_u":
            return self.generate_distribution_chart(df, indep, dep, h_id)

        elif test_type == "pearson_correlation":
            corr = parsed.get("details", {}).get("correlation", 0.0)
            return self.generate_correlation_scatter(df, indep, dep, h_id, corr)

        elif test_type == "chi_square":
            return self.generate_categorical_bar(df, indep, dep, h_id)

        elif test_type == "anova":
            return self.generate_distribution_chart(df, dep, indep, h_id)

        elif test_type == "random_forest_cv":
            top_features = parsed.get("details", {}).get("top_features", {})
            return self.generate_feature_importance(top_features, h_id, dep)

        return None
