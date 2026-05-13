'use client';

import type { SessionResult } from './useTerminal';

interface Props {
  email: string;
  history: SessionResult[];
}

const CELL: React.CSSProperties = { padding: '12px 16px', background: 'var(--panel)' };
const LABEL: React.CSSProperties = {
  fontSize: 9, color: 'var(--t3)', letterSpacing: '0.13em',
  textTransform: 'uppercase', marginBottom: 8,
};
const VAL: React.CSSProperties = {
  fontSize: 24, fontWeight: 700, color: 'var(--t1)',
  letterSpacing: '-0.02em',
};

export default function DashboardView({ email, history }: Props) {
  const n = history.length;
  const avgWpm  = n ? history.reduce((a, s) => a + s.wpm, 0) / n : null;
  const bestWpm = n ? Math.max(...history.map(s => s.wpm)) : null;
  const avgAcc  = n ? history.reduce((a, s) => a + s.accuracy, 0) / n : null;

  const stats = [
    { label: 'sessions',  value: n.toString() },
    { label: 'avg wpm',   value: avgWpm  !== null ? avgWpm.toFixed(1)               : '—' },
    { label: 'best wpm',  value: bestWpm !== null ? bestWpm.toFixed(1)              : '—' },
    { label: 'avg acc',   value: avgAcc  !== null ? (avgAcc * 100).toFixed(1) + '%' : '—' },
  ];

  return (
    <div>
      {/* Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        marginBottom: 20,
      }}>
        <span style={{ fontSize: 10, color: 'var(--t3)', letterSpacing: '0.13em', textTransform: 'uppercase' }}>
          stats
        </span>
        <span style={{ fontSize: 11, color: 'var(--t3)' }}>{email}</span>
      </div>

      {/* Stats grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${stats.length}, 1fr)`,
        gap: 1,
        background: 'var(--b-inner)',
        marginBottom: 24,
      }}>
        {stats.map(s => (
          <div key={s.label} style={CELL}>
            <div style={LABEL}>{s.label}</div>
            <div style={VAL}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Session history */}
      {n > 0 ? (
        <>
          <div style={{
            fontSize: 10, color: 'var(--t3)', letterSpacing: '0.1em',
            textTransform: 'uppercase', marginBottom: 12,
          }}>
            recent
          </div>
          {history.slice(-8).reverse().map((s, i) => (
            <div key={i} style={{
              display: 'grid',
              gridTemplateColumns: '28px 92px 66px 1fr',
              alignItems: 'baseline',
              padding: '8px 0',
              borderBottom: '1px solid var(--b-inner)',
            }}>
              <span style={{ fontSize: 10, color: 'var(--t3)' }}>
                {String(n - i).padStart(2, '0')}
              </span>
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--t1)' }}>
                {s.wpm.toFixed(1)}
                <span style={{ fontSize: 10, fontWeight: 400, color: 'var(--t3)', marginLeft: 4 }}>wpm</span>
              </span>
              <span style={{
                fontSize: 12,
                color: s.accuracy >= 0.9 ? 'var(--green)' : 'var(--t2)',
              }}>
                {(s.accuracy * 100).toFixed(1)}%
              </span>
              <span style={{
                fontSize: 11, color: 'var(--t3)',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {s.passageSnippet}
              </span>
            </div>
          ))}
        </>
      ) : (
        <div style={{ fontSize: 12, color: 'var(--t3)', paddingTop: 4 }}>
          no typing tests yet — type /type to start
        </div>
      )}
    </div>
  );
}
