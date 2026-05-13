'use client';

import { useMemo, useState } from 'react';
import type { VocabListItem } from '@/lib/api';

interface Props {
  words: VocabListItem[];
  onWordClick: (word: string) => void;
}

const LEVEL_ORDER: Record<string, number> = { A1: 0, A2: 1, B1: 2, B2: 3, C1: 4, C2: 5 };
const LEVEL_COLOR: Record<string, string> = {
  A1: '#4ade80', A2: '#2dd4bf', B1: '#60a5fa', B2: '#818cf8', C1: '#c084fc', C2: '#f472b6',
};
const LEVEL_SIZE: Record<string, number> = {
  A1: 11, A2: 12, B1: 14, B2: 17, C1: 21, C2: 26,
};

const GOLDEN = Math.PI * (3 - Math.sqrt(5)); // ~137.5° golden angle
const LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] as const;

export default function VocabCloud({ words, onWordClick }: Props) {
  const [hovered, setHovered] = useState<VocabListItem | null>(null);

  const positioned = useMemo(() => {
    // Sort highest CEFR first → those land at center of spiral
    const sorted = [...words].sort((a, b) =>
      (LEVEL_ORDER[b.cefr_level] ?? 0) - (LEVEL_ORDER[a.cefr_level] ?? 0)
    );
    return sorted.map((word, i) => {
      const r = 22 * Math.sqrt(i + 0.5);
      const theta = i * GOLDEN;
      return {
        ...word,
        x: r * Math.cos(theta),
        y: r * Math.sin(theta) * 0.52, // flatten into ellipse
      };
    });
  }, [words]);

  const levelCounts = Object.fromEntries(
    LEVELS.map(l => [l, words.filter(w => w.cefr_level === l).length])
  );

  if (words.length === 0) {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', height: 280, gap: 10,
      }}>
        <div style={{ fontSize: 13, color: 'var(--t2)' }}>no words in your library yet</div>
        <div style={{ fontSize: 11, color: 'var(--t3)' }}>/vocab to start learning</div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 20,
      }}>
        <span style={{ fontSize: 10, color: 'var(--t3)', letterSpacing: '0.13em', textTransform: 'uppercase' }}>
          vocab library
        </span>
        <span style={{ fontSize: 11, color: 'var(--t3)' }}>
          {words.length} word{words.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Cloud canvas */}
      <div style={{ position: 'relative', height: 400, overflow: 'hidden' }}>
        {/* Faint radial gradient glow at center */}
        <div style={{
          position: 'absolute', inset: 0,
          background: 'radial-gradient(ellipse 40% 30% at 50% 50%, rgba(129,140,248,0.045) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        {/* Coordinate origin at center */}
        <div style={{ position: 'absolute', left: '50%', top: '50%', width: 0, height: 0 }}>
          {positioned.map((w) => {
            const color = LEVEL_COLOR[w.cefr_level] ?? '#aaa';
            const size  = LEVEL_SIZE[w.cefr_level] ?? 13;
            const isH   = hovered?.word === w.word;
            return (
              <span
                key={w.word}
                onMouseEnter={() => setHovered(w)}
                onMouseLeave={() => setHovered(null)}
                onClick={() => onWordClick(w.word)}
                style={{
                  position: 'absolute',
                  transform: `translate(calc(${w.x}px - 50%), calc(${w.y}px - 50%))`,
                  fontSize: size,
                  color: isH ? '#fff' : color,
                  opacity: isH ? 1 : 0.65,
                  fontWeight: isH ? 700 : 500,
                  cursor: 'pointer',
                  letterSpacing: '0.015em',
                  textShadow: isH
                    ? `0 0 18px ${color}, 0 0 36px ${color}60`
                    : `0 0 8px ${color}20`,
                  transition: 'all 0.14s ease',
                  userSelect: 'none',
                  whiteSpace: 'nowrap',
                }}
              >
                {w.word}
              </span>
            );
          })}
        </div>
      </div>

      {/* Hovered word strip */}
      <div style={{
        height: 40,
        display: 'flex', alignItems: 'center', gap: 10,
        borderTop: '1px solid var(--b-inner)',
        paddingTop: 12,
        opacity: hovered ? 1 : 0,
        transition: 'opacity 0.15s',
      }}>
        {hovered && (
          <>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--t1)' }}>
              {hovered.word}
            </span>
            <span style={{ fontSize: 10, color: 'var(--t3)' }}>·</span>
            <span style={{
              fontSize: 11, fontWeight: 600,
              color: LEVEL_COLOR[hovered.cefr_level] ?? 'var(--t2)',
            }}>
              {hovered.cefr_level}
            </span>
            <span style={{ fontSize: 10, color: 'var(--t3)' }}>·</span>
            <span style={{ fontSize: 11, color: 'var(--t3)' }}>{hovered.pos}</span>
            <span style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--t3)' }}>
              click to explore
            </span>
          </>
        )}
      </div>

      {/* CEFR legend */}
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 14 }}>
        {LEVELS.filter(l => levelCounts[l] > 0).map(l => (
          <span key={l} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{
              width: 6, height: 6, borderRadius: '50%',
              background: LEVEL_COLOR[l], display: 'inline-block',
              boxShadow: `0 0 5px ${LEVEL_COLOR[l]}80`,
            }} />
            <span style={{ fontSize: 10, color: 'var(--t3)' }}>
              {l} <span style={{ color: 'var(--t2)' }}>({levelCounts[l]})</span>
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
