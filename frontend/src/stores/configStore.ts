import { create } from 'zustand';
import { getConfig, updateConfig } from '../api/config';

interface LLMSettings {
  provider: string;
  model: string;
  apiKey: string;
  baseUrl: string;
  hasKey: boolean;
}

interface ConfigStore {
  textLlm: LLMSettings;
  visionLlm: LLMSettings;
  loaded: boolean;

  load: () => Promise<void>;
  saveTextLlm: (values: Partial<LLMSettings>) => Promise<void>;
  saveVisionLlm: (values: Partial<LLMSettings>) => Promise<void>;
}

const defaultTextLlm: LLMSettings = {
  provider: 'openai', model: 'gpt-4o', apiKey: '', baseUrl: '', hasKey: false,
};

const defaultVisionLlm: LLMSettings = {
  provider: 'claude', model: 'claude-sonnet-4-20250514', apiKey: '', baseUrl: '', hasKey: false,
};

export const useConfigStore = create<ConfigStore>((set, get) => ({
  textLlm: { ...defaultTextLlm },
  visionLlm: { ...defaultVisionLlm },
  loaded: false,

  load: async () => {
    try {
      const data = await getConfig();
      const tl = data.text_llm as Record<string, unknown> | undefined;
      const vl = data.vision_llm as Record<string, unknown> | undefined;
      set({
        textLlm: {
          provider: (tl?.provider as string) || 'openai',
          model: (tl?.model as string) || '',
          baseUrl: (tl?.base_url as string) || '',
          apiKey: '',
          hasKey: (tl?.has_key as boolean) || false,
        },
        visionLlm: {
          provider: (vl?.provider as string) || 'claude',
          model: (vl?.model as string) || '',
          baseUrl: (vl?.base_url as string) || '',
          apiKey: '',
          hasKey: (vl?.has_key as boolean) || false,
        },
        loaded: true,
      });
    } catch {
      // ignore
    }
  },

  saveTextLlm: async (values) => {
    const merged = { ...get().textLlm, ...values };
    set({ textLlm: merged });
    await updateConfig({
      text_llm: {
        provider: merged.provider,
        model: merged.model,
        api_key: merged.apiKey || undefined,
        base_url: merged.baseUrl || undefined,
      },
    });
  },

  saveVisionLlm: async (values) => {
    const merged = { ...get().visionLlm, ...values };
    set({ visionLlm: merged });
    await updateConfig({
      vision_llm: {
        provider: merged.provider,
        model: merged.model,
        api_key: merged.apiKey || undefined,
        base_url: merged.baseUrl || undefined,
      },
    });
  },
}));
