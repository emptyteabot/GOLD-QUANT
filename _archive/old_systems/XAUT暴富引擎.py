"""
XAUT暴富引擎 - 一键启动脚本
整合所有智能体，实现全自动化交易

使用方法：
1. 配置 .env 文件（飞书Webhook、交易所API）
2. 运行: python XAUT暴富引擎.py
3. 等待飞书通知，看信号赚钱
"""

import asyncio
import multiprocessing
import sys
import os
import logging
from datetime import datetime

# 添加路径
sys.path.append(os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("暴富引擎")


def run_sentinel():
    """运行哨兵智能体"""
    from xaut_agents.哨兵智能体 import 哨兵智能体
    sentinel = 哨兵智能体()
    asyncio.run(sentinel.run())


def run_analyst():
    """运行分析师智能体"""
    from xaut_agents.分析师智能体 import 分析师智能体
    analyst = 分析师智能体()
    asyncio.run(analyst.analyze_market())


def run_sniper():
    """运行狙击手智能体"""
    from xaut_agents.狙击手智能体 import 狙击手智能体
    
    # 从环境变量读取API密钥
    api_keys = {
        'okx': {
            'api_key': os.getenv('OKX_API_KEY', ''),
            'secret': os.getenv('OKX_SECRET', ''),
            'password': os.getenv('OKX_PASSWORD', '')
        }
    }
    
    sniper = 狙击手智能体(api_keys=api_keys if api_keys['okx']['api_key'] else None)
    asyncio.run(sniper.run())


def run_governor():
    """运行执政官智能体"""
    from xaut_agents.执政官智能体 import 执政官智能体
    
    total_capital = float(os.getenv('TOTAL_CAPITAL', '100000'))
    max_drawdown = float(os.getenv('MAX_DRAWDOWN', '0.20'))
    
    governor = 执政官智能体(total_capital=total_capital, max_drawdown=max_drawdown)
    asyncio.run(governor.run())


def run_command_center():
    """运行指挥中心"""
    from xaut_agents.黄金军团指挥中心 import 黄金军团指挥中心
    command_center = 黄金军团指挥中心()
    command_center.run()


def check_dependencies():
    """检查依赖"""
    required_packages = [
        'redis',
        'ccxt',
        'numpy',
        'aiohttp',
        'requests',
        'python-dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"❌ 缺少依赖: {', '.join(missing)}")
        logger.info("请运行: pip install " + ' '.join(missing))
        return False
    
    return True


def check_redis():
    """检查Redis连接"""
    try:
        import redis
        r = redis.Redis(host='localhost', decode_responses=True)
        r.ping()
        logger.info("✅ Redis连接正常")
        return True
    except Exception as e:
        logger.error(f"❌ Redis连接失败: {e}")
        logger.info("请确保Redis已启动: redis-server")
        return False


def check_env():
    """检查环境变量"""
    from dotenv import load_dotenv
    load_dotenv()
    
    feishu_webhook = os.getenv('FEISHU_WEBHOOK_URL', '')
    if not feishu_webhook:
        logger.warning("⚠️ 未配置飞书Webhook，将无法接收通知")
        logger.info("请在.env文件中设置: FEISHU_WEBHOOK_URL=https://...")
    
    okx_api = os.getenv('OKX_API_KEY', '')
    if not okx_api:
        logger.warning("⚠️ 未配置OKX API，将以模拟模式运行")
        logger.info("请在.env文件中设置: OKX_API_KEY, OKX_SECRET, OKX_PASSWORD")
    
    return True


def main():
    """主函数"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        🏆 XAUT暴富引擎 - 黄金军团多智能体系统 🏆          ║
║                                                           ║
║  策略: 暴跌反弹 | 阶梯接针 | 延迟套利 | 动态风控         ║
║  智能体: 哨兵 | 分析师 | 狙击手 | 执政官                 ║
║                                                           ║
║  ⚠️  高风险高收益，请严格遵守风控纪律 ⚠️                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    logger.info("🔍 系统自检中...")
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 检查Redis
    if not check_redis():
        return
    
    # 检查环境变量
    check_env()
    
    logger.info("✅ 系统自检完成")
    logger.info("🚀 启动黄金军团...")
    
    # 创建进程池
    processes = []
    
    try:
        # 启动各个智能体
        agents = [
            ('哨兵', run_sentinel),
            ('分析师', run_analyst),
            ('狙击手', run_sniper),
            ('执政官', run_governor),
            ('指挥中心', run_command_center)
        ]
        
        for name, func in agents:
            p = multiprocessing.Process(target=func, name=name)
            p.start()
            processes.append(p)
            logger.info(f"✅ {name}智能体已启动 (PID: {p.pid})")
        
        logger.info("=" * 60)
        logger.info("🎯 黄金军团全部就绪！")
        logger.info("📱 请查看飞书通知，等待交易信号")
        logger.info("💰 祝您暴富！")
        logger.info("=" * 60)
        
        # 等待所有进程
        for p in processes:
            p.join()
            
    except KeyboardInterrupt:
        logger.info("\n⏹️ 收到停止信号，正在关闭系统...")
        
        for p in processes:
            p.terminate()
            p.join(timeout=5)
            if p.is_alive():
                p.kill()
        
        logger.info("✅ 系统已安全关闭")
    
    except Exception as e:
        logger.error(f"❌ 系统错误: {e}")
        
        for p in processes:
            if p.is_alive():
                p.terminate()


if __name__ == "__main__":
    # Windows需要这个
    multiprocessing.freeze_support()
    main()

