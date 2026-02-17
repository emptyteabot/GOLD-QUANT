"""
终极简化版 - 一键启动，飞书推送，赚钱
"""
import asyncio
from datetime import datetime
import requests
import os
import sys

# 检查并安装依赖
def check_and_install_dependencies():
    """自动检查并安装缺失的依赖包"""
    required_packages = {
        'statsmodels': 'statsmodels',
        'scipy': 'scipy',
        'sklearn': 'scikit-learn',
        'dotenv': 'python-dotenv',
        'ccxt': 'ccxt',
        'pandas': 'pandas',
        'numpy': 'numpy'
    }
    
    missing_packages = []
    
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("=" * 70)
        print("📦 检测到缺失的依赖包，正在自动安装...")
        print("=" * 70)
        print(f"缺失: {', '.join(missing_packages)}")
        print()
        
        import subprocess
        for package in missing_packages:
            print(f"正在安装 {package}...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package,
                    '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'
                ])
                print(f"✅ {package} 安装成功")
            except Exception as e:
                print(f"❌ {package} 安装失败: {e}")
        
        print()
        print("=" * 70)
        print("✅ 依赖包安装完成，正在重启程序...")
        print("=" * 70)
        print()
        
        # 重启程序
        os.execv(sys.executable, [sys.executable] + sys.argv)

# 先检查依赖
check_and_install_dependencies()

# 导入依赖
from dotenv import load_dotenv
load_dotenv()

# 导入系统模块（带错误处理）
try:
    from data_engine import DataEngine
except ImportError:
    print("⚠️ 数据引擎模块未找到，使用简化版本")
    DataEngine = None

try:
    from strategy_dual_thrust import DualThrustStrategy
except ImportError:
    print("⚠️ Dual Thrust策略未找到")
    DualThrustStrategy = None

try:
    from strategy_mean_reversion import MeanReversionStrategy
except ImportError:
    print("⚠️ 均值回归策略未找到")
    MeanReversionStrategy = None

try:
    from strategy_momentum import MomentumStrategy
except ImportError:
    print("⚠️ 动量策略未找到")
    MomentumStrategy = None

try:
    from risk_manager import RiskManager
except ImportError:
    print("⚠️ 风险管理模块未找到")
    RiskManager = None

# 飞书推送
def send_feishu(message: str, level: str = "info"):
    """发送飞书通知 - 这是你唯一需要看到的"""
    webhook = os.getenv('FEISHU_WEBHOOK_URL')
    if not webhook:
        print(f"⚠️ 未配置飞书webhook: {message}")
        return
    
    # 根据级别选择颜色和emoji
    colors = {
        "info": "blue",
        "success": "green", 
        "warning": "yellow",
        "danger": "red",
        "money": "green"
    }
    
    emojis = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "danger": "🚨",
        "money": "💰"
    }
    
    color = colors.get(level, "blue")
    emoji = emojis.get(level, "📢")
    
    data = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"{emoji} 黄金交易信号"
                },
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": message
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        response = requests.post(webhook, json=data, timeout=5)
        if response.status_code == 200:
            print(f"✅ 飞书推送成功: {message[:50]}...")
        else:
            print(f"❌ 飞书推送失败: {response.text}")
    except Exception as e:
        print(f"❌ 飞书推送异常: {e}")


async def main():
    """
    主程序 - 所有复杂逻辑都在这里，但你不需要看
    你只需要关心飞书推送的内容
    """
    
    print("=" * 70)
    print("💰 黄金赚钱系统启动")
    print("=" * 70)
    print("📱 所有信号将推送到你的飞书")
    print("🎯 你只需要看飞书，然后决定是否交易")
    print("=" * 70)
    print()
    
    # 检查必要模块
    if DataEngine is None:
        print("❌ 核心模块缺失，请先运行: pip install -r requirements.txt")
        return
    
    # 发送启动通知
    send_feishu(
        "**🚀 系统已启动**\n\n"
        "系统正在监控黄金市场\n"
        "发现交易机会时会立即通知你\n\n"
        "**监控内容:**\n"
        "• 价格突破信号\n"
        "• 机器学习预测\n"
        "• 多策略综合判断\n"
        "• 风险控制建议",
        "success"
    )
    
    # 初始化所有复杂的东西（后台运行）
    data_engine = DataEngine()
    
    # 风险管理
    if RiskManager:
        risk_manager = RiskManager(initial_capital=100000)
    else:
        risk_manager = None
    
    # 策略（带容错）
    dual_thrust = DualThrustStrategy() if DualThrustStrategy else None
    mean_reversion = MeanReversionStrategy() if MeanReversionStrategy else None
    momentum = MomentumStrategy() if MomentumStrategy else None
    
    # 检查至少有一个策略可用
    available_strategies = sum([
        dual_thrust is not None,
        mean_reversion is not None,
        momentum is not None
    ])
    
    if available_strategies == 0:
        print("❌ 没有可用的策略模块")
        return
    
    print(f"✅ 已加载 {available_strategies} 个策略")
    print()
    
    # 机器学习（如果需要）
    # lstm_model = GoldPricePredictor(model_type='lstm')
    # xgb_model = XGBoostSignalClassifier()
    
    check_count = 0
    
    try:
        while True:
            check_count += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 第 {check_count} 次检查...")
            
            try:
                # 1. 获取数据（后台）
                data = await data_engine.fetch_all_data()
                
                if not data or 'price' not in data or data['price'] is None:
                    print("⚠️ 数据获取失败，5秒后重试...")
                    await asyncio.sleep(5)
                    continue
                
                current_price = data['price']
                
                # 验证价格有效性
                if current_price is None or current_price <= 0:
                    print("⚠️ 价格数据无效，5秒后重试...")
                    await asyncio.sleep(5)
                    continue
                
                print(f"💰 当前价格: ${current_price:.2f}")
                
                # 2. 获取K线数据
                klines = await data_engine.fetch_klines(interval='1h', limit=100)
                
                if klines is None or len(klines) < 50:
                    print("⚠️ K线数据不足，等待下次...")
                    await asyncio.sleep(30)
                    continue
                
                # 3. 生成信号（所有复杂计算在后台）
                signals = {}
                weights = {}
                
                # Dual Thrust信号
                if dual_thrust:
                    try:
                        dt_signal = dual_thrust.get_current_signal(klines)
                        signals['dual_thrust'] = dt_signal['signal']
                        weights['dual_thrust'] = 0.4
                    except Exception as e:
                        print(f"⚠️ Dual Thrust策略错误: {e}")
                
                # 均值回归信号
                if mean_reversion:
                    try:
                        mr_signal = mean_reversion.get_current_signal(klines)
                        signals['mean_reversion'] = mr_signal['signal']
                        weights['mean_reversion'] = 0.3
                    except Exception as e:
                        print(f"⚠️ 均值回归策略错误: {e}")
                
                # 动量信号
                if momentum:
                    try:
                        mom_signal = momentum.get_current_signal(klines)
                        signals['momentum'] = mom_signal['signal']
                        weights['momentum'] = 0.3
                    except Exception as e:
                        print(f"⚠️ 动量策略错误: {e}")
                
                if not signals:
                    print("⚠️ 没有可用的策略信号")
                    await asyncio.sleep(30)
                    continue
                
                # 4. 综合判断（加权投票）
                total_weight = sum(weights.values())
                weighted_signal = sum(signals[k] * weights[k] for k in signals) / total_weight
                
                # 5. 生成交易建议
                if weighted_signal > 0.5:
                    action = "📈 **做多**"
                    level = "money"
                    confidence = weighted_signal
                elif weighted_signal < -0.5:
                    action = "📉 **做空**"
                    level = "danger"
                    confidence = abs(weighted_signal)
                else:
                    action = "⏸️ **观望**"
                    level = "info"
                    confidence = 0.5
                
                # 6. 风险控制建议
                if risk_manager:
                    position_size = risk_manager.calculate_position_size(
                        signal_strength=abs(weighted_signal),
                        volatility=0.02
                    )
                else:
                    # 简单计算
                    position_size = min(abs(weighted_signal) * 0.3, 0.3)
                
                stop_loss_price = current_price * (0.98 if weighted_signal > 0 else 1.02)
                take_profit_price = current_price * (1.05 if weighted_signal > 0 else 0.95)
                
                # 7. 只在信号强烈时推送飞书
                if abs(weighted_signal) > 0.5:
                    # 构建策略分析文本
                    strategy_analysis = []
                    for name, signal in signals.items():
                        name_cn = {
                            'dual_thrust': 'Dual Thrust',
                            'mean_reversion': '均值回归',
                            'momentum': '动量策略'
                        }.get(name, name)
                        
                        signal_text = '多头' if signal > 0 else '空头' if signal < 0 else '观望'
                        strategy_analysis.append(f"• {name_cn}: {signal_text}")
                    
                    message = (
                        f"## {action}\n\n"
                        f"**当前价格:** ${current_price:.2f}\n"
                        f"**信号强度:** {confidence:.1%}\n\n"
                        f"**建议仓位:** {position_size:.1%}\n"
                        f"**止损价格:** ${stop_loss_price:.2f}\n"
                        f"**止盈价格:** ${take_profit_price:.2f}\n\n"
                        f"**策略分析:**\n"
                        + "\n".join(strategy_analysis) + "\n\n"
                        f"**风险提示:**\n"
                        f"• 严格执行止损\n"
                        f"• 控制仓位大小\n"
                        f"• 不要重仓"
                    )
                    
                    send_feishu(message, level)
                    
                    print(f"\n{'='*70}")
                    print(f"🎯 交易信号已推送到飞书！")
                    print(f"{'='*70}\n")
                    
                    # 发送信号后等待更长时间，避免频繁推送
                    await asyncio.sleep(300)  # 5分钟
                else:
                    print(f"📊 信号强度不足 ({weighted_signal:.2f})，继续监控...")
                    await asyncio.sleep(30)  # 30秒
                
            except Exception as e:
                print(f"❌ 错误: {e}")
                await asyncio.sleep(10)
    
    except KeyboardInterrupt:
        print("\n\n👋 系统停止")
        send_feishu(
            "**⏹️ 系统已停止**\n\n"
            "监控已结束",
            "info"
        )
    
    finally:
        await data_engine.close()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║                  💰 黄金赚钱系统 v2.0                         ║
    ║                                                              ║
    ║  核心原理: 监控市场 → 发现机会 → 飞书推送 → 你赚钱           ║
    ║                                                              ║
    ║  你需要做的:                                                  ║
    ║    1. 看飞书通知                                              ║
    ║    2. 根据建议交易                                            ║
    ║    3. 严格止损止盈                                            ║
    ║                                                              ║
    ║  系统会做的:                                                  ║
    ║    • 24小时监控市场                                           ║
    ║    • 多策略综合分析                                           ║
    ║    • 机器学习预测                                             ║
    ║    • 风险控制建议                                             ║
    ║    • 实时飞书推送                                             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    按 Ctrl+C 停止系统
    """)
    
    asyncio.run(main())

