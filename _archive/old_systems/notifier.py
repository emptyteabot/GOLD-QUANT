"""
飞书通知模块
负责发送预警消息到飞书群
"""
import aiohttp
import json
from datetime import datetime
from typing import Optional
from config import config


class FeishuNotifier:
    """飞书消息推送器"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_alert(
        self, 
        title: str, 
        content: str, 
        alert_type: str = "warning",
        price: Optional[float] = None,
        change_pct: Optional[float] = None,
        extra_info: Optional[dict] = None
    ) -> bool:
        """
        发送预警消息
        
        Args:
            title: 警报标题
            content: 警报内容
            alert_type: 警报类型 (warning/danger/info)
            price: 当前价格
            change_pct: 涨跌幅
            extra_info: 额外信息字典
        """
        # 颜色映射
        color_map = {
            "warning": "orange",
            "danger": "red",
            "info": "blue"
        }
        color = color_map.get(alert_type, "orange")
        
        # 构建消息卡片
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"⚠️ {title}"
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
        
        # 添加价格信息
        if price is not None:
            price_text = f"**当前价格**: ${price:.2f}"
            if change_pct is not None:
                emoji = "📉" if change_pct < 0 else "📈"
                price_text += f"\n**涨跌幅**: {emoji} {change_pct:.2%}"
            
            card["card"]["elements"].append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": price_text
                }
            })
        
        # 添加额外信息
        if extra_info:
            for key, value in extra_info.items():
                card["card"]["elements"].append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{key}**: {value}"
                    }
                })
        
        # 添加时间戳
        card["card"]["elements"].append({
            "tag": "div",
            "text": {
                "tag": "plain_text",
                "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        })
        
        # 发送请求
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=card,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("code") == 0:
                            return True
                        else:
                            print(f"❌ 飞书推送失败: {result}")
                            return False
                    else:
                        print(f"❌ 飞书推送失败: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 飞书推送异常: {e}")
            return False
    
    async def send_price_alert(
        self, 
        price: float, 
        change_1m: float, 
        change_5m: Optional[float] = None
    ) -> bool:
        """发送价格暴跌警报"""
        content = f"🚨 **黄金价格急速下跌!**\n\n"
        content += f"1分钟跌幅: **{change_1m:.2%}**"
        
        if change_5m is not None:
            content += f"\n5分钟跌幅: **{change_5m:.2%}**"
        
        content += f"\n\n⚡ 建议立即检查持仓风险!"
        
        return await self.send_alert(
            title="黄金急跌警报",
            content=content,
            alert_type="danger",
            price=price,
            change_pct=change_1m
        )
    
    async def send_news_alert(
        self, 
        news_title: str, 
        sentiment_score: int, 
        analysis: str,
        news_url: Optional[str] = None
    ) -> bool:
        """发送舆情利空警报"""
        content = f"📰 **重大利空新闻检测!**\n\n"
        content += f"**新闻标题**: {news_title}\n\n"
        content += f"**AI情感分析**: {sentiment_score}/10 (极度利空)\n\n"
        content += f"**影响分析**: {analysis}"
        
        extra_info = {}
        if news_url:
            extra_info["新闻链接"] = news_url
        
        return await self.send_alert(
            title="舆情重大利空",
            content=content,
            alert_type="danger",
            extra_info=extra_info
        )
    
    async def send_system_start(self) -> bool:
        """发送系统启动通知"""
        content = "✅ 黄金崩盘预警系统已启动\n\n"
        content += f"监控标的: PAXG/USDT (黄金代理)\n"
        content += f"价格检查间隔: {config.PRICE_CHECK_INTERVAL}秒\n"
        content += f"新闻检查间隔: {config.NEWS_CHECK_INTERVAL}秒\n"
        content += f"跌幅预警阈值: {config.THRESHOLD_PRICE_DROP_1M:.2%} (1分钟)"
        
        return await self.send_alert(
            title="系统启动",
            content=content,
            alert_type="info"
        )


# 全局通知器实例
notifier = FeishuNotifier(config.FEISHU_WEBHOOK)




