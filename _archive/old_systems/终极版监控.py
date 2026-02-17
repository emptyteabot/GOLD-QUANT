"""
终极版黄金监控 - 整合所有数据源
包括：OKX, Binance期货, GoldAPI, Tushare
"""
import time
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class UltimateGoldMonitor:
    """终极版黄金监控器"""
    
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
        
        # API Keys
        self.goldapi_key = os.getenv("GOLDAPI_KEY", "")
        self.tushare_token = os.getenv("TUSHARE_TOKEN", "")
        
        self.last_alert_time = 0
        self.running = False
    
    def fetch_okx(self):
        """OKX PAXG/USDT（最稳定）"""
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
            print(f"❌ OKX: {str(e)[:30]}")
        return None
    
    def fetch_binance_futures(self):
        """Binance 期货 XAUUSDT（你提供的方案）"""
        try:
            url = "https://fapi.binance.com/fapi/v1/ticker/price?symbol=XAUUSDT"
            
            # 如果需要代理（VPN）
            proxies = None
            # proxies = {'https': 'http://127.0.0.1:7890'}  # 取消注释并修改端口
            
            response = requests.get(url, timeout=10, proxies=proxies)
            if response.status_code == 200:
                data = response.json()
                price = float(data.get("price", 0))
                if price > 0:
                    return {"price": price, "source": "Binance期货"}
        except Exception as e:
            print(f"❌ Binance期货: {str(e)[:30]}")
        return None
    
    def fetch_goldapi(self):
        """GoldAPI（你已申请）"""
        if not self.goldapi_key:
            return None
        
        try:
            url = "https://www.goldapi.io/api/XAU/USD"
            headers = {"x-access-token": self.goldapi_key}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                price = data.get("price")
                if price and price > 0:
                    return {"price": price, "source": "GoldAPI"}
        except Exception as e:
            print(f"❌ GoldAPI: {str(e)[:30]}")
        return None
    
    def fetch_tushare_gold_etf(self):
        """Tushare A股黄金ETF（备用）"""
        if not self.tushare_token:
            return None
        
        try:
            import tushare as ts
            ts.set_token(self.tushare_token)
            pro = ts.pro_api()
            
            # 获取黄金ETF实时行情（518880.SH）
            df = pro.fund_daily(ts_code='518880.SH', trade_date=datetime.now().strftime('%Y%m%d'))
            if not df.empty:
                # A股黄金ETF价格需要转换为美元/盎司
                # 这里简化处理，实际需要汇率转换
                etf_price = float(df['close'].iloc[0])
                # 假设 ETF 价格与黄金价格的比例（需要校准）
                gold_price = etf_price * 100  # 简化计算
                return {"price": gold_price, "source": "Tushare黄金ETF"}
        except Exception as e:
            print(f"❌ Tushare: {str(e)[:30]}")
        return None
    
    def fetch_gold_price(self):
        """智能获取黄金价格 - 按优先级尝试"""
        sources = [
            ("OKX", self.fetch_okx),
            ("Binance期货", self.fetch_binance_futures),
            ("GoldAPI", self.fetch_goldapi),
            # ("Tushare", self.fetch_tushare_gold_etf),  # 需要安装 tushare
        ]
        
        for source_name, fetch_func in sources:
            result = fetch_func()
            if result:
                return result
        
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
• 📰 关注市场新闻（美联储/美元）
• 🛡️ 考虑止损策略
• ⏰ 等待反弹机会

**可能原因**
• 美元走强
• 美联储鹰派言论
• 避险情绪降温
• 技术性回调
"""
            
            self.send_feishu("🚨 黄金急跌预警", content, "red")
            self.last_alert_time = current_time
            self.alert_count += 1
        
        # 急涨预警
        elif change_1m >= self.threshold_spike:
            print(f"📈 触发急涨预警: {change_1m:.2%}")
            
            content = f"""🚀 **黄金价格快速上涨！投机机会！**

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
            
            self.send_feishu("📈 黄金急涨预警（投机机会）", content, "green")
            self.last_alert_time = current_time
            self.alert_count += 1
    
    def run(self):
        """主监控循环"""
        print("\n" + "=" * 70)
        print("💰 黄金价格监控系统（终极版）")
        print("=" * 70)
        print(f"⏱️  检查间隔: {self.check_interval}秒")
        print(f"📉 急跌阈值: {self.threshold_drop:.2%}")
        print(f"📈 急涨阈值: {self.threshold_spike:.2%}")
        print(f"🔑 GoldAPI: {'已配置' if self.goldapi_key else '未配置'}")
        print(f"🔑 Tushare: {'已配置' if self.tushare_token else '未配置'}")
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

**数据源**
• OKX PAXG/USDT ✅
• Binance 期货 XAUUSDT
• GoldAPI {'✅' if self.goldapi_key else '❌'}
• Tushare 黄金ETF {'✅' if self.tushare_token else '❌'}

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


def test_all_sources():
    """测试所有数据源"""
    print("\n🧪 测试所有黄金数据源\n")
    print("=" * 70)
    
    monitor = UltimateGoldMonitor()
    
    # 测试 OKX
    print("\n1️⃣ 测试 OKX PAXG/USDT...")
    result = monitor.fetch_okx()
    if result:
        print(f"   ✅ 价格: ${result['price']:,.2f}/盎司")
    else:
        print(f"   ❌ 获取失败")
    
    # 测试 Binance 期货
    print("\n2️⃣ 测试 Binance 期货 XAUUSDT...")
    result = monitor.fetch_binance_futures()
    if result:
        print(f"   ✅ 价格: ${result['price']:,.2f}/盎司")
    else:
        print(f"   ❌ 获取失败（可能需要 VPN 全局模式）")
    
    # 测试 GoldAPI
    print("\n3️⃣ 测试 GoldAPI...")
    if monitor.goldapi_key:
        result = monitor.fetch_goldapi()
        if result:
            print(f"   ✅ 价格: ${result['price']:,.2f}/盎司")
        else:
            print(f"   ❌ 获取失败")
    else:
        print(f"   ⚠️ 未配置 API Key")
    
    # 测试 Tushare
    print("\n4️⃣ 测试 Tushare 黄金ETF...")
    if monitor.tushare_token:
        print(f"   ⚠️ 需要安装 tushare: pip install tushare")
        # result = monitor.fetch_tushare_gold_etf()
    else:
        print(f"   ⚠️ 未配置 Token")
    
    print("\n" + "=" * 70)
    print("\n✅ 测试完成！")
    print("\n💡 推荐使用：")
    print("   • OKX（最稳定，已测试成功）")
    print("   • GoldAPI（备用，你已申请）")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_all_sources()
    else:
        monitor = UltimateGoldMonitor()
        monitor.run()



