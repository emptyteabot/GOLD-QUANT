"""
🎯 一键下单工具 - 您确认后执行
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'

import asyncio
from okx_client import OKXClient


async def main():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🎯 一键下单工具                            ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    client = OKXClient()
    await client.initialize()
    
    # 获取当前价格
    price = await client.get_ticker("XAU-USDT-SWAP")
    print(f"💰 当前价格: ${price:.2f}")
    
    # 获取账户余额
    account = await client.get_account_balance()
    if account:
        details = account.get('details', [])
        for d in details:
            if d.get('ccy') == 'USDT':
                balance = float(d.get('availBal', 0))
                print(f"💵 可用余额: ${balance:.2f}")
    
    # 获取当前持仓
    positions = await client.get_positions()
    current_pos = 0
    if positions:
        for pos in positions:
            if pos.get('instId') == 'XAU-USDT-SWAP':
                current_pos = int(float(pos.get('pos', 0)))
                entry = float(pos.get('avgPx', 0))
                pnl = float(pos.get('uplRatio', 0))
                print(f"📊 当前持仓: {current_pos}张 @ ${entry:.2f} ({pnl:+.1%})")
    
    print("\n" + "="*60)
    print("请选择操作：")
    print("  1. 做多（买入）")
    print("  2. 做空（卖出）")
    print("  3. 平仓（全部）")
    print("  4. 平仓（部分）")
    print("  0. 退出")
    print("="*60)
    
    choice = input("\n请输入选项 (0-4): ").strip()
    
    if choice == "0":
        print("👋 已退出")
        await client.close()
        return
    
    if choice == "1":  # 做多
        print(f"\n💡 建议：每次使用10%资金")
        print(f"   10%资金 ≈ {balance * 0.1:.2f} USDT")
        print(f"   10x杠杆 ≈ {int(balance * 0.1 * 10 / price / 0.01)}张")
        
        size = input("\n请输入张数（1张=0.01 XAUT≈$49）: ").strip()
        if not size.isdigit():
            print("❌ 无效输入")
            await client.close()
            return
        
        size = int(size)
        value = size * 0.01 * price
        margin = value / 10  # 假设10x杠杆
        
        print(f"\n📝 订单确认:")
        print(f"   方向: 做多（买入）")
        print(f"   数量: {size}张 = {size*0.01:.2f} XAUT")
        print(f"   价值: ~${value:.2f}")
        print(f"   保证金: ~${margin:.2f}")
        
        confirm = input("\n确认下单？(输入 yes 确认): ").strip()
        if confirm.lower() != 'yes':
            print("❌ 已取消")
            await client.close()
            return
        
        result = await client.place_order(
            inst_id="XAU-USDT-SWAP",
            side="buy",
            size=size,
            pos_side="long"
        )
        
        if result:
            print(f"\n🎉 下单成功！订单ID: {result.get('ordId')}")
        else:
            print("❌ 下单失败")
    
    elif choice == "2":  # 做空
        print("\n⚠️ 您当前有多头持仓，无法同时开空头")
        print("如需做空，请先平掉多头仓位")
    
    elif choice == "3":  # 全部平仓
        if current_pos == 0:
            print("❌ 没有持仓")
            await client.close()
            return
        
        print(f"\n📝 平仓确认:")
        print(f"   数量: {abs(current_pos)}张")
        
        confirm = input("\n确认平仓？(输入 yes 确认): ").strip()
        if confirm.lower() != 'yes':
            print("❌ 已取消")
            await client.close()
            return
        
        side = "sell" if current_pos > 0 else "buy"
        pos_side = "long" if current_pos > 0 else "short"
        
        result = await client.place_order(
            inst_id="XAU-USDT-SWAP",
            side=side,
            size=abs(current_pos),
            pos_side=pos_side,
            reduce_only=True
        )
        
        if result:
            print(f"\n🎉 平仓成功！订单ID: {result.get('ordId')}")
        else:
            print("❌ 平仓失败")
    
    elif choice == "4":  # 部分平仓
        if current_pos == 0:
            print("❌ 没有持仓")
            await client.close()
            return
        
        size = input(f"\n请输入平仓张数（当前持仓{abs(current_pos)}张）: ").strip()
        if not size.isdigit():
            print("❌ 无效输入")
            await client.close()
            return
        
        size = int(size)
        if size > abs(current_pos):
            print(f"❌ 超过持仓数量")
            await client.close()
            return
        
        print(f"\n📝 平仓确认:")
        print(f"   数量: {size}张 (剩余{abs(current_pos)-size}张)")
        
        confirm = input("\n确认平仓？(输入 yes 确认): ").strip()
        if confirm.lower() != 'yes':
            print("❌ 已取消")
            await client.close()
            return
        
        side = "sell" if current_pos > 0 else "buy"
        pos_side = "long" if current_pos > 0 else "short"
        
        result = await client.place_order(
            inst_id="XAU-USDT-SWAP",
            side=side,
            size=size,
            pos_side=pos_side,
            reduce_only=True
        )
        
        if result:
            print(f"\n🎉 平仓成功！订单ID: {result.get('ordId')}")
        else:
            print("❌ 平仓失败")
    
    await client.close()
    print("\n✅ 完成")


if __name__ == "__main__":
    asyncio.run(main())
