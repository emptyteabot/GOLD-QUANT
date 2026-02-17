"""
命令处理器
处理用户通过飞书发送的各种命令
"""
from typing import List, Optional
from datetime import datetime, timedelta
from feishu_bot import FeishuBot, FeishuMessage


class CommandHandler:
    """命令处理器"""
    
    def __init__(self, bot: FeishuBot, monitor=None):
        self.bot = bot
        self.monitor = monitor  # OKXPriceMonitor 实例
        
        # 注册所有命令
        self._register_commands()
    
    def _register_commands(self):
        """注册所有命令处理器"""
        self.bot.register_command("help", self.cmd_help)
        self.bot.register_command("price", self.cmd_price)
        self.bot.register_command("status", self.cmd_status)
        self.bot.register_command("history", self.cmd_history)
        self.bot.register_command("subscribe", self.cmd_subscribe)
        self.bot.register_command("unsubscribe", self.cmd_unsubscribe)
        self.bot.register_command("set", self.cmd_set)
        self.bot.register_command("settings", self.cmd_settings)
        self.bot.register_command("news", self.cmd_news)
        self.bot.register_command("about", self.cmd_about)
        self.bot.register_command("start", self.cmd_start)
        self.bot.register_command("stop", self.cmd_stop)
    
    async def cmd_help(self, message: FeishuMessage, args: List[str]):
        """帮助命令"""
        await self.bot.send_help()
    
    async def cmd_price(self, message: FeishuMessage, args: List[str]):
        """查询当前价格"""
        if not self.monitor:
            await self.bot.send_text("❌ 监控器未启动")
            return
        
        content = "**📊 实时价格**\n\n"
        
        for name, symbol in self.monitor.symbols.items():
            # 获取最新价格
            price = await self.monitor.fetch_price(symbol)
            
            if price is None:
                content += f"❌ {name.upper()} ({symbol}): 获取失败\n"
                continue
            
            # 计算涨跌幅
            change_1m = await self.monitor.calculate_change(symbol, minutes=1)
            change_5m = await self.monitor.calculate_change(symbol, minutes=5)
            
            content += f"**{name.upper()}** ({symbol})\n"
            content += f"• 价格: ${price:,.2f}\n"
            
            if change_1m is not None:
                emoji = "📉" if change_1m < 0 else "📈"
                content += f"• 1分钟: {emoji} {change_1m:+.2%}\n"
            
            if change_5m is not None:
                emoji = "📉" if change_5m < 0 else "📈"
                content += f"• 5分钟: {emoji} {change_5m:+.2%}\n"
            
            content += "\n"
        
        await self.bot.send_card(
            title="📊 实时价格",
            content=content,
            color="blue"
        )
    
    async def cmd_status(self, message: FeishuMessage, args: List[str]):
        """查看系统状态"""
        if not self.monitor:
            await self.bot.send_text("❌ 监控器未启动")
            return
        
        # 计算运行时间
        uptime = datetime.now() - datetime.fromtimestamp(self.monitor.start_time) if hasattr(self.monitor, 'start_time') else timedelta(0)
        
        content = f"**🟢 系统运行中**\n\n"
        content += f"**📊 统计数据**\n"
        content += f"• 运行时间: {str(uptime).split('.')[0]}\n"
        content += f"• 检查次数: {self.monitor.check_count}\n"
        content += f"• 预警次数: {self.monitor.alert_count}\n\n"
        
        content += f"**⚙️ 配置信息**\n"
        content += f"• 监控品种: {', '.join(self.monitor.symbols.keys())}\n"
        content += f"• 检查间隔: {self.monitor.check_interval}秒\n"
        content += f"• 预警阈值: {self.monitor.threshold_drop:.2%}\n\n"
        
        content += f"**📈 数据点数**\n"
        for symbol, history in self.monitor.price_history.items():
            content += f"• {symbol}: {len(history)} 个数据点\n"
        
        await self.bot.send_card(
            title="⚙️ 系统状态",
            content=content,
            color="green"
        )
    
    async def cmd_history(self, message: FeishuMessage, args: List[str]):
        """查看价格历史"""
        if not self.monitor:
            await self.bot.send_text("❌ 监控器未启动")
            return
        
        # 默认显示最近 10 个数据点
        limit = 10
        if args and args[0].isdigit():
            limit = min(int(args[0]), 60)
        
        content = f"**📈 价格历史（最近 {limit} 个数据点）**\n\n"
        
        for name, symbol in self.monitor.symbols.items():
            history = self.monitor.price_history.get(symbol, [])
            
            if not history:
                content += f"**{name.upper()}**: 暂无数据\n\n"
                continue
            
            content += f"**{name.upper()}** ({symbol})\n"
            
            recent = history[-limit:]
            if len(recent) >= 2:
                first_price = recent[0]
                last_price = recent[-1]
                change = (last_price - first_price) / first_price
                
                emoji = "📉" if change < 0 else "📈"
                content += f"• 起始: ${first_price:,.2f}\n"
                content += f"• 当前: ${last_price:,.2f}\n"
                content += f"• 变化: {emoji} {change:+.2%}\n"
            
            content += "\n"
        
        await self.bot.send_card(
            title="📈 价格历史",
            content=content,
            color="blue"
        )
    
    async def cmd_subscribe(self, message: FeishuMessage, args: List[str]):
        """订阅预警"""
        if not args:
            content = """**🔔 订阅管理**

请指定订阅类型：
• `/subscribe price` - 价格预警
• `/subscribe news` - 新闻预警
• `/subscribe daily` - 每日报告

示例: `/subscribe price`
"""
            await self.bot.send_card(
                title="🔔 订阅管理",
                content=content,
                color="blue"
            )
            return
        
        alert_type = args[0].lower()
        type_map = {
            "price": "price_alert",
            "news": "news_alert",
            "daily": "daily_report"
        }
        
        if alert_type not in type_map:
            await self.bot.send_text(f"❌ 未知的订阅类型: {alert_type}")
            return
        
        mapped_type = type_map[alert_type]
        
        if self.bot.is_subscribed(message.user_id, mapped_type):
            await self.bot.send_text(f"ℹ️ 您已经订阅了 {alert_type} 预警")
            return
        
        self.bot.subscribe(message.user_id, mapped_type)
        
        await self.bot.send_card(
            title="✅ 订阅成功",
            content=f"您已成功订阅 **{alert_type}** 预警\n\n使用 `/unsubscribe {alert_type}` 可以取消订阅",
            color="green"
        )
    
    async def cmd_unsubscribe(self, message: FeishuMessage, args: List[str]):
        """取消订阅"""
        if not args:
            await self.bot.send_text("❌ 请指定要取消的订阅类型，例如: `/unsubscribe price`")
            return
        
        alert_type = args[0].lower()
        type_map = {
            "price": "price_alert",
            "news": "news_alert",
            "daily": "daily_report"
        }
        
        if alert_type not in type_map:
            await self.bot.send_text(f"❌ 未知的订阅类型: {alert_type}")
            return
        
        mapped_type = type_map[alert_type]
        
        if not self.bot.is_subscribed(message.user_id, mapped_type):
            await self.bot.send_text(f"ℹ️ 您还未订阅 {alert_type} 预警")
            return
        
        self.bot.unsubscribe(message.user_id, mapped_type)
        
        await self.bot.send_card(
            title="✅ 取消订阅成功",
            content=f"您已取消订阅 **{alert_type}** 预警",
            color="blue"
        )
    
    async def cmd_set(self, message: FeishuMessage, args: List[str]):
        """设置参数"""
        if len(args) < 2:
            content = """**⚙️ 设置命令**

可用设置：
• `/set threshold <值>` - 设置预警阈值（如 -0.005 表示 -0.5%）
• `/set interval <秒>` - 设置检查间隔
• `/set cooldown <秒>` - 设置预警冷却时间

示例: `/set threshold -0.005`
"""
            await self.bot.send_card(
                title="⚙️ 设置命令",
                content=content,
                color="blue"
            )
            return
        
        setting_key = args[0].lower()
        setting_value = args[1]
        
        try:
            if setting_key == "threshold":
                value = float(setting_value)
                self.bot.set_user_setting(message.user_id, "threshold", value)
                await self.bot.send_text(f"✅ 预警阈值已设置为: {value:.2%}")
            
            elif setting_key == "interval":
                value = int(setting_value)
                if value < 1 or value > 60:
                    await self.bot.send_text("❌ 间隔必须在 1-60 秒之间")
                    return
                self.bot.set_user_setting(message.user_id, "interval", value)
                await self.bot.send_text(f"✅ 检查间隔已设置为: {value} 秒")
            
            elif setting_key == "cooldown":
                value = int(setting_value)
                if value < 60 or value > 3600:
                    await self.bot.send_text("❌ 冷却时间必须在 60-3600 秒之间")
                    return
                self.bot.set_user_setting(message.user_id, "cooldown", value)
                await self.bot.send_text(f"✅ 预警冷却时间已设置为: {value} 秒")
            
            else:
                await self.bot.send_text(f"❌ 未知的设置项: {setting_key}")
        
        except ValueError:
            await self.bot.send_text(f"❌ 无效的值: {setting_value}")
    
    async def cmd_settings(self, message: FeishuMessage, args: List[str]):
        """查看当前设置"""
        threshold = self.bot.get_user_setting(message.user_id, "threshold", -0.002)
        interval = self.bot.get_user_setting(message.user_id, "interval", 2)
        cooldown = self.bot.get_user_setting(message.user_id, "cooldown", 300)
        
        content = f"**⚙️ 您的设置**\n\n"
        content += f"• 预警阈值: {threshold:.2%}\n"
        content += f"• 检查间隔: {interval} 秒\n"
        content += f"• 预警冷却: {cooldown} 秒\n\n"
        
        content += f"**🔔 订阅状态**\n"
        for alert_type, subscribers in self.bot.subscribers.items():
            status = "✅" if message.user_id in subscribers else "❌"
            content += f"• {alert_type}: {status}\n"
        
        await self.bot.send_card(
            title="⚙️ 当前设置",
            content=content,
            color="blue"
        )
    
    async def cmd_news(self, message: FeishuMessage, args: List[str]):
        """查看新闻"""
        content = """**📰 新闻功能**

此功能需要配置新闻源和 AI 分析。

可用命令：
• `/news` - 查看最新新闻
• `/news analyze` - AI 分析新闻情绪

⚠️ 功能开发中...
"""
        await self.bot.send_card(
            title="📰 新闻中心",
            content=content,
            color="blue"
        )
    
    async def cmd_about(self, message: FeishuMessage, args: List[str]):
        """关于系统"""
        content = """**🤖 黄金监控系统 v2.0**

**功能特性：**
✅ 实时价格监控（OKX 交易所）
✅ 智能预警系统
✅ 飞书交互式控制
✅ 多维度数据分析
✅ AI 驱动的新闻分析

**技术栈：**
• Python 3.8+
• CCXT (交易所接口)
• Asyncio (异步处理)
• 飞书开放平台

**开发者：** AI Assistant
**版本：** 2.0.0
**更新时间：** 2026-02-01

💡 输入 `/help` 查看所有命令
"""
        await self.bot.send_card(
            title="ℹ️ 关于系统",
            content=content,
            color="blue"
        )
    
    async def cmd_start(self, message: FeishuMessage, args: List[str]):
        """启动监控"""
        await self.bot.send_text("⚠️ 监控已在后台运行，无需手动启动")
    
    async def cmd_stop(self, message: FeishuMessage, args: List[str]):
        """停止监控"""
        await self.bot.send_text("⚠️ 请使用 Ctrl+C 停止程序")



