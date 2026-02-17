"""
查看所有持仓 - 包括SWAP合约和现货杠杆
"""
import asyncio
import logging
import os
from okx_client import OKXClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'


async def check_all_positions():
    """检查所有类型的持仓"""
    client = OKXClient()
    await client.initialize()
    
    print("\n" + "="*80)
    print("📊 OKX账户完整持仓报告")
    print("="*80)
    
    # 1. 获取账户余额
    print("\n💰 账户余额：")
    account = await client.get_account_balance()
    if account:
        print(f"  总权益：${account['total_equity']:.2f}")
        print(f"  可用资金：${account['available']:.2f}")
        print(f"  已用保证金：${account['margin_used']:.2f}")
        print(f"  未实现盈亏：${account['unrealized_pnl']:.2f}")
        print(f"  仓位使用率：{account['margin_used']/account['total_equity']:.1%}")
    else:
        print("  ❌ 无法获取账户信息")
    
    # 2. 获取SWAP永续合约持仓
    print("\n📈 SWAP永续合约持仓：")
    swap_positions = await client.get_positions()
    if swap_positions:
        for pos in swap_positions:
            inst_id = pos['instId']
            size = float(pos['pos'])
            side = "多" if size > 0 else "空"
            entry_price = float(pos['avgPx'])
            current_price = float(pos.get('last', entry_price))
            unrealized_pnl = float(pos['upl'])
            unrealized_pnl_ratio = float(pos['uplRatio'])
            leverage = pos.get('lever', 'N/A')
            # 安全转换margin（可能是空字符串）
            margin_str = pos.get('margin', '0')
            margin = float(margin_str) if margin_str else 0
            
            print(f"\n  合约：{inst_id}")
            print(f"  方向：{side}")
            print(f"  数量：{abs(size):.4f}")
            print(f"  开仓价：${entry_price:.2f}")
            print(f"  当前价：${current_price:.2f}")
            print(f"  杠杆：{leverage}x")
            print(f"  保证金：${margin:.2f}")
            print(f"  未实现盈亏：${unrealized_pnl:.2f} ({unrealized_pnl_ratio:.2%})")
    else:
        print("  无SWAP持仓")
    
    # 3. 获取现货杠杆余额
    print("\n💎 现货杠杆账户：")
    margin_balances = await client.get_margin_balance()
    if margin_balances:
        for ccy, balance in margin_balances.items():
            if balance['equity'] > 0.001:  # 只显示有余额的
                print(f"\n  币种：{ccy}")
                print(f"  权益：{balance['equity']:.4f}")
                print(f"  可用：{balance['available']:.4f}")
                print(f"  冻结：{balance['frozen']:.4f}")
                print(f"  借币：{balance['borrowed']:.4f}")
                print(f"  利息：{balance['interest']:.4f}")
    else:
        print("  无现货杠杆持仓")
    
    # 4. 获取所有持仓汇总
    print("\n📊 持仓汇总：")
    all_positions = await client.get_all_positions()
    
    print(f"\n  SWAP合约数量：{len(all_positions['swap_positions'])}")
    print(f"  现货杠杆币种：{len(all_positions['margin_balances'])}")
    print(f"  总权益（USDT）：${all_positions['total_equity_usdt']:.2f}")
    
    print("\n" + "="*80)
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(check_all_positions())

