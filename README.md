# 建筑业事故案例标注工具

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)

**一个简单易用的建筑业事故案例人工标注工具**

[快速开始](#-快速开始) • [功能特点](#-功能特点) • [使用文档](#-使用文档) • [多人协作](#-多人协作) • [贡献指南](#-贡献指南)

</div>

---

## 📖 简介

建筑业事故案例标注工具是一个交互式命令行应用，专为人工标注事故案例数据集而设计。它帮助研究人员和数据标注员快速、准确地标注事故案例是否属于建筑业范畴，支持断点续传、多人协作等功能。

### 适用场景

- 建筑安全研究的数据集构建
- 事故案例分类与分析
- 机器学习训练数据准备
- 行业数据清洗与标注

## ✨ 功能特点

- 🖥️ **零代码上手**: 双击启动脚本即可使用，无需编程知识
- 🎯 **交互式标注**: 逐条显示案例全文，支持快速单键标注
- 💾 **断点续传**: 自动保存进度，随时暂停和继续
- ↶ **撤销功能**: 支持撤销上一个标注，避免误操作
- ⊘ **跳过功能**: 不确定的案例可以先跳过
- 📊 **实时统计**: 显示标注进度和统计信息
- 🔄 **自动保存**: 每标注10个案例自动保存
- 🎲 **随机模式**: 支持随机顺序标注，避免多人协作冲突
- 👥 **多人协作**: 不同标注者独立文件，支持后期合并
- 📁 **智能检测**: 自动检测并选择CSV文件
- 📈 **双格式输出**: CSV（人工审查）+ Parquet（快速加载）

## 🚀 快速开始

### 系统要求

- Python 3.8 或更高版本
- macOS / Windows / Linux

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/LRSnowX/construction-accident-annotator.git
cd construction-accident-annotator
```

2. **安装依赖**

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install pandas pyarrow
```

3. **准备数据**

将CSV数据文件放在 `data/raw/` 目录下。

**CSV文件必须包含以下列**：
- `full_text` (必需): 事故案例的完整文本内容

4. **启动程序**

**方式一：双击启动（推荐，适合非程序员）**

- **macOS/Linux**: 双击 `启动标注工具.command`
- **Windows**: 双击 `启动标注工具.bat`

**方式二：命令行启动**

```bash
python main.py
```

## 📂 项目结构

```
construction-accident-annotator/
├── data/
│   ├── raw/                    # 原始数据文件（放置CSV文件）
│   └── annotated/              # 标注输出文件
├── main.py                     # 主程序
├── utils.py                    # 工具函数
├── merge_annotations.py        # 多人标注合并工具
├── 启动标注工具.command        # macOS/Linux启动脚本
├── 启动标注工具.bat            # Windows启动脚本
├── README.md                   # 本文档
├── 快速入门.md                 # 新手指南
├── GB-T4757-2017.md           # 建筑业分类国家标准参考
└── pyproject.toml             # 项目依赖配置
```

## 📝 使用文档

### 标注流程

1. **启动程序**后，按提示输入用户名和选择模式
2. **选择CSV文件**（如有多个）
3. **开始标注**：程序逐条显示案例

### 操作指南

### 建筑业范围参考

如果不确定某个案例是否属于建筑业，可以参考项目中的 **`GB-T4757-2017.md`** 文件，该文件包含了国家标准《国民经济行业分类》（GB/T 4754-2017）中建筑业的详细分类：

- **房屋建筑业**：住宅、体育场馆等建筑
- **土木工程建筑业**：道路、桥梁、隧道、管道、电力工程等
- **建筑安装业**：电气安装、管道设备安装等
- **建筑装饰装修业**：装饰、装修、拆除等

**简单判断标准**：凡是涉及建筑施工、安装、装修的事故都属于建筑业。

### 标注选项

| 按键 | 功能 | 说明 |
|------|------|------|
| `1` | 建筑业案例 | 确认该案例属于建筑业 |
| `0` | 非建筑业案例 | 确认该案例不属于建筑业 |
| `s` | 跳过 | 暂时不确定，跳过此案例 |
| `u` | 撤销 | 撤销上一个标注 |
| `q` | 退出 | 保存并退出程序 |

### 输出文件

标注结果保存在 `data/annotated/` 目录：

```
data/annotated/
├── accident_cases_annotated_[用户名].csv        # CSV格式（可用Excel打开）
├── accident_cases_annotated_[用户名].parquet    # Parquet格式（快速加载）
├── accident_cases_annotated_[用户名]_progress.txt    # 进度记录
├── accident_cases_annotated_[用户名]_random_seed.txt  # 随机种子
└── accident_cases_annotated_[用户名]_random_indices.txt # 随机索引
```

**标注字段**：
- `is_construction`: 标注结果
  - `1`: 建筑业案例
  - `0`: 非建筑业案例
  - `-1`: 跳过的案例
  - 空值: 未标注

## 👥 多人协作

### 分工标注

1. 每个标注者使用不同的用户名运行程序
2. **建议启用随机模式**，避免标注相同的案例
3. 各自独立标注，互不干扰

### 合并标注结果

使用 `merge_annotations.py` 合并多人标注：

```bash
python merge_annotations.py \
    data/annotated/accident_cases_annotated_张三.csv \
    data/annotated/accident_cases_annotated_李四.csv \
    data/annotated/accident_cases_annotated_王五.csv \
    -o data/annotated/merged_result.csv
```

**输出文件**：
- `merged_result.csv`: 合并后的标注结果
- `merged_result.parquet`: Parquet格式
- `merged_result_conflicts.csv`: 冲突案例（需要复议）

**合并统计**：
```
================================================================================
合并完成！统计信息：
================================================================================
总案例数:         29875
已标注案例数:     15000
是否建筑业冲突:   120
标注一致率:       99.20%
================================================================================
```

## 🔧 高级功能

### 随机标注模式

适用于多人协作场景，避免标注冲突：

```bash
# 启动时选择 'y' 启用随机模式
# 或命令行方式（已废弃，现改为交互式）
```

**特点**：
- 使用固定随机种子，确保可重现
- 每个标注者看到的案例顺序不同
- 进度文件独立，互不影响

### 断点续传

程序会自动保存进度：
- 每标注10个案例自动保存
- 按 `q` 退出时保存
- 异常中断时紧急保存

下次启动自动从上次位置继续。

## 📊 数据统计

程序会实时显示：
- 已标注数量
- 已跳过数量
- 未处理数量
- 总案例数

每次保存时自动输出统计信息。

## ❓ 常见问题

<details>
<summary><b>如何修改已标注的数据？</b></summary>

可以直接编辑 `data/annotated/*.csv` 文件，或使用 `u` 键撤销最近的标注。
</details>

<details>
<summary><b>程序崩溃了，数据会丢失吗？</b></summary>

不会。程序有异常处理机制，会在崩溃前紧急保存数据。
</details>

<details>
<summary><b>可以暂停标注吗？</b></summary>

可以。按 `q` 退出，进度会自动保存，下次继续。
</details>

<details>
<summary><b>CSV文件必须是特定格式吗？</b></summary>

只需包含 `full_text` 列即可。建议包含 `title`、`url` 等字段以获得更好体验。
</details>

<details>
<summary><b>多人标注时如何避免冲突？</b></summary>

启用随机模式，每个人看到的案例顺序不同，大大降低冲突概率。
</details>

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 贡献方式

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 报告问题

如遇到问题，请在 [Issues](https://github.com/LRSnowX/construction-accident-annotator/issues) 页面提交，包含：
- 问题描述
- 复现步骤
- 错误信息/截图
- 系统环境（OS、Python版本）

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 感谢所有贡献者的付出
- 建筑业分类标准来源于国家标准 GB/T 4754-2017

## 📮 联系方式

- 项目主页：[https://github.com/LRSnowX/construction-accident-annotator](https://github.com/LRSnowX/construction-accident-annotator)
- 问题反馈：[Issues](https://github.com/LRSnowX/construction-accident-annotator/issues)

---

<div align="center">
如果这个项目对你有帮助，请给个 ⭐️ Star 支持一下！
</div>

### 标注选项

- **输入 `1`**: 标注为建筑业案例
- **输入 `0`**: 标注为非建筑业案例
- **输入 `s`**: 跳过此案例（暂时不确定）
- **输入 `u`**: 撤销上一个标注
- **输入 `q`**: 保存并退出

输入后自动进入下一个案例，无需按回车键。

## 输出文件

标注结果会保存在 `data/annotated/` 目录下：

- **accident_cases_annotated_[用户名].csv**: 人工审查用CSV文件
- **accident_cases_annotated_[用户名].parquet**: 快速加载用Parquet文件
- **accident_cases_annotated_[用户名]_progress.txt**: 进度记录
- **accident_cases_annotated_[用户名]_random_seed.txt**: 随机种子（随机模式）
- **accident_cases_annotated_[用户名]_random_indices.txt**: 随机索引映射（随机模式）

### 标注结果字段

CSV文件包含原始数据的所有列，外加：
- **is_construction**: 标注结果
  - `1`: 建筑业案例
  - `0`: 非建筑业案例
  - `-1`: 跳过的案例
  - 空值: 未标注

## 多人协作

### 分工标注

1. 每个标注者使用不同的用户名运行程序
2. 建议启用随机模式，避免标注相同的案例
3. 各自独立标注，互不干扰

### 合并标注结果

使用 `merge_annotations.py` 合并多人标注：

```bash
python merge_annotations.py \
    data/annotated/accident_cases_annotated_张三.csv \
    data/annotated/accident_cases_annotated_李四.csv \
    data/annotated/accident_cases_annotated_王五.csv \
    -o data/annotated/merged_result.csv
```

合并后会生成：
- `merged_result.csv`: 合并结果
- `merged_result_conflicts.csv`: 冲突案例（需要复议）

## 断点续传

- 程序每标注10个案例自动保存一次
- 下次运行时自动从上次位置继续
- 可以随时按 `q` 退出，进度会被保存

## 快捷键

- **Ctrl+C**: 紧急退出并保存进度

## 示例工作流程

```
进度: 1/100
================================================================================

标题: 某建筑工地高处坠落事故
发布日期: 2025-05-06
分类: 高处坠落
URL: https://...

--------------------------------------------------------------------------------
案例全文:
--------------------------------------------------------------------------------

2025年5月6日，某工地发生高处坠落事故...

================================================================================

请标注此案例:
  1 - 建筑业案例
  0 - 非建筑业案例
  s - 跳过此案例
  u - 撤销上一个标注
  q - 保存并退出

请输入: 1
✓ 已标注为: 建筑业案例
```

## 注意事项

1. 建议定期保存（程序会每10条自动保存）
2. 不确定的案例可以先跳过，后续再处理
3. 标注完成后会显示统计信息
4. 输出文件会覆盖同名文件，请注意备份

## 技术栈

- Python 3.14+
- pandas 2.3.3+