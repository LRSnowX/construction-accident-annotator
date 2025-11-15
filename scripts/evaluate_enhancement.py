import os
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd

# 允许从项目根目录导入 hints（脚本从 scripts/ 运行时）
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from hints import (
    _tokenize_for_learning,  # internal tokenizer for warm-up
    extract_features,
    extract_features_enhanced,
    load_hint_model,
    load_hint_model_enhanced,
    normalize_text,
    predict_non_construction_proba,
    predict_non_construction_proba_enhanced,
)


def five_number_summary(xs: List[float]) -> Tuple[float, float, float, float, float]:
    s = pd.Series(xs)
    q = s.quantile([0, 0.25, 0.5, 0.75, 1.0])
    return (
        float(q.iloc[0]),
        float(q.iloc[1]),
        float(q.iloc[2]),
        float(q.iloc[3]),
        float(q.iloc[4]),
    )


def main():
    # 支持两种路径：项目根目录或 data/raw 目录
    csv_path = Path("accident_cases.csv")
    if not csv_path.exists():
        csv_path = Path("data/raw/accident_cases.csv")
    if not csv_path.exists():
        raise SystemExit("未找到 accident_cases.csv，请放置在项目根目录或 data/raw/")

    df = pd.read_csv(csv_path)
    if "full_text" not in df.columns:
        raise SystemExit("accident_cases.csv 缺少列: full_text")

    # 采样一小批数据
    sample = df[df["full_text"].notna()].sample(n=min(300, len(df)), random_state=42)

    # 加载两个模型（互不影响）
    base_model = load_hint_model("eval_baseline")
    enh_model = load_hint_model_enhanced("eval_enhanced")

    # 预热 TF-IDF：无监督地为增强模型累积文档频率
    for _, row in sample.iterrows():
        text = normalize_text(row)
        tokens = _tokenize_for_learning(text)
        enh_model["tfidf"].learn_one(tokens)

    base_probs: List[float] = []
    enh_probs: List[float] = []

    contrib_examples = []  # 保存差异最大的若干条，展示Top贡献特征

    for idx, row in sample.iterrows():
        feats_base = extract_features(row)
        p_base, c_base = predict_non_construction_proba(base_model, feats_base)

        feats_enh = extract_features_enhanced(enh_model, row)
        p_enh, c_enh = predict_non_construction_proba_enhanced(enh_model, feats_enh)

        base_probs.append(p_base)
        enh_probs.append(p_enh)

        contrib_examples.append(
            {
                "index": idx,
                "desc": str(row.get("case_description", ""))[:120],
                "p_base": p_base,
                "p_enh": p_enh,
                "delta": p_enh - p_base,
                "top_base": c_base[:5],
                "top_enh": c_enh[:5],
            }
        )

    # 汇总分布
    b_min, b_q1, b_med, b_q3, b_max = five_number_summary(base_probs)
    e_min, e_q1, e_med, e_q3, e_max = five_number_summary(enh_probs)

    # Spearman 相关（无需 SciPy）：先取秩再做 Pearson
    s_base = pd.Series(base_probs).rank(method="average")
    s_enh = pd.Series(enh_probs).rank(method="average")
    corr = s_base.corr(s_enh)

    print("=== 概率分布（非建筑业概率）===")
    print(
        "Baseline  min/Q1/med/Q3/max:",
        f"{b_min:.3f}/{b_q1:.3f}/{b_med:.3f}/{b_q3:.3f}/{b_max:.3f}",
    )
    print(
        "Enhanced  min/Q1/med/Q3/max:",
        f"{e_min:.3f}/{e_q1:.3f}/{e_med:.3f}/{e_q3:.3f}/{e_max:.3f}",
    )
    print(f"Spearman 相关: {corr:.3f}")

    # 展示差异最大的样本
    print("\n=== 增强提高最多的样本（Top 5）===")
    for item in sorted(contrib_examples, key=lambda x: x["delta"], reverse=True)[:5]:
        print(
            f"[+]{item['delta']:+.3f} idx={item['index']} base={item['p_base']:.3f} enh={item['p_enh']:.3f}"
        )
        print("  摘要:", item["desc"])
        print("  Base:", item["top_base"])  # (feature, contribution)
        print("  Enh :", item["top_enh"])  # (feature, contribution)

    print("\n=== 增强降低最多的样本（Top 5）===")
    for item in sorted(contrib_examples, key=lambda x: x["delta"])[:5]:
        print(
            f"[-]{item['delta']:+.3f} idx={item['index']} base={item['p_base']:.3f} enh={item['p_enh']:.3f}"
        )
        print("  摘要:", item["desc"])
        print("  Base:", item["top_base"])  # (feature, contribution)
        print("  Enh :", item["top_enh"])  # (feature, contribution)


if __name__ == "__main__":
    main()
