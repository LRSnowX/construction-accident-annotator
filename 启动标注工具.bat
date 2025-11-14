@echo off
chcp 65001 >nul
title 建筑业事故案例标注工具

REM 切换到脚本所在目录
cd /d "%~dp0"

cls
echo ==================================
echo   建筑业事故案例标注工具
echo ==================================
echo.
echo 正在启动程序...
echo.

REM 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo ✓ 检测到虚拟环境
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  未检测到虚拟环境，使用系统Python
)

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ 错误: 未找到Python
    echo 请先安装Python 3.8或更高版本
    echo.
    pause
    exit /b 1
)

REM 检查依赖
echo ✓ 检查依赖包...
python -c "import pandas, pyarrow" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  检测到缺少依赖包，正在安装...
    pip install pandas pyarrow
    if errorlevel 1 (
        echo.
        echo ❌ 依赖安装失败
        echo.
        pause
        exit /b 1
    )
)

REM 检查原始数据文件
if not exist "data\raw\*.csv" (
    echo.
    echo ❌ 错误: 未找到原始数据文件
    echo 请将CSV文件放在 data\raw\ 目录下
    echo.
    pause
    exit /b 1
)

echo ✓ 所有检查通过
echo.
echo ==================================
echo.

REM 运行主程序
python main.py

REM 程序结束后的提示
echo.
echo ==================================
echo ✅ 程序已结束，所有数据已保存
echo 🔒 现在可以安全地关闭此窗口了
echo ==================================
echo.
pause
