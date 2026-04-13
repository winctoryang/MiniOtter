import React, { useEffect, useState } from 'react';
import { useConfigStore } from '../../stores/configStore';

interface LLMFormState {
  provider: string;
  model: string;
  apiKey: string;
  baseUrl: string;
}

const LLMSection: React.FC<{
  title: string;
  description: string;
  initial: LLMFormState & { hasKey: boolean };
  onSave: (values: LLMFormState) => Promise<void>;
}> = ({ title, description, initial, onSave }) => {
  const [provider, setProvider] = useState(initial.provider);
  const [model, setModel] = useState(initial.model);
  const [apiKey, setApiKey] = useState(initial.apiKey);
  const [baseUrl, setBaseUrl] = useState(initial.baseUrl);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setProvider(initial.provider);
    setModel(initial.model);
    setApiKey(initial.apiKey);
    setBaseUrl(initial.baseUrl);
  }, [initial.provider, initial.model, initial.apiKey, initial.baseUrl]);

  const handleSave = async () => {
    await onSave({ provider, model, apiKey, baseUrl });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid var(--border)',
    borderRadius: 6,
    fontSize: 14,
    outline: 'none',
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    fontSize: 13,
    fontWeight: 600,
    marginBottom: 6,
    color: 'var(--text-secondary)',
  };

  return (
    <div style={{
      padding: 20,
      border: '1px solid var(--border)',
      borderRadius: 10,
      background: 'var(--bg-secondary)',
      marginBottom: 24,
    }}>
      <h3 style={{ margin: '0 0 4px', fontSize: 16 }}>{title}</h3>
      <p style={{ margin: '0 0 16px', fontSize: 13, color: 'var(--text-secondary)' }}>{description}</p>

      <div style={{ marginBottom: 16 }}>
        <label style={labelStyle}>Provider</label>
        <select value={provider} onChange={(e) => setProvider(e.target.value)} style={inputStyle}>
          <option value="claude">Claude (Anthropic)</option>
          <option value="openai">OpenAI / 兼容端点</option>
        </select>
      </div>

      <div style={{ marginBottom: 16 }}>
        <label style={labelStyle}>Model</label>
        <input value={model} onChange={(e) => setModel(e.target.value)} style={inputStyle}
          placeholder={provider === 'claude' ? 'claude-sonnet-4-20250514' : 'gpt-4o'} />
      </div>

      <div style={{ marginBottom: 16 }}>
        <label style={labelStyle}>
          API Key
          {initial.hasKey && !apiKey && (
            <span style={{ fontWeight: 400, color: 'var(--success)', marginLeft: 8 }}>
              (已配置)
            </span>
          )}
        </label>
        <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
          style={inputStyle} placeholder={initial.hasKey ? '留空保持不变' : 'sk-...'} />
      </div>

      <div style={{ marginBottom: 20 }}>
        <label style={labelStyle}>Base URL (可选)</label>
        <input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} style={inputStyle}
          placeholder="留空使用官方端点" />
      </div>

      <button onClick={handleSave} style={{
        padding: '8px 20px',
        background: 'var(--accent)',
        color: '#fff',
        border: 'none',
        borderRadius: 6,
        cursor: 'pointer',
        fontSize: 14,
        fontWeight: 500,
      }}>
        {saved ? '已保存 ✓' : '保存'}
      </button>
    </div>
  );
};

const SettingsPage: React.FC = () => {
  const { textLlm, visionLlm, loaded, load, saveTextLlm, saveVisionLlm } = useConfigStore();

  useEffect(() => { load(); }, []);

  if (!loaded) {
    return <div style={{ padding: 32, color: 'var(--text-secondary)' }}>加载中...</div>;
  }

  return (
    <div style={{ padding: 32, maxWidth: 640, overflow: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: 24, fontSize: 20 }}>模型设置</h2>

      <LLMSection
        title="文本 LLM"
        description="用于主Agent任务分发和文本Agent执行命令，不需要视觉能力。"
        initial={textLlm}
        onSave={saveTextLlm}
      />

      <LLMSection
        title="视觉 LLM（多模态）"
        description="用于GUI Agent看截图操作桌面，需要支持图片输入的多模态模型。"
        initial={visionLlm}
        onSave={saveVisionLlm}
      />
    </div>
  );
};

export default SettingsPage;
