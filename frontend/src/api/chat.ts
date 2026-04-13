import api from './index';
import type { ChatRequest, ChatResponse, TaskSummary } from './types';

export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>('/chat', request);
  return data;
}

export async function cancelTask(taskId: string): Promise<void> {
  await api.post(`/chat/${taskId}/cancel`);
}

export async function listTasks(): Promise<TaskSummary[]> {
  const { data } = await api.get<TaskSummary[]>('/tasks');
  return data;
}

export async function getTask(taskId: string): Promise<TaskSummary> {
  const { data } = await api.get<TaskSummary>(`/tasks/${taskId}`);
  return data;
}
