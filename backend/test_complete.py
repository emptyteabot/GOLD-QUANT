"""
AURUM后端API - 一键测试脚本
测试所有核心功能
"""
import sys
import time


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(step, text):
    """打印步骤"""
    print(f"\n[{step}] {text}")


def check_dependencies():
    """检查依赖"""
    print_step("1/6", "检查Python依赖...")

    required = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "jose",
        "passlib"
    ]

    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (缺失)")
            missing.append(package)

    if missing:
        print(f"\n缺少依赖包: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        return False

    print("\n所有依赖已安装！")
    return True


def check_database():
    """检查数据库连接"""
    print_step("2/6", "检查数据库连接...")

    try:
        from app.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("  ✓ 数据库连接成功")
            return True
    except Exception as e:
        print(f"  ✗ 数据库连接失败: {e}")
        print("\n请确保:")
        print("  1. PostgreSQL已启动")
        print("  2. 数据库已创建 (aurum_db)")
        print("  3. .env配置正确")
        return False


def check_tables():
    """检查数据表"""
    print_step("3/6", "检查数据表...")

    try:
        from app.database import engine
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        required_tables = ["users", "strategies", "orders", "positions", "api_keys"]

        for table in required_tables:
            if table in tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (缺失)")

        if len(tables) >= len(required_tables):
            print("\n数据表检查通过！")
            return True
        else:
            print("\n请运行数据库初始化:")
            print("  python init_db.py")
            return False

    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
        return False


def test_api_endpoints():
    """测试API端点"""
    print_step("4/6", "测试API端点...")

    try:
        import requests

        base_url = "http://localhost:8000"

        # 测试健康检查
        print("\n  测试健康检查...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("  ✓ 健康检查通过")
        else:
            print(f"  ✗ 健康检查失败: {response.status_code}")
            return False

        # 测试根路径
        print("\n  测试根路径...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ API名称: {data.get('name')}")
            print(f"  ✓ 版本: {data.get('version')}")
        else:
            print(f"  ✗ 根路径失败: {response.status_code}")
            return False

        print("\nAPI端点测试通过！")
        return True

    except requests.exceptions.ConnectionError:
        print("\n  ✗ 无法连接到服务器")
        print("  请先启动服务: python -m uvicorn app.main:app")
        return False
    except Exception as e:
        print(f"\n  ✗ 测试失败: {e}")
        return False


def test_authentication():
    """测试认证功能"""
    print_step("5/6", "测试认证功能...")

    try:
        import requests
        import uuid

        base_url = "http://localhost:8000/api/v1"

        # 生成随机用户名
        username = f"test_{uuid.uuid4().hex[:8]}"

        # 测试注册
        print("\n  测试用户注册...")
        register_data = {
            "username": username,
            "email": f"{username}@test.com",
            "password": "test123456",
            "full_name": "测试用户"
        }

        response = requests.post(f"{base_url}/auth/register", json=register_data)
        if response.status_code == 201:
            print(f"  ✓ 注册成功: {username}")
            data = response.json()
            token = data.get("data", {}).get("access_token")
        else:
            print(f"  ✗ 注册失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return False

        # 测试登录
        print("\n  测试用户登录...")
        login_data = {
            "username": username,
            "password": "test123456"
        }

        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            print("  ✓ 登录成功")
            data = response.json()
            token = data.get("data", {}).get("access_token")
        else:
            print(f"  ✗ 登录失败: {response.status_code}")
            return False

        # 测试获取用户信息
        print("\n  测试获取用户信息...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/users/me", headers=headers)
        if response.status_code == 200:
            data = response.json()
            user = data.get("data", {})
            print(f"  ✓ 用户名: {user.get('username')}")
            print(f"  ✓ 邮箱: {user.get('email')}")
        else:
            print(f"  ✗ 获取用户信息失败: {response.status_code}")
            return False

        print("\n认证功能测试通过！")
        return True

    except Exception as e:
        print(f"\n  ✗ 测试失败: {e}")
        return False


def print_summary(results):
    """打印测试总结"""
    print_step("6/6", "测试总结")

    print("\n测试结果:")
    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {status} - {name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n" + "=" * 60)
        print("  🎉 所有测试通过！后端API已就绪！")
        print("=" * 60)
        print("\n下一步:")
        print("  1. 访问API文档: http://localhost:8000/docs")
        print("  2. 运行完整测试: python test_api.py")
        print("  3. 开始开发前端应用")
    else:
        print("\n" + "=" * 60)
        print("  ⚠️  部分测试失败，请检查上述错误")
        print("=" * 60)

    return all_passed


def main():
    """主函数"""
    print_header("AURUM后端API - 完整性测试")

    results = {}

    # 1. 检查依赖
    results["依赖检查"] = check_dependencies()
    if not results["依赖检查"]:
        print("\n请先安装依赖后再运行测试")
        sys.exit(1)

    time.sleep(1)

    # 2. 检查数据库
    results["数据库连接"] = check_database()
    if not results["数据库连接"]:
        print("\n请先配置数据库后再运行测试")
        sys.exit(1)

    time.sleep(1)

    # 3. 检查数据表
    results["数据表检查"] = check_tables()
    if not results["数据表检查"]:
        print("\n请先初始化数据库后再运行测试")
        sys.exit(1)

    time.sleep(1)

    # 4. 测试API端点
    results["API端点"] = test_api_endpoints()

    time.sleep(1)

    # 5. 测试认证
    if results["API端点"]:
        results["认证功能"] = test_authentication()
    else:
        results["认证功能"] = False

    time.sleep(1)

    # 6. 打印总结
    success = print_summary(results)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试出错: {e}")
        sys.exit(1)
