-- AURUM数据库初始化脚本

-- 创建TimescaleDB扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ==================== 交易记录表 ====================
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    price DECIMAL(18, 8) NOT NULL,
    quantity DECIMAL(18, 8) NOT NULL,
    pnl DECIMAL(18, 8),
    strategy VARCHAR(50),
    order_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 转换为时序表
SELECT create_hypertable('trades', 'timestamp', if_not_exists => TRUE);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades (symbol);
CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades (strategy);

-- ==================== 用户表 ====================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== 策略配置表 ====================
CREATE TABLE IF NOT EXISTS strategy_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    strategy_name VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_strategy_configs_user_id ON strategy_configs (user_id);
CREATE INDEX IF NOT EXISTS idx_strategy_configs_active ON strategy_configs (is_active);

-- ==================== 持仓表 ====================
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('long', 'short')),
    quantity DECIMAL(18, 8) NOT NULL,
    entry_price DECIMAL(18, 8) NOT NULL,
    current_price DECIMAL(18, 8),
    unrealized_pnl DECIMAL(18, 8),
    leverage INTEGER DEFAULT 1,
    margin DECIMAL(18, 8),
    liquidation_price DECIMAL(18, 8),
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_positions_user_id ON positions (user_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions (symbol);

-- ==================== 账户余额表 ====================
CREATE TABLE IF NOT EXISTS account_balances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    currency VARCHAR(10) NOT NULL,
    available DECIMAL(18, 8) NOT NULL DEFAULT 0,
    frozen DECIMAL(18, 8) NOT NULL DEFAULT 0,
    total DECIMAL(18, 8) GENERATED ALWAYS AS (available + frozen) STORED,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建唯一索引
CREATE UNIQUE INDEX IF NOT EXISTS idx_account_balances_user_currency ON account_balances (user_id, currency);

-- ==================== 市场数据表 ====================
CREATE TABLE IF NOT EXISTS market_data (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NOT NULL,
    PRIMARY KEY (timestamp, symbol)
);

-- 转换为时序表
SELECT create_hypertable('market_data', 'timestamp', if_not_exists => TRUE);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data (symbol, timestamp DESC);

-- ==================== 系统日志表 ====================
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    level VARCHAR(10) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    module VARCHAR(50),
    message TEXT NOT NULL,
    extra JSONB
);

-- 转换为时序表
SELECT create_hypertable('system_logs', 'timestamp', if_not_exists => TRUE);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs (level);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs (timestamp DESC);

-- ==================== 性能指标表 ====================
CREATE TABLE IF NOT EXISTS performance_metrics (
    timestamp TIMESTAMPTZ NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    total_pnl DECIMAL(18, 8),
    daily_pnl DECIMAL(18, 8),
    win_rate DECIMAL(5, 2),
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown DECIMAL(5, 4),
    total_trades INTEGER,
    PRIMARY KEY (timestamp, user_id)
);

-- 转换为时序表
SELECT create_hypertable('performance_metrics', 'timestamp', if_not_exists => TRUE);

-- ==================== 数据保留策略 ====================
-- 市场数据保留1年
SELECT add_retention_policy('market_data', INTERVAL '1 year', if_not_exists => TRUE);

-- 系统日志保留3个月
SELECT add_retention_policy('system_logs', INTERVAL '3 months', if_not_exists => TRUE);

-- ==================== 数据压缩策略 ====================
-- 7天后压缩交易数据
SELECT add_compression_policy('trades', INTERVAL '7 days', if_not_exists => TRUE);

-- 7天后压缩市场数据
SELECT add_compression_policy('market_data', INTERVAL '7 days', if_not_exists => TRUE);

-- ==================== 创建默认管理员用户 ====================
-- 密码: admin123 (请在生产环境修改)
INSERT INTO users (username, email, password_hash, is_admin)
VALUES ('admin', 'admin@aurum.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIeWEgKK3q', TRUE)
ON CONFLICT (username) DO NOTHING;

-- ==================== 创建视图 ====================
-- 每日交易统计视图
CREATE OR REPLACE VIEW daily_trade_stats AS
SELECT
    DATE(timestamp) as trade_date,
    symbol,
    COUNT(*) as trade_count,
    SUM(CASE WHEN side = 'buy' THEN quantity ELSE 0 END) as total_buy,
    SUM(CASE WHEN side = 'sell' THEN quantity ELSE 0 END) as total_sell,
    SUM(pnl) as total_pnl
FROM trades
GROUP BY DATE(timestamp), symbol
ORDER BY trade_date DESC;

-- 用户持仓汇总视图
CREATE OR REPLACE VIEW user_position_summary AS
SELECT
    user_id,
    symbol,
    SUM(quantity) as total_quantity,
    AVG(entry_price) as avg_entry_price,
    SUM(unrealized_pnl) as total_unrealized_pnl
FROM positions
GROUP BY user_id, symbol;

-- ==================== 完成 ====================
-- 输出初始化信息
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'AURUM数据库初始化完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '已创建表：';
    RAISE NOTICE '  - trades (交易记录)';
    RAISE NOTICE '  - users (用户)';
    RAISE NOTICE '  - strategy_configs (策略配置)';
    RAISE NOTICE '  - positions (持仓)';
    RAISE NOTICE '  - account_balances (账户余额)';
    RAISE NOTICE '  - market_data (市场数据)';
    RAISE NOTICE '  - system_logs (系统日志)';
    RAISE NOTICE '  - performance_metrics (性能指标)';
    RAISE NOTICE '========================================';
    RAISE NOTICE '默认管理员账号：';
    RAISE NOTICE '  用户名: admin';
    RAISE NOTICE '  密码: admin123';
    RAISE NOTICE '  ⚠️ 请立即修改默认密码！';
    RAISE NOTICE '========================================';
END $$;
