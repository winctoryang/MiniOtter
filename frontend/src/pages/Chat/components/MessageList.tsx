import React from 'react';
import { useChatStore } from '../../../stores/chatStore';
import { useAutoScroll } from '../../../hooks/useAutoScroll';
import { MessageBubble } from './MessageBubble';

export const MessageList: React.FC = () => {
  const messages = useChatStore((s) => s.messages);
  const isRunning = useChatStore((s) => s.isRunning);
  const scrollRef = useAutoScroll<HTMLDivElement>([messages, isRunning]);

  return (
    <div
      ref={scrollRef}
      style={{
        flex: 1,
        overflow: 'auto',
        padding: '24px 0',
      }}
    >
      {messages.length === 0 && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: 'var(--text-secondary)',
          gap: 12,
        }}>
          <div style={{ fontSize: 48 }}>🦦</div>
          <div style={{ fontSize: 18, fontWeight: 600 }}>MiniOtter</div>
          <div style={{ fontSize: 14 }}>输入任务，让 Agent 帮你操作电脑</div>
        </div>
      )}

      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {isRunning && (
        <div style={{
          padding: '8px 24px',
          color: 'var(--text-secondary)',
          fontSize: 13,
        }}>
          Agent 执行中...
        </div>
      )}
    </div>
  );
};
