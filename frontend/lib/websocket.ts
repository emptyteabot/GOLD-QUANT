// WebSocket 实时数据服务
import { WebSocketMessage } from '@/types';

type MessageHandler = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectTimer: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private url: string;

  constructor(url: string = 'ws://localhost:8000/ws') {
    this.url = url;
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('✅ WebSocket 连接成功');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('❌ 解析消息失败:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket 错误:', error);
      };

      this.ws.onclose = () => {
        console.log('🔌 WebSocket 连接关闭');
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('❌ WebSocket 连接失败:', error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ 达到最大重连次数，停止重连');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

    console.log(`🔄 ${delay}ms 后尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private handleMessage(message: WebSocketMessage) {
    const handlers = this.handlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => handler(message.data));
    }
  }

  subscribe(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    // 返回取消订阅函数
    return () => {
      const handlers = this.handlers.get(type);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }

  send(type: string, data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    } else {
      console.warn('⚠️ WebSocket 未连接，无法发送消息');
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.handlers.clear();
  }
}

// 单例模式
export const wsService = new WebSocketService();
