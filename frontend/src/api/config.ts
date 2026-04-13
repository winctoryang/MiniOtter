import api from './index';

export async function getConfig(): Promise<Record<string, unknown>> {
  const { data } = await api.get('/config');
  return data;
}

export async function updateConfig(config: Record<string, unknown>): Promise<void> {
  await api.put('/config', config);
}
