"""
测试运行脚本
提供便捷的测试执行命令
"""
import sys
import subprocess
from pathlib import Path


def run_all_tests():
    """运行所有测试"""
    print("🧪 运行所有测试...")
    cmd = ["pytest", "tests/", "-v"]
    subprocess.run(cmd)


def run_unit_tests():
    """运行单元测试"""
    print("🧪 运行单元测试...")
    cmd = ["pytest", "tests/unit/", "-v", "-m", "unit"]
    subprocess.run(cmd)


def run_integration_tests():
    """运行集成测试"""
    print("🧪 运行集成测试...")
    cmd = ["pytest", "tests/integration/", "-v", "-m", "integration"]
    subprocess.run(cmd)


def run_performance_tests():
    """运行性能测试"""
    print("🧪 运行性能测试...")
    cmd = ["pytest", "tests/performance/", "-v", "-m", "performance"]
    subprocess.run(cmd)


def run_security_tests():
    """运行安全测试"""
    print("🧪 运行安全测试...")
    cmd = ["pytest", "tests/security/", "-v", "-m", "security"]
    subprocess.run(cmd)


def run_with_coverage():
    """运行测试并生成覆盖率报告"""
    print("🧪 运行测试并生成覆盖率报告...")
    cmd = [
        "pytest",
        "tests/",
        "-v",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing"
    ]
    subprocess.run(cmd)
    print("\n✅ 覆盖率报告已生成: htmlcov/index.html")


def run_specific_test(test_path):
    """运行特定测试"""
    print(f"🧪 运行测试: {test_path}")
    cmd = ["pytest", test_path, "-v"]
    subprocess.run(cmd)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python run_tests.py all              # 运行所有测试")
        print("  python run_tests.py unit             # 运行单元测试")
        print("  python run_tests.py integration      # 运行集成测试")
        print("  python run_tests.py performance      # 运行性能测试")
        print("  python run_tests.py security         # 运行安全测试")
        print("  python run_tests.py coverage         # 运行测试并生成覆盖率")
        print("  python run_tests.py <test_file>      # 运行特定测试文件")
        return

    command = sys.argv[1]

    if command == "all":
        run_all_tests()
    elif command == "unit":
        run_unit_tests()
    elif command == "integration":
        run_integration_tests()
    elif command == "performance":
        run_performance_tests()
    elif command == "security":
        run_security_tests()
    elif command == "coverage":
        run_with_coverage()
    else:
        # 假设是测试文件路径
        run_specific_test(command)


if __name__ == "__main__":
    main()
