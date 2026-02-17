@echo off
cls
echo.
echo ========================================================
echo    Gold Trading System - Quick Start
echo ========================================================
echo.

REM Step 1: Check Python
echo [Step 1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please install Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python installed
echo.

REM Step 2: Check dependencies
echo [Step 2/5] Checking dependencies...
python -c "import ccxt" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        pip install -r requirements.txt
    )
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies ready
)
echo.

REM Step 3: Check config
echo [Step 3/5] Checking config file...
if not exist .env (
    echo [WARNING] .env file not found
    echo Creating config file...
    copy env.ultimate.example .env >nul
    echo.
    echo Please configure:
    echo   1. Feishu Webhook (required)
    echo   2. Other settings (optional)
    echo.
    pause
    notepad .env
    echo.
    echo Press any key after configuration...
    pause >nul
)
echo [OK] Config file exists
echo.

REM Step 4: Test Feishu (skip in batch, use test_feishu.py instead)
echo [Step 4/5] Testing Feishu notification...
echo [INFO] Feishu test skipped in batch mode
echo [INFO] To test manually, run: python test_feishu.py
echo.

REM Step 5: Start system
echo [Step 5/5] Starting system...
echo.
echo ========================================================
echo Choose run mode:
echo ========================================================
echo [1] Foreground (recommended, see real-time logs)
echo [2] Background (production, no window)
echo [3] Test leading indicators (DXY/Orderbook/VIX)
echo [4] Exit
echo.
set /p run_mode="Choose (1/2/3/4): "

if "%run_mode%"=="1" (
    echo.
    echo Starting system in foreground mode...
    echo Press Ctrl+C to stop
    echo.
    python main_live.py
) else if "%run_mode%"=="2" (
    echo.
    echo Starting system in background mode...
    start /B pythonw main_live.py
    echo [OK] System started in background
    echo.
    echo Tips:
    echo   - System will keep running
    echo   - Alerts will be sent to Feishu
    echo   - Stop command: taskkill /F /IM pythonw.exe
    echo.
    pause
) else if "%run_mode%"=="3" (
    echo.
    echo Testing leading indicators...
    echo.
    python leading_indicators.py
    echo.
    pause
) else if "%run_mode%"=="4" (
    echo.
    echo Goodbye!
    exit /b 0
) else (
    echo.
    echo [ERROR] Invalid choice
    pause
    exit /b 1
)

echo.
echo Deployment complete!
pause
