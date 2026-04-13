import React from 'react';
import { useChatStore } from '../../stores/chatStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { MessageList } from './components/MessageList';
import { InputBar } from './components/InputBar';

const ChatPage: React.FC = () => {
  const sessionId = useChatStore((s) => s.sessionId);
  useWebSocket(sessionId);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
    }}>
      <div style={{
        padding: '16px 24px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-secondary)',
        fontSize: 16,
        fontWeight: 600,
      }}>
        对话
      </div>
      <MessageList />
      <InputBar />
    </div>
  );
};

export default ChatPage;
