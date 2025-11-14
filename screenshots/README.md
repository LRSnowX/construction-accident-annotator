# 截图指南

为了让项目更加生动，建议在上传到 GitHub 后添加一些截图。

## 建议添加的截图

### 1. 启动界面
- 位置：README.md 中的"快速开始"章节
- 内容：显示程序启动后的欢迎界面和文件选择界面
- 文件名：`screenshots/startup.png`

### 2. 标注界面
- 位置：README.md 中的"使用文档"章节  
- 内容：显示案例信息和标注选项
- 文件名：`screenshots/annotation.png`

### 3. 统计信息
- 位置：README.md 中的"数据统计"章节
- 内容：显示实时统计信息
- 文件名：`screenshots/statistics.png`

### 4. 合并结果
- 位置：README.md 中的"多人协作"章节
- 内容：显示合并工具的输出结果
- 文件名：`screenshots/merge.png`

## 添加截图的步骤

1. 创建 `screenshots` 目录
   ```bash
   mkdir screenshots
   ```

2. 运行程序并截图

3. 将截图放入 `screenshots` 目录

4. 在 README.md 中添加图片引用
   ```markdown
   ![启动界面](screenshots/startup.png)
   ```

5. 更新 .gitignore（如需要）
   ```
   # 但保留示例截图
   !screenshots/*.png
   ```

## 注意事项

- 截图中不要包含敏感数据
- 确保截图清晰可读
- 图片大小控制在 500KB 以内
- 使用 PNG 格式以获得最佳质量
