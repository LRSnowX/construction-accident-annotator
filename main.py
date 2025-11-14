import random
import sys
from pathlib import Path

import pandas as pd

from construction_categories import (
    get_category_info,
    is_valid_construction_code,
    suggest_codes_from_text,
)
from utils import (
    clear_screen,
    display_case,
    get_user_input,
    load_progress,
    save_progress,
)


def get_detailed_suggestions(row):
    """获取详细的分类建议"""
    text_for_suggestion = (
        str(row.get("title", "") or "") + " " + str(row.get("full_text", "") or "")
    )
    return suggest_codes_from_text(text=text_for_suggestion, top_n=5)


def handle_construction_case(df, current_index, row):
    """处理建筑业案例的标注和建议选择"""
    df.loc[current_index, "is_construction"] = 1
    suggestions = get_detailed_suggestions(row)

    selected_code = None

    if suggestions:
        print("\n系统建议的细分类:")
        for i, (c, n, s) in enumerate(suggestions, start=1):
            print(f"  {i}. {c} - {n} (score={s:.2f})")
        print("  m. 手动输入代码")
        print("  n. 无匹配/不选择")

        sel_options = [str(i) for i in range(1, len(suggestions) + 1)] + ["m", "n"]
        sel = input(f"请选择({','.join(sel_options)}, 回车跳过): ").strip().lower()

        if sel in sel_options and sel not in ["m", "n"]:
            idx = int(sel) - 1
            selected_code, _, _ = suggestions[idx]
        elif sel == "m":
            while True:
                manual_code = input("请输入4位分类代码(例如4812): ").strip()
                if is_valid_construction_code(manual_code):
                    category_name = get_category_info(manual_code)["name"]
                    confirm = (
                        input(
                            f"您输入的是: {manual_code} - {category_name}。确认吗? (y/n): "
                        )
                        .strip()
                        .lower()
                    )
                    if confirm == "y":
                        selected_code = manual_code
                        break
                else:
                    print("无效代码，请重新输入。")
    else:
        print("\n未生成任何建议。")

    df.loc[current_index, "construction_code_selected"] = (
        selected_code if selected_code else pd.NA
    )
    print("✓ 已标注为: 建筑业案例")


def main():
    # 检查命令行参数
    random_mode = "--random" in sys.argv
    annotator_id = None

    for arg in sys.argv:
        if arg.startswith("--annotator="):
            annotator_id = arg.split("=")[1]

    input_file = "accident_cases.csv"
    # 使用基础名称，如果有标注者ID则加上ID
    if annotator_id:
        base_output_name = f"accident_cases_annotated_{annotator_id}"
    else:
        base_output_name = "accident_cases_annotated"

    output_parquet = f"{base_output_name}.parquet"
    output_csv = f"{base_output_name}.csv"

    if not Path(input_file).exists():
        print(f"错误: 找不到输入文件 '{input_file}'")
        return

    # 优先从 Parquet 加载，否则从 CSV，最后从原始文件
    if Path(output_parquet).exists():
        print(f"检测到快速加载文件，正在从 {output_parquet} 继续...")
        df = pd.read_parquet(output_parquet)
        start_index = load_progress(base_output_name)
        print(f"从第 {start_index + 1} 条继续标注")
    elif Path(output_csv).exists():
        print(f"检测到已标注的CSV文件，正在从 {output_csv} 继续...")
        df = pd.read_csv(output_csv, encoding="utf-8-sig")
        start_index = load_progress(base_output_name)
        print(f"从第 {start_index + 1} 条继续标注")
    else:
        print(f"未找到标注文件，正在从原始文件 {input_file} 开始...")
        try:
            df = pd.read_csv(input_file, encoding="utf-8-sig")
            start_index = 0
        except Exception as e:
            print(f"读取文件失败: {e}")
            return

    total_cases = len(df)

    # 如果是随机模式，创建随机索引序列
    if random_mode:
        print("\n📊 随机标注模式已启用")
        # 保存/加载随机种子以确保可重复性
        seed_file = Path(f"{base_output_name}_random_seed.txt")
        if seed_file.exists():
            with open(seed_file, "r") as f:
                seed = int(f.read().strip())
        else:
            seed = random.randint(0, 999999)
            with open(seed_file, "w") as f:
                f.write(str(seed))

        random.seed(seed)
        # 创建随机索引列表
        indices = list(range(total_cases))
        random.shuffle(indices)

        # 保存/加载索引映射
        index_file = Path(f"{base_output_name}_random_indices.txt")
        if not index_file.exists():
            with open(index_file, "w") as f:
                f.write(",".join(map(str, indices)))
        else:
            with open(index_file, "r") as f:
                indices = list(map(int, f.read().strip().split(",")))
    else:
        indices = None

    if annotator_id:
        print(f"👤 标注者ID: {annotator_id}")

    print(f"\n共有 {total_cases} 个案例需要标注")
    print(f"当前将从第 {start_index + 1} 条开始标注\n")

    # 初始化列
    for col in [
        "is_construction",
        "construction_code_selected",
    ]:
        if col not in df.columns:
            df[col] = pd.NA

    annotation_history = []
    current_index = start_index

    print("=" * 80)
    print("准备开始标注...")
    print(f"- 起始位置: 第 {start_index + 1} 条")
    print(f"- 剩余数量: {total_cases - start_index} 条")
    print("=" * 80)
    print("\n按回车键开始...")
    input()

    try:
        while current_index < total_cases:
            # 如果是随机模式，使用随机索引
            actual_index = indices[current_index] if indices else current_index
            row = df.iloc[actual_index]
            display_case(row, current_index, total_cases)

            if pd.notna(df.loc[actual_index, "is_construction"]):
                label = df.loc[actual_index, "is_construction"]
                status = (
                    "跳过" if label == -1 else ("建筑业" if label == 1 else "非建筑业")
                )
                print(f"\n[此案例之前已标注为: {status}]")

            user_input = get_user_input()

            if user_input == "1":
                handle_construction_case(df, actual_index, row)
                annotation_history.append(actual_index)
                current_index += 1
            elif user_input == "0":
                df.loc[actual_index, "is_construction"] = 0
                annotation_history.append(actual_index)
                print("✓ 已标注为: 非建筑业案例")
                current_index += 1
            elif user_input in ["s", "skip"]:
                df.loc[actual_index, "is_construction"] = -1
                annotation_history.append(actual_index)
                print("⊘ 已跳过此案例")
                current_index += 1
            elif user_input in ["u", "undo"]:
                if annotation_history:
                    last_actual_index = annotation_history.pop()
                    current_index = current_index - 1 if current_index > 0 else 0
                    # 清理相关列
                    for col in [
                        "is_construction",
                        "construction_code_selected",
                    ]:
                        df.loc[last_actual_index, col] = pd.NA
                    print("↶ 已撤销上一个标注")
                else:
                    print("⚠ 没有可以撤销的标注")
            elif user_input in ["q", "quit"]:
                print("\n正在保存并退出...")
                save_progress(df, base_output_name, current_index)
                return

            if (current_index - start_index) > 0 and (
                current_index - start_index
            ) % 10 == 0:
                save_progress(df, base_output_name, current_index)

        clear_screen()
        print("🎉 恭喜！所有案例标注完成！")
        save_progress(df, base_output_name, current_index)

        progress_file = Path(f"{base_output_name}_progress.txt")
        if progress_file.exists():
            progress_file.unlink()

    except (KeyboardInterrupt, Exception) as e:
        print(f"\n\n操作中断或发生错误: {e}")
        print("正在紧急保存进度...")
        save_progress(df, base_output_name, current_index)


if __name__ == "__main__":
    main()
