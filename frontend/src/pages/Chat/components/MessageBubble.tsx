import React from 'react';
import type { Message } from '../../../api/types';
import { AgentStepCard } from './AgentStepCard';

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

        {/* Text content */}
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

        {/* Agent steps */}
        {message.steps && message.steps.length > 0 && (
          <div style={{ marginTop: 8 }}>
            {message.steps.map((step, i) => (
              <AgentStepCard
                key={`${step.agentType}-${step.stepNum}`}
                step={step}
                isLatest={i === message.steps!.length - 1}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
