#!/bin/bash

# 建筑业事故案例标注工具 - 启动脚本
# 双击此文件即可启动程序

# 获取脚本所在目录（即项目根目录）
cd "$(dirname "$0")"

# 打印欢迎信息
clear
echo "=================================="
echo "  建筑业事故案例标注工具"
echo "=================================="
echo ""
echo "正在启动程序..."
echo ""

# 检查虚拟环境是否存在
if [ -d ".venv" ]; then
    echo "✓ 检测到虚拟环境"
    source .venv/bin/activate
else
    echo "⚠️  未检测到虚拟环境，使用系统Python"
fi

# 检查Python是否可用
if ! command -v python &> /dev/null; then
    echo ""
    echo "❌ 错误: 未找到Python"
    echo "请先安装Python 3.8或更高版本"
    echo ""
    read -p "按回车键退出..."
    exit 1
fi

# 检查依赖
echo "✓ 检查依赖包..."
python -c "import pandas, pyarrow" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  检测到缺少依赖包，正在安装..."
    pip install pandas pyarrow
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ 依赖安装失败"
        echo ""
        read -p "按回车键退出..."
        exit 1
    fi
fi

# 检查原始数据文件
if [ ! -d "data/raw" ] || [ -z "$(ls -A data/raw/*.csv 2>/dev/null)" ]; then
    echo ""
    echo "❌ 错误: 未找到原始数据文件"
    echo "请将CSV文件放在 data/raw/ 目录下"
    echo ""
    read -p "按回车键退出..."
    exit 1
fi

echo "✓ 所有检查通过"
echo ""
echo "=================================="
echo ""

# 运行主程序
python main.py

# 程序结束后的提示
echo ""
echo "=================================="
echo "✅ 程序已结束，所有数据已保存"
echo "🔒 现在可以安全地关闭此终端窗口了"
echo "=================================="
echo ""
read -p "按回车键退出..."
