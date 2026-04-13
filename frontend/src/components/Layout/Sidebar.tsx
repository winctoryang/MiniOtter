import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { key: '/', label: '对话', icon: '💬' },
    { key: '/settings', label: '设置', icon: '⚙️' },
  ];

  return (
    <div style={{
      width: 220,
      height: '100%',
      background: 'var(--bg-sidebar)',
      color: '#fff',
      display: 'flex',
      flexDirection: 'column',
      padding: '20px 0',
    }}>
      <div style={{
        padding: '0 20px 24px',
        fontSize: 20,
        fontWeight: 700,
        borderBottom: '1px solid rgba(255,255,255,0.1)',
      }}>
        MiniOtter
      </div>

      <nav style={{ flex: 1, padding: '12px 0' }}>
        {menuItems.map((item) => (
          <div
            key={item.key}
            onClick={() => navigate(item.key)}
            style={{
              padding: '10px 20px',
              cursor: 'pointer',
              background: location.pathname === item.key ? 'rgba(255,255,255,0.1)' : 'transparent',
              borderLeft: location.pathname === item.key ? '3px solid var(--accent)' : '3px solid transparent',
              transition: 'all 0.2s',
            }}
          >
            <span style={{ marginRight: 8 }}>{item.icon}</span>
            {item.label}
          </div>
        ))}
      </nav>

      <div style={{
        padding: '12px 20px',
        fontSize: 12,
        color: 'rgba(255,255,255,0.4)',
        borderTop: '1px solid rgba(255,255,255,0.1)',
      }}>
        v0.1.0
      </div>
    </div>
  );
};
