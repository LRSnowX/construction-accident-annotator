import os
from pathlib import Path

import pandas as pd


def clear_screen():
    """清屏函数"""
    os.system("clear" if os.name != "nt" else "cls")


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


def save_progress(df, output_path, current_index):
    """保存当前进度"""
    # 保存标注结果
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    # 保存进度索引
    progress_file = Path(output_path).parent / ".annotation_progress.txt"
    with open(progress_file, "w") as f:
        f.write(str(current_index))

    print(f"\n进度已保存到: {output_path}")


def load_progress(output_path):
    """加载上次的进度"""
    progress_file = Path(output_path).parent / ".annotation_progress.txt"
    if progress_file.exists():
        with open(progress_file, "r") as f:
            return int(f.read().strip())
    return 0


def main():
    # 文件路径配置
    input_file = "accident_cases.csv"
    output_file = "accident_cases_annotated.csv"

    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 '{input_file}'")
        return

    # 读取CSV文件
    print(f"正在读取文件: {input_file}")
    try:
        df = pd.read_csv(input_file, encoding="utf-8-sig")
    except Exception as e:
        print(f"读取文件失败: {e}")
        return

    total_cases = len(df)
    print(f"共有 {total_cases} 个案例需要标注\n")

    # 初始化或读取现有的标注列
    if os.path.exists(output_file):
        print(f"检测到已存在的标注文件: {output_file}")
        response = input("是否继续之前的标注? (y/n): ").strip().lower()
        if response == "y":
            df = pd.read_csv(output_file, encoding="utf-8-sig")
            start_index = load_progress(output_file)
            print(f"从第 {start_index + 1} 条继续标注")
        else:
            start_index = 0
            if "is_construction" not in df.columns:
                df["is_construction"] = pd.NA
    else:
        start_index = 0
        if "is_construction" not in df.columns:
            df["is_construction"] = pd.NA

    # 标注历史记录（用于撤销功能）
    annotation_history = []

    # 开始标注流程
    current_index = start_index

    try:
        while current_index < total_cases:
            row = df.iloc[current_index]

            # 显示案例
            display_case(row, current_index, total_cases)

            # 如果已经标注过，显示之前的标注
            if pd.notna(df.loc[current_index, "is_construction"]):
                current_label = df.loc[current_index, "is_construction"]
                if current_label == -1:
                    print("\n[此案例之前被跳过]")
                else:
                    print(
                        f"\n[此案例之前已标注为: {'建筑业' if current_label == 1 else '非建筑业'}]"
                    )

            # 获取用户输入
            user_input = get_user_input()

            # 处理用户输入
            if user_input == "1":
                df.loc[current_index, "is_construction"] = 1
                annotation_history.append(current_index)
                print("✓ 已标注为: 建筑业案例")
                current_index += 1

            elif user_input == "0":
                df.loc[current_index, "is_construction"] = 0
                annotation_history.append(current_index)
                print("✓ 已标注为: 非建筑业案例")
                current_index += 1

            elif user_input in ["s", "skip"]:
                df.loc[current_index, "is_construction"] = -1  # 用-1表示跳过
                annotation_history.append(current_index)
                print("⊘ 已跳过此案例")
                current_index += 1

            elif user_input in ["u", "undo"]:
                if annotation_history:
                    last_index = annotation_history.pop()
                    df.loc[last_index, "is_construction"] = pd.NA
                    current_index = last_index
                    print("↶ 已撤销上一个标注")
                    input("\n按回车键继续...")
                else:
                    print("⚠ 没有可以撤销的标注")
                    input("\n按回车键继续...")

            elif user_input in ["q", "quit"]:
                print("\n正在保存并退出...")
                save_progress(df, output_file, current_index)
                print(f"已标注 {current_index - start_index} 个案例")
                print("下次运行程序时可以继续标注")
                return

            # 自动保存（每标注10个案例保存一次）
            if (current_index - start_index) % 10 == 0 and current_index > start_index:
                save_progress(df, output_file, current_index)

        # 全部标注完成
        clear_screen()
        print("=" * 80)
        print("🎉 恭喜！所有案例标注完成！")
        print("=" * 80)

        # 保存最终结果
        save_progress(df, output_file, current_index)

        # 显示统计信息
        construction_count = (df["is_construction"] == 1).sum()
        non_construction_count = (df["is_construction"] == 0).sum()
        skipped_count = (df["is_construction"] == -1).sum()

        print("\n标注统计:")
        print(f"  建筑业案例: {construction_count}")
        print(f"  非建筑业案例: {non_construction_count}")
        print(f"  跳过的案例: {skipped_count}")
        print(f"  总计: {total_cases}")

        # 删除进度文件
        progress_file = Path(output_file).parent / ".annotation_progress.txt"
        if progress_file.exists():
            progress_file.unlink()

    except KeyboardInterrupt:
        print("\n\n检测到 Ctrl+C，正在保存进度...")
        save_progress(df, output_file, current_index)
        print(f"已标注 {current_index - start_index} 个案例")
        print("下次运行程序时可以继续标注")
    except Exception as e:
        print(f"\n发生错误: {e}")
        save_progress(df, output_file, current_index)
        print("进度已保存")


if __name__ == "__main__":
    main()
