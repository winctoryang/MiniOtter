import React, { useState } from 'react';
import { useChatStore } from '../../../stores/chatStore';

export const InputBar: React.FC = () => {
  const [input, setInput] = useState('');
  const { send, cancel, isRunning } = useChatStore();

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isRunning) return;
    setInput('');
    await send(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{
      padding: '16px 24px',
      borderTop: '1px solid var(--border)',
      background: 'var(--bg-secondary)',
      display: 'flex',
      gap: 12,
      alignItems: 'flex-end',
    }}>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="输入你的任务..."
        disabled={isRunning}
        rows={1}
        style={{
          flex: 1,
          padding: '10px 16px',
          border: '1px solid var(--border)',
          borderRadius: 8,
          fontSize: 14,
          resize: 'none',
          outline: 'none',
          fontFamily: 'inherit',
          minHeight: 42,
          maxHeight: 120,
        }}
      />
      {isRunning ? (
        <button
          onClick={cancel}
          style={{
            padding: '10px 20px',
            background: 'var(--error)',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            cursor: 'pointer',
            fontSize: 14,
            fontWeight: 500,
          }}
        >
          取消
        </button>
      ) : (
        <button
          onClick={handleSend}
          disabled={!input.trim()}
          style={{
            padding: '10px 20px',
            background: input.trim() ? 'var(--accent)' : '#ccc',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            cursor: input.trim() ? 'pointer' : 'not-allowed',
            fontSize: 14,
            fontWeight: 500,
          }}
        >
          发送
        </button>
      )}
    </div>
  );
};
