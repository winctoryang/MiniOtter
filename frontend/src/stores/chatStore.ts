import { create } from 'zustand';
import type { AgentStep, Message, WSMessage } from '../api/types';
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

      // Find or create the assistant message for this task
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
          steps: [],
        };
        messages.push(assistantMsg);
      }

      if (!assistantMsg) return { messages };

      switch (msg.type) {
        case 'agent_activated':
          assistantMsg.agentType = msg.agent_type;
          break;

        case 'thought': {
          const step = _findOrCreateStep(assistantMsg, msg);
          step.thought = msg.content;
          step.phase = 'thinking';
          break;
        }

        case 'action': {
          const step = _findOrCreateStep(assistantMsg, msg);
          step.actions.push({
            toolName: msg.tool_name || '',
            toolArgs: (msg.tool_args || {}) as Record<string, unknown>,
          });
          step.phase = 'acting';
          break;
        }

        case 'observation': {
          const step = _findOrCreateStep(assistantMsg, msg);
          step.observations.push({
            result: msg.result,
            isError: msg.is_error || false,
            screenshot: msg.screenshot,
          });
          step.phase = 'observed';
          break;
        }

        case 'task_complete':
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

function _findOrCreateStep(msg: Message, wsMsg: WSMessage): AgentStep {
  if (!msg.steps) msg.steps = [];

  const stepNum = wsMsg.step_num ?? 0;
  const agentType = wsMsg.agent_type || '';

  let step = msg.steps.find(
    (s) => s.stepNum === stepNum && s.agentType === agentType
  );

  if (!step) {
    step = {
      stepNum,
      agentType,
      actions: [],
      observations: [],
      phase: 'thinking',
    };
    msg.steps.push(step);
  }

  return step;
}
