@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║        🏆 XAUT暴富引擎 - 依赖安装脚本 🏆                  ║
echo ║                                                           ║
╚═══════════════════════════════════════════════════════════╝

echo.
echo [1/5] 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/5] 升级pip...
python -m pip install --upgrade pip

echo.
echo [3/5] 安装核心依赖...
pip install redis ccxt numpy aiohttp requests python-dotenv

echo.
echo [4/5] 检查Redis...
where redis-server >nul 2>&1
if errorlevel 1 (
    echo ⚠️  未检测到Redis
    echo.
    echo Redis安装方法：
    echo 1. 下载: https://github.com/tporadowski/redis/releases
    echo 2. 解压后运行: redis-server.exe
    echo.
) else (
    echo ✅ Redis已安装
)

echo.
echo [5/5] 创建配置文件...
if not exist .env (
    copy .env.template .env
    echo ✅ 已创建.env配置文件，请编辑填入真实配置
) else (
    echo ℹ️  .env文件已存在，跳过创建
)

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                    ✅ 安装完成！                          ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo 下一步：
echo 1. 编辑 .env 文件，填入飞书Webhook和交易所API
echo 2. 启动Redis: redis-server
echo 3. 运行系统: python XAUT暴富引擎.py
echo.
pause

