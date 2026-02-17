#!/usr/bin/env python3
"""
前后端联调测试脚本
测试所有API端点是否正常工作
"""
import requests
import sys
from typing import Dict, Any
from datetime import datetime

# 配置
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 10

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def test_endpoint(name: str, url: str, method: str = "GET", data: Dict = None) -> bool:
    """测试单个API端点"""
    try:
        print_info(f"测试 {name}...")

        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT)
        else:
            print_error(f"不支持的HTTP方法: {method}")
            return False

        if response.status_code == 200:
            result = response.json()
            print_success(f"{name} - 状态码: {response.status_code}")
            print(f"  响应数据: {str(result)[:100]}...")
            return True
        else:
            print_error(f"{name} - 状态码: {response.status_code}")
            print(f"  错误信息: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print_error(f"{name} - 连接失败，请确保后端服务已启动")
        return False
    except requests.exceptions.Timeout:
        print_error(f"{name} - 请求超时")
        return False
    except Exception as e:
        print_error(f"{name} - 异常: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print(f"{Colors.BLUE}🔧 Gold Advisor Pro - 前后端联调测试{Colors.END}")
    print(f"API地址: {API_BASE_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    results = []

    # 1. 测试根路径
    results.append(test_endpoint(
        "根路径",
        f"{API_BASE_URL}/"
    ))

    # 2. 测试市场状态
    results.append(test_endpoint(
        "市场状态",
        f"{API_BASE_URL}/api/market-status"
    ))

    # 3. 测试标的列表
    results.append(test_endpoint(
        "标的列表",
        f"{API_BASE_URL}/api/instruments"
    ))

    # 4. 测试实时行情
    results.append(test_endpoint(
        "实时行情",
        f"{API_BASE_URL}/api/quotes?codes=518880,518800"
    ))

    # 5. 测试K线数据
    results.append(test_endpoint(
        "K线数据",
        f"{API_BASE_URL}/api/klines?code=518880&period=5&days=5"
    ))

    # 6. 测试交易信号
    results.append(test_endpoint(
        "交易信号",
        f"{API_BASE_URL}/api/signals?codes=518880,518800"
    ))

    # 7. 测试宏观分析
    results.append(test_endpoint(
        "宏观分析",
        f"{API_BASE_URL}/api/macro"
    ))

    # 8. 测试行情识别
    results.append(test_endpoint(
        "行情识别",
        f"{API_BASE_URL}/api/regime?code=518880"
    ))

    # 统计结果
    print("\n" + "="*60)
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\n测试结果汇总:")
    print(f"  总计: {total} 个测试")
    print_success(f"通过: {passed} 个")
    if failed > 0:
        print_error(f"失败: {failed} 个")

    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\n  成功率: {success_rate:.1f}%")

    if success_rate == 100:
        print_success("\n🎉 所有测试通过！前后端联调成功！")
        return 0
    elif success_rate >= 80:
        print_warning("\n⚠️  大部分测试通过，但仍有问题需要解决")
        return 1
    else:
        print_error("\n❌ 测试失败较多，请检查后端服务")
        return 1

if __name__ == "__main__":
    sys.exit(main())
