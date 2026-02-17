"""
API集成测试
测试OKX API交互
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from okx_client import OKXClient


class TestOKXAPI:
    """OKX API集成测试"""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """测试客户端初始化"""
        client = OKXClient()

        assert client is not None
        assert hasattr(client, 'api_key')
        assert hasattr(client, 'secret_key')

    @pytest.mark.asyncio
    @patch('okx_client.OKXClient.get_account_balance')
    async def test_get_account_balance_mock(self, mock_balance):
        """测试获取账户余额（Mock）"""
        # Mock返回值
        mock_balance.return_value = {
            'total_equity': 1000.0,
            'available': 900.0,
            'margin_used': 100.0
        }

        client = OKXClient()
        balance = await client.get_account_balance()

        assert balance is not None
        assert 'total_equity' in balance
        assert balance['total_equity'] == 1000.0

    @pytest.mark.asyncio
    @patch('okx_client.OKXClient.get_ticker')
    async def test_get_ticker_mock(self, mock_ticker):
        """测试获取行情（Mock）"""
        mock_ticker.return_value = {
            'last': '2000.0',
            'bid': '1999.5',
            'ask': '2000.5'
        }

        client = OKXClient()
        ticker = await client.get_ticker('XAUUSDT-SWAP')

        assert ticker is not None
        assert 'last' in ticker
        assert float(ticker['last']) == 2000.0

    @pytest.mark.asyncio
    @patch('okx_client.OKXClient.get_klines')
    async def test_get_klines_mock(self, mock_klines):
        """测试获取K线数据（Mock）"""
        mock_klines.return_value = [
            ['1704067200000', '2000', '2010', '1990', '2005', '1000', '0', '0', '1'],
            ['1704067800000', '2005', '2015', '2000', '2010', '1100', '0', '0', '1'],
        ]

        client = OKXClient()
        klines = await client.get_klines('XAUUSDT-SWAP', '15m', 100)

        assert klines is not None
        assert len(klines) == 2

    @pytest.mark.asyncio
    @patch('okx_client.OKXClient.place_order')
    async def test_place_order_mock(self, mock_order):
        """测试下单（Mock）"""
        mock_order.return_value = {
            'ordId': '12345',
            'clOrdId': 'test_order',
            'sCode': '0',
            'sMsg': ''
        }

        client = OKXClient()
        result = await client.place_order(
            inst_id='XAUUSDT-SWAP',
            side='buy',
            size=1,
            price=2000.0
        )

        assert result is not None
        assert 'ordId' in result

    @pytest.mark.asyncio
    @patch('okx_client.OKXClient.get_positions')
    async def test_get_positions_mock(self, mock_positions):
        """测试获取持仓（Mock）"""
        mock_positions.return_value = [
            {
                'instId': 'XAUUSDT-SWAP',
                'pos': '10',
                'avgPx': '2000.0',
                'upl': '50.0'
            }
        ]

        client = OKXClient()
        positions = await client.get_positions()

        assert positions is not None
        assert len(positions) == 1
        assert positions[0]['instId'] == 'XAUUSDT-SWAP'


class TestAPIErrorHandling:
    """API错误处理测试"""

    @pytest.mark.asyncio
    @patch('okx_client.OKXClient.get_account_balance')
    async def test_api_error_handling(self, mock_balance):
        """测试API错误处理"""
        # Mock抛出异常
        mock_balance.side_effect = Exception("API Error")

        client = OKXClient()

        with pytest.raises(Exception):
            await client.get_account_balance()

    @pytest.mark.asyncio
    @patch('okx_client.OKXClient.place_order')
    async def test_order_failure_handling(self, mock_order):
        """测试下单失败处理"""
        # Mock返回失败响应
        mock_order.return_value = {
            'sCode': '50001',
            'sMsg': 'Insufficient balance'
        }

        client = OKXClient()
        result = await client.place_order(
            inst_id='XAUUSDT-SWAP',
            side='buy',
            size=1000000,  # 超大订单
            price=2000.0
        )

        assert result['sCode'] != '0'


class TestEndToEndWorkflow:
    """端到端工作流测试"""

    @pytest.mark.asyncio
    @patch('okx_client.OKXClient.get_account_balance')
    @patch('okx_client.OKXClient.get_ticker')
    @patch('okx_client.OKXClient.place_order')
    async def test_complete_trading_workflow(
        self,
        mock_order,
        mock_ticker,
        mock_balance
    ):
        """测试完整交易流程"""
        # Mock各个API
        mock_balance.return_value = {
            'total_equity': 1000.0,
            'available': 900.0
        }

        mock_ticker.return_value = {
            'last': '2000.0'
        }

        mock_order.return_value = {
            'ordId': '12345',
            'sCode': '0'
        }

        client = OKXClient()

        # 1. 获取账户信息
        balance = await client.get_account_balance()
        assert balance['available'] > 0

        # 2. 获取当前价格
        ticker = await client.get_ticker('XAUUSDT-SWAP')
        price = float(ticker['last'])

        # 3. 下单
        order = await client.place_order(
            inst_id='XAUUSDT-SWAP',
            side='buy',
            size=1,
            price=price
        )

        assert order['sCode'] == '0'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
