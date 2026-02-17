@echo off
REM AURUM测试运行脚本 (Windows)

echo ========================================
echo AURUM 测试系统
echo ========================================
echo.

if "%1"=="" (
    echo 用法:
    echo   run_tests.bat all              # 运行所有测试
    echo   run_tests.bat unit             # 运行单元测试
    echo   run_tests.bat integration      # 运行集成测试
    echo   run_tests.bat performance      # 运行性能测试
    echo   run_tests.bat security         # 运行安全测试
    echo   run_tests.bat coverage         # 运行测试并生成覆盖率
    goto :eof
)

REM 激活虚拟环境
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo 警告: 未找到虚拟环境
)

REM 运行测试
python run_tests.py %1

echo.
echo ========================================
echo 测试完成
echo ========================================
