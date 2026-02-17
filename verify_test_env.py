"""
测试环境验证脚本
检查测试环境是否正确配置
"""
import sys
import importlib
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"✓ Python版本: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ⚠️  警告: 建议使用Python 3.8+")
        return False
    return True


def check_dependencies():
    """检查测试依赖"""
    required = [
        'pytest',
        'pytest_cov',
        'pytest_asyncio',
        'pandas',
        'numpy',
        'sklearn'
    ]

    missing = []
    for package in required:
        try:
            importlib.import_module(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (未安装)")
            missing.append(package)

    return len(missing) == 0, missing


def check_test_structure():
    """检查测试目录结构"""
    base_path = Path(__file__).parent
    test_path = base_path / 'tests'

    required_dirs = [
        'tests',
        'tests/unit',
        'tests/integration',
        'tests/performance',
        'tests/security'
    ]

    required_files = [
        'tests/__init__.py',
        'tests/conftest.py',
        'tests/unit/test_risk_manager.py',
        'tests/unit/test_ml_models.py',
        'tests/unit/test_backtest.py',
        'pytest.ini',
        '.coveragerc'
    ]

    all_ok = True

    print("\n检查目录结构:")
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ {dir_path}/ (不存在)")
            all_ok = False

    print("\n检查测试文件:")
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (不存在)")
            all_ok = False

    return all_ok


def check_source_files():
    """检查源代码文件"""
    base_path = Path(__file__).parent

    required_files = [
        'risk_manager.py',
        'complete_multi_agent.py',
        'backtest_engine.py',
        'config.py'
    ]

    print("\n检查源代码文件:")
    all_ok = True
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (不存在)")
            all_ok = False

    return all_ok


def main():
    """主函数"""
    print("="*60)
    print("AURUM 测试环境验证")
    print("="*60)

    print("\n1. 检查Python版本:")
    python_ok = check_python_version()

    print("\n2. 检查依赖包:")
    deps_ok, missing = check_dependencies()

    print("\n3. 检查测试结构:")
    structure_ok = check_test_structure()

    print("\n4. 检查源代码:")
    source_ok = check_source_files()

    print("\n" + "="*60)
    print("验证结果:")
    print("="*60)

    if python_ok and deps_ok and structure_ok and source_ok:
        print("✅ 测试环境配置正确！")
        print("\n可以运行测试:")
        print("  python run_tests.py all")
        print("  python run_tests.py coverage")
        return 0
    else:
        print("❌ 测试环境配置不完整")

        if not deps_ok:
            print("\n缺少依赖包，请运行:")
            print("  pip install -r requirements_test.txt")

        if not structure_ok:
            print("\n测试目录结构不完整")

        if not source_ok:
            print("\n源代码文件缺失")

        return 1


if __name__ == "__main__":
    sys.exit(main())
