"""
专属仓位监控 - 10倍杠杆风险管理
"""
import asyncio
from datetime import datetime
from china_data_monitor import ChinaDataMonitor
import os
from dotenv import load_dotenv
import requests

load_dotenv()

# 你的仓位信息
POSITION = {
    'size': 0.3061,  # 持仓量
    'leverage': 10,  # 杠杆
    'entry_price': 4546.7,  # 开仓价
    'margin': 139.34,  # 保证金
    'liquidation_price': 4229.8,  # 预估强平价
}

# 风险阈值
RISK_LEVELS = {
    'extreme': 4300,  # 极度危险（距离爆仓<2%）
    'high': 4400,     # 高风险（距离爆仓<5%）
    'medium': 4500,   # 中风险（距离爆仓<8%）
    'safe': 4600,     # 安全区域
}


def send_feishu(message: str, level: str = "warning"):
    """发送飞书通知"""
    webhook = os.getenv('FEISHU_WEBHOOK_URL')
    if not webhook:
        print(f"消息: {message}")
        return
    
    colors = {
        "danger": "red",
        "warning": "orange",
        "info": "blue",
        "success": "green"
    }
    
    data = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🚨 仓位风险警报"
                },
                "template": colors.get(level, "orange")
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": message
                    }
                }
            ]
        }
    }
    
    try:
        requests.post(webhook, json=data, timeout=5)
    except:
        pass


async def monitor_position():
    """监控仓位风险"""
    monitor = ChinaDataMonitor()
    await monitor.initialize()
    
    print("=" * 70)
    print("🚨 专属仓位监控启动")
    print("=" * 70)
    print(f"持仓：{POSITION['size']} XAUT")
    print(f"杠杆：{POSITION['leverage']}x")
    print(f"开仓价：${POSITION['entry_price']}")
    print(f"强平价：${POSITION['liquidation_price']}")
    print("=" * 70)
    print()
    
    # 发送启动通知
    send_feishu(
        f"**🚨 仓位监控已启动**\n\n"
        f"**持仓信息：**\n"
        f"• 持仓量：{POSITION['size']} XAUT\n"
        f"• 杠杆：{POSITION['leverage']}x\n"
        f"• 开仓价：${POSITION['entry_price']}\n"
        f"• 强平价：${POSITION['liquidation_price']}\n"
        f"• 保证金：${POSITION['margin']}\n\n"
        f"**风险提示：**\n"
        f"• 价格跌破 ${RISK_LEVELS['extreme']} → 极度危险\n"
        f"• 价格跌破 ${RISK_LEVELS['high']} → 高风险\n"
        f"• 价格跌破 ${RISK_LEVELS['medium']} → 中风险",
        "warning"
    )
    
    last_alert_level = None
    check_count = 0
    
    try:
        while True:
            check_count += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # 获取当前价格
            price = await monitor.fetch_current_price()
            
            if not price:
                print(f"[{current_time}] ⚠️ 价格获取失败")
                await asyncio.sleep(10)
                continue
            
            # 计算盈亏
            pnl = (price - POSITION['entry_price']) * POSITION['size'] * POSITION['leverage']
            pnl_pct = (price - POSITION['entry_price']) / POSITION['entry_price'] * 100 * POSITION['leverage']
            
            # 计算距离强平价
            distance_to_liq = price - POSITION['liquidation_price']
            distance_pct = distance_to_liq / price * 100
            
            # 判断风险等级
            if price <= RISK_LEVELS['extreme']:
                risk_level = 'extreme'
                risk_text = '🔴 极度危险'
                alert_level = 'danger'
            elif price <= RISK_LEVELS['high']:
                risk_level = 'high'
                risk_text = '🟠 高风险'
                alert_level = 'warning'
            elif price <= RISK_LEVELS['medium']:
                risk_level = 'medium'
                risk_text = '🟡 中风险'
                alert_level = 'warning'
            else:
                risk_level = 'safe'
                risk_text = '🟢 安全'
                alert_level = 'info'
            
            # 打印状态
            print(f"[{current_time}] 第 {check_count} 次检查")
            print(f"  💰 当前价格: ${price:.2f}")
            print(f"  📊 盈亏: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
            print(f"  ⚠️  距离强平: ${distance_to_liq:.2f} ({distance_pct:.2f}%)")
            print(f"  🎯 风险等级: {risk_text}")
            print()
            
            # 发送警报
            if risk_level != last_alert_level and risk_level != 'safe':
                message = f"**{risk_text}**\n\n"
                message += f"**当前价格：** ${price:.2f}\n"
                message += f"**开仓价：** ${POSITION['entry_price']}\n"
                message += f"**强平价：** ${POSITION['liquidation_price']}\n\n"
                message += f"**盈亏：** ${pnl:+.2f} ({pnl_pct:+.2f}%)\n"
                message += f"**距离强平：** ${distance_to_liq:.2f} ({distance_pct:.2f}%)\n\n"
                
                if risk_level == 'extreme':
                    message += "**🚨 立即行动：**\n"
                    message += "• 马上追加保证金！\n"
                    message += "• 或立即平仓止损！\n"
                    message += "• 距离爆仓不到2%！"
                elif risk_level == 'high':
                    message += "**⚠️ 建议操作：**\n"
                    message += "• 考虑追加保证金\n"
                    message += "• 或平掉部分仓位\n"
                    message += "• 设置止损保护"
                elif risk_level == 'medium':
                    message += "**💡 注意：**\n"
                    message += "• 密切关注价格\n"
                    message += "• 准备追加保证金\n"
                    message += "• 考虑降低杠杆"
                
                send_feishu(message, alert_level)
                last_alert_level = risk_level
            
            # 检查加仓机会
            if price <= 4500 and price > 4450:
                if check_count % 10 == 0:  # 每10次检查提醒一次
                    send_feishu(
                        f"**💰 加仓机会**\n\n"
                        f"当前价格：${price:.2f}\n"
                        f"建议：可以考虑小仓位加仓\n"
                        f"建议仓位：$300（5倍杠杆）\n"
                        f"止损：${price * 0.98:.2f}",
                        "info"
                    )
            
            # 等待下次检查
            await asyncio.sleep(30)  # 30秒检查一次
    
    except KeyboardInterrupt:
        print("\n监控已停止")
    finally:
        await monitor.close()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║              🚨 专属仓位风险监控系统                          ║
    ║                                                              ║
    ║  功能：                                                       ║
    ║    • 实时监控价格                                             ║
    ║    • 计算盈亏和风险                                           ║
    ║    • 距离强平价预警                                           ║
    ║    • 加仓机会提醒                                             ║
    ║                                                              ║
    ║  风险等级：                                                   ║
    ║    🔴 极度危险 - 距离爆仓<2%                                  ║
    ║    🟠 高风险 - 距离爆仓<5%                                    ║
    ║    🟡 中风险 - 距离爆仓<8%                                    ║
    ║    🟢 安全 - 距离爆仓>8%                                      ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    按 Ctrl+C 停止监控
    """)
    
    asyncio.run(monitor_position())


