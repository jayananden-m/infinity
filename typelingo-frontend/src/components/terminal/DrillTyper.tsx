'use client';

import { useRef, useState } from 'react';
import PassageTyper from './PassageTyper';

export interface DrillRoundData {
  round_type: 'model' | 'vary' | 'produce';
  text: string;
  stem?: string;
  target_word?: string;
}

interface Props {
  rounds: DrillRoundData[];
  grammarTarget: string;
  onComplete: (totalTyped: number, durationMs: number) => void;
}

const ROUND_LABELS: Record<string, { label: string; hint: string }> = {
  model:   { label: 'Model',   hint: 'type this sentence to encode the pattern' },
  vary:    { label: 'Variation', hint: 'same grammar, different context' },
  produce: { label: 'Produce', hint: 'complete the sentence from the stem above' },
};

export default function DrillTyper({ rounds, grammarTarget, onComplete }: Props) {
  const [roundIdx, setRoundIdx] = useState(0);
  const [transitioning, setTransitioning] = useState(false);

  const totalTypedRef  = useRef(0);
  const totalDurationRef = useRef(0);

  function handleRoundComplete(typed: string, durationMs: number) {
    totalTypedRef.current  += typed.length;
    totalDurationRef.current += durationMs;

    const next = roundIdx + 1;
    if (next >= rounds.length) {
      onComplete(totalTypedRef.current, totalDurationRef.current);
    } else {
      setTransitioning(true);
      setTimeout(() => { setTransitioning(false); setRoundIdx(next); }, 1000);
    }
  }

  const round = rounds[roundIdx];
  if (!round) return null;

  const meta = ROUND_LABELS[round.round_type] ?? { label: round.round_type, hint: '' };

  if (transitioning) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ fontSize: 11, color: 'var(--green)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          round {roundIdx} complete
        </div>
        <div style={{ fontSize: 13, color: 'var(--t3)' }}>
          next round…
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Round header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{
            fontSize: 10, padding: '2px 8px', borderRadius: 3,
            background: 'rgba(255,255,255,0.06)', color: 'var(--t2)',
            letterSpacing: '0.08em', textTransform: 'uppercase',
          }}>
            {meta.label}
          </span>
          <span style={{ fontSize: 11, color: 'var(--t3)' }}>{meta.hint}</span>
        </div>
        <span style={{ fontSize: 10, color: 'var(--t3)' }}>
          {roundIdx + 1} / {rounds.length}
        </span>
      </div>

      {/* Grammar target badge */}
      <div style={{ fontSize: 11, color: 'var(--t3)' }}>
        focus:{' '}
        <span style={{
          color: 'var(--t2)',
          padding: '1px 6px',
          background: 'rgba(255,255,255,0.04)',
          borderRadius: 3,
        }}>
          {grammarTarget}
        </span>
      </div>

      {/* Produce round: show stem as cue above the typer */}
      {round.round_type === 'produce' && round.stem && (
        <div style={{
          padding: '12px 14px',
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid var(--b-inner)',
          borderRadius: 4,
          fontSize: 14,
          color: 'var(--t3)',
          lineHeight: 1.7,
        }}>
          <div style={{ fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--t3)', marginBottom: 6 }}>
            stem
          </div>
          {round.stem}
        </div>
      )}

      {/* Typing area */}
      <PassageTyper
        key={`round-${roundIdx}`}
        passage={round.text}
        minimal
        onComplete={handleRoundComplete}
      />
    </div>
  );
}
