"""
数据质量校验与报告

面试导向：把“清洗、去重、质检、统计”工程化，形成可复用模块与可追溯产物。

兼容性：考虑到部分面试/演示环境仍可能使用 Python 3.6，这里不依赖 dataclasses。
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import pandas as pd


def _count_missing_cells(df: pd.DataFrame) -> int:
    return int(df.isna().sum().sum())


def _safe_rate(n: int, d: int) -> float:
    return float(n / d) if d else 0.0


def build_quality_report(
    *,
    dataset: str,
    df: pd.DataFrame,
    input_path: str,
    primary_key: Optional[Tuple[str, ...]] = None,
    notes: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if primary_key:
        dup_rows = int(df.duplicated(list(primary_key), keep="last").sum())
    else:
        dup_rows = int(df.duplicated(keep="last").sum())

    total = int(len(df))
    missing_cells = _count_missing_cells(df)
    col_missing = {c: int(df[c].isna().sum()) for c in df.columns}

    metrics = {
        "total_rows": total,
        "duplicate_rows": dup_rows,
        "missing_cells": missing_cells,
        "missing_rate": _safe_rate(missing_cells, total * max(len(df.columns), 1)),
        "duplicate_rate": _safe_rate(dup_rows, total),
    }

    return {
        "dataset": dataset,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_path": input_path,
        "primary_key": primary_key,
        "metrics": metrics,
        "column_missing": col_missing,
        "notes": notes or {},
    }


def write_quality_report(report: Dict[str, Any], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, "quality_report__{}__{}.json".format(report["dataset"], ts))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return out_path


def clean_survey_points(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """轻量清洗：类型转换、缺失过滤、去重。"""
    notes: Dict[str, Any] = {"dropped_rows": 0, "deduped_rows": 0}

    df = df.copy()
    expected_cols = [
        "point_name",
        "chainage",
        "x_coord",
        "y_coord",
        "h_initial",
        "point_type",
    ]
    missing_cols = [c for c in expected_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"survey_points 缺少字段: {missing_cols}")

    # 关键字段：point_name, x/y 坐标
    before = len(df)
    df["point_name"] = df["point_name"].astype(str).str.strip()
    df = df[df["point_name"].notna() & (df["point_name"].str.len() > 0)]
    df = df[df["x_coord"].notna() & df["y_coord"].notna()]
    notes["dropped_rows"] += int(before - len(df))

    # 类型转换（容错）
    for col in ["x_coord", "y_coord", "h_initial"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 去重：以 point_name 为主键，保留最后一条
    before = len(df)
    df = df.drop_duplicates(subset=["point_name"], keep="last")
    notes["deduped_rows"] += int(before - len(df))

    return df, notes


def clean_settlement_observations(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """轻量清洗：日期解析、类型转换、缺失过滤、去重。"""
    notes: Dict[str, Any] = {"dropped_rows": 0, "deduped_rows": 0}

    df = df.copy()
    expected_cols = [
        "point_name",
        "obs_date",
        "period",
        "settlement_rate",
        "cumulative_settlement",
        "remark",
    ]
    missing_cols = [c for c in expected_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"settlement_observations 缺少字段: {missing_cols}")

    df["point_name"] = df["point_name"].astype(str).str.strip()
    df = df[df["point_name"].notna() & (df["point_name"].str.len() > 0)]

    # 日期标准化
    df["obs_date"] = pd.to_datetime(df["obs_date"], errors="coerce").dt.date
    before = len(df)
    df = df[df["obs_date"].notna()]
    notes["dropped_rows"] += int(before - len(df))

    # 数值字段
    for col in ["period", "settlement_rate", "cumulative_settlement"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 去重：point_name + obs_date 作为业务主键
    before = len(df)
    df = df.drop_duplicates(subset=["point_name", "obs_date"], keep="last")
    notes["deduped_rows"] += int(before - len(df))

    return df, notes

