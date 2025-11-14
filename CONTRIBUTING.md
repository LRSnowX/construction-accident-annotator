# 贡献指南

感谢你对建筑业事故案例标注工具的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug

如果你发现了 bug，请在 [Issues](https://github.com/LRSnowX/construction-accident-annotator/issues) 页面创建一个新的 issue，并包含以下信息：

- **清晰的标题**：简要描述问题
- **详细描述**：说明问题是什么，预期行为是什么
- **复现步骤**：详细的步骤，让其他人能够重现问题
- **系统环境**：操作系统、Python 版本等
- **错误信息**：完整的错误日志或截图

### 提出新功能

如果你有新功能的想法：

1. 先在 Issues 中搜索，确保该功能还未被提出
2. 创建一个新的 Feature Request issue
3. 详细描述功能需求和使用场景
4. 如果可能，提供实现思路

### 提交代码

1. **Fork 项目**

   点击右上角的 Fork 按钮，将项目 fork 到你的账号下。

2. **克隆到本地**

   ```bash
   git clone https://github.com/你的用户名/construction-accident-annotator.git
   cd construction-accident-annotator
   ```

3. **创建分支**

   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

4. **进行开发**

   - 保持代码风格一致
   - 添加必要的注释
   - 如果修改了功能，请更新文档

5. **测试**

   确保你的修改没有破坏现有功能：

   ```bash
   python -m py_compile *.py
   # 测试基本功能
   python main.py
   ```

6. **提交更改**

   ```bash
   git add .
   git commit -m "feat: 添加了某某功能"
   # 或
   git commit -m "fix: 修复了某某问题"
   ```

   提交信息格式建议：
   - `feat:` 新功能
   - `fix:` 修复 bug
   - `docs:` 文档更新
   - `style:` 代码格式调整
   - `refactor:` 代码重构
   - `test:` 测试相关
   - `chore:` 构建或辅助工具的变动

7. **推送到远程**

   ```bash
   git push origin feature/your-feature-name
   ```

8. **创建 Pull Request**

   - 前往你 fork 的仓库页面
   - 点击 "New Pull Request"
   - 填写 PR 的标题和描述
   - 说明你做了什么改动，为什么要做这个改动

## 代码规范

### Python 代码风格

- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 函数和类需要添加文档字符串
- 变量名使用小写字母和下划线
- 类名使用驼峰命名法

### 文档

- 所有新功能都需要在 README.md 中更新说明
- 复杂的功能需要在代码中添加详细注释
- 如有必要，更新快速入门.md

## 开发环境设置

1. **安装依赖**

   ```bash
   # 使用 uv（推荐）
   uv sync

   # 或使用 pip
   pip install -e .
   ```

2. **运行测试**

   ```bash
   python main.py
   ```

## 问题讨论

如果你有任何疑问：

- 查看 [Issues](https://github.com/LRSnowX/construction-accident-annotator/issues) 看是否有类似问题
- 在 Issue 中提问
- 直接在 Pull Request 中讨论

## 行为准则

请注意，我们希望所有贡献者：

- 保持友好和尊重
- 乐于接受建设性的批评
- 关注对项目和社区最有利的事情
- 对其他社区成员表现出同理心

## 许可协议

当你提交代码时，即表示你同意将你的贡献以 MIT 许可证开源。

---

再次感谢你的贡献！ 🎉
