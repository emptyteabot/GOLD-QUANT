"""
Web控制面板 - 实时监控和控制
使用 Flask + WebSocket 实现实时数据推送
"""
import asyncio
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
from datetime import datetime
from typing import Dict, List
import threading
import time

# 导入系统模块
try:
    from data_engine import DataEngine
    from feature_engineering import FeatureEngineer
    from strategy_dual_thrust import DualThrustStrategy
    from strategy_mean_reversion import MeanReversionStrategy
    from risk_manager import RiskManager
    from live_trader import LiveTrader
    from ml_predictor import GoldPricePredictor, XGBoostSignalClassifier, EnsemblePredictor
except ImportError as e:
    print(f"⚠️ 导入模块失败: {e}")
    print("请确保所有模块都在同一目录下")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gold_trading_secret_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 全局状态
system_state = {
    'running': False,
    'trader': None,
    'start_time': None,
    'total_trades': 0,
    'win_trades': 0,
    'current_position': 0,
    'current_price': 0,
    'balance': 100000,
    'initial_balance': 100000,
    'max_drawdown': 0,
    'signals': [],
    'performance': {
        'return': 0,
        'sharpe': 0,
        'win_rate': 0,
        'profit_factor': 0
    }
}

# 实时数据缓存
realtime_data = {
    'prices': [],
    'signals': [],
    'positions': [],
    'balance_history': []
}


@app.route('/')
def index():
    """主页"""
    return render_template('dashboard.html')


@app.route('/api/status')
def get_status():
    """获取系统状态"""
    return jsonify({
        'running': system_state['running'],
        'start_time': system_state['start_time'],
        'total_trades': system_state['total_trades'],
        'win_trades': system_state['win_trades'],
        'current_position': system_state['current_position'],
        'current_price': system_state['current_price'],
        'balance': system_state['balance'],
        'return': (system_state['balance'] - system_state['initial_balance']) / system_state['initial_balance'] * 100,
        'max_drawdown': system_state['max_drawdown'],
        'performance': system_state['performance']
    })


@app.route('/api/realtime_data')
def get_realtime_data():
    """获取实时数据"""
    return jsonify({
        'prices': realtime_data['prices'][-100:],
        'signals': realtime_data['signals'][-50:],
        'positions': realtime_data['positions'][-50:],
        'balance_history': realtime_data['balance_history'][-100:]
    })


@app.route('/api/start', methods=['POST'])
def start_system():
    """启动交易系统"""
    if system_state['running']:
        return jsonify({'success': False, 'message': '系统已在运行中'})
    
    try:
        config = request.json or {}
        thread = threading.Thread(target=run_trading_system, args=(config,))
        thread.daemon = True
        thread.start()
        
        system_state['running'] = True
        system_state['start_time'] = datetime.now().isoformat()
        
        return jsonify({'success': True, 'message': '系统启动成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动失败: {str(e)}'})


@app.route('/api/stop', methods=['POST'])
def stop_system():
    """停止交易系统"""
    if not system_state['running']:
        return jsonify({'success': False, 'message': '系统未运行'})
    
    system_state['running'] = False
    return jsonify({'success': True, 'message': '系统已停止'})


@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """配置管理"""
    if request.method == 'GET':
        return jsonify({
            'initial_balance': 100000,
            'max_position': 0.3,
            'stop_loss': 0.02,
            'take_profit': 0.05,
            'check_interval': 5,
            'strategies': ['dual_thrust', 'mean_reversion']
        })
    else:
        new_config = request.json
        return jsonify({'success': True, 'message': '配置已更新'})


def run_trading_system(config: Dict):
    """在后台运行交易系统"""
    print("🚀 交易系统启动...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        data_engine = DataEngine()
        
        while system_state['running']:
            try:
                data = loop.run_until_complete(data_engine.fetch_all_data())
                
                if data and 'price' in data:
                    current_price = data['price']
                    system_state['current_price'] = current_price
                    
                    realtime_data['prices'].append({
                        'time': datetime.now().isoformat(),
                        'price': current_price
                    })
                    
                    socketio.emit('price_update', {
                        'price': current_price,
                        'time': datetime.now().isoformat()
                    })
                
                time.sleep(config.get('check_interval', 5))
                
            except Exception as e:
                print(f"❌ 错误: {e}")
                time.sleep(5)
        
        loop.run_until_complete(data_engine.close())
        
    except Exception as e:
        print(f"❌ 系统错误: {e}")
    finally:
        loop.close()
        system_state['running'] = False


@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('✅ 客户端已连接')
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print('❌ 客户端已断开')


if __name__ == '__main__':
    print("=" * 70)
    print("🌐 Web控制面板启动")
    print("=" * 70)
    print("📊 访问地址: http://localhost:5000")
    print("=" * 70)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)



