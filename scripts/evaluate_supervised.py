import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import pandas as pd

# 允许从项目根导入
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from hints import (
    extract_features,
    extract_features_enhanced,
    load_hint_model,
    load_hint_model_enhanced,
    predict_non_construction_proba,
    predict_non_construction_proba_enhanced,
    update_model_online,
    update_model_online_enhanced,
)


@dataclass
class Metrics:
    acc: float
    auc: float
    precision: float
    recall: float
    size: int


def simple_auc(y_true: List[int], y_score: List[float]) -> float:
    # ROC AUC（纯 Python）：排序后用梯形积分
    data = sorted(zip(y_score, y_true), key=lambda x: x[0])
    P = sum(y_true)
    N = len(y_true) - P
    if P == 0 or N == 0:
        return 0.5
    tp = fp = 0
    prev_score = None
    tpr_fpr: List[Tuple[float, float]] = [(0.0, 0.0)]
    for score, label in data:
        if prev_score is None or score != prev_score:
            tpr_fpr.append((tp / P, fp / N))
            prev_score = score
        if label == 1:
            tp += 1
        else:
            fp += 1
    tpr_fpr.append((tp / P, fp / N))
    # 按 FPR 升序积分
    tpr_fpr = sorted(set(tpr_fpr), key=lambda x: x[1])
    auc = 0.0
    for i in range(1, len(tpr_fpr)):
        tpr1, fpr1 = tpr_fpr[i - 1]
        tpr2, fpr2 = tpr_fpr[i]
        auc += (fpr2 - fpr1) * (tpr1 + tpr2) / 2.0
    return max(0.0, min(1.0, auc))


def compute_metrics(y_true: List[int], y_score: List[float]) -> Metrics:
    # 1 表示“非建筑业”
    y_pred = [1 if s >= 0.5 else 0 for s in y_score]
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)
    acc = (tp + tn) / max(1, len(y_true))
    precision = tp / max(1, (tp + fp))
    recall = tp / max(1, (tp + fn))
    auc = simple_auc(y_true, y_score)
    return Metrics(
        acc=acc, auc=auc, precision=precision, recall=recall, size=len(y_true)
    )


def main():
    # 读取标注数据
    p = Path("data/annotated/accident_cases_annotated_lizhijie.csv")
    if not p.exists():
        raise SystemExit(
            "未找到带标签数据 data/annotated/accident_cases_annotated_lizhijie.csv"
        )
    df = pd.read_csv(p)
    df = df[df["full_text"].notna()]
    df = df[df["is_construction"].isin([0, 1])]
    if df.empty:
        raise SystemExit("标注数据为空或缺少 is_construction 标签")

    # 采样并划分训练/测试（在线学习）
    df = df.sample(frac=1.0, random_state=2025)
    n = min(3000, len(df))
    df = df.head(n)
    split = int(len(df) * 0.7)
    train = df.iloc[:split]
    test = df.iloc[split:]

    # 准备两套独立模型
    base_model = load_hint_model("eval_sup_base")
    enh_model = load_hint_model_enhanced("eval_sup_enh")

    # 在线训练（按行更新）
    for _, row in train.iterrows():
        label_non_construction = 1 if row["is_construction"] == 0 else 0
        # baseline
        feats_b = extract_features(row)
        update_model_online(base_model, feats_b, label_non_construction)
        # enhanced（注意传 row+feats）
        feats_e = extract_features_enhanced(enh_model, row)
        update_model_online_enhanced(enh_model, row, feats_e, label_non_construction)

    # 评估
    y_true: List[int] = []
    y_base: List[float] = []
    y_enh: List[float] = []
    for _, row in test.iterrows():
        label_non_construction = 1 if row["is_construction"] == 0 else 0
        y_true.append(label_non_construction)
        # baseline
        feats_b = extract_features(row)
        p_b, _ = predict_non_construction_proba(base_model, feats_b)
        y_base.append(p_b)
        # enhanced
        feats_e = extract_features_enhanced(enh_model, row)
        p_e, _ = predict_non_construction_proba_enhanced(enh_model, feats_e)
        y_enh.append(p_e)

    m_base = compute_metrics(y_true, y_base)
    m_enh = compute_metrics(y_true, y_enh)

    print("=== 有监督评估（在线学习，70/30） ===")
    print(f"样本规模: 训练 {len(train)} / 测试 {len(test)}")
    print("Baseline:", vars(m_base))
    print("Enhanced:", vars(m_enh))
    print(
        "提升(绝对值):",
        {
            "acc": round(m_enh.acc - m_base.acc, 4),
            "auc": round(m_enh.auc - m_base.auc, 4),
            "precision": round(m_enh.precision - m_base.precision, 4),
            "recall": round(m_enh.recall - m_base.recall, 4),
        },
    )


if __name__ == "__main__":
    main()
