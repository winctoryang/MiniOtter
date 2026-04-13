export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  task_id: string;
  status: string;
}

export interface TaskSummary {
  task_id: string;
  status: string;
  success?: boolean;
  summary: string;
  steps_count: number;
  created_at: string;
}

export interface WSMessage {
  type:
    | 'task_started'
    | 'agent_activated'
    | 'thought'
    | 'action'
    | 'observation'
    | 'task_complete'
    | 'error';
  task_id?: string;
  agent_type?: string;
  step_num?: number;
  phase?: string;
  content?: string;
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  result?: unknown;
  is_error?: boolean;
  screenshot?: string;
  success?: boolean;
  summary?: string;
  message?: string;
}

export interface AgentStep {
  stepNum: number;
  agentType: string;
  thought?: string;
  actions: { toolName: string; toolArgs: Record<string, unknown> }[];
  observations: {
    result: unknown;
    isError: boolean;
    screenshot?: string;
  }[];
  phase: 'thinking' | 'acting' | 'observed' | 'complete';
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  agentType?: string;
  steps?: AgentStep[];
  taskId?: string;
}
