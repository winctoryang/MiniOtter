import { create } from 'zustand';
import type { AgentExecution, AgentStep, Message, WSMessage } from '../api/types';
import { sendMessage, cancelTask } from '../api/chat';

interface ChatStore {
  messages: Message[];
  currentTaskId: string | null;
  isRunning: boolean;
  sessionId: string;

  send: (content: string) => Promise<void>;
  cancel: () => Promise<void>;
  handleWSMessage: (msg: WSMessage) => void;
  clearMessages: () => void;
}

let msgCounter = 0;

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  currentTaskId: null,
  isRunning: false,
  sessionId: 'default',

  send: async (content: string) => {
    const userMsg: Message = {
      id: `msg-${++msgCounter}`,
      role: 'user',
      content,
      timestamp: Date.now(),
    };
    set((s) => ({ messages: [...s.messages, userMsg] }));

    try {
      const res = await sendMessage({ message: content, session_id: get().sessionId });
      set({ currentTaskId: res.task_id, isRunning: true });
    } catch (e) {
      const errMsg: Message = {
        id: `msg-${++msgCounter}`,
        role: 'system',
        content: `发送失败: ${e instanceof Error ? e.message : String(e)}`,
        timestamp: Date.now(),
      };
      set((s) => ({ messages: [...s.messages, errMsg] }));
    }
  },

  cancel: async () => {
    const taskId = get().currentTaskId;
    if (taskId) {
      await cancelTask(taskId);
      set({ isRunning: false });
    }
  },

  handleWSMessage: (msg: WSMessage) => {
    set((state) => {
      const messages = [...state.messages];

      let assistantMsg = messages.find(
        (m) => m.role === 'assistant' && m.taskId === msg.task_id
      );

      if (!assistantMsg && msg.type !== 'error') {
        assistantMsg = {
          id: `msg-${++msgCounter}`,
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          taskId: msg.task_id,
          executions: [],
        };
        messages.push(assistantMsg);
      }

      if (!assistantMsg) return { messages };

      switch (msg.type) {
        case 'agent_activated': {
          if (!assistantMsg.executions) assistantMsg.executions = [];
          const agentType = msg.agent_type || 'main';

          // Skip if there's already a non-returned execution for this agent type
          const alreadyActive = assistantMsg.executions.some(
            (e) => e.agentType === agentType && !e.returned
          );
          if (alreadyActive) break;

          const newIndex = assistantMsg.executions.length;
          // The caller is the last active (not-yet-returned) execution
          const callerIndex = _findActiveCallerIndex(assistantMsg.executions);

          assistantMsg.executions.push({
            invocationIndex: newIndex,
            agentType,
            callerIndex,
            steps: [],
            returned: false,
          });
          break;
        }

        case 'thought': {
          const exec = _findOrCreateExecution(assistantMsg, msg);
          const step = _findOrCreateStep(exec, msg);
          step.thought = msg.content;
          step.phase = 'thinking';
          break;
        }

        case 'action': {
          const exec = _findOrCreateExecution(assistantMsg, msg);
          const step = _findOrCreateStep(exec, msg);
          step.actions.push({
            toolName: msg.tool_name || '',
            toolArgs: (msg.tool_args || {}) as Record<string, unknown>,
          });
          step.phase = 'acting';
          break;
        }

        case 'observation': {
          const exec = _findOrCreateExecution(assistantMsg, msg);
          const step = _findOrCreateStep(exec, msg);
          step.observations.push({
            result: msg.result,
            isError: msg.is_error || false,
            screenshot: msg.screenshot,
          });
          step.phase = 'observed';

          // If this was a route_to_* action, mark the sub-agent as returned
          // when the observation arrives on the main agent
          _markReturnedSubAgents(assistantMsg, exec);
          break;
        }

        case 'task_complete':
          // Mark all executions as returned
          if (assistantMsg.executions) {
            assistantMsg.executions.forEach((e) => (e.returned = true));
          }
          assistantMsg.content = msg.summary || '任务完成';
          return { messages, isRunning: false, currentTaskId: null };

        case 'error':
          if (assistantMsg) {
            assistantMsg.content = `错误: ${msg.message || '未知错误'}`;
          }
          return { messages, isRunning: false, currentTaskId: null };
      }

      return { messages };
    });
  },

  clearMessages: () => set({ messages: [], currentTaskId: null, isRunning: false }),
}));

/** Find the last execution that is still active (not yet returned) — that's the caller. */
function _findActiveCallerIndex(executions: AgentExecution[]): number | undefined {
  for (let i = executions.length - 1; i >= 0; i--) {
    if (!executions[i].returned) return i;
  }
  return undefined;
}

/** Find the execution for the current agent_type in the WS message.
 *  Never creates a new execution — steps must always belong to an already-activated agent. */
function _findOrCreateExecution(msg: Message, wsMsg: WSMessage): AgentExecution {
  if (!msg.executions) msg.executions = [];
  const agentType = wsMsg.agent_type || '';

  // Find the last non-returned execution matching this agent type
  for (let i = msg.executions.length - 1; i >= 0; i--) {
    if (msg.executions[i].agentType === agentType && !msg.executions[i].returned) {
      return msg.executions[i];
    }
  }

  // Fallback: auto-create the execution if agent_activated was somehow missed
  // (e.g. race condition). Attach it as a child of the last active execution.
  const callerIndex = _findActiveCallerIndex(msg.executions);
  const exec: AgentExecution = {
    invocationIndex: msg.executions.length,
    agentType,
    callerIndex,
    steps: [],
    returned: false,
  };
  msg.executions.push(exec);
  return exec;
}

function _findOrCreateStep(exec: AgentExecution, wsMsg: WSMessage): AgentStep {
  const stepNum = wsMsg.step_num ?? 0;

  let step = exec.steps.find((s) => s.stepNum === stepNum);
  if (!step) {
    step = {
      stepNum,
      agentType: exec.agentType,
      actions: [],
      observations: [],
      phase: 'thinking',
    };
    exec.steps.push(step);
  }
  return step;
}

/** When the main agent receives an observation for a route_to_* call,
 *  the corresponding sub-agent execution has finished — mark it returned. */
function _markReturnedSubAgents(msg: Message, callerExec: AgentExecution) {
  if (!msg.executions) return;
  // Any execution whose callerIndex is callerExec.invocationIndex and is not yet returned
  msg.executions.forEach((exec) => {
    if (exec.callerIndex === callerExec.invocationIndex && !exec.returned) {
      exec.returned = true;
    }
  });
}
