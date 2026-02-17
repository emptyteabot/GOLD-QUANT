# AURUM 测试系统

## 📋 概述

AURUM项目的完整测试体系，包含单元测试、集成测试、性能测试和安全测试。

## 🚀 快速开始

### 1. 安装测试依赖

```bash
pip install -r requirements_test.txt
```

### 2. 运行测试

```bash
# 运行所有测试
python run_tests.py all

# 运行单元测试
python run_tests.py unit

# 运行集成测试
python run_tests.py integration

# 运行性能测试
python run_tests.py performance

# 运行安全测试
python run_tests.py security

# 生成覆盖率报告
python run_tests.py coverage
```

### 3. Windows用户

```batch
run_tests.bat all
run_tests.bat coverage
```

## 📁 目录结构

```
tests/
├── __init__.py
├── conftest.py              # 全局fixtures
├── unit/                    # 单元测试
│   ├── test_risk_manager.py
│   ├── test_ml_models.py
│   └── test_backtest.py
├── integration/             # 集成测试
│   ├── test_system.py
│   └── test_api.py
├── performance/             # 性能测试
│   └── test_performance.py
└── security/                # 安全测试
    └── test_security.py
```

## 🧪 测试类型

### 单元测试 (Unit Tests)

测试单个函数和类的功能：

- **风控模块**: 仓位计算、止损止盈、加仓逻辑
- **ML模型**: 模型训练、特征计算、信号生成
- **回测引擎**: 开平仓逻辑、统计计算、图表生成

```bash
pytest tests/unit/ -v
```

### 集成测试 (Integration Tests)

测试模块间的协作：

- **系统集成**: Agent + 风控 + 回测
- **API集成**: OKX API交互（Mock）
- **数据流**: K线 → 特征 → 信号 → 订单

```bash
pytest tests/integration/ -v
```

### 性能测试 (Performance Tests)

测试系统性能指标：

- ML训练速度 < 5秒
- 决策速度 < 50ms
- 回测速度 > 10 bars/sec

```bash
pytest tests/performance/ -v
```

### 安全测试 (Security Tests)

测试风控和安全机制：

- 单日亏损限制
- 仓位大小限制
- 止损强制执行
- 输入验证

```bash
pytest tests/security/ -v
```

## 📊 测试覆盖率

### 查看覆盖率

```bash
# 生成HTML报告
pytest --cov=. --cov-report=html

# 打开报告
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac/Linux
```

### 覆盖率目标

| 模块 | 目标 |
|-----|------|
| risk_manager.py | > 90% |
| complete_multi_agent.py | > 85% |
| backtest_engine.py | > 85% |
| **总体** | **> 80%** |

## 🔧 配置文件

- `pytest.ini`: pytest配置
- `.coveragerc`: 覆盖率配置
- `conftest.py`: 全局fixtures

## 📝 编写测试

### 测试命名规范

```python
def test_<功能>_<场景>():
    """测试描述"""
    # Arrange: 准备测试数据
    # Act: 执行测试
    # Assert: 验证结果
```

### 使用Fixtures

```python
def test_example(sample_account, sample_klines):
    """使用预定义的fixtures"""
    risk_manager = RiskManager()
    result = risk_manager.calculate_position_size(
        account=sample_account,
        price=2000.0,
        leverage=10
    )
    assert result is not None
```

### Mock外部依赖

```python
from unittest.mock import patch

@patch('okx_client.OKXClient.get_ticker')
async def test_with_mock(mock_ticker):
    mock_ticker.return_value = {'last': '2000.0'}
    # 测试代码
```

## 🐛 调试测试

### 运行单个测试

```bash
pytest tests/unit/test_risk_manager.py::TestRiskManager::test_calculate_position_size_basic -v
```

### 显示print输出

```bash
pytest tests/unit/test_risk_manager.py -v -s
```

### 进入调试模式

```bash
pytest tests/unit/test_risk_manager.py --pdb
```

## 📈 持续集成

### GitHub Actions示例

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements_test.txt
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
```

## 📚 参考文档

- [完整测试计划](docs/09_测试计划.md)
- [Pytest官方文档](https://docs.pytest.org/)
- [Coverage.py文档](https://coverage.readthedocs.io/)

## ❓ 常见问题

### Q: 测试失败怎么办？

A: 查看错误信息，检查：
1. 是否安装了所有依赖
2. 是否在正确的目录运行
3. 是否有环境变量配置问题

### Q: 如何跳过某些测试？

A: 使用pytest标记：

```python
@pytest.mark.skip(reason="暂时跳过")
def test_example():
    pass
```

### Q: 如何只运行快速测试？

A: 使用标记过滤：

```bash
pytest -m "not slow" -v
```

## 🤝 贡献

欢迎提交测试用例！请确保：

1. 测试命名清晰
2. 包含文档字符串
3. 覆盖正常+异常+边界情况
4. 运行通过且不影响其他测试

## 📞 联系

如有问题，请提交Issue或联系测试团队。

---

**Happy Testing! 🎉**
