# -*- coding: utf-8 -*-
"""
辅助函数模块，包含UI显示、文件IO等功能。
"""

import os
from pathlib import Path

import pandas as pd


def clear_screen():
    """清屏函数"""
    os.system("clear" if os.name != "nt" else "cls")


def display_stats(df: pd.DataFrame):
    """显示当前的标注统计信息"""
    total_cases = len(df)
    annotated_mask = df["is_construction"].notna() & (df["is_construction"] != -1)
    annotated_count = annotated_mask.sum()
    skipped_count = (df["is_construction"] == -1).sum()

    print("\n--- 统计信息 ---")
    print(f"  已标注: {annotated_count}")
    print(f"  已跳过: {skipped_count}")
    print(f"  未处理: {total_cases - annotated_count - skipped_count}")
    print(f"  总计:   {total_cases}")
    print("--------------------")


def display_case(row, index, total):
    """显示单个案例信息"""
    clear_screen()
    print("=" * 80)
    print(f"进度: {index + 1}/{total}")
    print("=" * 80)
    print(f"\n标题: {row['title']}")
    print(f"\n发布日期: {row.get('publish_date', 'N/A')}")
    print(f"\n分类: {row.get('category', 'N/A')}")
    print(f"\nURL: {row['url']}")
    print("\n" + "-" * 80)
    print("案例全文:")
    print("-" * 80)
    print(f"\n{row['full_text']}\n")
    print("=" * 80)


def get_user_input():
    """获取用户输入并验证"""
    print("\n请标注此案例:")
    print("  1 - 建筑业案例")
    print("  0 - 非建筑业案例")
    print("  s - 跳过此案例")
    print("  u - 撤销上一个标注")
    print("  q - 保存并退出")
    print("\n请输入: ", end="", flush=True)

    while True:
        user_input = input().strip().lower()
        if user_input in ["1", "0", "s", "skip", "u", "undo", "q", "quit"]:
            return user_input
        else:
            print("无效输入，请输入 1, 0, s, u 或 q: ", end="", flush=True)


def save_progress(df: pd.DataFrame, base_output_path: str, current_index: int):
    """保存当前进度到 Parquet 和 CSV，并显示统计信息"""
    path_obj = Path(base_output_path)
    parquet_path = path_obj.with_suffix(".parquet")
    csv_path = path_obj.with_suffix(".csv")

    # 保存为 Parquet (用于快速加载) 和 CSV (用于人工审查)
    try:
        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(
            f"\n进度已同步保存到: \n  - {parquet_path} (快速加载)\n  - {csv_path} (人工审查)"
        )
    except Exception as e:
        print(f"文件保存失败: {e}")
        return

    # 保存进度索引
    progress_file = path_obj.parent / f"{path_obj.stem}_progress.txt"
    with open(progress_file, "w") as f:
        f.write(str(current_index))

    display_stats(df)


def load_progress(base_output_path: str):
    """加载上次的进度索引"""
    path_obj = Path(base_output_path)
    progress_file = path_obj.parent / f"{path_obj.stem}_progress.txt"
    if progress_file.exists():
        with open(progress_file, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                return int(content)
    return 0
