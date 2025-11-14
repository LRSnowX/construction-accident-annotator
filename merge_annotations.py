# -*- coding: utf-8 -*-
"""
多人标注结果合并工具

用法：
    python merge_annotations.py file1.csv file2.csv file3.csv ... -o merged_output.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd


def load_annotation_file(filepath):
    """加载标注文件"""
    path = Path(filepath)
    if path.suffix == ".parquet":
        return pd.read_parquet(filepath)
    else:
        return pd.read_csv(filepath, encoding="utf-8-sig")


def merge_annotations(files, output_file):
    """合并多个标注文件"""
    print(f"\n开始合并 {len(files)} 个标注文件...")

    # 加载所有文件
    dfs = []
    for i, file in enumerate(files, 1):
        print(f"[{i}/{len(files)}] 加载: {file}")
        df = load_annotation_file(file)
        dfs.append(df)

    # 使用第一个文件作为基准
    base_df = dfs[0].copy()
    total_cases = len(base_df)

    # 添加合并相关的列
    base_df["annotation_count"] = 0  # 有多少人标注了这条
    base_df["is_construction_conflict"] = False  # 是否建筑业判断有冲突
    base_df["annotators"] = ""  # 标注者列表

    # 统计
    stats = {
        "total": total_cases,
        "annotated": 0,
        "construction_conflicts": 0,
        "agreement_rate": 0.0,
    }

    print("\n开始合并标注...")

    for idx in range(total_cases):
        # 收集所有标注者对这条数据的标注
        is_construction_votes = []
        annotator_ids = []

        for df_idx, df in enumerate(dfs):
            if (
                pd.notna(df.loc[idx, "is_construction"])
                and df.loc[idx, "is_construction"] != -1
            ):
                is_construction_votes.append(df.loc[idx, "is_construction"])
                annotator_ids.append(f"A{df_idx + 1}")

        # 如果没有人标注这条，跳过
        if not is_construction_votes:
            continue

        base_df.loc[idx, "annotation_count"] = len(is_construction_votes)
        base_df.loc[idx, "annotators"] = ",".join(annotator_ids)

        # 检查 is_construction 是否一致
        if len(set(is_construction_votes)) > 1:
            # 有冲突
            base_df.loc[idx, "is_construction_conflict"] = True
            base_df.loc[idx, "is_construction"] = pd.NA  # 标记为待复议
            stats["construction_conflicts"] += 1
        else:
            # 一致，使用该值
            base_df.loc[idx, "is_construction"] = is_construction_votes[0]

        stats["annotated"] += 1

    # 计算一致性率
    if stats["annotated"] > 0:
        conflicts = stats["construction_conflicts"]
        stats["agreement_rate"] = (
            (stats["annotated"] - conflicts) / stats["annotated"] * 100
        )

    # 保存结果
    print(f"\n保存合并结果到: {output_file}")
    output_path = Path(output_file)

    # 同时保存为 CSV 和 Parquet
    base_df.to_csv(output_path.with_suffix(".csv"), index=False, encoding="utf-8-sig")
    base_df.to_parquet(output_path.with_suffix(".parquet"), index=False)

    # 输出统计信息
    print("\n" + "=" * 80)
    print("合并完成！统计信息：")
    print("=" * 80)
    print(f"总案例数:         {stats['total']}")
    print(f"已标注案例数:     {stats['annotated']}")
    print(f"是否建筑业冲突:   {stats['construction_conflicts']}")
    print(f"标注一致率:       {stats['agreement_rate']:.2f}%")
    print("=" * 80)

    # 导出冲突案例到单独文件
    conflict_df = base_df[base_df["is_construction_conflict"]]

    if len(conflict_df) > 0:
        conflict_file = output_path.parent / f"{output_path.stem}_conflicts.csv"
        conflict_df.to_csv(conflict_file, index=False, encoding="utf-8-sig")
        print(f"\n冲突案例已导出到: {conflict_file}")
        print(f"共 {len(conflict_df)} 条冲突案例需要复议\n")

    return base_df, stats


def main():
    parser = argparse.ArgumentParser(
        description="合并多人标注的结果文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 合并三个标注者的文件
    python merge_annotations.py \\
        accident_cases_annotated_user1.csv \\
        accident_cases_annotated_user2.csv \\
        accident_cases_annotated_user3.csv \\
        -o merged_result.csv
        
    # 也支持 parquet 格式
    python merge_annotations.py \\
        accident_cases_annotated_user1.parquet \\
        accident_cases_annotated_user2.parquet \\
        -o merged_result.csv
        """,
    )

    parser.add_argument("files", nargs="+", help="要合并的标注文件（至少2个）")
    parser.add_argument("-o", "--output", required=True, help="输出文件路径")

    args = parser.parse_args()

    if len(args.files) < 2:
        print("错误: 至少需要2个标注文件才能合并")
        sys.exit(1)

    # 检查所有文件是否存在
    for file in args.files:
        if not Path(file).exists():
            print(f"错误: 文件不存在: {file}")
            sys.exit(1)

    # 执行合并
    merge_annotations(args.files, args.output)


if __name__ == "__main__":
    main()
