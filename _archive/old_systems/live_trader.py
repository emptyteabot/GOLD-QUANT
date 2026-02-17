"""
实盘交易引擎 - 专业版
整合所有模块，实现完整的交易系统
"""
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# 导入自定义模块
from data_engine import DataEngine
from feature_engineering import FeatureEngineer
from strategy_dual_thrust import DualThrustStrategy
from strategy_mean_reversion import MeanReversionStrategy
from risk_manager import RiskManager

load_dotenv()


class LiveTradingEngine:
    """
    实盘交易引擎
    
    整合：
    1. 数据引擎 - 多源数据
    2. 特征工程 - 完整特征
    3. 多策略 - Dual Thrust + 均值回归
    4. 风险管理 - Kelly + VaR
    5. 执行引擎 - 信号生成 + 订单管理
    6. 通知系统 - 飞书推送
    """
    
    def __init__(
        self,
        initial_capital: float = 100000,
        check_interval: int = 5,  # 检查间隔（秒）
        enable_dual_thrust: bool = True,
        enable_mean_reversion: bool = True,
        enable_ml: bool = False,  # 机器学习（需要训练）
        feishu_webhook: Optional[str] = None
    ):
        # 初始化各模块
        self.data_engine = DataEngine()
        self.feature_engineer = FeatureEngineer()
        self.risk_manager = RiskManager(initial_capital=initial_capital)
        
        # 策略
        self.strategies = {}
        if enable_dual_thrust:
            self.strategies['dual_thrust'] = DualThrustStrategy()
        if enable_mean_reversion:
            self.strategies['mean_reversion'] = MeanReversionStrategy()
        
        # 配置
        self.check_interval = check_interval
        self.feishu_webhook = feishu_webhook or os.getenv("FEISHU_WEBHOOK_URL", "")
        
        # 状态
        self.running = False
        self.positions = {}
        self.orders = []
        self.signals_history = []
        
        # 统计
        self.check_count = 0
        self.signal_count = 0
        self.trade_count = 0
        
        # 数据缓存
        self.price_data = pd.DataFrame()
        self.last_update = datetime.now()
    
    async def fetch_market_data(self) -> Dict:
        """
        获取市场数据
        
        Returns:
            完整的市场数据
        """
        # 获取所有数据
        all_data = await self.data_engine.fetch_all_data()
        
        # 获取K线数据
        ohlcv = await self.data_engine.fetch_ohlcv(limit=100)
        
        # 获取订单簿
        orderbook = await self.data_engine.fetch_orderbook()
        
        # 检测大单
        large_orders = await self.data_engine.detect_large_orders()
        
        return {
            'price': all_data['price'],
            'ohlcv': ohlcv,
            'orderbook': orderbook,
            'large_orders': large_orders,
            'dxy': all_data['dxy'],
            'vix': all_data['vix'],
            'us10y': all_data['us10y'],
            'news': all_data['news'],
            'twitter': all_data['twitter'],
            'timestamp': all_data['timestamp']
        }
    
    def generate_combined_signal(
        self,
        market_data: Dict,
        features_df: pd.DataFrame
    ) -> Dict:
        """
        生成综合信号
        
        多策略加权投票
        
        Returns:
            {
                'signal': int,  # 1: 做多, -1: 做空, 0: 观望
                'strength': float,  # 信号强度 (0-1)
                'strategies': Dict,  # 各策略信号
                'reason': str
            }
        """
        signals = {}
        weights = {}
        
        # 1. Dual Thrust策略
        if 'dual_thrust' in self.strategies:
            dt_signal = self.strategies['dual_thrust'].generate_signal(
                features_df,
                datetime.now()
            )
            signals['dual_thrust'] = dt_signal['signal']
            weights['dual_thrust'] = 0.4
        
        # 2. 均值回归策略
        if 'mean_reversion' in self.strategies:
            mr_signal = self.strategies['mean_reversion'].generate_signal(features_df)
            signals['mean_reversion'] = mr_signal['signal']
            weights['mean_reversion'] = 0.3
        
        # 3. 订单簿信号
        if market_data.get('orderbook'):
            ob = market_data['orderbook']
            # 买卖失衡度 > 0.3 → 做多
            # 买卖失衡度 < -0.3 → 做空
            if ob['imbalance'] > 0.3:
                signals['orderbook'] = 1
            elif ob['imbalance'] < -0.3:
                signals['orderbook'] = -1
            else:
                signals['orderbook'] = 0
            weights['orderbook'] = 0.2
        
        # 4. 宏观信号
        if market_data.get('dxy'):
            dxy = market_data['dxy']
            # DXY急涨 → 黄金跌 → 做空
            if dxy['change_1h'] > 0.005:
                signals['macro'] = -1
            elif dxy['change_1h'] < -0.005:
                signals['macro'] = 1
            else:
                signals['macro'] = 0
            weights['macro'] = 0.1
        
        # 加权投票
        total_weight = sum(weights.values())
        weighted_signal = sum([signals[k] * weights[k] for k in signals.keys()]) / total_weight if total_weight > 0 else 0
        
        # 最终信号
        if weighted_signal > 0.3:
            final_signal = 1
            strength = min(weighted_signal, 1.0)
            reason = f"多头信号 (强度: {strength:.2f})"
        elif weighted_signal < -0.3:
            final_signal = -1
            strength = min(abs(weighted_signal), 1.0)
            reason = f"空头信号 (强度: {strength:.2f})"
        else:
            final_signal = 0
            strength = 0
            reason = "信号不明确，观望"
        
        return {
            'signal': final_signal,
            'strength': strength,
            'strategies': signals,
            'weights': weights,
            'weighted_signal': weighted_signal,
            'reason': reason
        }
    
    async def execute_trade(
        self,
        signal: int,
        signal_strength: float,
        market_data: Dict
    ) -> Optional[Dict]:
        """
        执行交易
        
        Args:
            signal: 交易信号
            signal_strength: 信号强度
            market_data: 市场数据
        
        Returns:
            交易记录
        """
        # 检查风险限制
        risk_check = self.risk_manager.check_risk_limits()
        
        if not risk_check['can_trade']:
            print(f"⚠️ 风险限制：{', '.join(risk_check['warnings'])}")
            await self.send_feishu_alert(
                "⚠️ 风险限制触发",
                "\n".join(risk_check['warnings']),
                "orange"
            )
            return None
        
        # 获取价格和ATR
        price = market_data['price']['price']
        atr = market_data['ohlcv']['atr'].iloc[-1] if 'atr' in market_data['ohlcv'].columns else 20
        
        # 计算仓位
        position_info = self.risk_manager.calculate_position_size(
            signal_strength=signal_strength,
            price=price,
            atr=atr,
            win_rate=0.6,  # 从历史统计获取
            avg_win=100,
            avg_loss=50
        )
        
        # 创建订单
        order = {
            'timestamp': datetime.now(),
            'signal': signal,
            'price': price,
            'position_size': position_info['position_size'],
            'shares': position_info['shares'],
            'stop_loss': position_info['stop_loss'],
            'take_profit': position_info['take_profit'],
            'status': 'pending'
        }
        
        # 模拟执行（实盘需要对接交易所API）
        order['status'] = 'filled'
        self.orders.append(order)
        self.trade_count += 1
        
        # 发送通知
        await self.send_feishu_alert(
            f"{'📈 开多' if signal == 1 else '📉 开空'} 交易执行",
            f"""
**价格**: ${price:,.2f}
**仓位**: ${position_info['position_size']:,.0f} ({position_info['position_pct']:.1%})
**股数**: {position_info['shares']}
**止损**: ${position_info['stop_loss']:.2f}
**止盈**: ${position_info['take_profit']:.2f}
**信号强度**: {signal_strength:.2f}
            """,
            "blue"
        )
        
        return order
    
    async def send_feishu_alert(
        self,
        title: str,
        content: str,
        color: str = "blue"
    ):
        """发送飞书通知"""
        if not self.feishu_webhook:
            return
        
        import aiohttp
        
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
            async with aiohttp.ClientSession() as session:
                async with session.post(self.feishu_webhook, json=card) as response:
                    if response.status == 200:
                        print("✅ 飞书通知已发送")
        except Exception as e:
            print(f"❌ 飞书通知失败: {e}")
    
    async def run(self):
        """主循环"""
        print("\n" + "=" * 70)
        print("🚀 实盘交易引擎启动")
        print("=" * 70)
        print(f"💰 初始资金: ${self.risk_manager.initial_capital:,.0f}")
        print(f"📊 启用策略: {', '.join(self.strategies.keys())}")
        print(f"⏱️  检查间隔: {self.check_interval}秒")
        print("=" * 70)
        print()
        
        # 发送启动通知
        await self.send_feishu_alert(
            "🚀 交易系统已启动",
            f"""
**初始资金**: ${self.risk_manager.initial_capital:,.0f}
**启用策略**: {', '.join(self.strategies.keys())}
**检查间隔**: {self.check_interval}秒
**风险限制**:
• 最大仓位: {self.risk_manager.max_position_size:.0%}
• 单笔止损: {self.risk_manager.max_single_loss:.0%}
• 最大回撤: {self.risk_manager.max_drawdown:.0%}

系统将自动监控市场，发现交易机会时立即执行！
            """,
            "green"
        )
        
        self.running = True
        
        while self.running:
            try:
                self.check_count += 1
                
                # 1. 获取市场数据
                market_data = await self.fetch_market_data()
                
                if not market_data['price'] or market_data['ohlcv'] is None:
                    print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] 数据获取失败")
                    await asyncio.sleep(self.check_interval)
                    continue
                
                # 2. 特征工程
                features_df = self.feature_engineer.create_features(
                    price_df=market_data['ohlcv'],
                    orderbook_data=market_data['orderbook'],
                    macro_data=market_data['dxy'],
                    timestamp=datetime.now()
                )
                
                # 3. 生成信号
                signal_data = self.generate_combined_signal(market_data, features_df)
                
                # 记录信号
                self.signals_history.append({
                    'timestamp': datetime.now(),
                    'signal': signal_data['signal'],
                    'strength': signal_data['strength'],
                    'price': market_data['price']['price']
                })
                
                # 4. 显示信息（每分钟显示一次）
                if self.check_count % 12 == 0:
                    price = market_data['price']['price']
                    signal = signal_data['signal']
                    strength = signal_data['strength']
                    
                    signal_str = "📈 多头" if signal == 1 else ("📉 空头" if signal == -1 else "⏸️ 观望")
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"价格: ${price:,.2f} | "
                          f"信号: {signal_str} ({strength:.2f}) | "
                          f"资金: ${self.risk_manager.current_capital:,.0f}")
                
                # 5. 执行交易
                if signal_data['signal'] != 0 and signal_data['strength'] > 0.5:
                    self.signal_count += 1
                    
                    # 检查是否需要交易
                    # 这里简化处理，实际需要更复杂的逻辑
                    if len(self.positions) == 0:  # 空仓时才开仓
                        await self.execute_trade(
                            signal_data['signal'],
                            signal_data['strength'],
                            market_data
                        )
                
                # 6. 风险监控
                if self.check_count % 60 == 0:  # 每5分钟检查一次
                    risk_metrics = self.risk_manager.get_risk_metrics()
                    if risk_metrics:
                        print(f"\n📊 风险指标:")
                        print(f"   资金: ${risk_metrics['current_capital']:,.0f}")
                        print(f"   收益率: {risk_metrics['total_return']:.2%}")
                        print(f"   回撤: {risk_metrics['current_drawdown']:.2%}")
                        print()
                
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n\n⚠️ 收到停止信号...")
                break
            except Exception as e:
                print(f"❌ 系统异常: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(10)
        
        # 关闭
        await self.shutdown()
    
    async def shutdown(self):
        """关闭系统"""
        print("\n正在关闭系统...")
        
        # 获取最终统计
        risk_metrics = self.risk_manager.get_risk_metrics()
        
        # 发送关闭通知
        if risk_metrics:
            await self.send_feishu_alert(
                "⚠️ 交易系统已停止",
                f"""
**运行统计**:
• 检查次数: {self.check_count}
• 信号次数: {self.signal_count}
• 交易次数: {self.trade_count}

**绩效指标**:
• 最终资金: ${risk_metrics['current_capital']:,.0f}
• 总收益率: {risk_metrics['total_return']:.2%}
• 夏普比率: {risk_metrics['sharpe_ratio']:.2f}
• 最大回撤: {risk_metrics['max_drawdown']:.2%}
• 胜率: {risk_metrics['win_rate']:.2%}
                """,
                "orange"
            )
        
        # 关闭数据引擎
        await self.data_engine.close()
        
        print("✅ 系统已安全关闭")


# ==================== 主函数 ====================

async def main():
    """主函数"""
    engine = LiveTradingEngine(
        initial_capital=100000,
        check_interval=5,
        enable_dual_thrust=True,
        enable_mean_reversion=True
    )
    
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())



