"""
执政官智能体 (The Governor)
职能：风控层 - 资金分配、熔断机制、动态止损、USDT脱锚监控
运行频率：实时
"""

import asyncio
import ccxt.async_support as ccxt
import redis
import json
import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("执政官")


@dataclass
class RiskMetrics:
    """风险指标"""
    total_capital: float
    used_capital: float
    available_capital: float
    current_drawdown: float
    max_drawdown_limit: float
    usdt_rate: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL


class 动态ATR止损:
    """技能10: 动态ATR止损 (Dynamic ATR Stop Loss)"""
    
    def __init__(self, base_k: float = 2.0, panic_k: float = 4.0):
        self.base_k = base_k
        self.panic_k = panic_k
        
    def calculate_stop_loss(
        self, 
        entry_price: float, 
        atr: float,
        volatility_spike: bool = False
    ) -> float:
        """
        计算动态止损价格
        
        公式: Stop Loss = Entry Price - (K × ATR)
        
        参数:
            entry_price: 入场价格
            atr: 平均真实波幅
            volatility_spike: 是否处于波动率飙升状态
        """
        k = self.panic_k if volatility_spike else self.base_k
        stop_loss = entry_price - (k * atr)
        
        logger.info(f"🛡️ 动态止损: ${stop_loss:.2f} (K={k}, ATR=${atr:.2f})")
        return stop_loss
    
    def detect_volatility_spike(self, recent_atr: list) -> bool:
        """
        检测波动率飙升
        
        逻辑：当前ATR > 过去平均ATR的2倍
        """
        if len(recent_atr) < 20:
            return False
        
        current_atr = recent_atr[-1]
        avg_atr = np.mean(recent_atr[:-1])
        
        if current_atr > 2 * avg_atr:
            logger.warning(f"⚠️ 波动率飙升: 当前ATR {current_atr:.2f} vs 平均 {avg_atr:.2f}")
            return True
        
        return False


class USDT脱锚监控器:
    """技能11: USDT脱锚熔断机制 (USDT De-peg Kill Switch)"""
    
    def __init__(self, depeg_threshold: float = 0.97):
        self.depeg_threshold = depeg_threshold
        self.alert_triggered = False
        
    async def monitor_usdt_rate(self, exchange: ccxt.Exchange) -> Optional[Dict]:
        """
        监控USDT汇率
        
        策略：
        - USDT < $0.97: 立即停止所有XAUT买入
        - 持有仓位转换为USDC或BTC
        
        返回:
            {
                'usdt_rate': 0.95,
                'status': 'CRITICAL',
                'action': 'STOP_ALL_TRADING'
            }
        """
        try:
            # 获取USDC/USDT价格（反向推算USDT/USD）
            ticker = await exchange.fetch_ticker('USDC/USDT')
            usdt_rate = 1 / ticker['last']  # USDT/USD
            
            if usdt_rate < self.depeg_threshold:
                if not self.alert_triggered:
                    logger.critical(f"🚨 USDT脱锚警报！当前汇率: ${usdt_rate:.4f}")
                    self.alert_triggered = True
                
                return {
                    'usdt_rate': usdt_rate,
                    'status': 'CRITICAL',
                    'action': 'STOP_ALL_TRADING',
                    'recommendation': '立即将XAUT转换为USDC或BTC'
                }
            else:
                self.alert_triggered = False
                return {
                    'usdt_rate': usdt_rate,
                    'status': 'NORMAL',
                    'action': 'CONTINUE'
                }
                
        except Exception as e:
            logger.error(f"USDT监控失败: {e}")
            return None


class 交易所偿付能力监控器:
    """技能12: 交易所偿付能力监控 (Proof of Reserves Monitor)"""
    
    def __init__(self):
        self.reserve_addresses = {
            'okx': {
                'cold_wallet': '0x...',  # OKX冷钱包地址
                'hot_wallet': '0x...'
            }
        }
        self.last_reserves = {}
        
    async def check_reserves(self, exchange_name: str) -> Optional[Dict]:
        """
        检查交易所储备金
        
        策略：
        - 如果热钱包短时间内流出大量资金 = 挤兑现象
        - 触发自动提币脚本
        """
        # 实际需要调用区块链浏览器API
        # 这里使用模拟数据
        
        current_reserves = 1_000_000_000  # $10亿
        last_reserves = self.last_reserves.get(exchange_name, current_reserves)
        
        change_pct = (current_reserves - last_reserves) / last_reserves
        
        if change_pct < -0.1:  # 储备金下降超过10%
            logger.critical(f"🚨 {exchange_name}储备金异常下降: {change_pct:.1%}")
            return {
                'exchange': exchange_name,
                'status': 'WARNING',
                'action': 'WITHDRAW_TO_COLD_WALLET',
                'reserves_change': change_pct
            }
        
        self.last_reserves[exchange_name] = current_reserves
        return None


class 凯利公式资金管理:
    """凯利公式仓位管理"""
    
    def __init__(self, total_capital: float):
        self.total_capital = total_capital
        
    def calculate_position_size(
        self, 
        win_rate: float, 
        avg_win: float, 
        avg_loss: float,
        use_half_kelly: bool = True
    ) -> float:
        """
        计算最优仓位大小
        
        凯利公式: f* = (p×b - q) / b
        其中:
            p = 胜率
            q = 1 - p
            b = 平均盈利/平均亏损
        
        参数:
            win_rate: 胜率 (0-1)
            avg_win: 平均盈利百分比
            avg_loss: 平均亏损百分比
            use_half_kelly: 是否使用半凯利（更保守）
        """
        p = win_rate
        q = 1 - p
        b = avg_win / avg_loss
        
        kelly_fraction = (p * b - q) / b
        
        if use_half_kelly:
            kelly_fraction *= 0.5
        
        # 限制最大仓位为20%
        kelly_fraction = max(0, min(kelly_fraction, 0.20))
        
        position_size = self.total_capital * kelly_fraction
        
        logger.info(f"💰 凯利仓位: {kelly_fraction:.1%} (${position_size:,.0f})")
        return position_size


class 执政官智能体:
    """
    执政官智能体主控制器
    
    职责：
    1. 实时风险监控
    2. 资金分配管理
    3. 熔断机制
    4. 保护系统生存
    """
    
    def __init__(
        self, 
        redis_host: str = 'localhost',
        total_capital: float = 100_000,
        max_drawdown: float = 0.20
    ):
        self.redis_client = redis.Redis(host=redis_host, decode_responses=True)
        self.total_capital = total_capital
        self.max_drawdown = max_drawdown
        
        self.动态止损 = 动态ATR止损()
        self.usdt监控 = USDT脱锚监控器()
        self.储备监控 = 交易所偿付能力监控器()
        self.凯利管理 = 凯利公式资金管理(total_capital)
        
        # 初始化交易所（只读模式）
        self.exchange = ccxt.okx({'enableRateLimit': True})
        
        self.circuit_breaker_active = False
        
    async def calculate_risk_metrics(self) -> RiskMetrics:
        """计算当前风险指标"""
        # 从Redis获取当前持仓和资金使用情况
        used_capital = float(self.redis_client.get('used_capital') or 0)
        available_capital = self.total_capital - used_capital
        
        # 计算回撤
        peak_capital = float(self.redis_client.get('peak_capital') or self.total_capital)
        current_capital = float(self.redis_client.get('current_capital') or self.total_capital)
        drawdown = (peak_capital - current_capital) / peak_capital
        
        # 获取USDT汇率
        usdt_status = await self.usdt监控.monitor_usdt_rate(self.exchange)
        usdt_rate = usdt_status['usdt_rate'] if usdt_status else 1.0
        
        # 判断风险等级
        if drawdown > self.max_drawdown or usdt_rate < 0.97:
            risk_level = "CRITICAL"
        elif drawdown > self.max_drawdown * 0.7 or usdt_rate < 0.98:
            risk_level = "HIGH"
        elif drawdown > self.max_drawdown * 0.5:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return RiskMetrics(
            total_capital=self.total_capital,
            used_capital=used_capital,
            available_capital=available_capital,
            current_drawdown=drawdown,
            max_drawdown_limit=self.max_drawdown,
            usdt_rate=usdt_rate,
            risk_level=risk_level
        )
    
    async def check_circuit_breaker(self, risk_metrics: RiskMetrics) -> bool:
        """
        检查是否触发熔断
        
        熔断条件：
        1. 回撤超过最大限制
        2. USDT严重脱锚
        3. 交易所储备金异常
        """
        should_break = False
        reasons = []
        
        # 条件1: 回撤过大
        if risk_metrics.current_drawdown > risk_metrics.max_drawdown_limit:
            should_break = True
            reasons.append(f"回撤超限: {risk_metrics.current_drawdown:.1%}")
        
        # 条件2: USDT脱锚
        if risk_metrics.usdt_rate < 0.97:
            should_break = True
            reasons.append(f"USDT脱锚: ${risk_metrics.usdt_rate:.4f}")
        
        # 条件3: 交易所风险
        reserve_status = await self.储备监控.check_reserves('okx')
        if reserve_status and reserve_status['status'] == 'WARNING':
            should_break = True
            reasons.append("交易所储备金异常")
        
        if should_break and not self.circuit_breaker_active:
            self.circuit_breaker_active = True
            logger.critical(f"🔴 触发熔断机制！原因: {', '.join(reasons)}")
            
            # 发布熔断信号
            self.redis_client.publish('signal:CIRCUIT_BREAKER', json.dumps({
                'active': True,
                'reasons': reasons,
                'timestamp': time.time()
            }))
            
            # 设置全局熔断标志
            self.redis_client.set('circuit_breaker', '1')
        
        elif not should_break and self.circuit_breaker_active:
            self.circuit_breaker_active = False
            logger.info("✅ 熔断解除")
            self.redis_client.set('circuit_breaker', '0')
        
        return should_break
    
    async def approve_trade(self, trade_request: Dict) -> bool:
        """
        审批交易请求
        
        参数:
            trade_request: {
                'action': 'BUY',
                'amount_usdt': 50000,
                'confidence': 0.85
            }
        """
        # 检查熔断状态
        if self.circuit_breaker_active:
            logger.warning("⛔ 熔断中，拒绝交易")
            return False
        
        # 检查资金充足性
        risk_metrics = await self.calculate_risk_metrics()
        requested_amount = trade_request.get('amount_usdt', 0)
        
        if requested_amount > risk_metrics.available_capital:
            logger.warning(f"⛔ 资金不足: 需要${requested_amount:,.0f}, 可用${risk_metrics.available_capital:,.0f}")
            return False
        
        # 根据风险等级调整仓位
        if risk_metrics.risk_level == "HIGH":
            adjusted_amount = requested_amount * 0.5
            logger.warning(f"⚠️ 高风险状态，仓位减半: ${adjusted_amount:,.0f}")
            trade_request['amount_usdt'] = adjusted_amount
        
        elif risk_metrics.risk_level == "CRITICAL":
            logger.critical("⛔ 极端风险，拒绝新开仓")
            return False
        
        logger.info(f"✅ 交易审批通过: {trade_request['action']} ${trade_request['amount_usdt']:,.0f}")
        return True
    
    async def monitor_risk(self):
        """主风控循环"""
        logger.info("🛡️ 执政官智能体启动")
        
        while True:
            try:
                # 计算风险指标
                risk_metrics = await self.calculate_risk_metrics()
                
                # 检查熔断
                await self.check_circuit_breaker(risk_metrics)
                
                # 更新Redis
                self.redis_client.hset('risk_metrics', mapping={
                    'total_capital': risk_metrics.total_capital,
                    'used_capital': risk_metrics.used_capital,
                    'available_capital': risk_metrics.available_capital,
                    'drawdown': risk_metrics.current_drawdown,
                    'usdt_rate': risk_metrics.usdt_rate,
                    'risk_level': risk_metrics.risk_level,
                    'timestamp': time.time()
                })
                
                # 日志输出
                logger.info(
                    f"📊 风险状态: {risk_metrics.risk_level} | "
                    f"回撤: {risk_metrics.current_drawdown:.1%} | "
                    f"可用资金: ${risk_metrics.available_capital:,.0f} | "
                    f"USDT: ${risk_metrics.usdt_rate:.4f}"
                )
                
                await asyncio.sleep(5)  # 5秒更新一次
                
            except Exception as e:
                logger.error(f"风控循环错误: {e}")
                await asyncio.sleep(10)
    
    async def listen_for_trade_requests(self):
        """监听交易请求"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('request:TRADE_APPROVAL')
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    trade_request = json.loads(message['data'])
                    approved = await self.approve_trade(trade_request)
                    
                    # 发布审批结果
                    self.redis_client.publish('response:TRADE_APPROVAL', json.dumps({
                        'request_id': trade_request.get('request_id'),
                        'approved': approved,
                        'timestamp': time.time()
                    }))
                    
                except Exception as e:
                    logger.error(f"处理交易请求失败: {e}")
    
    async def run(self):
        """启动执政官"""
        logger.info("🛡️ 执政官智能体启动")
        tasks = [
            self.monitor_risk(),
            self.listen_for_trade_requests()
        ]
        await asyncio.gather(*tasks)
    
    async def close(self):
        """关闭连接"""
        await self.exchange.close()


if __name__ == "__main__":
    governor = 执政官智能体(total_capital=100_000, max_drawdown=0.20)
    try:
        asyncio.run(governor.run())
    finally:
        asyncio.run(governor.close())

