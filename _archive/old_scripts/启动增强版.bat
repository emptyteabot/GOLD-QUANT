@echo off
chcp 65001 >nul
title 黄金量化交易系统 - 增强版 v2.0

color 0A
cls

echo ========================================================================
echo.
echo     ⚡ 黄金量化交易系统 - 增强版 v2.0
echo.
echo     🚀 新增功能:
echo        • LSTM价格预测
echo        • XGBoost信号分类
echo        • 在线学习
echo        • Web控制面板
echo        • 移动端API
echo        • 动量策略
echo.
echo ========================================================================
echo.

:menu
echo.
echo 请选择操作:
echo.
echo ==================== 核心功能 ====================
echo.
echo   1. 测试数据引擎
echo   2. 测试特征工程
echo   3. 测试Dual Thrust策略
echo   4. 测试均值回归策略
echo   5. 测试风险管理
echo   6. 启动实盘交易 ⭐
echo.
echo ==================== 新增功能 ====================
echo.
echo   7. 测试LSTM预测模型 🆕
echo   8. 测试XGBoost分类器 🆕
echo   9. 测试动量策略 🆕
echo   10. 启动Web控制面板 🆕
echo   11. 启动移动端API 🆕
echo.
echo ==================== 系统管理 ====================
echo.
echo   12. 查看系统文档
echo   13. 安装依赖包
echo   14. 运行完整测试
echo   0. 退出
echo.
echo ========================================================================
echo.

set /p choice=请输入选项 (0-14): 

if "%choice%"=="1" goto test_data_engine
if "%choice%"=="2" goto test_feature_engineering
if "%choice%"=="3" goto test_dual_thrust
if "%choice%"=="4" goto test_mean_reversion
if "%choice%"=="5" goto test_risk_manager
if "%choice%"=="6" goto start_live_trader
if "%choice%"=="7" goto test_ml_predictor
if "%choice%"=="8" goto test_xgboost
if "%choice%"=="9" goto test_momentum
if "%choice%"=="10" goto start_web_dashboard
if "%choice%"=="11" goto start_mobile_api
if "%choice%"=="12" goto view_docs
if "%choice%"=="13" goto install_deps
if "%choice%"=="14" goto run_all_tests
if "%choice%"=="0" goto exit

echo.
echo ❌ 无效选项，请重新输入
timeout /t 2 >nul
cls
goto menu

:test_data_engine
cls
echo ========================================================================
echo 🧪 测试数据引擎
echo ========================================================================
echo.
python data_engine.py
echo.
echo ========================================================================
pause
cls
goto menu

:test_feature_engineering
cls
echo ========================================================================
echo 🧪 测试特征工程
echo ========================================================================
echo.
python feature_engineering.py
echo.
echo ========================================================================
pause
cls
goto menu

:test_dual_thrust
cls
echo ========================================================================
echo 🧪 测试Dual Thrust策略
echo ========================================================================
echo.
python strategy_dual_thrust.py
echo.
echo ========================================================================
pause
cls
goto menu

:test_mean_reversion
cls
echo ========================================================================
echo 🧪 测试均值回归策略
echo ========================================================================
echo.
python strategy_mean_reversion.py
echo.
echo ========================================================================
pause
cls
goto menu

:test_risk_manager
cls
echo ========================================================================
echo 🧪 测试风险管理
echo ========================================================================
echo.
python risk_manager.py
echo.
echo ========================================================================
pause
cls
goto menu

:start_live_trader
cls
echo ========================================================================
echo 🚀 启动实盘交易引擎
echo ========================================================================
echo.
echo ⚠️  警告: 这是实盘交易，请确保:
echo    1. 已配置好 .env 文件
echo    2. 已充分测试各个模块
echo    3. 了解风险并做好资金管理
echo.
set /p confirm=确认启动? (Y/N): 

if /i "%confirm%"=="Y" (
    echo.
    echo 正在启动实盘交易引擎...
    echo.
    python live_trader.py
) else (
    echo.
    echo 已取消启动
    timeout /t 2 >nul
)
echo.
echo ========================================================================
pause
cls
goto menu

:test_ml_predictor
cls
echo ========================================================================
echo 🧪 测试机器学习预测模型
echo ========================================================================
echo.
echo 测试内容:
echo   • LSTM价格预测
echo   • MLP价格预测
echo   • XGBoost信号分类
echo   • 集成预测器
echo   • 在线学习
echo.
python ml_predictor.py
echo.
echo ========================================================================
pause
cls
goto menu

:test_xgboost
cls
echo ========================================================================
echo 🧪 测试XGBoost分类器
echo ========================================================================
echo.
python -c "from ml_predictor import XGBoostSignalClassifier; import numpy as np; print('XGBoost模块加载成功')"
echo.
echo ========================================================================
pause
cls
goto menu

:test_momentum
cls
echo ========================================================================
echo 🧪 测试动量策略
echo ========================================================================
echo.
python strategy_momentum.py
echo.
echo ========================================================================
pause
cls
goto menu

:start_web_dashboard
cls
echo ========================================================================
echo 🌐 启动Web控制面板
echo ========================================================================
echo.
echo 访问地址: http://localhost:5000
echo.
echo 功能:
echo   • 实时价格监控
echo   • 交易信号展示
echo   • 性能指标统计
echo   • 系统启动/停止控制
echo.
echo 按 Ctrl+C 停止服务器
echo.
python web_dashboard.py
echo.
echo ========================================================================
pause
cls
goto menu

:start_mobile_api
cls
echo ========================================================================
echo 📱 启动移动端API
echo ========================================================================
echo.
echo API地址: http://localhost:5001
echo.
echo 测试登录:
echo   用户名: admin
echo   密码: admin123
echo.
echo 按 Ctrl+C 停止服务器
echo.
python mobile_api.py
echo.
echo ========================================================================
pause
cls
goto menu

:view_docs
cls
echo ========================================================================
echo 📖 查看系统文档
echo ========================================================================
echo.
start 系统文档-专业版.md
echo.
echo 文档已在默认编辑器中打开
timeout /t 2 >nul
cls
goto menu

:install_deps
cls
echo ========================================================================
echo 📦 安装依赖包
echo ========================================================================
echo.
echo 正在安装依赖包...
echo.
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.
echo ========================================================================
echo.
echo ✅ 依赖包安装完成！
echo.
echo ⚠️  注意: 如果 ta-lib 安装失败，这是正常的
echo    系统会自动使用 pandas 实现技术指标
echo.
echo ========================================================================
pause
cls
goto menu

:run_all_tests
cls
echo ========================================================================
echo 🧪 运行完整测试
echo ========================================================================
echo.
echo 测试顺序:
echo   1. 数据引擎
echo   2. 特征工程
echo   3. Dual Thrust策略
echo   4. 均值回归策略
echo   5. 动量策略
echo   6. 风险管理
echo   7. 机器学习预测
echo.
set /p confirm=确认运行完整测试? (Y/N): 

if /i "%confirm%"=="Y" (
    echo.
    echo ========================================================================
    echo 1/7 测试数据引擎...
    echo ========================================================================
    python data_engine.py
    echo.
    
    echo ========================================================================
    echo 2/7 测试特征工程...
    echo ========================================================================
    python feature_engineering.py
    echo.
    
    echo ========================================================================
    echo 3/7 测试Dual Thrust策略...
    echo ========================================================================
    python strategy_dual_thrust.py
    echo.
    
    echo ========================================================================
    echo 4/7 测试均值回归策略...
    echo ========================================================================
    python strategy_mean_reversion.py
    echo.
    
    echo ========================================================================
    echo 5/7 测试动量策略...
    echo ========================================================================
    python strategy_momentum.py
    echo.
    
    echo ========================================================================
    echo 6/7 测试风险管理...
    echo ========================================================================
    python risk_manager.py
    echo.
    
    echo ========================================================================
    echo 7/7 测试机器学习预测...
    echo ========================================================================
    python ml_predictor.py
    echo.
    
    echo ========================================================================
    echo ✅ 所有测试完成！
    echo ========================================================================
) else (
    echo.
    echo 已取消测试
    timeout /t 2 >nul
)
echo.
pause
cls
goto menu

:exit
cls
echo.
echo ========================================================================
echo.
echo     👋 感谢使用黄金量化交易系统！
echo.
echo     💡 提示:
echo        • 记得定期备份数据
echo        • 严格执行风险管理
echo        • 持续优化策略参数
echo.
echo ========================================================================
echo.
timeout /t 3 >nul
exit



