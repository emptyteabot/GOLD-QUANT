// API 请求工具
import axios from 'axios';
import { Strategy, BacktestResult } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 详细的错误处理
    if (error.response) {
      // 服务器返回错误状态码
      console.error('API Error:', {
        status: error.response.status,
        data: error.response.data,
        url: error.config?.url,
      });
    } else if (error.request) {
      // 请求已发送但没有收到响应（网络问题或CORS）
      console.error('Network Error:', {
        message: '无法连接到后端服务，请检查：',
        checks: [
          '1. 后端服务是否启动 (http://localhost:8000)',
          '2. CORS配置是否正确',
          '3. 网络连接是否正常',
        ],
      });
    } else {
      // 请求配置错误
      console.error('Request Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// API 方法
export const apiClient = {
  // 获取账户信息
  getAccount: () => api.get('/api/account'),

  // 获取持仓信息
  getPositions: () => api.get('/api/positions'),

  // 获取交易信号
  getSignals: (limit = 50) => api.get(`/api/signals?limit=${limit}`),

  // 获取市场数据
  getMarketData: (symbol: string) => api.get(`/api/market/${symbol}`),

  // 策略管理
  getStrategies: () => api.get('/api/strategies'),
  getStrategy: (id: string) => api.get(`/api/strategies/${id}`),
  createStrategy: (data: Partial<Strategy>) => api.post('/api/strategies', data),
  updateStrategy: (id: string, data: Partial<Strategy>) => api.put(`/api/strategies/${id}`, data),
  deleteStrategy: (id: string) => api.delete(`/api/strategies/${id}`),
  startStrategy: (id: string) => api.post(`/api/strategies/${id}/start`),
  stopStrategy: (id: string) => api.post(`/api/strategies/${id}/stop`),

  // 回测
  runBacktest: (strategyId: string, params: any) =>
    api.post(`/api/backtest/${strategyId}`, params),
  getBacktestResult: (id: string): Promise<BacktestResult> =>
    api.get(`/api/backtest/${id}`),

  // 交易操作
  placeOrder: (data: any) => api.post('/api/orders', data),
  closePosition: (symbol: string) => api.post('/api/positions/close', { symbol }),
};

export default api;
