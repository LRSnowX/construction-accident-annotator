# 多人协作标注指南

## 功能说明

本项目支持多人同时进行标注，通过以下机制实现：

1. **随机标注模式** - 每个标注者看到的案例顺序不同，避免重复劳动
2. **标注者ID识别** - 每个人的标注保存到独立文件
3. **智能合并工具** - 自动合并多人标注，识别冲突并标记待复议

## 使用方法

### 1. 单人标注（顺序模式）

```bash
python main.py
```

### 2. 多人协作标注（推荐）

#### 方式A：随机顺序标注

每个标注者使用不同的ID和随机模式：

```bash
# 标注者1
python main.py --random --annotator=user1

# 标注者2  
python main.py --random --annotator=user2

# 标注者3
python main.py --random --annotator=user3
```

**说明：**
- `--random`：启用随机标注模式，每次运行看到的案例顺序相同（使用固定随机种子）
- `--annotator=用户名`：指定标注者ID，生成独立的标注文件

**生成的文件：**
- `accident_cases_annotated_user1.csv` / `.parquet` - 用户1的标注结果
- `accident_cases_annotated_user2.csv` / `.parquet` - 用户2的标注结果
- `accident_cases_annotated_user3.csv` / `.parquet` - 用户3的标注结果
- `accident_cases_annotated_user1_random_seed.txt` - 随机种子
- `accident_cases_annotated_user1_random_indices.txt` - 随机索引映射

#### 方式B：分段标注

如果不使用随机模式，可以人工分配范围（需要手动管理）：

```bash
# 标注者1标注前10000条
python main.py --annotator=user1
# 手动标注到第10000条后退出

# 标注者2从源文件复制后10000条开始...
```

### 3. 合并标注结果

所有标注者完成后，使用合并工具：

```bash
python merge_annotations.py \
    accident_cases_annotated_user1.csv \
    accident_cases_annotated_user2.csv \
    accident_cases_annotated_user3.csv \
    -o final_merged_result.csv
```

**输出文件：**
- `final_merged_result.csv` - 合并后的CSV文件（人工审查用）
- `final_merged_result.parquet` - 合并后的Parquet文件（快速加载用）
- `final_merged_result_conflicts.csv` - 冲突案例列表（需要复议）

**合并规则：**

1. **是否建筑业判断**
   - 所有标注者一致 → 采用该结果
   - 存在不一致 → 标记为冲突，`is_construction_conflict = True`

2. **分类代码判断**
   - 所有标注者代码一致 → 采用该代码
   - 存在不一致 → 标记为冲突，`code_conflict = True`

3. **新增字段**
   - `annotation_count`：有多少人标注了该条
   - `is_construction_conflict`：是否建筑业判断是否有冲突
   - `code_conflict`：分类代码是否有冲突
   - `annotators`：标注者ID列表（如 "A1,A2,A3"）

### 4. 处理冲突案例

打开 `final_merged_result_conflicts.csv`，可以看到所有需要复议的案例。

**复议流程：**
1. 组织标注者一起review冲突案例
2. 讨论并达成一致
3. 手动修改 `final_merged_result.csv` 中的对应记录
4. 将 `is_construction_conflict` 和 `code_conflict` 改为 `False`

## 工作流程示例

### 场景：3人协作标注30000条数据

```bash
# === 第一阶段：分配任务 ===
# 每人在各自电脑上运行（使用相同的源文件）

# 张三的电脑
python main.py --random --annotator=zhangsan

# 李四的电脑  
python main.py --random --annotator=lisi

# 王五的电脑
python main.py --random --annotator=wangwu

# === 第二阶段：标注工作 ===
# 每人标注约10000条，随时可以退出和继续
# 程序会自动保存进度，下次启动继续

# === 第三阶段：收集结果 ===
# 将三个人的标注文件收集到一起：
# - accident_cases_annotated_zhangsan.csv
# - accident_cases_annotated_lisi.csv
# - accident_cases_annotated_wangwu.csv

# === 第四阶段：合并 ===
python merge_annotations.py \
    accident_cases_annotated_zhangsan.csv \
    accident_cases_annotated_lisi.csv \
    accident_cases_annotated_wangwu.csv \
    -o final_result.csv

# === 第五阶段：查看统计 ===
# 程序会输出：
# - 总案例数
# - 已标注案例数  
# - 冲突数量
# - 标注一致率

# === 第六阶段：处理冲突 ===
# 打开 final_result_conflicts.csv
# 组织团队复议并修改 final_result.csv
```

## 注意事项

1. **随机种子固定**：每个标注者的随机序列是固定的，中途退出后重新开始会继续相同的顺序
2. **文件备份**：定期备份标注文件，防止意外丢失
3. **进度同步**：无需等所有人标注完成，随时可以进行部分合并
4. **冲突率监控**：如果冲突率过高（>20%），建议重新培训标注规则

## 高级用法

### 查看随机顺序

如果需要查看某个标注者的随机顺序：

```bash
cat accident_cases_annotated_user1_random_indices.txt
# 输出：3,1,4,1,5,9,2,6,5,3,5...（索引序列）
```

### 恢复顺序标注

如果想要重新开始顺序标注（不使用随机模式）：

```bash
# 删除旧文件
rm accident_cases_annotated.csv accident_cases_annotated.parquet
rm accident_cases_annotated_progress.txt

# 重新开始
python main.py
```

### 继续他人的标注

```bash
# 以user1的身份继续标注
python main.py --random --annotator=user1
# 程序会自动加载之前的进度
```
