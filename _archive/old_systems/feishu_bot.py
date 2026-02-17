"""
飞书交互式机器人
支持命令交互、实时查询、订阅管理
"""
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
import json


@dataclass
class FeishuMessage:
    """飞书消息"""
    message_id: str
    chat_id: str
    user_id: str
    content: str
    timestamp: int


class FeishuBot:
    """飞书交互式机器人"""
    
    def __init__(self, webhook_url: str, app_id: str = "", app_secret: str = ""):
        self.webhook_url = webhook_url
        self.app_id = app_id
        self.app_secret = app_secret
        
        # 命令处理器
        self.command_handlers: Dict[str, Callable] = {}
        
        # 订阅管理
        self.subscribers: Dict[str, List[str]] = {
            "price_alert": [],      # 价格预警订阅
            "news_alert": [],       # 新闻预警订阅
            "daily_report": [],     # 日报订阅
        }
        
        # 用户设置
        self.user_settings: Dict[str, Dict] = {}
    
    def register_command(self, command: str, handler: Callable):
        """注册命令处理器"""
        self.command_handlers[command] = handler
    
    async def send_card(
        self, 
        title: str, 
        content: str, 
        color: str = "blue",
        buttons: Optional[List[Dict]] = None
    ) -> bool:
        """
        发送交互式卡片
        
        Args:
            title: 卡片标题
            content: 卡片内容（支持 Markdown）
            color: 卡片颜色 (blue/red/orange/green)
            buttons: 按钮列表
        """
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True,
                    "enable_forward": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    },
                    "template": color
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": content
                        }
                    }
                ]
            }
        }
        
        # 添加按钮
        if buttons:
            button_elements = []
            for btn in buttons:
                button_elements.append({
                    "tag": "button",
                    "text": {
                        "tag": "plain_text",
                        "content": btn.get("text", "按钮")
                    },
                    "type": btn.get("type", "default"),
                    "value": btn.get("value", {})
                })
            
            card["card"]["elements"].append({
                "tag": "action",
                "actions": button_elements
            })
        
        # 添加时间戳
        card["card"]["elements"].append({
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=card,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("code") == 0
                    return False
        except Exception as e:
            print(f"❌ 发送卡片失败: {e}")
            return False
    
    async def send_text(self, text: str) -> bool:
        """发送纯文本消息"""
        message = {
            "msg_type": "text",
            "content": {
                "text": text
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ 发送文本失败: {e}")
            return False
    
    async def handle_command(self, message: FeishuMessage) -> bool:
        """处理用户命令"""
        content = message.content.strip()
        
        # 解析命令
        if not content.startswith("/"):
            return False
        
        parts = content[1:].split()
        if not parts:
            return False
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # 查找处理器
        handler = self.command_handlers.get(command)
        if handler:
            try:
                await handler(message, args)
                return True
            except Exception as e:
                await self.send_text(f"❌ 命令执行失败: {str(e)}")
                return False
        else:
            await self.send_help()
            return False
    
    async def send_help(self):
        """发送帮助信息"""
        content = """**🤖 黄金监控机器人 - 命令列表**

**📊 查询命令**
• `/price` - 查询当前价格
• `/status` - 查看系统状态
• `/history` - 查看价格历史

**🔔 订阅管理**
• `/subscribe price` - 订阅价格预警
• `/subscribe news` - 订阅新闻预警
• `/subscribe daily` - 订阅每日报告
• `/unsubscribe <类型>` - 取消订阅

**⚙️ 设置命令**
• `/set threshold <值>` - 设置预警阈值
• `/set interval <秒>` - 设置检查间隔
• `/settings` - 查看当前设置

**📰 新闻命令**
• `/news` - 查看最新新闻
• `/news analyze` - AI 分析新闻

**💡 其他**
• `/help` - 显示此帮助
• `/about` - 关于本系统
"""
        
        await self.send_card(
            title="📖 帮助文档",
            content=content,
            color="blue"
        )
    
    async def send_welcome(self):
        """发送欢迎消息"""
        content = """**🎉 欢迎使用黄金监控系统！**

本系统提供：
✅ 实时价格监控（OKX 交易所）
✅ 智能新闻分析（AI 驱动）
✅ 多维度预警（价格、新闻、情绪）
✅ 交互式命令控制

**快速开始：**
• 输入 `/price` 查看当前价格
• 输入 `/subscribe price` 订阅价格预警
• 输入 `/help` 查看所有命令

祝您交易顺利！💰
"""
        
        buttons = [
            {"text": "📊 查看价格", "value": {"cmd": "price"}},
            {"text": "🔔 订阅预警", "value": {"cmd": "subscribe"}},
            {"text": "📖 帮助文档", "value": {"cmd": "help"}}
        ]
        
        await self.send_card(
            title="🚀 系统已启动",
            content=content,
            color="green",
            buttons=buttons
        )
    
    async def send_price_update(
        self, 
        symbol: str,
        price: float, 
        change_1m: Optional[float] = None,
        change_5m: Optional[float] = None,
        volume_24h: Optional[float] = None
    ):
        """发送价格更新"""
        content = f"**交易对**: {symbol}\n"
        content += f"**当前价格**: ${price:,.2f}\n\n"
        
        if change_1m is not None:
            emoji = "📉" if change_1m < 0 else "📈"
            content += f"{emoji} **1分钟**: {change_1m:+.2%}\n"
        
        if change_5m is not None:
            emoji = "📉" if change_5m < 0 else "📈"
            content += f"{emoji} **5分钟**: {change_5m:+.2%}\n"
        
        if volume_24h is not None:
            content += f"\n💰 **24h成交量**: ${volume_24h:,.0f}"
        
        color = "red" if (change_1m and change_1m < -0.01) else "blue"
        
        await self.send_card(
            title="📊 价格更新",
            content=content,
            color=color
        )
    
    async def send_alert(
        self, 
        alert_type: str,
        title: str, 
        content: str,
        severity: str = "warning"
    ):
        """
        发送预警消息
        
        Args:
            alert_type: 预警类型 (price/news/system)
            title: 标题
            content: 内容
            severity: 严重程度 (info/warning/danger)
        """
        color_map = {
            "info": "blue",
            "warning": "orange",
            "danger": "red"
        }
        
        emoji_map = {
            "price": "📉",
            "news": "📰",
            "system": "⚙️"
        }
        
        color = color_map.get(severity, "orange")
        emoji = emoji_map.get(alert_type, "⚠️")
        
        await self.send_card(
            title=f"{emoji} {title}",
            content=content,
            color=color
        )
    
    async def send_daily_report(
        self,
        date: str,
        price_open: float,
        price_close: float,
        price_high: float,
        price_low: float,
        change_pct: float,
        news_count: int,
        alert_count: int,
        summary: str
    ):
        """发送每日报告"""
        content = f"**📅 日期**: {date}\n\n"
        content += f"**📊 价格数据**\n"
        content += f"• 开盘: ${price_open:,.2f}\n"
        content += f"• 收盘: ${price_close:,.2f}\n"
        content += f"• 最高: ${price_high:,.2f}\n"
        content += f"• 最低: ${price_low:,.2f}\n"
        content += f"• 涨跌: {change_pct:+.2%}\n\n"
        
        content += f"**📰 统计数据**\n"
        content += f"• 新闻数量: {news_count}\n"
        content += f"• 预警次数: {alert_count}\n\n"
        
        content += f"**💡 AI 总结**\n{summary}"
        
        color = "red" if change_pct < 0 else "green"
        
        await self.send_card(
            title="📊 每日报告",
            content=content,
            color=color
        )
    
    def subscribe(self, user_id: str, alert_type: str) -> bool:
        """订阅预警"""
        if alert_type not in self.subscribers:
            return False
        
        if user_id not in self.subscribers[alert_type]:
            self.subscribers[alert_type].append(user_id)
        
        return True
    
    def unsubscribe(self, user_id: str, alert_type: str) -> bool:
        """取消订阅"""
        if alert_type not in self.subscribers:
            return False
        
        if user_id in self.subscribers[alert_type]:
            self.subscribers[alert_type].remove(user_id)
        
        return True
    
    def is_subscribed(self, user_id: str, alert_type: str) -> bool:
        """检查是否已订阅"""
        return user_id in self.subscribers.get(alert_type, [])
    
    def get_user_setting(self, user_id: str, key: str, default=None):
        """获取用户设置"""
        return self.user_settings.get(user_id, {}).get(key, default)
    
    def set_user_setting(self, user_id: str, key: str, value):
        """设置用户配置"""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        
        self.user_settings[user_id][key] = value


# 测试函数
async def test_bot():
    """测试机器人"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    webhook = os.getenv("FEISHU_WEBHOOK_URL", "")
    
    if not webhook:
        print("❌ 未配置 FEISHU_WEBHOOK_URL")
        return
    
    bot = FeishuBot(webhook)
    
    print("🧪 测试飞书机器人\n")
    
    # 测试欢迎消息
    print("1️⃣ 发送欢迎消息...")
    await bot.send_welcome()
    await asyncio.sleep(2)
    
    # 测试价格更新
    print("2️⃣ 发送价格更新...")
    await bot.send_price_update(
        symbol="BTC/USDT",
        price=95234.56,
        change_1m=-0.0023,
        change_5m=-0.0067,
        volume_24h=1234567890
    )
    await asyncio.sleep(2)
    
    # 测试预警
    print("3️⃣ 发送预警...")
    await bot.send_alert(
        alert_type="price",
        title="价格急跌预警",
        content="**BTC/USDT** 1分钟跌幅达到 **-0.5%**\n\n建议立即检查持仓！",
        severity="danger"
    )
    
    print("\n✅ 测试完成！请检查飞书群消息")


if __name__ == "__main__":
    asyncio.run(test_bot())



