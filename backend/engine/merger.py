"""
DataMergeEngine — Intelligently merges supplemental CSV data with the original dataset.

Supports three merge strategies detected automatically from column names:
  1. Time-based  — join on year/date columns
  2. Geographic  — join on state/region/country columns
  3. Entity      — join on id/name/code columns

After merging, the enriched dataset is written to disk and returned for re-profiling.
"""

import os
import uuid
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple


class DataMergeEngine:
    """
    Performs intelligent left-joins between an original dataset and a supplemental
    CSV. Detects the best merge key automatically based on column name patterns.
    """

    # Keywords used to auto-detect merge key candidates
    TIME_KEYS = ["year", "date", "month", "period", "quarter", "week", "day", "timestamp"]
    GEO_KEYS = ["state", "region", "country", "city", "district", "county", "province",
                "territory", "zone", "location", "area", "place"]
    ENTITY_KEYS = ["id", "code", "key", "identifier", "name", "label", "category",
                   "entity", "group", "type", "class"]

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self.uploads_dir = os.path.join(self.working_dir, "uploads")
        os.makedirs(self.uploads_dir, exist_ok=True)

    def merge(
        self,
        original_csv_path: str,
        supplemental_csv_path: str,
        gap_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Merge the supplemental CSV into the original dataset.

        Returns:
            {
              "enriched_csv_path": str,
              "strategy": "time_based" | "geographic" | "entity" | "column_append",
              "merge_keys": [...],
              "original_shape": (rows, cols),
              "enriched_shape": (rows, cols),
              "rows_matched": int,
              "new_columns": [...],
              "success": bool,
              "message": str
            }
        """
        try:
            df_orig = pd.read_csv(original_csv_path)
            df_supp = pd.read_csv(supplemental_csv_path)
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to read CSV files: {e}",
                "enriched_csv_path": original_csv_path,
            }

        orig_shape = df_orig.shape
        orig_cols = [c.lower().strip() for c in df_orig.columns]
        supp_cols = [c.lower().strip() for c in df_supp.columns]

        # Rename columns to lowercase for consistency
        df_orig.columns = [c.lower().strip() for c in df_orig.columns]
        df_supp.columns = [c.lower().strip() for c in df_supp.columns]

        # Find best merge strategy
        strategy, merge_keys = self._detect_merge_strategy(orig_cols, supp_cols)

        if strategy == "column_append":
            # No join keys found — just add supplemental columns that don't already exist
            new_cols = [c for c in df_supp.columns if c not in df_orig.columns]
            if not new_cols:
                return {
                    "success": False,
                    "message": "Supplemental CSV contains no new columns not already in the original dataset.",
                    "enriched_csv_path": original_csv_path,
                    "strategy": strategy,
                    "merge_keys": [],
                }

            # Align rows by index (truncate to original length)
            for col in new_cols:
                if len(df_supp) >= len(df_orig):
                    df_orig[col] = df_supp[col].iloc[:len(df_orig)].values
                else:
                    df_orig[col] = pd.concat([
                        df_supp[col],
                        pd.Series([None] * (len(df_orig) - len(df_supp)))
                    ]).values

            enriched_path = self._save_enriched(df_orig, original_csv_path)
            return {
                "success": True,
                "strategy": "column_append",
                "merge_keys": [],
                "original_shape": orig_shape,
                "enriched_shape": df_orig.shape,
                "rows_matched": len(df_orig),
                "new_columns": new_cols,
                "enriched_csv_path": enriched_path,
                "message": f"Appended {len(new_cols)} new column(s) from supplemental data.",
            }

        # Perform the join on detected merge keys
        try:
            # Normalize merge key types for alignment
            for key in merge_keys:
                if key in df_orig.columns and key in df_supp.columns:
                    try:
                        df_orig[key] = df_orig[key].astype(str).str.lower().str.strip()
                        df_supp[key] = df_supp[key].astype(str).str.lower().str.strip()
                    except Exception:
                        pass

            # Only bring in new columns from supplemental (avoid duplicate conflicts)
            existing = set(df_orig.columns)
            cols_to_add = merge_keys + [c for c in df_supp.columns if c not in existing]
            df_supp_slim = df_supp[cols_to_add].drop_duplicates(subset=merge_keys)

            df_merged = pd.merge(
                df_orig,
                df_supp_slim,
                on=merge_keys,
                how="left",
            )

            new_cols = [c for c in df_merged.columns if c not in set(df_orig.columns)]
            rows_matched = df_merged[new_cols[0]].notna().sum() if new_cols else 0

            enriched_path = self._save_enriched(df_merged, original_csv_path)

            return {
                "success": True,
                "strategy": strategy,
                "merge_keys": merge_keys,
                "original_shape": orig_shape,
                "enriched_shape": df_merged.shape,
                "rows_matched": int(rows_matched),
                "new_columns": new_cols,
                "enriched_csv_path": enriched_path,
                "message": (
                    f"Successfully merged on {merge_keys} using {strategy} strategy. "
                    f"{rows_matched}/{orig_shape[0]} rows enriched with {len(new_cols)} new column(s)."
                ),
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Merge failed on keys {merge_keys}: {e}",
                "enriched_csv_path": original_csv_path,
                "strategy": strategy,
                "merge_keys": merge_keys,
            }

    def _detect_merge_strategy(
        self,
        orig_cols: List[str],
        supp_cols: List[str],
    ) -> Tuple[str, List[str]]:
        """
        Detect the best merge strategy by finding common column name patterns.
        Returns (strategy_name, list_of_merge_key_column_names).
        """
        # Find columns that exist in both datasets
        common_cols = [c for c in orig_cols if c in supp_cols]

        if not common_cols:
            return "column_append", []

        # Score each common column against strategy keywords
        def matches(col: str, keywords: List[str]) -> bool:
            return any(kw in col for kw in keywords)

        time_keys = [c for c in common_cols if matches(c, self.TIME_KEYS)]
        geo_keys = [c for c in common_cols if matches(c, self.GEO_KEYS)]
        entity_keys = [c for c in common_cols if matches(c, self.ENTITY_KEYS)]

        # Prefer combinations: geo + time is ideal for panel data
        if geo_keys and time_keys:
            return "time_geographic", geo_keys[:1] + time_keys[:1]
        elif time_keys:
            return "time_based", time_keys[:2]  # at most 2 time keys
        elif geo_keys:
            return "geographic", geo_keys[:2]
        elif entity_keys:
            return "entity", entity_keys[:1]
        elif common_cols:
            # Use the first common column as key
            return "entity", common_cols[:1]
        else:
            return "column_append", []

    def _save_enriched(self, df: pd.DataFrame, original_csv_path: str) -> str:
        """Save the enriched DataFrame as a new CSV in the uploads directory."""
        base_name = os.path.basename(original_csv_path)
        name_no_ext = os.path.splitext(base_name)[0]
        enriched_name = f"enriched_{uuid.uuid4().hex[:6]}_{name_no_ext}.csv"
        enriched_path = os.path.join(self.uploads_dir, enriched_name)
        df.to_csv(enriched_path, index=False)
        return enriched_path

    @staticmethod
    def get_columns(csv_path: str) -> List[str]:
        """Read only the header row to get column names without loading full CSV."""
        try:
            df = pd.read_csv(csv_path, nrows=0)
            return list(df.columns)
        except Exception:
            return []
