@echo off
chcp 65001 >nul
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║     🏆 黄金崩盘预警系统 - 终极版一键启动                  ║
echo ║     Ultimate Gold Sentinel - Auto Setup                  ║
echo ║                                                           ║
echo ║     ⚡ Grok AI + 🐦 推特监控 + 📱 微信推送               ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未检测到 Python
    echo.
    echo 💡 请先安装 Python 3.10+
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python 已安装
echo.

REM 步骤1: 安装依赖
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 📦 步骤 1/4: 安装依赖包
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

REM 步骤2: 配置文件
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ⚙️  步骤 2/4: 配置系统
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

if not exist .env (
    echo 📝 创建配置文件...
    copy env.ultimate.example .env >nul
    echo.
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
    echo 📱 方式2: Server酱 (备选)
    echo    1. 访问: https://sct.ftqq.com/
    echo    2. 微信扫码登录
    echo    3. 复制 SendKey
    echo    4. 在 .env 文件中填入: SERVERCHAN_KEY=你的key
    echo    5. 在 .env 中设置: PUSH_METHOD=serverchan
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
)
echo.

REM 步骤3: 测试配置
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 🧪 步骤 3/4: 测试配置
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo [1] 运行完整测试 (推荐首次使用)
echo [2] 快速测试微信推送
echo [3] 跳过测试，直接启动
echo.
set /p test_choice="请选择 (1/2/3): "

if "%test_choice%"=="1" (
    echo.
    echo 🧪 运行完整测试...
    echo.
    python test_ultimate.py
    echo.
    echo 测试完成！按任意键继续...
    pause >nul
) else if "%test_choice%"=="2" (
    echo.
    echo 📱 测试微信推送...
    python -c "import asyncio; from wechat_notifier import notifier; asyncio.run(notifier.send_alert('测试消息', '如果你收到这条消息，说明配置成功！', 'info'))"
    echo.
    echo 请检查你的微信是否收到测试消息
    echo.
    pause
)

REM 步骤4: 启动系统
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 🚀 步骤 4/4: 启动系统
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo ⚠️  系统即将启动，按 Ctrl+C 可随时停止
echo.
echo 💡 提示:
echo    • 系统会在后台持续监控
echo    • 有异常情况会推送到你的微信
echo    • 建议在服务器或24小时开机的电脑上运行
echo.
pause

echo.
echo 🚀 正在启动终极版黄金预警系统...
echo.

python main_ultimate.py

if errorlevel 1 (
    echo.
    echo ❌ 系统运行出错
    echo.
    echo 💡 常见问题:
    echo    1. 检查 .env 配置是否正确
    echo    2. 确认网络可以访问 Binance 和 Grok API
    echo    3. 验证微信推送 Token 是否有效
    echo.
    pause
    exit /b 1
)

pause




