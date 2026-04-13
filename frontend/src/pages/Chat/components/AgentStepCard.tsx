import React, { useState } from 'react';
import type { AgentStep } from '../../../api/types';
import { ScreenshotViewer } from './ScreenshotViewer';

const AGENT_LABELS: Record<string, string> = {
  main: '主Agent',
  gui: 'GUI Agent',
  text: '文本Agent',
  extension: '扩展Agent',
};

interface Props {
  step: AgentStep;
  isLatest: boolean;
}

export const AgentStepCard: React.FC<Props> = ({ step, isLatest }) => {
  const [expanded, setExpanded] = useState(isLatest);
  const agentLabel = AGENT_LABELS[step.agentType] || step.agentType;
  const isRunning = step.phase === 'thinking' || step.phase === 'acting';

  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: 8,
      marginBottom: 8,
      background: '#fff',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          cursor: 'pointer',
          background: isRunning ? 'var(--accent-light)' : '#fafafa',
          borderBottom: expanded ? '1px solid var(--border)' : 'none',
          fontSize: 13,
        }}
      >
        <span style={{
          display: 'inline-block',
          padding: '2px 8px',
          borderRadius: 4,
          background: 'var(--accent)',
          color: '#fff',
          fontSize: 11,
          fontWeight: 600,
        }}>
          {agentLabel}
        </span>
        <span style={{ color: 'var(--text-secondary)' }}>
          Step {step.stepNum + 1}
        </span>
        {isRunning && (
          <span style={{ color: 'var(--warning)', fontSize: 12 }}>
            ● 执行中...
          </span>
        )}
        {step.phase === 'observed' && (
          <span style={{ color: 'var(--success)', fontSize: 12 }}>✓</span>
        )}
        <span style={{ marginLeft: 'auto', color: '#aaa' }}>
          {expanded ? '▼' : '▶'}
        </span>
      </div>

      {/* Body */}
      {expanded && (
        <div style={{ padding: 12 }}>
          {/* Thought */}
          {step.thought && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 4, fontWeight: 600 }}>
                💭 思考
              </div>
              <div style={{
                padding: '8px 12px',
                background: '#f8f9fa',
                borderRadius: 6,
                fontSize: 13,
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
              }}>
                {step.thought}
              </div>
            </div>
          )}

          {/* Actions */}
          {step.actions.map((action, i) => (
            <div key={i} style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 4, fontWeight: 600 }}>
                🔧 操作
              </div>
              <code style={{
                display: 'inline-block',
                padding: '4px 10px',
                background: '#e8f0fe',
                borderRadius: 4,
                fontSize: 12,
                color: '#1a56db',
              }}>
                {action.toolName}({Object.entries(action.toolArgs).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(', ')})
              </code>
            </div>
          ))}

          {/* Observations */}
          {step.observations.map((obs, i) => (
            <div key={i} style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 4, fontWeight: 600 }}>
                👁 观察 {obs.isError && <span style={{ color: 'var(--error)' }}>(错误)</span>}
              </div>
              {obs.screenshot ? (
                <ScreenshotViewer screenshot={obs.screenshot} actions={step.actions} />
              ) : (
                <pre style={{
                  padding: '8px 12px',
                  background: obs.isError ? '#fef2f2' : '#f8f9fa',
                  borderRadius: 6,
                  fontSize: 12,
                  overflow: 'auto',
                  maxHeight: 200,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                }}>
                  {typeof obs.result === 'string' ? obs.result : JSON.stringify(obs.result, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
