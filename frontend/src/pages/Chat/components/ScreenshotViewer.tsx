import React from 'react';

interface Props {
  screenshot: string;
  actions?: { toolName: string; toolArgs: Record<string, unknown> }[];
}

export const ScreenshotViewer: React.FC<Props> = ({ screenshot, actions }) => {
  return (
    <div style={{ position: 'relative', display: 'inline-block', maxWidth: '100%' }}>
      <img
        src={`data:image/png;base64,${screenshot}`}
        alt="Screenshot"
        style={{
          maxWidth: '100%',
          maxHeight: 400,
          borderRadius: 8,
          border: '1px solid var(--border)',
        }}
      />
      {/* Overlay action indicators */}
      <svg
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
        }}
        viewBox="0 0 1280 800"
        preserveAspectRatio="none"
      >
        {actions?.map((action, i) => {
          const args = action.toolArgs;
          if (action.toolName.includes('click') || action.toolName === 'mouse_move') {
            const x = Number(args.x ?? 0);
            const y = Number(args.y ?? 0);
            return (
              <g key={i}>
                <circle cx={x} cy={y} r={12} fill="rgba(239,68,68,0.6)" stroke="#ef4444" strokeWidth={2} />
                <circle cx={x} cy={y} r={4} fill="#ef4444" />
              </g>
            );
          }
          if (action.toolName === 'mouse_drag') {
            const sx = Number(args.start_x ?? 0);
            const sy = Number(args.start_y ?? 0);
            const ex = Number(args.end_x ?? 0);
            const ey = Number(args.end_y ?? 0);
            return (
              <line key={i} x1={sx} y1={sy} x2={ex} y2={ey} stroke="#ef4444" strokeWidth={3} markerEnd="url(#arrow)" />
            );
          }
          return null;
        })}
      </svg>
    </div>
  );
};
