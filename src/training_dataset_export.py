"""
训练/评测数据导出（面试导向）

目标：从结构化数据库（PostGIS）导出 LLM 可用的数据形态：
- SFT/指令微调：instruction + input + output
- Eval/评测：question + answer(规则生成) + metadata

说明：这里以“沉降异常判别/摘要生成”为例，用规则生成弱标签，形成可复用数据生产模板。
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from config import OUTPUT_DIR
from src.database import get_engine


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def _rule_risk_level(max_settlement: float) -> str:
    # 面试可讲：阈值可配置、可迭代，后续可替换为模型评分
    if max_settlement >= 50:
        return "high"
    if max_settlement >= 45:
        return "medium"
    return "low"


def _build_point_summary_text(row: pd.Series) -> str:
    def _fmt(value: Any, suffix: str = "") -> str:
        # LEFT JOIN 会让无观测的测点产生 NaN；显式转为 None 以避免训练数据出现 "nan"
        return f"{value}{suffix}" if pd.notna(value) else "暂无数据"

    return (
        f"测点{row['point_name']}，里程{row['chainage']}；"
        f"观测期数{int(row['obs_count'])}；"
        f"平均沉降{_fmt(row['avg_settlement'], 'mm')}；"
        f"最大沉降{_fmt(row['max_settlement'], 'mm')}；"
        f"期末沉降{_fmt(row['final_settlement'], 'mm')}。"
    )


def export_training_datasets(
    *,
    out_dir: Optional[str] = None,
    include_figure_paths: bool = True,
    limit_points: Optional[int] = None,
) -> Dict[str, str]:
    out_dir = out_dir or os.path.join(OUTPUT_DIR, "training")
    engine = get_engine()

    df_summary = pd.read_sql(
        """
        WITH latest AS (
            -- 业务语义：期末沉降 = 每个测点 obs_date 最近一条观测的 cumulative_settlement
            -- 用 DISTINCT ON（PG 语法）取每组首行，再按 obs_date DESC 拿到最新期
            SELECT DISTINCT ON (point_name)
                point_name,
                cumulative_settlement AS final_settlement_raw
            FROM settlement_observations
            ORDER BY point_name, obs_date DESC, id DESC
        )
        SELECT
            s.point_name,
            s.chainage,
            COUNT(o.id) as obs_count,
            ROUND(AVG(o.cumulative_settlement)::numeric, 2) as avg_settlement,
            ROUND(MAX(o.cumulative_settlement)::numeric, 2) as max_settlement,
            ROUND(l.final_settlement_raw::numeric, 2) as final_settlement
        FROM survey_points s
        LEFT JOIN settlement_observations o ON s.point_name = o.point_name
        LEFT JOIN latest l ON s.point_name = l.point_name
        GROUP BY s.point_name, s.chainage, l.final_settlement_raw
        ORDER BY s.point_name
        """,
        engine,
    )

    if limit_points:
        df_summary = df_summary.head(int(limit_points))

    figure_paths: List[str] = []
    if include_figure_paths:
        # 面试讲法：图像模态（可视化）与结构化数据对齐，形成多模态样本
        figure_paths = [
            os.path.join(OUTPUT_DIR, "figures", "settlement_curves.png"),
            os.path.join(OUTPUT_DIR, "figures", "settlement_distribution.png"),
        ]

    sft_rows: List[Dict[str, Any]] = []
    eval_rows: List[Dict[str, Any]] = []
    now = datetime.now().isoformat(timespec="seconds")

    for _, row in df_summary.iterrows():
        max_settlement = (
            float(row["max_settlement"])
            if row["max_settlement"] is not None and pd.notna(row["max_settlement"])
            else 0.0
        )
        risk = _rule_risk_level(max_settlement)
        summary_text = _build_point_summary_text(row)

        instruction = "你是施工监测数据分析助手，请根据输入的测点沉降统计信息，给出风险等级与监测建议。"
        user_input = summary_text
        output = (
            f"风险等级：{risk}。\n"
            f"建议：{'加密观测频率并复核施工工况' if risk != 'low' else '按计划继续常规监测'}。"
        )

        meta = {
            "generated_at": now,
            "dataset": "settlement_monitoring_system",
            "point_name": row["point_name"],
            "chainage": row["chainage"],
            "obs_count": int(row["obs_count"]),
            "avg_settlement_mm": (
                float(row["avg_settlement"]) if pd.notna(row["avg_settlement"]) else None
            ),
            "max_settlement_mm": max_settlement,
            "final_settlement_mm": (
                float(row["final_settlement"]) if pd.notna(row["final_settlement"]) else None
            ),
            "risk_rule": {"medium_ge_mm": 45, "high_ge_mm": 50},
        }
        if figure_paths:
            meta["figure_paths"] = figure_paths

        sft_rows.append({"instruction": instruction, "input": user_input, "output": output, "meta": meta})

        eval_rows.append(
            {
                "question": user_input,
                "answer": output,
                "label_risk": risk,
                "meta": meta,
            }
        )

    sft_path = os.path.join(out_dir, "settlement_sft.jsonl")
    eval_path = os.path.join(out_dir, "settlement_eval.jsonl")
    return {
        "sft": _write_jsonl(sft_path, sft_rows),
        "eval": _write_jsonl(eval_path, eval_rows),
    }


def main():
    print("=" * 50)
    print("导出训练/评测数据集 (JSONL)")
    print("=" * 50)
    paths = export_training_datasets()
    for k, v in paths.items():
        print(f"[OK] {k}: {v}")
    print("=" * 50)


if __name__ == "__main__":
    main()

