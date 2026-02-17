"""
黄金军团指挥中心 (Golden Legion Command Center)
多智能体协同控制系统

职责：
1. 启动所有智能体
2. 协调智能体通信
3. 监控系统健康
4. 飞书通知集成
"""

import asyncio
import redis
import json
import time
import logging
from datetime import datetime
from typing import Dict, List
import requests
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("指挥中心")


class 飞书通知器:
    """飞书Webhook通知"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
    def send_alert(self, title: str, content: str, level: str = "INFO"):
        """
        发送飞书通知
        
        参数:
            title: 标题
            content: 内容
            level: INFO/WARNING/CRITICAL
        """
        color_map = {
            "INFO": "blue",
            "WARNING": "yellow",
            "CRITICAL": "red"
        }
        
        emoji_map = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "CRITICAL": "🚨"
        }
        
        message = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "content": f"{emoji_map.get(level, '')} {title}",
                        "tag": "plain_text"
                    },
                    "template": color_map.get(level, "blue")
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": content,
                            "tag": "lark_md"
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
            response = requests.post(self.webhook_url, json=message, timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ 飞书通知已发送: {title}")
            else:
                logger.error(f"❌ 飞书通知失败: {response.text}")
        except Exception as e:
            logger.error(f"❌ 飞书通知异常: {e}")


class 系统监控器:
    """监控所有智能体健康状态"""
    
    def __init__(self, redis_client: redis.Redis, feishu: 飞书通知器):
        self.redis = redis_client
        self.feishu = feishu
        self.agent_heartbeats = {}
        
    async def check_agent_health(self):
        """检查智能体心跳"""
        agents = ['哨兵', '分析师', '狙击手', '执政官']
        
        while True:
            try:
                for agent in agents:
                    last_heartbeat = self.redis.get(f'heartbeat:{agent}')
                    if last_heartbeat:
                        last_time = float(last_heartbeat)
                        if time.time() - last_time > 60:  # 超过60秒无心跳
                            logger.warning(f"⚠️ {agent}智能体心跳异常")
                            self.feishu.send_alert(
                                title=f"{agent}智能体离线",
                                content=f"{agent}已超过60秒无响应，请检查系统状态",
                                level="WARNING"
                            )
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"健康检查错误: {e}")
                await asyncio.sleep(30)


class 信号聚合器:
    """聚合所有智能体信号，生成交易决策"""
    
    def __init__(self, redis_client: redis.Redis, feishu: 飞书通知器):
        self.redis = redis_client
        self.feishu = feishu
        
    async def aggregate_signals(self):
        """聚合信号"""
        pubsub = self.redis.pubsub()
        pubsub.subscribe(
            'signal:CASCADE_DETECTED',
            'signal:WHALE_INFLOW',
            'signal:ANALYSIS',
            'signal:CIRCUIT_BREAKER'
        )
        
        logger.info("📡 信号聚合器启动")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    channel = message['channel']
                    data = json.loads(message['data'])
                    
                    await self.process_signal(channel, data)
                    
                except Exception as e:
                    logger.error(f"信号处理错误: {e}")
    
    async def process_signal(self, channel: str, data: Dict):
        """处理信号"""
        
        # 清算级联信号
        if channel == 'signal:CASCADE_DETECTED':
            intensity = data['data']['intensity']
            total_liq = data['data']['total_liquidation_usd']
            
            self.feishu.send_alert(
                title="🚨 检测到清算级联",
                content=(
                    f"**爆仓强度**: {intensity:.1f}x\n"
                    f"**总爆仓额**: ${total_liq:,.0f}\n"
                    f"**建议**: 准备接针，等待价格插针后分批买入"
                ),
                level="CRITICAL"
            )
        
        # 巨鲸异动
        elif channel == 'signal:WHALE_INFLOW':
            exchange = data['data']['exchange']
            amount = data['data']['amount_usd']
            
            self.feishu.send_alert(
                title="🐋 巨鲸转入交易所",
                content=(
                    f"**交易所**: {exchange}\n"
                    f"**金额**: ${amount:,.0f}\n"
                    f"**预测**: 潜在抛压，警惕短期下跌"
                ),
                level="WARNING"
            )
        
        # 分析师信号
        elif channel == 'signal:ANALYSIS':
            signal = data['signal']
            market = data['market_data']
            
            if signal['action'] in ['STRONG_BUY', 'BUY']:
                self.feishu.send_alert(
                    title=f"💎 {signal['action']} 信号",
                    content=(
                        f"**当前价格**: ${market['xaut_price']:.2f}\n"
                        f"**公允价值**: ${market['fair_value']:.2f}\n"
                        f"**价差**: {market['spread_pct']:.2%}\n"
                        f"**Z-Score**: {market['z_score']:.2f}\n"
                        f"**置信度**: {signal['confidence']:.1%}\n"
                        f"**原因**: {signal['reasoning'].get('interpretation', '')}\n\n"
                        f"**建议**: 分批建仓，严格止损"
                    ),
                    level="INFO"
                )
            
            elif signal['action'] in ['STRONG_SELL', 'SELL']:
                self.feishu.send_alert(
                    title=f"💰 {signal['action']} 信号",
                    content=(
                        f"**当前价格**: ${market['xaut_price']:.2f}\n"
                        f"**价差**: {market['spread_pct']:.2%}\n"
                        f"**建议**: 分批止盈，锁定利润"
                    ),
                    level="INFO"
                )
        
        # 熔断信号
        elif channel == 'signal:CIRCUIT_BREAKER':
            if data['active']:
                reasons = ', '.join(data['reasons'])
                self.feishu.send_alert(
                    title="🔴 系统熔断",
                    content=(
                        f"**原因**: {reasons}\n"
                        f"**状态**: 所有交易已暂停\n"
                        f"**建议**: 等待风险解除后再恢复交易"
                    ),
                    level="CRITICAL"
                )


class 黄金军团指挥中心:
    """主控制器"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', decode_responses=True)
        
        # 飞书Webhook
        feishu_webhook = os.getenv('FEISHU_WEBHOOK_URL', '')
        self.feishu = 飞书通知器(feishu_webhook)
        
        self.监控器 = 系统监控器(self.redis_client, self.feishu)
        self.信号聚合 = 信号聚合器(self.redis_client, self.feishu)
        
    async def start_agents(self):
        """启动所有智能体（需要在单独的进程中运行）"""
        logger.info("🚀 黄金军团指挥中心启动")
        
        self.feishu.send_alert(
            title="🚀 黄金军团系统启动",
            content=(
                "**系统**: XAUT多智能体激进套利系统\n"
                "**智能体**: 哨兵、分析师、狙击手、执政官\n"
                "**状态**: 全部就绪\n"
                "**策略**: 暴跌反弹、阶梯接针、延迟套利\n\n"
                "系统已开始监控市场，等待交易机会..."
            ),
            level="INFO"
        )
        
        # 启动监控和信号聚合
        tasks = [
            self.监控器.check_agent_health(),
            self.信号聚合.aggregate_signals()
        ]
        
        await asyncio.gather(*tasks)
    
    def run(self):
        """运行指挥中心"""
        try:
            asyncio.run(self.start_agents())
        except KeyboardInterrupt:
            logger.info("⏹️ 系统停止")
            self.feishu.send_alert(
                title="⏹️ 系统停止",
                content="黄金军团系统已手动停止",
                level="WARNING"
            )


if __name__ == "__main__":
    command_center = 黄金军团指挥中心()
    command_center.run()

