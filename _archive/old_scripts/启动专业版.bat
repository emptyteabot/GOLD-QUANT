@echo off
chcp 65001 >nul
cls
echo ========================================
echo 💰 黄金量化交易系统 - 专业版
echo ========================================
echo.

set PYTHON=D:\ANA\python.exe

echo 请选择操作：
echo.
echo 1. 测试数据引擎
echo 2. 测试特征工程
echo 3. 测试Dual Thrust策略
echo 4. 测试均值回归策略
echo 5. 测试风险管理
echo 6. 启动实盘交易 ⭐
echo 7. 查看系统文档
echo 8. 退出
echo.

set /p choice="请输入选项 (1-8): "

if "%choice%"=="1" (
    echo.
    echo 🧪 测试数据引擎...
    echo.
    %PYTHON% data_engine.py
) else if "%choice%"=="2" (
    echo.
    echo 🧪 测试特征工程...
    echo.
    %PYTHON% feature_engineering.py
) else if "%choice%"=="3" (
    echo.
    echo 🧪 测试Dual Thrust策略...
    echo.
    %PYTHON% strategy_dual_thrust.py
) else if "%choice%"=="4" (
    echo.
    echo 🧪 测试均值回归策略...
    echo.
    %PYTHON% strategy_mean_reversion.py
) else if "%choice%"=="5" (
    echo.
    echo 🧪 测试风险管理...
    echo.
    %PYTHON% risk_manager.py
) else if "%choice%"=="6" (
    echo.
    echo 🚀 启动实盘交易系统...
    echo.
    echo ⚠️ 警告：这是实盘系统，请确保：
    echo    1. 已完成所有测试
    echo    2. 已配置好.env文件
    echo    3. 了解所有风险
    echo.
    set /p confirm="确认启动？(Y/N): "
    if /i "%confirm%"=="Y" (
        %PYTHON% live_trader.py
    ) else (
        echo 已取消
    )
) else if "%choice%"=="7" (
    echo.
    echo 📖 打开系统文档...
    start 系统文档-专业版.md
) else if "%choice%"=="8" (
    echo 👋 再见！
    exit /b 0
) else (
    echo ❌ 无效的选项
)

echo.
pause



