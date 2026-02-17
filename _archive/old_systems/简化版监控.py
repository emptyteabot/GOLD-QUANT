"""
简化版黄金监控 - 直接使用 requests 库
无需复杂的异步，更容易调试
"""
import time
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class SimpleGoldMonitor:
    """简化版黄金监控器"""
    
    def __init__(self):
        self.price_history = []
        self.check_count = 0
        self.alert_count = 0
        
        # 配置
        self.check_interval = int(os.getenv("PRICE_CHECK_INTERVAL", "5"))
        self.threshold_drop = float(os.getenv("THRESHOLD_PRICE_DROP_1M", "-0.002"))
        self.threshold_spike = float(os.getenv("THRESHOLD_PRICE_SPIKE_1M", "0.003"))
        self.alert_cooldown = int(os.getenv("ALERT_COOLDOWN", "300"))
        self.feishu_webhook = os.getenv("FEISHU_WEBHOOK_URL", "")
        
        self.last_alert_time = 0
        self.running = False
    
    def fetch_gold_price(self):
        """获取黄金价格 - 尝试多个数据源"""
        
        # 数据源 1: Binance
        try:
            url = "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                price = float(data.get("price", 0))
                if price > 0:
                    return {"price": price, "source": "Binance"}
        except Exception as e:
            print(f"❌ Binance 失败: {str(e)[:30]}")
        
        # 数据源 2: OKX
        try:
            url = "https://www.okx.com/api/v5/market/ticker?instId=PAXG-USDT"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "0":
                    ticker_data = data.get("data", [])
                    if ticker_data:
                        price = float(ticker_data[0].get("last", 0))
                        if price > 0:
                            return {"price": price, "source": "OKX"}
        except Exception as e:
            print(f"❌ OKX 失败: {str(e)[:30]}")
        
        # 数据源 3: GoldAPI
        api_key = os.getenv("GOLDAPI_KEY", "")
        if api_key:
            try:
                url = "https://www.goldapi.io/api/XAU/USD"
                headers = {"x-access-token": api_key}
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    price = data.get("price")
                    if price and price > 0:
                        return {"price": price, "source": "GoldAPI"}
            except Exception as e:
                print(f"❌ GoldAPI 失败: {str(e)[:30]}")
        
        return None
    
    def calculate_change(self, minutes=1):
        """计算涨跌幅"""
        required_points = minutes * 60 // self.check_interval
        
        if len(self.price_history) < required_points:
            return None
        
        current_price = self.price_history[-1]["price"]
        old_price = self.price_history[-required_points]["price"]
        
        if old_price == 0:
            return None
        
        return (current_price - old_price) / old_price
    
    def send_feishu(self, title, content, color="red"):
        """发送飞书通知"""
        if not self.feishu_webhook:
            print("⚠️ 未配置飞书 Webhook")
            return False
        
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": color
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": content}
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
            response = requests.post(self.feishu_webhook, json=card, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    print("✅ 飞书通知已发送")
                    return True
            print(f"❌ 飞书通知失败: {response.text[:50]}")
            return False
        except Exception as e:
            print(f"❌ 飞书通知异常: {e}")
            return False
    
    def check_alert(self, price_data, change_1m):
        """检查预警条件"""
        current_time = time.time()
        
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
"""
            
            self.send_feishu("🚨 黄金急跌预警", content, "red")
            self.last_alert_time = current_time
            self.alert_count += 1
        
        # 急涨预警
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
"""
            
            self.send_feishu("📈 黄金急涨预警（投机机会）", content, "green")
            self.last_alert_time = current_time
            self.alert_count += 1
    
    def run(self):
        """主监控循环"""
        print("\n" + "=" * 70)
        print("💰 黄金价格监控系统（简化版）")
        print("=" * 70)
        print(f"⏱️  检查间隔: {self.check_interval}秒")
        print(f"📉 急跌阈值: {self.threshold_drop:.2%}")
        print(f"📈 急涨阈值: {self.threshold_spike:.2%}")
        print("=" * 70)
        print()
        
        # 发送启动通知
        if self.feishu_webhook:
            self.send_feishu(
                "🚀 黄金监控系统已启动",
                f"""✅ 系统已成功启动

**监控配置**
• 检查间隔: {self.check_interval}秒
• 急跌阈值: {self.threshold_drop:.2%}
• 急涨阈值: {self.threshold_spike:.2%}

系统将自动监控黄金价格，发现投资机会或风险时立即通知您！
""",
                "blue"
            )
        
        self.running = True
        
        while self.running:
            try:
                self.check_count += 1
                
                # 获取价格
                price_data = self.fetch_gold_price()
                
                if price_data is None:
                    print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] 所有数据源均失败")
                    time.sleep(self.check_interval)
                    continue
                
                price = price_data["price"]
                source = price_data["source"]
                
                # 记录价格
                self.price_history.append(price_data)
                
                # 只保留最近 300 个数据点
                if len(self.price_history) > 300:
                    self.price_history.pop(0)
                
                # 计算涨跌幅
                change_1m = self.calculate_change(minutes=1)
                change_5m = self.calculate_change(minutes=5)
                
                # 显示信息（每 12 次显示一次）
                if self.check_count % 12 == 0:
                    change_1m_str = f"{change_1m:+.2%}" if change_1m else "N/A"
                    change_5m_str = f"{change_5m:+.2%}" if change_5m else "N/A"
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 黄金: ${price:,.2f} | 1m: {change_1m_str} | 5m: {change_5m_str} | {source}")
                
                # 检查预警
                if change_1m is not None:
                    self.check_alert(price_data, change_1m)
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n\n⚠️ 收到停止信号...")
                break
            except Exception as e:
                print(f"❌ 监控异常: {e}")
                time.sleep(10)
        
        print("✅ 系统已安全关闭")


def test_sources():
    """测试所有数据源"""
    print("\n🧪 测试黄金数据源\n")
    print("=" * 70)
    
    monitor = SimpleGoldMonitor()
    
    # 测试 Binance
    print("\n测试 Binance PAXG/USDT...")
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT"
        response = requests.get(url, timeout=10)
        print(f"HTTP 状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            price = float(data.get("price", 0))
            print(f"✅ Binance: ${price:,.2f}/盎司")
        else:
            print(f"❌ Binance: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Binance: {e}")
    
    # 测试 OKX
    print("\n测试 OKX PAXG/USDT...")
    try:
        url = "https://www.okx.com/api/v5/market/ticker?instId=PAXG-USDT"
        response = requests.get(url, timeout=10)
        print(f"HTTP 状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "0":
                ticker_data = data.get("data", [])
                if ticker_data:
                    price = float(ticker_data[0].get("last", 0))
                    print(f"✅ OKX: ${price:,.2f}/盎司")
            else:
                print(f"❌ OKX: {data}")
        else:
            print(f"❌ OKX: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ OKX: {e}")
    
    print("\n" + "=" * 70)
    print("\n💡 如果都失败，可能需要：")
    print("1. 检查网络连接")
    print("2. 关闭防火墙/代理")
    print("3. 申请 GoldAPI: https://www.goldapi.io/")
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_sources()
    else:
        monitor = SimpleGoldMonitor()
        monitor.run()



