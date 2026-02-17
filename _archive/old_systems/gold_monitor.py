"""
黄金专用监控系统
支持多个黄金数据源，自动切换
"""
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()


class GoldPriceMonitor:
    """黄金价格监控器 - 多数据源"""
    
    def __init__(self):
        self.price_history = []
        self.check_count = 0
        self.alert_count = 0
        self.start_time = datetime.now().timestamp()
        
        # 配置
        self.check_interval = int(os.getenv("PRICE_CHECK_INTERVAL", "5"))
        self.threshold_drop = float(os.getenv("THRESHOLD_PRICE_DROP_1M", "-0.002"))
        self.threshold_spike = float(os.getenv("THRESHOLD_PRICE_SPIKE_1M", "0.003"))
        self.alert_cooldown = int(os.getenv("ALERT_COOLDOWN", "300"))
        
        self.last_alert_time = 0
        self.running = False
    
    async def fetch_gold_price_kitco(self) -> Optional[float]:
        """
        方案1: Kitco API (最权威的黄金价格)
        免费，无需 API Key
        """
        try:
            url = "https://www.kitco.com/market-charts/gold"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        text = await response.text()
                        # 解析页面中的价格（简化版）
                        # 实际需要更复杂的解析
                        return None  # 需要 HTML 解析
        except Exception as e:
            print(f"❌ Kitco 获取失败: {str(e)[:50]}")
            return None
    
    async def fetch_gold_price_goldapi(self) -> Optional[float]:
        """
        方案2: GoldAPI.io
        需要免费 API Key: https://www.goldapi.io/
        每月 100 次免费请求
        """
        api_key = os.getenv("GOLDAPI_KEY", "")
        if not api_key:
            return None
        
        try:
            url = "https://www.goldapi.io/api/XAU/USD"
            headers = {
                "x-access-token": api_key,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("price")
        except Exception as e:
            print(f"❌ GoldAPI 获取失败: {str(e)[:50]}")
            return None
    
    async def fetch_gold_price_metals(self) -> Optional[float]:
        """
        方案3: Metals-API.com
        免费额度: 每月 50 次
        """
        api_key = os.getenv("METALS_API_KEY", "")
        if not api_key:
            return None
        
        try:
            url = f"https://metals-api.com/api/latest?access_key={api_key}&base=USD&symbols=XAU"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            # XAU 是每盎司黄金的价格（倒数）
                            xau_rate = data.get("rates", {}).get("XAU")
                            if xau_rate:
                                return 1 / xau_rate  # 转换为美元/盎司
        except Exception as e:
            print(f"❌ Metals-API 获取失败: {str(e)[:50]}")
            return None
    
    async def fetch_gold_price_binance(self) -> Optional[float]:
        """
        方案4: 币安 PAXG/USDT (黄金代币)
        免费，稳定，1 PAXG = 1 盎司黄金
        """
        try:
            url = "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data.get("price", 0))
        except Exception as e:
            print(f"❌ Binance 获取失败: {str(e)[:50]}")
            return None
    
    async def fetch_gold_price_okx(self) -> Optional[float]:
        """
        方案5: OKX PAXG/USDT
        免费，国内可访问
        """
        try:
            # 修正 OKX API 端点
            url = "https://www.okx.com/api/v5/market/ticker?instId=PAXG-USDT"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("code") == "0":
                            ticker_data = data.get("data", [])
                            if ticker_data:
                                return float(ticker_data[0].get("last", 0))
        except Exception as e:
            print(f"❌ OKX 获取失败: {str(e)[:50]}")
            return None
    
    async def fetch_gold_price(self) -> Optional[Dict]:
        """
        智能获取黄金价格 - 自动尝试多个数据源
        返回: {"price": float, "source": str}
        """
        sources = [
            ("Binance PAXG", self.fetch_gold_price_binance),
            ("OKX PAXG", self.fetch_gold_price_okx),
            ("GoldAPI", self.fetch_gold_price_goldapi),
            ("Metals-API", self.fetch_gold_price_metals),
        ]
        
        for source_name, fetch_func in sources:
            price = await fetch_func()
            if price and price > 0:
                return {
                    "price": price,
                    "source": source_name
                }
        
        return None
    
    async def calculate_change(self, minutes: int = 1) -> Optional[float]:
        """计算涨跌幅"""
        required_points = minutes * 60 // self.check_interval
        
        if len(self.price_history) < required_points:
            return None
        
        current_price = self.price_history[-1]["price"]
        old_price = self.price_history[-required_points]["price"]
        
        if old_price == 0:
            return None
        
        change = (current_price - old_price) / old_price
        return change
    
    async def send_feishu_alert(self, title: str, content: str, color: str = "red"):
        """发送飞书预警"""
        webhook = os.getenv("FEISHU_WEBHOOK_URL", "")
        if not webhook:
            print("⚠️ 未配置飞书 Webhook")
            return
        
        card = {
            "msg_type": "interactive",
            "card": {
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
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook, json=card) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("code") == 0:
                            print(f"✅ 飞书通知已发送")
                        else:
                            print(f"❌ 飞书通知失败: {result}")
        except Exception as e:
            print(f"❌ 飞书通知异常: {e}")
    
    async def check_alert_conditions(self, price_data: Dict, change_1m: float):
        """检查预警条件"""
        current_time = datetime.now().timestamp()
        
        # 检查冷却时间
        if current_time - self.last_alert_time < self.alert_cooldown:
            return
        
        price = price_data["price"]
        source = price_data["source"]
        
        # 急跌预警
        if change_1m <= self.threshold_drop:
            print(f"🚨 触发急跌预警: {change_1m:.2%}")
            
            content = f"""⚠️ **黄金价格急速下跌！**

**当前价格**: ${price:,.2f}/盎司
**1分钟跌幅**: {change_1m:.2%}
**数据来源**: {source}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 **投资建议**
• 🔍 检查持仓风险
• 📰 关注市场新闻
• 🛡️ 考虑止损策略
• ⏰ 等待反弹机会

**可能原因**
• 美元走强
• 美联储鹰派言论
• 避险情绪降温
• 技术性回调
"""
            
            await self.send_feishu_alert(
                title="🚨 黄金急跌预警",
                content=content,
                color="red"
            )
            
            self.last_alert_time = current_time
            self.alert_count += 1
        
        # 急涨预警（投机机会）
        elif change_1m >= self.threshold_spike:
            print(f"📈 触发急涨预警: {change_1m:.2%}")
            
            content = f"""🚀 **黄金价格快速上涨！**

**当前价格**: ${price:,.2f}/盎司
**1分钟涨幅**: {change_1m:.2%}
**数据来源**: {source}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 **投资机会**
• 📈 关注突破确认
• 💰 考虑适量加仓
• 🎯 设置止盈目标
• ⚠️ 警惕假突破

**可能原因**
• 美元走弱
• 地缘政治风险
• 避险需求上升
• 通胀预期升温
"""
            
            await self.send_feishu_alert(
                title="📈 黄金急涨预警（投机机会）",
                content=content,
                color="green"
            )
            
            self.last_alert_time = current_time
            self.alert_count += 1
    
    async def monitor_loop(self):
        """主监控循环"""
        print("\n" + "=" * 70)
        print("💰 黄金价格监控系统")
        print("=" * 70)
        print(f"⏱️  检查间隔: {self.check_interval}秒")
        print(f"📉 急跌阈值: {self.threshold_drop:.2%}")
        print(f"📈 急涨阈值: {self.threshold_spike:.2%}")
        print(f"🔔 预警冷却: {self.alert_cooldown}秒")
        print("=" * 70)
        print()
        
        # 发送启动通知
        webhook = os.getenv("FEISHU_WEBHOOK_URL", "")
        if webhook:
            await self.send_feishu_alert(
                title="🚀 黄金监控系统已启动",
                content=f"""✅ 系统已成功启动

**监控配置**
• 检查间隔: {self.check_interval}秒
• 急跌阈值: {self.threshold_drop:.2%}
• 急涨阈值: {self.threshold_spike:.2%}

**数据源**
• Binance PAXG/USDT
• OKX PAXG/USDT
• GoldAPI (如已配置)
• Metals-API (如已配置)

系统将自动监控黄金价格，发现投资机会或风险时立即通知您！
""",
                color="blue"
            )
        
        self.running = True
        
        while self.running:
            try:
                self.check_count += 1
                
                # 获取价格
                price_data = await self.fetch_gold_price()
                
                if price_data is None:
                    print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] 所有数据源均失败")
                    await asyncio.sleep(self.check_interval)
                    continue
                
                price = price_data["price"]
                source = price_data["source"]
                
                # 记录价格
                self.price_history.append({
                    "price": price,
                    "source": source,
                    "time": datetime.now().timestamp()
                })
                
                # 只保留最近 300 个数据点（约 25 分钟）
                if len(self.price_history) > 300:
                    self.price_history.pop(0)
                
                # 计算涨跌幅
                change_1m = await self.calculate_change(minutes=1)
                change_5m = await self.calculate_change(minutes=5)
                
                # 显示信息（每 12 次显示一次，即每分钟）
                if self.check_count % 12 == 0:
                    change_1m_str = f"{change_1m:+.2%}" if change_1m else "N/A"
                    change_5m_str = f"{change_5m:+.2%}" if change_5m else "N/A"
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 黄金: ${price:,.2f} | 1m: {change_1m_str} | 5m: {change_5m_str} | 来源: {source}")
                
                # 检查预警
                if change_1m is not None:
                    await self.check_alert_conditions(price_data, change_1m)
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ 监控异常: {e}")
                await asyncio.sleep(10)
    
    async def close(self):
        """关闭监控"""
        self.running = False


async def test_all_sources():
    """测试所有数据源"""
    monitor = GoldPriceMonitor()
    
    print("\n🧪 测试所有黄金数据源\n")
    print("=" * 70)
    
    sources = [
        ("Binance PAXG/USDT", monitor.fetch_gold_price_binance),
        ("OKX PAXG/USDT", monitor.fetch_gold_price_okx),
        ("GoldAPI", monitor.fetch_gold_price_goldapi),
        ("Metals-API", monitor.fetch_gold_price_metals),
    ]
    
    for source_name, fetch_func in sources:
        print(f"\n测试 {source_name}...")
        price = await fetch_func()
        if price and price > 0:
            print(f"✅ {source_name}: ${price:,.2f}/盎司")
        else:
            print(f"❌ {source_name}: 获取失败或未配置")
    
    print("\n" + "=" * 70)
    print("\n🎯 推荐配置：")
    print("• Binance 和 OKX 免费，无需配置")
    print("• GoldAPI 需要注册: https://www.goldapi.io/")
    print("• Metals-API 需要注册: https://metals-api.com/")
    print("\n✅ 测试完成！")


async def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        await test_all_sources()
    else:
        monitor = GoldPriceMonitor()
        try:
            await monitor.monitor_loop()
        except KeyboardInterrupt:
            print("\n\n⚠️ 收到停止信号...")
        finally:
            await monitor.close()
            print("✅ 系统已安全关闭")


if __name__ == "__main__":
    asyncio.run(main())



