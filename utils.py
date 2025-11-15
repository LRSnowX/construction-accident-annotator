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

    # 统计已标注数据中建筑业和非建筑业的数量
    construction_count = (df["is_construction"] == 1).sum()
    non_construction_count = (df["is_construction"] == 0).sum()

    print("\n--- 统计信息 ---")
    print(f"  已标注: {annotated_count}")
    if annotated_count > 0:
        print(f"    └─ 建筑业: {construction_count}")
        print(f"    └─ 非建筑业: {non_construction_count}")
    print(f"  已跳过: {skipped_count}")
    print(f"  未处理: {total_cases - annotated_count - skipped_count}")
    print(f"  总计:   {total_cases}")
    print("--------------------")


def display_case(row, index, total, random_mode=False):
    """显示单个案例信息"""
    clear_screen()
    print("=" * 80)
    if random_mode:
        print(f"进度: 已完成 {index}/{total}，剩余 {total - index}")
    else:
        print(f"进度: 第 {index + 1}/{total} 条")
    print("=" * 80)

    # 只显示存在的字段（full_text除外，它在最后单独显示）
    optional_fields = {
        "title": "标题",
        "publish_date": "发布日期",
        "date": "日期",
        "category": "分类",
        "url": "链接",
        "source": "来源",
    }

    for field, label in optional_fields.items():
        if field in row.index and pd.notna(row[field]):
            print(f"\n{label}: {row[field]}")

    # 智能显示案例全文
    print("\n" + "-" * 80)
    full_text = str(row["full_text"])

    # 改进的关键段落识别策略
    # 1. 查找更具体的模式，避免匹配目录
    # 2. 要求关键词后有实质性内容（如日期、时间、描述等）

    import re

    # 定义关键词模式，要求后面有实质内容
    key_patterns = [
        # 匹配带有时间信息的事故经过描述（如：2024年1月18日...）
        r"(?:事故发生经过|事故经过|事发经过)[:：\s]*(?:\n\s*)?(\d{4}年|\d{1,2}月\d{1,2}日|.*?时.*?分)",
        # 匹配段落开头的事故描述
        r"\n\s*(?:事故发生经过|事故经过|事发经过)[:：]\s*\n",
        # 匹配带编号的段落（如：（六）事故发生经过）后的实质内容
        r"[（(][一二三四五六七八九十\d]+[）)][\s]*(?:事故发生经过|事故经过).*?\n\s*(\d{4}年|\d{1,2}月)",
    ]

    key_position = -1
    matched_keyword = None
    match_end = -1

    for pattern in key_patterns:
        match = re.search(pattern, full_text)
        if match:
            key_position = match.start()
            match_end = match.end()
            matched_keyword = "事故经过"

            # 验证这不是目录（目录通常前后都有短行和特定格式）
            # 检查匹配位置前后200字符
            context_before = full_text[max(0, key_position - 200) : key_position]
            context_after = full_text[match_end : min(len(full_text), match_end + 300)]

            # 如果前后都有很多短行（目录特征），跳过这个匹配
            lines_before = context_before.split("\n")
            lines_after = context_after.split("\n")[:5]

            short_lines_before = sum(
                1
                for line in lines_before[-5:]
                if len(line.strip()) < 40 and "- " in line
            )
            short_lines_after = sum(
                1 for line in lines_after if len(line.strip()) < 40 and "- " in line
            )

            # 如果前后都有很多带"-"的短行，可能是目录，继续找下一个
            if short_lines_before >= 2 and short_lines_after >= 2:
                continue

            # 找到了合适的匹配
            break

    # 如果上述模式都没找到，尝试更宽松的匹配
    if key_position == -1:
        fallback_patterns = [
            "事故发生经过",
            "事故经过",
            "事发经过",
            "事故情况",
            "事故概况",
        ]
        for pattern in fallback_patterns:
            # 找到所有匹配位置
            pos = 0
            while pos < len(full_text):
                pos = full_text.find(pattern, pos)
                if pos == -1:
                    break

                # 检查这个位置是否在目录中
                context = full_text[max(0, pos - 150) : min(len(full_text), pos + 150)]
                lines = context.split("\n")
                short_lines = sum(
                    1
                    for line in lines
                    if len(line.strip()) < 40
                    and ("- " in line or "）" in line or "(" in line)
                )

                # 如果周围短行很少，可能是正文
                if short_lines < 3:
                    key_position = pos
                    matched_keyword = pattern
                    match_end = pos + len(pattern)
                    break

                pos += len(pattern)

            if key_position != -1:
                break

    # 如果找到关键段落，优先显示该部分
    if key_position != -1:
        print(f"【关键信息】（找到 '{matched_keyword}'）:")
        print("-" * 80)

        # 从匹配结束位置开始取内容（跳过关键词本身）
        start = max(0, match_end - 50)  # 保留少量上下文
        # 向后取足够的内容（最多1500字符，约3-4段）
        end = min(len(full_text), match_end + 1500)

        excerpt = full_text[start:end]
        # 如果不是从头开始，添加省略号
        if start > 0:
            # 尝试从完整句子开始
            newline_pos = excerpt.find("\n")
            if newline_pos > 0 and newline_pos < 100:
                excerpt = excerpt[newline_pos + 1 :]
            else:
                excerpt = "..." + excerpt
        if end < len(full_text):
            excerpt = excerpt + "..."

        print(f"\n{excerpt}\n")
        print("-" * 80)
        print(f"💡 提示: 以上已截取关键部分。全文共 {len(full_text)} 字符。")
    else:
        # 没找到关键词，显示完整全文
        print("⚠️  未找到关键词，显示完整案例全文:")
        print("-" * 80)
        print(f"\n{full_text}\n")
        print("-" * 80)
        print(
            f"💡 提示: 未识别到关键段落，已显示全文({len(full_text)}字符)供人工判断。"
        )

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
