"""
移动端API - RESTful接口
为移动App提供数据和控制接口

功能:
- 实时行情推送
- 交易信号通知
- 账户状态查询
- 远程控制系统
- 历史数据查询
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import json

# 导入系统模块
try:
    from data_engine import DataEngine
    from live_trader import LiveTrader
    from risk_manager import RiskManager
except ImportError as e:
    print(f"⚠️ 导入模块失败: {e}")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gold_mobile_api_2024'
app.config['JWT_SECRET_KEY'] = 'jwt_secret_2024'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

CORS(app)
jwt = JWTManager(app)

# 全局状态
api_state = {
    'system_running': False,
    'last_price': 0,
    'last_update': None,
    'alerts': [],
    'notifications': []
}


# ==================== 认证接口 ====================

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """
    用户登录
    
    Request:
        {
            "username": "admin",
            "password": "password"
        }
    
    Response:
        {
            "success": true,
            "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "expires_in": 604800
        }
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # 简单验证 (实际应该查询数据库)
    if username == 'admin' and password == 'admin123':
        access_token = create_access_token(identity=username)
        return jsonify({
            'success': True,
            'token': access_token,
            'expires_in': 604800,
            'user': {
                'username': username,
                'role': 'admin'
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': '用户名或密码错误'
        }), 401


# ==================== 行情接口 ====================

@app.route('/api/v1/market/price', methods=['GET'])
@jwt_required()
def get_current_price():
    """
    获取当前价格
    
    Response:
        {
            "success": true,
            "data": {
                "symbol": "XAUUSD",
                "price": 2650.50,
                "change": 5.30,
                "change_percent": 0.20,
                "timestamp": "2024-01-01T12:00:00"
            }
        }
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        data_engine = DataEngine()
        data = loop.run_until_complete(data_engine.fetch_all_data())
        loop.run_until_complete(data_engine.close())
        loop.close()
        
        if data and 'price' in data:
            return jsonify({
                'success': True,
                'data': {
                    'symbol': 'XAUUSD',
                    'price': data['price'],
                    'change': data.get('change_24h', 0),
                    'change_percent': data.get('change_24h_pct', 0),
                    'timestamp': datetime.now().isoformat(),
                    'bid': data.get('bid', 0),
                    'ask': data.get('ask', 0),
                    'volume_24h': data.get('volume_24h', 0)
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '获取价格失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/v1/market/kline', methods=['GET'])
@jwt_required()
def get_kline():
    """
    获取K线数据
    
    Query Parameters:
        interval: 1m, 5m, 15m, 1h, 4h, 1d
        limit: 数量限制 (默认100)
    
    Response:
        {
            "success": true,
            "data": [
                {
                    "timestamp": "2024-01-01T12:00:00",
                    "open": 2650.00,
                    "high": 2655.00,
                    "low": 2648.00,
                    "close": 2652.00,
                    "volume": 12345
                }
            ]
        }
    """
    interval = request.args.get('interval', '1h')
    limit = int(request.args.get('limit', 100))
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        data_engine = DataEngine()
        klines = loop.run_until_complete(data_engine.fetch_klines(interval=interval, limit=limit))
        loop.run_until_complete(data_engine.close())
        loop.close()
        
        if klines is not None and len(klines) > 0:
            data = []
            for _, row in klines.iterrows():
                data.append({
                    'timestamp': row['timestamp'].isoformat() if 'timestamp' in row else '',
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume'])
                })
            
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            return jsonify({
                'success': False,
                'message': '获取K线数据失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==================== 信号接口 ====================

@app.route('/api/v1/signals/latest', methods=['GET'])
@jwt_required()
def get_latest_signals():
    """
    获取最新信号
    
    Response:
        {
            "success": true,
            "data": [
                {
                    "timestamp": "2024-01-01T12:00:00",
                    "type": "buy",
                    "strategy": "dual_thrust",
                    "price": 2650.50,
                    "confidence": 0.85,
                    "reason": "突破上轨"
                }
            ]
        }
    """
    # 从全局状态获取信号
    signals = api_state.get('signals', [])[-10:]  # 最近10个信号
    
    return jsonify({
        'success': True,
        'data': signals
    })


# ==================== 账户接口 ====================

@app.route('/api/v1/account/status', methods=['GET'])
@jwt_required()
def get_account_status():
    """
    获取账户状态
    
    Response:
        {
            "success": true,
            "data": {
                "balance": 100000.00,
                "equity": 102500.00,
                "margin_used": 30000.00,
                "margin_free": 72500.00,
                "margin_level": 341.67,
                "positions": [
                    {
                        "symbol": "XAUUSD",
                        "type": "buy",
                        "volume": 1.0,
                        "entry_price": 2650.00,
                        "current_price": 2655.00,
                        "profit": 500.00,
                        "profit_percent": 1.89
                    }
                ]
            }
        }
    """
    # 模拟数据 (实际应该从交易系统获取)
    return jsonify({
        'success': True,
        'data': {
            'balance': 100000.00,
            'equity': 102500.00,
            'margin_used': 30000.00,
            'margin_free': 72500.00,
            'margin_level': 341.67,
            'total_profit': 2500.00,
            'total_profit_percent': 2.50,
            'positions': []
        }
    })


@app.route('/api/v1/account/history', methods=['GET'])
@jwt_required()
def get_trade_history():
    """
    获取交易历史
    
    Query Parameters:
        limit: 数量限制 (默认50)
        offset: 偏移量 (默认0)
    
    Response:
        {
            "success": true,
            "data": {
                "total": 100,
                "trades": [...]
            }
        }
    """
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    # 模拟数据
    return jsonify({
        'success': True,
        'data': {
            'total': 0,
            'trades': []
        }
    })


@app.route('/api/v1/account/performance', methods=['GET'])
@jwt_required()
def get_performance():
    """
    获取绩效统计
    
    Response:
        {
            "success": true,
            "data": {
                "total_return": 25.50,
                "sharpe_ratio": 2.15,
                "max_drawdown": -8.30,
                "win_rate": 65.5,
                "profit_factor": 2.3,
                "total_trades": 150,
                "win_trades": 98,
                "loss_trades": 52
            }
        }
    """
    return jsonify({
        'success': True,
        'data': {
            'total_return': 25.50,
            'sharpe_ratio': 2.15,
            'max_drawdown': -8.30,
            'win_rate': 65.5,
            'profit_factor': 2.3,
            'total_trades': 150,
            'win_trades': 98,
            'loss_trades': 52,
            'avg_win': 850.00,
            'avg_loss': -370.00
        }
    })


# ==================== 控制接口 ====================

@app.route('/api/v1/system/start', methods=['POST'])
@jwt_required()
def start_system():
    """
    启动交易系统
    
    Response:
        {
            "success": true,
            "message": "系统启动成功"
        }
    """
    if api_state['system_running']:
        return jsonify({
            'success': False,
            'message': '系统已在运行中'
        }), 400
    
    api_state['system_running'] = True
    
    return jsonify({
        'success': True,
        'message': '系统启动成功'
    })


@app.route('/api/v1/system/stop', methods=['POST'])
@jwt_required()
def stop_system():
    """
    停止交易系统
    
    Response:
        {
            "success": true,
            "message": "系统已停止"
        }
    """
    if not api_state['system_running']:
        return jsonify({
            'success': False,
            'message': '系统未运行'
        }), 400
    
    api_state['system_running'] = False
    
    return jsonify({
        'success': True,
        'message': '系统已停止'
    })


@app.route('/api/v1/system/status', methods=['GET'])
@jwt_required()
def get_system_status():
    """
    获取系统状态
    
    Response:
        {
            "success": true,
            "data": {
                "running": true,
                "uptime": 3600,
                "version": "2.0.0",
                "strategies": ["dual_thrust", "mean_reversion", "momentum"]
            }
        }
    """
    return jsonify({
        'success': True,
        'data': {
            'running': api_state['system_running'],
            'uptime': 3600,
            'version': '2.0.0',
            'strategies': ['dual_thrust', 'mean_reversion', 'momentum'],
            'last_update': api_state.get('last_update', datetime.now().isoformat())
        }
    })


# ==================== 通知接口 ====================

@app.route('/api/v1/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """
    获取通知列表
    
    Response:
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "type": "signal",
                    "title": "交易信号",
                    "message": "检测到买入信号",
                    "timestamp": "2024-01-01T12:00:00",
                    "read": false
                }
            ]
        }
    """
    notifications = api_state.get('notifications', [])
    
    return jsonify({
        'success': True,
        'data': notifications
    })


@app.route('/api/v1/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """
    标记通知为已读
    
    Response:
        {
            "success": true,
            "message": "已标记为已读"
        }
    """
    return jsonify({
        'success': True,
        'message': '已标记为已读'
    })


# ==================== 配置接口 ====================

@app.route('/api/v1/config', methods=['GET'])
@jwt_required()
def get_config():
    """
    获取系统配置
    
    Response:
        {
            "success": true,
            "data": {
                "max_position": 0.3,
                "stop_loss": 0.02,
                "take_profit": 0.05,
                "strategies": {...}
            }
        }
    """
    return jsonify({
        'success': True,
        'data': {
            'max_position': 0.3,
            'stop_loss': 0.02,
            'take_profit': 0.05,
            'check_interval': 5,
            'strategies': {
                'dual_thrust': {'enabled': True, 'weight': 0.4},
                'mean_reversion': {'enabled': True, 'weight': 0.3},
                'momentum': {'enabled': True, 'weight': 0.3}
            }
        }
    })


@app.route('/api/v1/config', methods=['PUT'])
@jwt_required()
def update_config():
    """
    更新系统配置
    
    Request:
        {
            "max_position": 0.3,
            "stop_loss": 0.02
        }
    
    Response:
        {
            "success": true,
            "message": "配置已更新"
        }
    """
    data = request.json
    
    # TODO: 保存配置
    
    return jsonify({
        'success': True,
        'message': '配置已更新'
    })


# ==================== 健康检查 ====================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """
    健康检查
    
    Response:
        {
            "status": "ok",
            "timestamp": "2024-01-01T12:00:00"
        }
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500


if __name__ == '__main__':
    print("=" * 70)
    print("📱 移动端API启动")
    print("=" * 70)
    print("🌐 API地址: http://localhost:5001")
    print("\n📚 API文档:")
    print("   认证: POST /api/v1/auth/login")
    print("   行情: GET  /api/v1/market/price")
    print("   K线: GET  /api/v1/market/kline")
    print("   信号: GET  /api/v1/signals/latest")
    print("   账户: GET  /api/v1/account/status")
    print("   控制: POST /api/v1/system/start")
    print("   配置: GET  /api/v1/config")
    print("\n💡 测试登录:")
    print("   用户名: admin")
    print("   密码: admin123")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5001, debug=False)



