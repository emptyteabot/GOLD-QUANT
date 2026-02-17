"""
Pytest配置文件
提供测试fixtures和全局配置
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_klines():
    """生成模拟K线数据"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')

    # 生成模拟价格数据
    base_price = 2000.0
    prices = base_price + np.cumsum(np.random.randn(100) * 5)

    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices + np.random.randn(100) * 2,
        'high': prices + np.abs(np.random.randn(100) * 3),
        'low': prices - np.abs(np.random.randn(100) * 3),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 100)
    })

    return df


@pytest.fixture
def sample_account():
    """模拟账户信息"""
    return {
        'total_equity': 1000.0,
        'available': 900.0,
        'margin_used': 100.0,
        'unrealized_pnl': 0.0
    }


@pytest.fixture
def sample_position():
    """模拟持仓信息"""
    return {
        'instId': 'XAUUSDT-SWAP',
        'avgPx': '2000.0',
        'pos': '10',
        'lever': '10',
        'upl': '50.0',
        'uplRatio': '0.05'
    }


@pytest.fixture
def mock_okx_response():
    """模拟OKX API响应"""
    return {
        'code': '0',
        'msg': '',
        'data': [
            {
                'instId': 'XAUUSDT-SWAP',
                'last': '2000.0',
                'bidPx': '1999.5',
                'askPx': '2000.5',
                'vol24h': '1000000'
            }
        ]
    }
