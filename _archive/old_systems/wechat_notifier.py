"""
微信推送模块 - 支持多种推送方式
"""
import aiohttp
import json
from datetime import datetime
from typing import Optional
import config_ultimate as config


class WeChatNotifier:
    """微信推送器 (支持多种方式)"""
    
    def __init__(self):
        self.push_method = getattr(config, 'PUSH_METHOD', 'pushplus')
        self.success_count = 0
        self.fail_count = 0
    
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
        发送预警消息到微信
        
        Args:
            title: 警报标题
            content: 警报内容
            alert_type: 警报类型 (warning/danger/info)
            price: 当前价格
            change_pct: 涨跌幅
            extra_info: 额外信息
        """
        # 构建完整消息
        message = self._build_message(title, content, alert_type, price, change_pct, extra_info)
        
        # 根据配置选择推送方式
        if self.push_method == "pushplus":
            success = await self._send_pushplus(title, message)
        elif self.push_method == "serverchan":
            success = await self._send_serverchan(title, message)
        elif self.push_method == "wechat":
            success = await self._send_wechat_webhook(title, message)
        elif self.push_method == "wxpusher":
            success = await self._send_wxpusher(title, message)
        else:
            print(f"❌ 未知的推送方式: {self.push_method}")
            return False
        
        if success:
            self.success_count += 1
        else:
            self.fail_count += 1
        
        return success
    
    def _build_message(
        self, 
        title: str, 
        content: str, 
        alert_type: str,
        price: Optional[float],
        change_pct: Optional[float],
        extra_info: Optional[dict]
    ) -> str:
        """构建消息内容"""
        emoji_map = {
            "warning": "⚠️",
            "danger": "🚨",
            "info": "ℹ️"
        }
        emoji = emoji_map.get(alert_type, "⚠️")
        
        msg = f"{emoji} {title}\n\n"
        msg += f"{content}\n\n"
        
        if price is not None:
            msg += f"💰 当前价格: ${price:.2f}\n"
            if change_pct is not None:
                emoji = "📉" if change_pct < 0 else "📈"
                msg += f"{emoji} 涨跌幅: {change_pct:+.2%}\n"
            msg += "\n"
        
        if extra_info:
            for key, value in extra_info.items():
                msg += f"• {key}: {value}\n"
            msg += "\n"
        
        msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return msg
    
    async def _send_pushplus(self, title: str, content: str) -> bool:
        """
        PushPlus 推送 (推荐)
        官网: https://www.pushplus.plus/
        免费额度: 200次/天
        """
        pushplus_token = getattr(config, 'PUSHPLUS_TOKEN', '')
        if not pushplus_token:
            print("❌ 未配置 PUSHPLUS_TOKEN")
            return False
        
        url = "http://www.pushplus.plus/send"
        data = {
            "token": pushplus_token,
            "title": title,
            "content": content.replace("\n", "<br>"),
            "template": "html"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("code") == 200:
                            print(f"✅ PushPlus 推送成功")
                            return True
                        else:
                            print(f"❌ PushPlus 推送失败: {result.get('msg')}")
                            return False
                    else:
                        print(f"❌ PushPlus HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ PushPlus 推送异常: {e}")
            return False
    
    async def _send_serverchan(self, title: str, content: str) -> bool:
        """
        Server酱 推送
        官网: https://sct.ftqq.com/
        免费额度: 5次/天 (需要关注公众号)
        """
        serverchan_key = getattr(config, 'SERVERCHAN_KEY', '')
        if not serverchan_key:
            print("❌ 未配置 SERVERCHAN_KEY")
            return False
        
        url = f"https://sctapi.ftqq.com/{serverchan_key}.send"
        data = {
            "title": title,
            "desp": content
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("code") == 0:
                            print(f"✅ Server酱推送成功")
                            return True
                        else:
                            print(f"❌ Server酱推送失败: {result.get('message')}")
                            return False
                    else:
                        print(f"❌ Server酱 HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Server酱推送异常: {e}")
            return False
    
    async def _send_wechat_webhook(self, title: str, content: str) -> bool:
        """
        企业微信机器人 (最稳定)
        需要企业微信账号
        """
        wechat_webhook = getattr(config, 'WECHAT_WEBHOOK', '')
        if not wechat_webhook:
            print("❌ 未配置 WECHAT_WEBHOOK")
            return False
        
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"## {title}\n\n{content}"
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(wechat_webhook, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("errcode") == 0:
                            print(f"✅ 企业微信推送成功")
                            return True
                        else:
                            print(f"❌ 企业微信推送失败: {result.get('errmsg')}")
                            return False
                    else:
                        print(f"❌ 企业微信 HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 企业微信推送异常: {e}")
            return False
    
    async def _send_wxpusher(self, title: str, content: str) -> bool:
        """
        WxPusher 推送 (支持多人)
        官网: https://wxpusher.zjiecode.com/
        免费额度: 无限制
        """
        wxpusher_token = getattr(config, 'WXPUSHER_TOKEN', '')
        if not wxpusher_token:
            print("❌ 未配置 WXPUSHER_TOKEN")
            return False
        
        url = "http://wxpusher.zjiecode.com/api/send/message"
        
        # 获取接收用户UID列表
        wxpusher_uids = getattr(config, 'WXPUSHER_UIDS', '')
        uids = wxpusher_uids.split(",") if wxpusher_uids else []
        
        data = {
            "appToken": wxpusher_token,
            "content": content.replace("\n", "<br>"),
            "summary": title,
            "contentType": 2,  # HTML格式
            "uids": uids
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("code") == 1000:
                            print(f"✅ WxPusher 推送成功")
                            return True
                        else:
                            print(f"❌ WxPusher 推送失败: {result.get('msg')}")
                            return False
                    else:
                        print(f"❌ WxPusher HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ WxPusher 推送异常: {e}")
            return False
    
    async def send_price_alert(
        self, 
        price: float, 
        change_1m: float, 
        change_5m: Optional[float] = None
    ) -> bool:
        """发送价格暴跌警报"""
        content = f"🚨 黄金价格急速下跌!\n\n"
        content += f"1分钟跌幅: {change_1m:.2%}"
        
        if change_5m is not None:
            content += f"\n5分钟跌幅: {change_5m:.2%}"
        
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
        content = f"📰 重大利空新闻检测!\n\n"
        content += f"新闻: {news_title}\n\n"
        content += f"AI情感分析: {sentiment_score}/10 (极度利空)\n\n"
        content += f"影响分析: {analysis}"
        
        extra_info = {}
        if news_url:
            extra_info["新闻链接"] = news_url
        
        return await self.send_alert(
            title="舆情重大利空",
            content=content,
            alert_type="danger",
            extra_info=extra_info
        )
    
    async def send_twitter_alert(
        self, 
        username: str,
        tweet_text: str,
        sentiment_score: int,
        analysis: str,
        tweet_url: Optional[str] = None
    ) -> bool:
        """发送推特警报"""
        content = f"🐦 推特重要信息!\n\n"
        content += f"来源: @{username}\n\n"
        content += f"内容: {tweet_text}\n\n"
        content += f"AI分析: {analysis} (分数: {sentiment_score}/10)"
        
        extra_info = {}
        if tweet_url:
            extra_info["推文链接"] = tweet_url
        
        return await self.send_alert(
            title="推特重要信息",
            content=content,
            alert_type="warning",
            extra_info=extra_info
        )
    
    async def send_system_start(self) -> bool:
        """发送系统启动通知"""
        content = "✅ 黄金崩盘预警系统已启动\n\n"
        content += f"AI引擎: {getattr(config, 'AI_PROVIDER', 'N/A').upper()}\n"
        content += f"监控标的: {getattr(config, 'GOLD_SYMBOL', 'XAU/USDT')}\n"
        content += f"价格检查: {getattr(config, 'PRICE_CHECK_INTERVAL', 60)}秒\n"
        content += f"推特监控: {len(getattr(config, 'TWITTER_WATCHLIST', []))}个账号\n"
        content += f"跌幅阈值: {getattr(config, 'THRESHOLD_PRICE_DROP_1M', 0.01):.2%}"
        
        return await self.send_alert(
            title="系统启动",
            content=content,
            alert_type="info"
        )


# 全局通知器实例
notifier = WeChatNotifier()



