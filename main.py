import random
from pathlib import Path

import pandas as pd

from hints import (
    extract_features_enhanced,
    format_hint_line,
    get_seed_load_summary,
    load_hint_model_enhanced,
    maybe_expand_features,
    predict_non_construction_proba_enhanced,
    remove_learned_features,
    rollback_token_stats,
    rollback_update,
    save_hint_model_enhanced,
    update_model_online_enhanced,
    update_token_stats,
)
from utils import (
    clear_screen,
    display_case,
    get_user_input,
    load_progress,
    save_progress,
)


def main():
    print("=" * 80)
    print("                     建筑业事故案例标注系统")
    print("=" * 80)

    # 设置文件路径
    output_dir = Path("data/annotated")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 尝试读取上次使用的用户名
    last_user_file = output_dir / ".last_user"
    last_user = None
    if last_user_file.exists():
        try:
            with open(last_user_file, "r", encoding="utf-8") as f:
                last_user = f.read().strip()
        except Exception:
            pass

    # 交互式询问用户名
    print("\n📝 请输入您的用户名/标注者ID（用于区分不同标注者的文件）")
    if last_user:
        print(f"   上次使用: {last_user}")
        annotator_id = input(f"   用户名 (直接回车使用 '{last_user}'): ").strip()
        if not annotator_id:
            annotator_id = last_user
            print(f"   ✓ 继续使用: {annotator_id}")
        else:
            print(f"   ✓ 用户名: {annotator_id}")
    else:
        annotator_id = input("   用户名: ").strip()
        if not annotator_id:
            annotator_id = "default"
            print(f"   ⚠️  未输入用户名，使用默认值: {annotator_id}")
        else:
            print(f"   ✓ 用户名: {annotator_id}")

    # 保存用户名供下次使用
    try:
        with open(last_user_file, "w", encoding="utf-8") as f:
            f.write(annotator_id)
    except Exception:
        pass

    # 交互式询问是否使用随机模式
    print("\n🎲 是否启用随机标注模式？（多人协作时建议启用，避免冲突）")
    random_choice = input("   请选择 (y/n, 默认n): ").strip().lower()
    random_mode = random_choice == "y"

    if random_mode:
        print("   ✓ 随机模式已启用")
    else:
        print("   ✓ 顺序模式（按原始顺序标注）")

    print("\n" + "=" * 80)

    # 设置文件路径
    raw_dir = Path("data/raw")
    output_dir = Path("data/annotated")

    # 确保目录存在
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 自动检测 data/raw 目录下的 CSV 文件
    csv_files = list(raw_dir.glob("*.csv"))

    if not csv_files:
        print(f"\n❗ 错误: 在 {raw_dir}/ 目录下未找到任何CSV文件")
        print(f"\n请将原始CSV文件放在 {raw_dir}/ 目录下")
        print("\n按回车键退出...")
        input()
        return
    elif len(csv_files) == 1:
        # 只有一个CSV文件，直接使用
        input_file = csv_files[0]
        print(f"\n📄 检测到数据文件: {input_file.name}")
    else:
        # 多个CSV文件，让用户选择
        print(f"\n📂 检测到 {len(csv_files)} 个CSV文件，请选择要标注的文件：")
        print()
        for i, csv_file in enumerate(csv_files, 1):
            file_size = csv_file.stat().st_size / (1024 * 1024)  # MB
            print(f"  {i}. {csv_file.name} ({file_size:.1f} MB)")
        print()

        while True:
            try:
                choice = input("请输入文件序号: ").strip()
                file_index = int(choice) - 1
                if 0 <= file_index < len(csv_files):
                    input_file = csv_files[file_index]
                    print(f"\n✅ 已选择: {input_file.name}")
                    break
                else:
                    print(f"⚠️  请输入 1 到 {len(csv_files)} 之间的数字")
            except ValueError:
                print("⚠️  请输入有效的数字")

    print("\n" + "=" * 80)

    # 使用基础名称，如果有标注者ID则加上ID
    if annotator_id:
        base_output_name = f"accident_cases_annotated_{annotator_id}"
    else:
        base_output_name = "accident_cases_annotated"

    output_parquet = output_dir / f"{base_output_name}.parquet"
    output_csv = output_dir / f"{base_output_name}.csv"
    progress_file = output_dir / f"{base_output_name}_progress.txt"

    # 优先从 Parquet 加载，否则从 CSV，最后从原始文件
    if output_parquet.exists():
        print(f"检测到快速加载文件，正在从 {output_parquet} 继续...")
        df = pd.read_parquet(output_parquet)
        start_index = load_progress(str(output_dir / base_output_name))
        # 确保start_index不超过总案例数
        start_index = min(start_index, len(df) - 1) if len(df) > 0 else 0
    elif output_csv.exists():
        print(f"检测到已标注的CSV文件，正在从 {output_csv} 继续...")
        df = pd.read_csv(output_csv, encoding="utf-8-sig")
        start_index = load_progress(str(output_dir / base_output_name))
        # 确保start_index不超过总案例数
        start_index = min(start_index, len(df) - 1) if len(df) > 0 else 0
    else:
        print(f"未找到标注文件，正在从原始文件 {input_file.name} 开始...")
        try:
            df = pd.read_csv(input_file, encoding="utf-8-sig")

            # 检查必需列
            if "full_text" not in df.columns:
                print("\n❗ 错误: CSV文件中缺少必需的 'full_text' 列")
                print("\n请确保原始CSV文件包含 full_text 列（案例文本）")
                print("其他列（如 title、url、date 等）为可选，程序会自动识别")
                print("\n按回车键退出...")
                input()
                return

            start_index = 0
        except Exception as e:
            print(f"读取文件失败: {e}")
            print("\n按回车键退出...")
            input()
            return

    total_cases = len(df)

    # 如果是随机模式，创建随机索引序列
    if random_mode:
        print("\n📊 随机标注模式已启用")

        # 保存/加载索引映射
        index_file = output_dir / f"{base_output_name}_random_indices.txt"
        if index_file.exists():
            # 加载已保存的随机序列
            with open(index_file, "r") as f:
                indices = list(map(int, f.read().strip().split(",")))
            # 验证索引列表长度是否匹配
            if len(indices) != total_cases:
                print(
                    f"⚠️  警告: 随机索引文件长度({len(indices)})与当前数据({total_cases})不匹配，将重新生成"
                )
                indices = list(range(total_cases))
                random.shuffle(indices)
                with open(index_file, "w") as f:
                    f.write(",".join(map(str, indices)))
        else:
            # 第一次运行，生成新的随机序列
            indices = list(range(total_cases))
            random.shuffle(indices)
            with open(index_file, "w") as f:
                f.write(",".join(map(str, indices)))
    else:
        indices = None

    # 初始化列
    if "is_construction" not in df.columns:
        df["is_construction"] = pd.NA

    # 计算实际已标注的数量（不包括跳过的）
    already_annotated = (
        (df["is_construction"].notna()) & (df["is_construction"] != -1)
    ).sum()
    total_unannotated = total_cases - already_annotated

    print(f"\n共有 {total_cases} 个案例需要标注")
    if random_mode:
        print(f"已标注: {already_annotated} 条，剩余: {total_unannotated} 条")
        print(f"(随机模式: 将从第 {start_index + 1} 个随机位置继续)")
    else:
        print(f"已标注: {already_annotated} 条，剩余: {total_unannotated} 条")
        print(f"当前将从第 {start_index + 1} 条数据开始标注\n")

    annotation_history = []
    update_history = []  # 存储模型增量用于撤销
    current_index = start_index
    annotated_count = 0  # 记录本次会话实际标注的数量

    # 加载智能提示模型
    base_output_path = str(output_dir / base_output_name)
    hint_model = load_hint_model_enhanced(base_output_path)
    # 打印关键词加载摘要
    try:
        print(get_seed_load_summary())
    except Exception:
        pass

    print("=" * 80)
    print("准备开始标注...")
    if random_mode:
        print("- 标注模式: 随机顺序")
        print(f"- 已标注: {already_annotated} 条")
        print(f"- 剩余数量: {total_unannotated} 条")
    else:
        print("- 标注模式: 顺序标注")
        print(f"- 已标注: {already_annotated} 条")
        print(f"- 起始位置: 第 {start_index + 1} 条数据")
        print(f"- 剩余数量: {total_unannotated} 条")
    print("=" * 80)
    print("\n按回车键开始...")
    input()

    try:
        while current_index < total_cases:
            # 如果是随机模式，使用随机索引
            actual_index = indices[current_index] if indices else current_index

            # 检查是否已标注（非空且不等于-1表示已标注）
            if (
                pd.notna(df.loc[actual_index, "is_construction"])
                and df.loc[actual_index, "is_construction"] != -1
            ):
                # 已标注，自动跳过
                current_index += 1
                continue

            row = df.iloc[actual_index]
            display_case(row, current_index, total_cases, random_mode)

            # 智能提示（非建筑业概率）
            try:
                feats = extract_features_enhanced(hint_model, row)
                prob, contrib = predict_non_construction_proba_enhanced(
                    hint_model, feats
                )
                print(format_hint_line(prob, contrib))
            except Exception:
                feats = None

            # 显示是否之前被跳过
            if (
                pd.notna(df.loc[actual_index, "is_construction"])
                and df.loc[actual_index, "is_construction"] == -1
            ):
                print("\n[此案例之前被跳过]")

            user_input = get_user_input()

            if user_input == "1":
                df.loc[actual_index, "is_construction"] = 1
                print("✓ 已标注为: 建筑业案例")
                annotation_history.append(actual_index)
                # 在线更新（建筑业=0 -> 非建筑业概率应降低）
                if feats is not None:
                    lr_delta = update_model_online_enhanced(
                        hint_model, row, feats, label_non_construction=0
                    )
                    tok_delta = update_token_stats(
                        hint_model, row, label_non_construction=0
                    )
                    new_feats = maybe_expand_features(hint_model)
                    update_history.append(
                        {"lr": lr_delta, "tok": tok_delta, "new": new_feats}
                    )
                else:
                    update_history.append(None)
                current_index += 1
                annotated_count += 1
            elif user_input == "0":
                df.loc[actual_index, "is_construction"] = 0
                annotation_history.append(actual_index)
                print("✓ 已标注为: 非建筑业案例")
                # 在线更新（非建筑业=1 -> 非建筑业概率应升高）
                if feats is not None:
                    lr_delta = update_model_online_enhanced(
                        hint_model, row, feats, label_non_construction=1
                    )
                    tok_delta = update_token_stats(
                        hint_model, row, label_non_construction=1
                    )
                    new_feats = maybe_expand_features(hint_model)
                    update_history.append(
                        {"lr": lr_delta, "tok": tok_delta, "new": new_feats}
                    )
                else:
                    update_history.append(None)
                current_index += 1
                annotated_count += 1
            elif user_input in ["s", "skip"]:
                df.loc[actual_index, "is_construction"] = -1
                annotation_history.append(actual_index)
                print("⊘ 已跳过此案例")
                update_history.append(None)
                current_index += 1
                annotated_count += 1
            elif user_input in ["u", "undo"]:
                if annotation_history:
                    last_actual_index = annotation_history.pop()
                    # 清理相关列
                    df.loc[last_actual_index, "is_construction"] = pd.NA
                    print("↶ 已撤销上一个标注")
                    annotated_count = max(0, annotated_count - 1)

                    # 撤销上一次模型更新
                    if update_history:
                        last_delta = update_history.pop()
                        try:
                            if last_delta:
                                if isinstance(last_delta, dict) and "lr" in last_delta:
                                    rollback_update(
                                        hint_model, last_delta.get("lr", {})
                                    )
                                    rollback_token_stats(
                                        hint_model, last_delta.get("tok", {})
                                    )
                                    remove_learned_features(
                                        hint_model, last_delta.get("new", [])
                                    )
                                else:
                                    rollback_update(hint_model, last_delta)
                        except Exception:
                            pass

                    # 在随机模式下，需要找到last_actual_index在indices中的位置
                    if indices:
                        try:
                            # 找到上一个标注案例在随机序列中的位置
                            last_position = indices.index(last_actual_index)
                            current_index = last_position
                        except ValueError:
                            # 如果找不到，保持当前位置不变
                            pass
                    else:
                        # 顺序模式下，直接回退到该索引
                        current_index = last_actual_index
                else:
                    print("⚠ 没有可以撤销的标注")
            elif user_input in ["q", "quit"]:
                print("\n正在保存并退出...")
                save_progress(df, str(output_dir / base_output_name), current_index)
                return

            # 每实际标注10个案例自动保存（不包括自动跳过的）
            if annotated_count > 0 and annotated_count % 10 == 0:
                save_progress(df, str(output_dir / base_output_name), current_index)
                # 同步保存模型
                try:
                    save_hint_model_enhanced(base_output_path, hint_model)
                except Exception:
                    pass

        clear_screen()
        print("🎉 恭喜！所有案例标注完成！")
        save_progress(df, str(output_dir / base_output_name), current_index)
        try:
            save_hint_model_enhanced(base_output_path, hint_model)
        except Exception:
            pass

        if progress_file.exists():
            progress_file.unlink()

    except (KeyboardInterrupt, Exception) as e:
        print(f"\n\n操作中断或发生错误: {e}")
        print("正在紧急保存进度...")
        save_progress(df, str(output_dir / base_output_name), current_index)
        try:
            save_hint_model_enhanced(base_output_path, hint_model)
        except Exception:
            pass


if __name__ == "__main__":
    main()
