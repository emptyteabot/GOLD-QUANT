@echo off
cls
echo.
echo ========================================================
echo    Installing Dependencies
echo ========================================================
echo.

echo [Step 1/3] Installing Python packages...
echo.

REM 使用清华镜像加速
pip install tweepy -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo Trying default pip...
    pip install tweepy
)

echo.
echo [Step 2/3] Installing all requirements...
echo.

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo Trying default pip...
    pip install -r requirements.txt
)

echo.
echo [Step 3/3] Verifying installation...
echo.

python -c "import tweepy; print('[OK] tweepy installed')"
python -c "import ccxt; print('[OK] ccxt installed')"
python -c "import aiohttp; print('[OK] aiohttp installed')"
python -c "import openai; print('[OK] openai installed')"

echo.
echo ========================================================
echo Installation complete!
echo ========================================================
echo.
echo Next step: Run start.bat
echo.
pause




