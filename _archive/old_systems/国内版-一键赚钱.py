"""
国内版 - 一键赚钱系统
使用OKX黄金代币 + 国内数据源
"""
import asyncio
from datetime import datetime
import requests
import os
import sys

# 导入依赖
from dotenv import load_dotenv
load_dotenv()

# 导入国内数据源
from china_data_monitor import ChinaDataMonitor

# 飞书推送
def send_feishu(message: str, level: str = "info"):
    """发送飞书通知"""
    webhook = os.getenv('FEISHU_WEBHOOK_URL')
    if not webhook:
        print(f"⚠️ 未配置飞书webhook")
        print(f"消息: {message[:100]}...")
        return
    
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
            print(f"✅ 飞书推送成功")
        else:
            print(f"❌ 飞书推送失败: {response.text}")
    except Exception as e:
        print(f"❌ 飞书推送异常: {e}")


async def main():
    """主程序"""
    
    print("=" * 70)
    print("💰 黄金赚钱系统启动 (国内版)")
    print("=" * 70)
    print("📱 监控 OKX PAXG-USDT (黄金代币)")
    print("🎯 所有信号将推送到你的飞书")
    print("=" * 70)
    print()
    
    # 发送启动通知
    send_feishu(
        "**🚀 系统已启动 (国内版)**\n\n"
        "监控标的: OKX XAUT-USDT (Tether Gold)\n"
        "数据源: OKX + Binance (代理)\n"
        "备用: 新浪财经 + 东方财富\n\n"
        "系统正在监控黄金市场\n"
        "发现交易机会时会立即通知你",
        "success"
    )
    
    # 初始化数据监控
    monitor = ChinaDataMonitor()
    await monitor.initialize()
    
    print("✅ 数据监控器已初始化")
    print()
    
    # 价格历史（用于计算变化）
    price_history = []
    last_signal_time = None
    check_count = 0
    
    try:
        while True:
            check_count += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 第 {check_count} 次检查...")
            
            try:
                # 1. 获取当前价格
                current_price = await monitor.fetch_current_price()
                
                if current_price is None or current_price <= 0:
                    print("⚠️ 价格获取失败，10秒后重试...")
                    await asyncio.sleep(10)
                    continue
                
                print(f"💰 当前价格: ${current_price:,.2f}")
                
                # 2. 记录价格历史
                price_history.append({
                    'time': datetime.now(),
                    'price': current_price
                })
                
                # 只保留最近100个数据点
                if len(price_history) > 100:
                    price_history.pop(0)
                
                # 3. 计算价格变化
                if len(price_history) >= 2:
                    # 1分钟变化（假设每30秒检查一次，取最近2个点）
                    change_1m = (current_price - price_history[-2]['price']) / price_history[-2]['price']
                    
                    # 5分钟变化（取最近10个点）
                    if len(price_history) >= 10:
                        change_5m = (current_price - price_history[-10]['price']) / price_history[-10]['price']
                    else:
                        change_5m = change_1m
                    
                    print(f"📊 1分钟变化: {change_1m:+.2%}")
                    if len(price_history) >= 10:
                        print(f"📊 5分钟变化: {change_5m:+.2%}")
                    
                    # 4. 生成交易信号
                    signal = 0  # -1: 做空, 0: 观望, 1: 做多
                    confidence = 0
                    reasons = []
                    
                    # 简单策略：价格突破
                    if change_5m > 0.01:  # 5分钟涨超过1%
                        signal = 1
                        confidence = min(abs(change_5m) * 50, 0.95)
                        reasons.append(f"5分钟涨幅 {change_5m:.2%}")
                    elif change_5m < -0.01:  # 5分钟跌超过1%
                        signal = -1
                        confidence = min(abs(change_5m) * 50, 0.95)
                        reasons.append(f"5分钟跌幅 {change_5m:.2%}")
                    
                    # 短期急涨急跌
                    if abs(change_1m) > 0.005:  # 1分钟变化超过0.5%
                        if change_1m > 0:
                            signal = 1
                            confidence = max(confidence, 0.7)
                            reasons.append(f"1分钟急涨 {change_1m:.2%}")
                        else:
                            signal = -1
                            confidence = max(confidence, 0.7)
                            reasons.append(f"1分钟急跌 {change_1m:.2%}")
                    
                    # 5. 发送信号
                    if signal != 0 and confidence > 0.5:
                        # 检查信号间隔（避免频繁推送）
                        now = datetime.now()
                        if last_signal_time is None or (now - last_signal_time).total_seconds() > 300:
                            
                            action = "📈 **做多**" if signal > 0 else "📉 **做空**"
                            level = "money" if signal > 0 else "danger"
                            
                            # 计算止损止盈
                            stop_loss_price = current_price * (0.98 if signal > 0 else 1.02)
                            take_profit_price = current_price * (1.03 if signal > 0 else 0.97)
                            
                            # 建议仓位
                            position_size = min(confidence * 0.3, 0.3)
                            
                            message = (
                                f"## {action}\n\n"
                                f"**当前价格:** ${current_price:,.2f}\n"
                                f"**信号强度:** {confidence:.1%}\n\n"
                                f"**建议仓位:** {position_size:.1%}\n"
                                f"**止损价格:** ${stop_loss_price:.2f}\n"
                                f"**止盈价格:** ${take_profit_price:.2f}\n\n"
                                f"**信号来源:**\n"
                            )
                            
                            for reason in reasons:
                                message += f"• {reason}\n"
                            
                            message += (
                                f"\n**风险提示:**\n"
                                f"• 严格执行止损\n"
                                f"• 控制仓位大小\n"
                                f"• 不要重仓"
                            )
                            
                            send_feishu(message, level)
                            
                            print(f"\n{'='*70}")
                            print(f"🎯 交易信号已推送到飞书！")
                            print(f"{'='*70}\n")
                            
                            last_signal_time = now
                            await asyncio.sleep(300)  # 5分钟
                        else:
                            print(f"⏱️  信号间隔过短，跳过推送")
                    else:
                        print(f"📊 信号强度不足或观望，继续监控...")
                
                # 等待下次检查
                await asyncio.sleep(30)  # 30秒检查一次
                
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
        await monitor.close()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║                  💰 黄金赚钱系统 v3.0 (国内版)                ║
    ║                                                              ║
    ║  监控标的: OKX XAUT-USDT (Tether Gold)                        ║
    ║  数据源: 国内可访问 + V2Ray代理备用                           ║
    ║                                                              ║
    ║  核心原理: 监控市场 → 发现机会 → 飞书推送 → 你赚钱           ║
    ║                                                              ║
    ║  你需要做的:                                                  ║
    ║    1. 看飞书通知                                              ║
    ║    2. 根据建议交易                                            ║
    ║    3. 严格止损止盈                                            ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    按 Ctrl+C 停止系统
    """)
    
    asyncio.run(main())

