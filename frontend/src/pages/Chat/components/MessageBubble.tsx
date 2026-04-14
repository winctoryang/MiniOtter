import React from 'react';
import type { Message } from '../../../api/types';
import { AgentTimeline } from './AgentTimeline';

interface Props {
  message: Message;
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 16,
      padding: '0 24px',
    }}>
      <div style={{
        maxWidth: isUser ? '60%' : '85%',
        minWidth: 100,
      }}>
        {/* Role label */}
        <div style={{
          fontSize: 11,
          color: 'var(--text-secondary)',
          marginBottom: 4,
          textAlign: isUser ? 'right' : 'left',
        }}>
          {isUser ? '你' : isSystem ? '系统' : 'MiniOtter'}
        </div>

        {/* Agent timeline (shown before final result) */}
        {message.executions && message.executions.length > 0 && (
          <div style={{ marginBottom: message.content ? 8 : 0 }}>
            <AgentTimeline executions={message.executions} />
          </div>
        )}

        {/* Text content (final result, shown at bottom) */}
        {message.content && (
          <div style={{
            padding: '10px 16px',
            borderRadius: 12,
            background: isUser ? 'var(--accent)' : isSystem ? '#fef3c7' : 'var(--bg-secondary)',
            color: isUser ? '#fff' : 'var(--text-primary)',
            border: isUser ? 'none' : '1px solid var(--border)',
            fontSize: 14,
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
          }}>
            {message.content}
          </div>
        )}
      </div>
    </div>
  );
};
