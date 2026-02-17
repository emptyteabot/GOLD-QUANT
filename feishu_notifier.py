"""
飞书推送模块
"""
import requests
import logging
import json
from typing import Optional
from pathlib import Path
import config

logger = logging.getLogger(__name__)


def _sanitize_message(message: str, plain: bool = False) -> str:
    text = message
    if plain:
        # strip simple markdown markers for plain text mode
        for token in ["**", "__", "`", "•"]:
            text = text.replace(token, "")
    if getattr(config, "FEISHU_FORCE_ASCII", False):
        text = text.encode("ascii", "ignore").decode("ascii")
    return text


def _write_local_cn(title: str, message: str):
    if not getattr(config, "LOCAL_CHINESE_LOG", False):
        return
    try:
        path = Path(getattr(config, "LOCAL_CHINESE_LOG_PATH", "_tmp\\feishu_zh.log"))
        if not path.is_absolute():
            base = Path(__file__).resolve().parent
            path = base / path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(f"\n[{title}] {message}\n")
    except Exception:
        pass


def send_feishu(message: str, level: str = "info", title: str = "AURUM Alert") -> bool:
    """
    发送飞书通知
    
    Args:
        message: 消息内容（支持Markdown）
        level: 消息级别 (info/success/warning/danger/money)
        title: 消息标题
    
    Returns:
        bool: 是否发送成功
    """
    if not config.FEISHU_WEBHOOK:
        logger.info(f"[飞书] {message[:200]}...")
        return False
    
    colors = {
        "info": "blue",
        "success": "green",
        "warning": "yellow",
        "danger": "red",
        "money": "green"
    }
    
    # always log the original (possibly Chinese) locally
    _write_local_cn(title, message)

    msg_type = getattr(config, "FEISHU_MSG_TYPE", "interactive")
    is_plain = msg_type == "text"
    safe_title = _sanitize_message(title, plain=is_plain)
    safe_message = _sanitize_message(message, plain=is_plain)

    if msg_type == "text":
        data = {
            "msg_type": "text",
            "content": {"text": f"{safe_title}\n\n{safe_message}"}
        }
    else:
        data = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": safe_title},
                    "template": colors.get(level, "blue")
                },
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content": safe_message}}
                ]
            }
        }
    
    try:
        # force UTF-8 JSON to avoid garbled Chinese
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        response = requests.post(
            config.FEISHU_WEBHOOK,
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=5,
            proxies={
                'http': config.HTTP_PROXY,
                'https': config.HTTPS_PROXY
            }
        )
        if response.status_code == 200:
            logger.info("✅ 飞书推送成功")
            return True
        else:
            logger.error(f"❌ 飞书推送失败: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ 飞书推送异常: {e}")
        return False


def send_signal_push(signal_data: dict) -> bool:
    """
    发送交易信号推送（白天模式）
    
    Args:
        signal_data: 信号数据字典
    """
    # 计算合约张数
    oz_size = signal_data.get('position_size', 0)
    contracts = int(oz_size / 0.001)  # 1张合约 = 0.001盎司
    
    # 安全获取数据，处理None值
    def safe_get(key, default=0):
        val = signal_data.get(key, default)
        return val if val is not None else default
    
    direction = "LONG" if safe_get('signal') > 0 else "SHORT"
    message = (
        "SIGNAL\\n"
        f"MacroScore: {safe_get('macro_score'):.0f}  "
        f"DXY: {safe_get('dxy'):.2f}  US10Y: {safe_get('us10y'):.2f}%  VIX: {safe_get('vix'):.2f}\\n"
        f"Dir: {direction}  Strength: {safe_get('signal_strength'):.0%}  "
        f"Hurst: {safe_get('hurst', 0.5):.2f}  ADX: {safe_get('adx'):.1f}  RSI: {safe_get('rsi', 50):.1f}  ML: {safe_get('ml_prob'):.0%}\\n"
        f"Entry: ${safe_get('entry_price'):.2f}  SL: ${safe_get('stop_loss'):.2f}  "
        f"TP: ${safe_get('take_profit'):.2f}  Size: {contracts} ctr  Lev: {safe_get('leverage')}x\\n"
        f"MaxLoss: ${safe_get('max_loss'):.2f}  Expect: ${safe_get('expected_profit'):.2f}  RR: {safe_get('risk_reward'):.1f}"
    )
    
    return send_feishu(message, level="money", title="🔔 交易信号")


def send_trade_execution(trade_data: dict) -> bool:
    """
    发送交易执行通知
    """
    action = "做多" if trade_data.get('side') == 'buy' else "做空"
    
    message = (
        "TRADE EXECUTED\\n"
        f"Side: {action}  Contracts: {trade_data.get('contracts', 0)}  Size: {trade_data.get('size', 0):.3f} XAU\\n"
        f"Price: ${trade_data.get('price', 0):.2f}  Lev: {trade_data.get('leverage', 0)}x  "
        f"Margin: ${trade_data.get('margin', 0):.2f}\\n"
        f"SL: ${trade_data.get('stop_loss', 0):.2f}  TP: ${trade_data.get('take_profit', 0):.2f}\\n"
        f"Equity: ${trade_data.get('equity', 0):.2f}  Available: ${trade_data.get('available', 0):.2f}  "
        f"Usage: {trade_data.get('position_usage', 0):.1%}"
    )
    
    return send_feishu(message, level="success", title="✅ 交易执行")


def send_heartbeat(account_data: dict, positions: list) -> bool:
    """
    发送心跳消息（5分钟）
    """
    position_summary = ""
    if positions:
        for pos in positions:
            side = "多" if float(pos.get('pos', 0)) > 0 else "空"
            size = abs(float(pos.get('pos', 0)))
            entry = float(pos.get('avgPx', 0))
            pnl = float(pos.get('upl', 0))
            pnl_ratio = float(pos.get('uplRatio', 0))
            position_summary += f"\n• {side}{size:.3f} XAU @ ${entry:.2f} | 盈亏: ${pnl:.2f} ({pnl_ratio:.1%})"
    else:
        position_summary = "\n• 无持仓"
    
    message = (
        "HEARTBEAT\\n"
        f"Equity: ${account_data.get('equity', 0):.2f}  Available: ${account_data.get('available', 0):.2f}  "
        f"Margin: ${account_data.get('margin_used', 0):.2f}\\n"
        f"Position:{position_summary}\\n"
        f"Price: ${account_data.get('price', 0):.2f}"
    )
    
    return send_feishu(message, level="info", title="📊 系统心跳")
