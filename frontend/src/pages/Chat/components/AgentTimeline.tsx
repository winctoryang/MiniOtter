import React, { useState } from 'react';
import type { AgentExecution, AgentStep } from '../../../api/types';
import { ScreenshotViewer } from './ScreenshotViewer';

// ─── Constants ────────────────────────────────────────────────────────────────

const AGENT_META: Record<string, { label: string; color: string; bg: string; borderColor: string }> = {
  main:      { label: '主 Agent',   color: '#4f46e5', bg: '#f5f3ff', borderColor: '#4f46e5' },
  gui:       { label: 'GUI Agent',  color: '#0891b2', bg: '#ecfeff', borderColor: '#0891b2' },
  text:      { label: '文本 Agent', color: '#059669', bg: '#f0fdf4', borderColor: '#059669' },
  extension: { label: '扩展 Agent', color: '#d97706', bg: '#fffbeb', borderColor: '#d97706' },
};

// ─── AgentStepItem ────────────────────────────────────────────────────────────

interface StepItemProps {
  step: AgentStep;
  isLatest: boolean;
  agentColor: string;
}

const ROUTE_TOOLS = new Set(['route_to_gui', 'route_to_text', 'route_to_extension']);

const AgentStepItem: React.FC<StepItemProps> = ({ step, isLatest, agentColor }) => {
  const [expanded, setExpanded] = useState(isLatest);
  const isRunning = step.phase === 'thinking' || step.phase === 'acting';
  // Don't show observations for route_to_* steps — the sub-agent box already shows the result
  const isRoutingStep = step.actions.some((a) => ROUTE_TOOLS.has(a.toolName));

  return (
    <div style={{
      border: `1px solid ${isRunning ? agentColor + '80' : '#e5e7eb'}`,
      borderRadius: 6,
      marginBottom: 6,
      background: '#fff',
      overflow: 'hidden',
      boxShadow: isRunning ? `0 0 0 2px ${agentColor}18` : 'none',
    }}>
      {/* Header */}
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          padding: '6px 10px',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          cursor: 'pointer',
          background: isRunning ? `${agentColor}0d` : '#fafafa',
          borderBottom: expanded ? '1px solid #e5e7eb' : 'none',
          fontSize: 12,
        }}
      >
        <span style={{ color: '#6b7280', fontWeight: 500 }}>
          Step {step.stepNum + 1}
        </span>
        {isRunning && (
          <span style={{ color: agentColor, fontSize: 11 }}>● 执行中...</span>
        )}
        {step.phase === 'observed' && (
          <span style={{ color: '#10b981', fontSize: 11 }}>✓ 完成</span>
        )}
        <span style={{ marginLeft: 'auto', color: '#aaa', fontSize: 11 }}>
          {expanded ? '▼' : '▶'}
        </span>
      </div>

      {/* Body */}
      {expanded && (
        <div style={{ padding: 10 }}>
          {step.thought && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4, fontWeight: 600 }}>
                💭 思考
              </div>
              <div style={{
                padding: '7px 10px',
                background: '#f8f9fa',
                borderRadius: 5,
                fontSize: 12,
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
              }}>
                {step.thought}
              </div>
            </div>
          )}

          {step.actions.map((action, i) => (
            <div key={i} style={{ marginBottom: 7 }}>
              <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4, fontWeight: 600 }}>
                🔧 操作
              </div>
              <code style={{
                display: 'block',
                padding: '4px 8px',
                background: '#e8f0fe',
                borderRadius: 4,
                fontSize: 11,
                color: '#1a56db',
                wordBreak: 'break-all',
              }}>
                {action.toolName}({Object.entries(action.toolArgs)
                  .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
                  .join(', ')})
              </code>
            </div>
          ))}

          {!isRoutingStep && step.observations.map((obs, i) => (
            <div key={i} style={{ marginBottom: 7 }}>
              <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4, fontWeight: 600 }}>
                👁 观察 {obs.isError && <span style={{ color: '#ef4444' }}>(错误)</span>}
              </div>
              {obs.screenshot ? (
                <ScreenshotViewer screenshot={obs.screenshot} actions={step.actions} />
              ) : (
                <pre style={{
                  padding: '6px 10px',
                  background: obs.isError ? '#fef2f2' : '#f8f9fa',
                  borderRadius: 5,
                  fontSize: 11,
                  overflow: 'auto',
                  maxHeight: 200,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                }}>
                  {typeof obs.result === 'string'
                    ? obs.result
                    : JSON.stringify(obs.result, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ─── Nested agent box ─────────────────────────────────────────────────────────

/**
 * Build a tree: for each execution, find which steps fall *before* a child
 * sub-agent invocation vs. *after* it, so we can interleave them naturally.
 *
 * Strategy: render steps in order. Whenever we would render a step whose
 * actions contain a `route_to_*` call AND the corresponding child execution
 * exists, inject the child box right after that step's observation.
 *
 * For simplicity we render:
 *   [steps before any route] → [child box (if any)] → [steps after route]
 * Since main agent typically has 1 route per child, this works well.
 * Multiple children are rendered in invocationIndex order.
 */
interface AgentBoxProps {
  execution: AgentExecution;
  allExecutions: AgentExecution[];
  /** children executions whose callerIndex === this execution's invocationIndex */
  children: AgentExecution[];
}

const AgentBox: React.FC<AgentBoxProps> = ({ execution, allExecutions, children }) => {
  const meta = AGENT_META[execution.agentType] ?? {
    label: execution.agentType,
    color: '#6b7280',
    bg: '#f9fafb',
    borderColor: '#6b7280',
  };
  const isRunning = !execution.returned;

  // Sort children by invocationIndex so they appear in call order
  const sortedChildren = [...children].sort((a, b) => a.invocationIndex - b.invocationIndex);

  // We interleave own steps with child boxes.
  // Heuristic: each route_to_* action corresponds to one child (in order).
  // Split steps into segments: before first child call, between calls, after last.
  // For now: render all own steps first (collapsed except latest), then child boxes.
  // This matches the ReAct flow: main thinks → routes → (child runs) → main observes.
  const ownSteps = execution.steps;
  const latestStepIndex = ownSteps.length - 1;

  return (
    <div style={{
      border: `2px solid ${meta.borderColor}`,
      borderRadius: 10,
      background: meta.bg,
      padding: '0 0 10px 0',
      marginBottom: 8,
      position: 'relative',
    }}>
      {/* Header bar */}
      <div style={{
        padding: '8px 14px',
        borderBottom: `1px solid ${meta.borderColor}40`,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        borderRadius: '8px 8px 0 0',
        background: `${meta.color}12`,
      }}>
        <span style={{
          padding: '2px 10px',
          borderRadius: 4,
          background: meta.color,
          color: '#fff',
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: 0.4,
        }}>
          {meta.label}
        </span>
        {isRunning && (
          <span style={{ fontSize: 11, color: meta.color, fontWeight: 500 }}>● 运行中</span>
        )}
        {execution.returned && (
          <span style={{ fontSize: 11, color: '#10b981', fontWeight: 500 }}>✓ 已完成</span>
        )}
      </div>

      {/* Content: own steps + nested children interleaved */}
      <div style={{ padding: '10px 12px 0 12px' }}>
        {/* Steps before children (all own steps that aren't "route" observations yet) */}
        {/* We render steps and children in interleaved order based on invocationIndex sequence */}
        <InterleavedContent
          ownSteps={ownSteps}
          latestStepIndex={latestStepIndex}
          isRunning={isRunning}
          agentColor={meta.color}
          children={sortedChildren}
          allExecutions={allExecutions}
        />
      </div>
    </div>
  );
};

// ─── Interleaved rendering ────────────────────────────────────────────────────

interface InterleavedProps {
  ownSteps: AgentStep[];
  latestStepIndex: number;
  isRunning: boolean;
  agentColor: string;
  children: AgentExecution[];
  allExecutions: AgentExecution[];
}

/**
 * Render parent's steps and child sub-agent boxes interleaved in natural order.
 *
 * For each child, we look for which step triggered the route_to_* call.
 * We render steps up to (and including) that step's actions, then inject the
 * child box (representing the sub-agent run), then continue with remaining steps.
 *
 * If we can't determine the trigger step we fall back to showing all own steps
 * first, then all children.
 */
const InterleavedContent: React.FC<InterleavedProps> = ({
  ownSteps, latestStepIndex, isRunning, agentColor, children, allExecutions,
}) => {
  // Map each child to the own-step index that triggered it.
  // A route_to_* action appears as an action named route_to_gui / route_to_text / etc.
  const routeToolNames = new Set(['route_to_gui', 'route_to_text', 'route_to_extension']);

  // Build segments: array of { type: 'step', step, index } | { type: 'child', execution }
  type Segment =
    | { type: 'step'; step: AgentStep; index: number }
    | { type: 'child'; execution: AgentExecution };

  const segments: Segment[] = [];
  let childQueue = [...children]; // children to inject, in order

  for (let i = 0; i < ownSteps.length; i++) {
    const step = ownSteps[i];
    segments.push({ type: 'step', step, index: i });

    // After a step that contains a route_to_* action, inject the next child
    const hasRoute = step.actions.some((a) => routeToolNames.has(a.toolName));
    if (hasRoute && childQueue.length > 0) {
      const child = childQueue.shift()!;
      segments.push({ type: 'child', execution: child });
    }
  }

  // Remaining children (e.g. if the route step hasn't completed yet)
  for (const child of childQueue) {
    segments.push({ type: 'child', execution: child });
  }

  if (segments.length === 0) {
    return (
      <div style={{ color: '#aaa', fontSize: 12, textAlign: 'center', padding: '8px 0' }}>
        等待执行...
      </div>
    );
  }

  return (
    <>
      {segments.map((seg) => {
        if (seg.type === 'step') {
          const isLatest = seg.index === latestStepIndex && isRunning;
          return (
            <AgentStepItem
              key={`step-${seg.step.stepNum}`}
              step={seg.step}
              isLatest={isLatest}
              agentColor={agentColor}
            />
          );
        }

        // Child sub-agent box
        const childExec = seg.execution;
        const grandChildren = allExecutions.filter(
          (e) => e.callerIndex === childExec.invocationIndex
        );
        return (
          <div key={`child-${childExec.invocationIndex}`} style={{ margin: '4px 0 8px 0' }}>
            {/* Call indicator */}
            <div style={{
              fontSize: 11,
              color: agentColor,
              marginBottom: 4,
              paddingLeft: 2,
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}>
              <span style={{ fontSize: 13 }}>↓</span>
              <span>调用子 Agent</span>
            </div>
            <AgentBox
              execution={childExec}
              allExecutions={allExecutions}
              children={grandChildren}
            />
            {/* Return indicator (only after sub-agent returned) */}
            {childExec.returned && (
              <div style={{
                fontSize: 11,
                color: agentColor,
                marginTop: 2,
                marginBottom: 4,
                paddingLeft: 2,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}>
                <span style={{ fontSize: 13 }}>↑</span>
                <span>子 Agent 返回</span>
              </div>
            )}
          </div>
        );
      })}
    </>
  );
};

// ─── AgentTimeline (main export) ──────────────────────────────────────────────

interface TimelineProps {
  executions: AgentExecution[];
}

export const AgentTimeline: React.FC<TimelineProps> = ({ executions }) => {
  if (executions.length === 0) return null;

  // Find root executions (no caller = top level, typically just the main agent)
  const roots = executions.filter((e) => e.callerIndex === undefined);

  return (
    <div style={{ padding: '2px 0' }}>
      {roots.map((root) => {
        const directChildren = executions.filter(
          (e) => e.callerIndex === root.invocationIndex
        );
        return (
          <AgentBox
            key={root.invocationIndex}
            execution={root}
            allExecutions={executions}
            children={directChildren}
          />
        );
      })}
    </div>
  );
};
