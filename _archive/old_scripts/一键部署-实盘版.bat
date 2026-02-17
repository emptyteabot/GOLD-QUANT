@echo off
chcp 65001 >nul
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║     🏆 黄金实盘预警系统 - 一键部署脚本                    ║
echo ║     Live Gold Trading System - Auto Setup                ║
echo ║                                                           ║
echo ║     ⚡ 提前5-30秒预警 + 真金白银实盘                      ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM ============================================================
REM 第一步: 检查 Python
REM ============================================================
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 📦 步骤 1/6: 检查 Python 环境
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未检测到 Python
    echo.
    echo 💡 请先安装 Python 3.10+
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python 已安装: %PYTHON_VERSION%
echo.

REM ============================================================
REM 第二步: 安装依赖
REM ============================================================
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 📦 步骤 2/6: 安装依赖包
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

python -c "import ccxt" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包，请稍候...
    echo.
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo.
        echo ⚠️  使用清华镜像失败，尝试官方源...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo ❌ 依赖安装失败
            pause
            exit /b 1
        )
    )
    echo.
    echo ✅ 依赖安装完成
) else (
    echo ✅ 依赖已安装，跳过
)
echo.

REM ============================================================
REM 第三步: 配置微信推送
REM ============================================================
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 📱 步骤 3/6: 配置微信推送
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

if not exist .env (
    echo 📝 创建配置文件...
    copy env.ultimate.example .env >nul
    echo ✅ 已创建 .env 配置文件
    echo.
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo 🔑 重要: 需要配置微信推送
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo.
    echo 📱 方式1: PushPlus (推荐，最简单)
    echo    1. 用手机浏览器访问: https://www.pushplus.plus/
    echo    2. 微信扫码登录
    echo    3. 复制你的 Token
    echo    4. 在 .env 文件中填入: PUSHPLUS_TOKEN=你的token
    echo.
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo.
    echo 按任意键打开配置文件进行编辑...
    pause >nul
    notepad .env
    echo.
    echo 配置完成后，按任意键继续...
    pause >nul
) else (
    echo ✅ 配置文件已存在
    echo.
    echo 是否需要重新配置？
    echo [1] 是，重新配置
    echo [2] 否，使用现有配置
    echo.
    set /p reconfig="请选择 (1/2): "
    
    if "%reconfig%"=="1" (
        notepad .env
        echo.
        echo 配置完成后，按任意键继续...
        pause >nul
    )
)
echo.

REM ============================================================
REM 第四步: 测试微信推送
REM ============================================================
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 🧪 步骤 4/6: 测试微信推送
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

echo 📤 发送测试消息到微信...
python -c "import asyncio; from wechat_notifier import notifier; asyncio.run(notifier.send_alert('🧪 测试消息', '如果你收到这条消息，说明配置成功！\n\n系统已准备就绪，可以开始实盘监控。', 'info'))"

if errorlevel 1 (
    echo.
    echo ❌ 微信推送测试失败
    echo.
    echo 💡 可能原因:
    echo    1. PUSHPLUS_TOKEN 未配置或错误
    echo    2. 网络连接问题
    echo    3. PushPlus 服务异常
    echo.
    echo 是否继续？
    echo [1] 是，继续部署 (不推荐)
    echo [2] 否，退出并检查配置
    echo.
    set /p continue_choice="请选择 (1/2): "
    
    if "%continue_choice%"=="2" (
        echo.
        echo 💡 请检查 .env 文件中的 PUSHPLUS_TOKEN 配置
        pause
        exit /b 1
    )
) else (
    echo.
    echo ✅ 微信推送测试成功！
    echo 💡 请检查你的微信是否收到测试消息
    echo.
    pause
)
echo.

REM ============================================================
REM 第五步: 测试领先指标
REM ============================================================
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 🧪 步骤 5/6: 测试领先指标监控
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

echo 📊 测试美元指数、订单簿、VIX...
python leading_indicators.py

if errorlevel 1 (
    echo.
    echo ⚠️  领先指标测试失败
    echo 💡 可能原因: 网络无法访问 Binance
    echo.
    echo 是否继续？
    echo [1] 是，继续部署
    echo [2] 否，退出
    echo.
    set /p continue_choice2="请选择 (1/2): "
    
    if "%continue_choice2%"=="2" (
        pause
        exit /b 1
    )
) else (
    echo.
    echo ✅ 领先指标测试成功！
)
echo.

REM ============================================================
REM 第六步: 启动系统
REM ============================================================
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 🚀 步骤 6/6: 启动实盘系统
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

echo ⚠️  重要提示:
echo.
echo 这是真金白银的实盘系统，请确认:
echo.
echo ✅ 已完成微信推送测试
echo ✅ 已了解系统的风险控制规则
echo ✅ 已设置合理的初始资金 (建议不超过总资产的10%%)
echo ✅ 已准备好接受可能的亏损
echo.
echo 系统配置:
echo   • 最大仓位: 30%%
echo   • 单笔止损: 2%%
echo   • 单日止损: 5%%
echo.
echo 监控指标:
echo   • 领先指标 (提前5-30秒): DXY/订单簿/VIX
echo   • 实时指标: 黄金价格/技术指标
echo   • 舆情指标: 推特/新闻
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 选择运行模式:
echo [1] 前台运行 (测试用，可以看到实时日志)
echo [2] 后台运行 (实盘用，不占用窗口)
echo [3] 退出
echo.
set /p run_mode="请选择 (1/2/3): "

if "%run_mode%"=="1" (
    echo.
    echo 🚀 正在启动实盘系统 (前台模式)...
    echo ⚠️  按 Ctrl+C 可随时停止
    echo.
    python main_live.py
) else if "%run_mode%"=="2" (
    echo.
    echo 🚀 正在启动实盘系统 (后台模式)...
    echo.
    start /B pythonw main_live.py
    echo ✅ 系统已在后台启动
    echo.
    echo 💡 提示:
    echo    • 系统会持续运行，即使关闭此窗口
    echo    • 所有预警会推送到你的微信
    echo    • 如需停止，运行: taskkill /F /IM pythonw.exe
    echo.
    pause
) else if "%run_mode%"=="3" (
    echo.
    echo 👋 再见！
    exit /b 0
) else (
    echo.
    echo ❌ 无效选择
    pause
    exit /b 1
)

echo.
echo ✅ 部署完成！
echo.
pause




