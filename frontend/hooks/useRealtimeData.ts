// 实时数据订阅 Hook
import { useEffect } from 'react';
import { wsService } from '@/lib/websocket';
import { useAppStore } from '@/stores/useAppStore';

export function useRealtimeData() {
  const { setAccount, setPositions, addSignal, updateMarketData } = useAppStore();

  useEffect(() => {
    // 连接WebSocket
    wsService.connect();

    // 订阅账户更新
    const unsubAccount = wsService.subscribe('account', (data) => {
      setAccount(data);
    });

    // 订阅持仓更新
    const unsubPosition = wsService.subscribe('position', (data) => {
      setPositions(data);
    });

    // 订阅信号更新
    const unsubSignal = wsService.subscribe('signal', (data) => {
      addSignal(data);
    });

    // 订阅价格更新
    const unsubPrice = wsService.subscribe('price', (data) => {
      updateMarketData(data.symbol, data);
    });

    // 清理函数
    return () => {
      unsubAccount();
      unsubPosition();
      unsubSignal();
      unsubPrice();
      wsService.disconnect();
    };
  }, [setAccount, setPositions, addSignal, updateMarketData]);
}
