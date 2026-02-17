@echo off
chcp 65001 >nul
cls
echo.
echo ========================================================
echo    黄金实盘预警系统 - 快速启动
echo    Live Gold Trading System
echo ========================================================
echo.

REM 检查 Python
echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python
    echo 请先安装 Python 3.10+
    pause
    exit /b 1
)
echo [成功] Python 已安装
echo.

REM 检查依赖
echo [2/5] 检查依赖包...
python -c "import ccxt" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        pip install -r requirements.txt
    )
    echo [成功] 依赖安装完成
) else (
    echo [成功] 依赖已安装
)
echo.

REM 检查配置文件
echo [3/5] 检查配置文件...
if not exist .env (
    echo [警告] 未找到 .env 文件
    echo 正在创建配置文件...
    copy env.ultimate.example .env >nul
    echo.
    echo 请配置以下内容:
    echo   1. 飞书 Webhook (必须)
    echo   2. 其他配置 (可选)
    echo.
    pause
    notepad .env
    echo.
    echo 配置完成后，按任意键继续...
    pause >nul
)
echo [成功] 配置文件已存在
echo.

REM 测试飞书推送
echo [4/5] 测试飞书推送...
python -c "import asyncio; from notifier import notifier; asyncio.run(notifier.send_alert('测试消息', '如果你在飞书收到这条消息，说明配置成功！', 'info'))" 2>nul
if errorlevel 1 (
    echo [警告] 飞书推送测试失败
    echo.
    echo 可能原因:
    echo   1. FEISHU_WEBHOOK_URL 未配置
    echo   2. 网络连接问题
    echo.
    echo 是否继续启动系统?
    echo [1] 是，继续
    echo [2] 否，退出检查配置
    echo.
    set /p continue_choice="请选择 (1/2): "
    if "%continue_choice%"=="2" (
        echo.
        echo 请检查 .env 文件中的配置
        pause
        exit /b 1
    )
) else (
    echo [成功] 飞书推送测试成功
    echo 请检查飞书是否收到测试消息
)
echo.

REM 启动系统
echo [5/5] 启动系统...
echo.
echo ========================================================
echo 选择运行模式:
echo ========================================================
echo [1] 前台运行 (推荐，可以看到实时日志)
echo [2] 后台运行 (实盘用，不占用窗口)
echo [3] 测试领先指标 (测试 DXY/订单簿/VIX)
echo [4] 退出
echo.
set /p run_mode="请选择 (1/2/3/4): "

if "%run_mode%"=="1" (
    echo.
    echo 正在启动实盘系统 (前台模式)...
    echo 按 Ctrl+C 可随时停止
    echo.
    python main_live.py
) else if "%run_mode%"=="2" (
    echo.
    echo 正在启动实盘系统 (后台模式)...
    start /B pythonw main_live.py
    echo [成功] 系统已在后台启动
    echo.
    echo 提示:
    echo   - 系统会持续运行
    echo   - 预警会推送到飞书
    echo   - 停止命令: taskkill /F /IM pythonw.exe
    echo.
    pause
) else if "%run_mode%"=="3" (
    echo.
    echo 测试领先指标监控...
    echo.
    python leading_indicators.py
    echo.
    pause
) else if "%run_mode%"=="4" (
    echo.
    echo 再见!
    exit /b 0
) else (
    echo.
    echo [错误] 无效选择
    pause
    exit /b 1
)

echo.
echo 部署完成!
pause




