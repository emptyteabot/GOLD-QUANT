"""API测试脚本"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"


def test_register():
    """测试注册"""
    print("\n=== 测试用户注册 ===")
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456",
        "full_name": "测试用户"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_login():
    """测试登录"""
    print("\n=== 测试用户登录 ===")
    data = {
        "username": "testuser",
        "password": "test123456"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=data)
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return result.get("data", {}).get("access_token")


def test_get_user_info(token):
    """测试获取用户信息"""
    print("\n=== 测试获取用户信息 ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_create_strategy(token):
    """测试创建策略"""
    print("\n=== 测试创建策略 ===")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "AURUM Multi-Agent v3.0",
        "description": "15+个AI协同决策",
        "symbol": "XAU-USDT-SWAP",
        "timeframe": "15m",
        "config": {
            "max_leverage": 10,
            "max_position_ratio": 0.8,
            "stop_loss_ratio": 0.015,
            "signal_threshold": 0.20,
            "confidence_threshold": 0.50,
            "agent_weights": {
                "macro": 0.30,
                "technical": 0.30,
                "ml": 0.25,
                "xaut": 0.15
            }
        }
    }
    response = requests.post(f"{BASE_URL}/strategies", json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_get_strategies(token):
    """测试获取策略列表"""
    print("\n=== 测试获取策略列表 ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/strategies", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_market_data():
    """测试市场数据"""
    print("\n=== 测试获取实时价格 ===")
    response = requests.get(f"{BASE_URL}/market/ticker?symbol=XAU-USDT-SWAP")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def main():
    """主测试流程"""
    print("=" * 50)
    print("AURUM API 测试")
    print("=" * 50)

    try:
        # 测试注册（如果已注册会失败，可以忽略）
        try:
            test_register()
        except Exception as e:
            print(f"注册失败（可能已存在）: {e}")

        # 测试登录
        token = test_login()
        if not token:
            print("登录失败，无法继续测试")
            return

        # 测试获取用户信息
        test_get_user_info(token)

        # 测试创建策略
        test_create_strategy(token)

        # 测试获取策略列表
        test_get_strategies(token)

        # 测试市场数据
        test_market_data()

        print("\n" + "=" * 50)
        print("测试完成！")
        print("=" * 50)

    except Exception as e:
        print(f"\n测试出错: {e}")


if __name__ == "__main__":
    main()
