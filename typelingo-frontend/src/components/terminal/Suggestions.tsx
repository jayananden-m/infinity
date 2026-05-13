'use client';

import { useMemo } from 'react';
import { COMMANDS } from './useTerminal';

interface Props {
  input: string;
  wordSuggestions?: string[];
  onSelect: (cmd: string) => void;
}

export default function Suggestions({ input, wordSuggestions, onSelect }: Props) {
  const isVocabInput = input.startsWith('/vocab ') && input.length > 7;

  const cmdMatches = useMemo(() => {
    if (isVocabInput || !input.startsWith('/') || input.length < 2) return [];
    return COMMANDS.filter(c => c.cmd.startsWith(input));
  }, [input, isVocabInput]);

  if (isVocabInput) {
    if (!wordSuggestions || wordSuggestions.length === 0) return null;
    return (
      <div style={{ background: 'var(--panel)', border: '1px solid var(--b-inner)', borderTop: 'none', zIndex: 10 }}>
        {wordSuggestions.map((w, i) => (
          <div
            key={w}
            onClick={() => onSelect(`/vocab ${w}`)}
            style={{
              display: 'flex', alignItems: 'center', gap: 16,
              padding: '9px 20px',
              borderBottom: i < wordSuggestions.length - 1 ? '1px solid var(--b-inner)' : 'none',
              cursor: 'default',
            }}
          >
            <span style={{ fontSize: 13, color: 'var(--t1)', fontWeight: 600 }}>{w}</span>
          </div>
        ))}
        <div style={{ padding: '6px 20px', fontSize: 10, color: 'var(--t3)', borderTop: '1px solid var(--b-inner)' }}>
          Tab to complete · spelling corrections included
        </div>
      </div>
    );
  }

  if (cmdMatches.length === 0) return null;

  return (
    <div style={{ background: 'var(--panel)', border: '1px solid var(--b-inner)', borderTop: 'none', zIndex: 10 }}>
      {cmdMatches.map((c, i) => (
        <div
          key={c.cmd}
          onClick={() => onSelect(c.cmd)}
          style={{
            display: 'flex', alignItems: 'baseline', gap: 16,
            padding: '10px 20px',
            borderBottom: i < cmdMatches.length - 1 ? '1px solid var(--b-inner)' : 'none',
            cursor: 'default',
          }}
        >
          <span style={{ fontSize: 13, color: 'var(--t1)', fontWeight: 600, minWidth: 110 }}>
            {c.cmd}
          </span>
          <span style={{ fontSize: 12, color: 'var(--t2)' }}>{c.desc}</span>
        </div>
      ))}
      <div style={{ padding: '6px 20px', fontSize: 10, color: 'var(--t3)', borderTop: '1px solid var(--b-inner)' }}>
        Tab to complete
      </div>
    </div>
  );
}
