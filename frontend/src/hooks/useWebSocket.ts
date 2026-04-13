import { useEffect, useRef } from 'react';
import type { WSMessage } from '../api/types';
import { useChatStore } from '../stores/chatStore';

export function useWebSocket(sessionId: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const handleWSMessage = useChatStore((s) => s.handleWSMessage);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/stream?session_id=${sessionId}`;

    const socket = new WebSocket(url);

    socket.onopen = () => {
      console.log('WebSocket connected');
    };

    socket.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);
        handleWSMessage(msg);
      } catch (e) {
        console.error('Failed to parse WS message:', e);
      }
    };

    socket.onclose = () => {
      console.log('WebSocket disconnected');
    };

    socket.onerror = (e) => {
      console.error('WebSocket error:', e);
    };

    wsRef.current = socket;

    return () => {
      socket.close();
    };
  }, [sessionId, handleWSMessage]);

  return wsRef;
}
