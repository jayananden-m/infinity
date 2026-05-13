'use client';

import { useEffect, useRef, useState } from 'react';

export interface ClozeItemData { full: string; stem: string; answer: string; }

interface Props {
  items: ClozeItemData[];
  onComplete: (results: { answer: string; correct: boolean }[], durationMs: number) => void;
}

type ItemState = 'idle' | 'correct' | 'wrong' | 'penalty';

export default function ClozeTyper({ items, onComplete }: Props) {
  const [idx, setIdx]           = useState(0);
  const [input, setInput]       = useState('');
  const [itemState, setItemState] = useState<ItemState>('idle');
  const [penaltyInput, setPenaltyInput] = useState('');
  const [results, setResults]   = useState<{ answer: string; correct: boolean }[]>([]);

  // eslint-disable-next-line react-hooks/purity
  const startRef    = useRef(Date.now());
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => { containerRef.current?.focus(); }, [idx, itemState]);

  const item = items[idx];

  function advance(wasCorrect: boolean) {
    const newResults = [...results, { answer: item.answer, correct: wasCorrect }];
    setResults(newResults);
    const next = idx + 1;
    if (next >= items.length) {
      onComplete(newResults, Date.now() - startRef.current);
    } else {
      setIdx(next);
      setInput('');
      setPenaltyInput('');
      setItemState('idle');
    }
  }

  function onKey(e: React.KeyboardEvent) {
    if (!item || itemState === 'correct') return;

    if (itemState === 'penalty') {
      if (e.key === 'Backspace') { setPenaltyInput(p => p.slice(0, -1)); return; }
      if (e.key.length !== 1) return;
      const n = penaltyInput + e.key;
      setPenaltyInput(n);
      if (n.toLowerCase() === item.answer.toLowerCase()) advance(false);
      return;
    }

    if (e.key === 'Enter') {
      const correct = input.toLowerCase().trim() === item.answer.toLowerCase();
      if (correct) {
        setItemState('correct');
        setTimeout(() => advance(true), 700);
      } else {
        setItemState('wrong');
        setTimeout(() => { setItemState('penalty'); setPenaltyInput(''); }, 900);
      }
      return;
    }
    if (e.key === 'Backspace') { setInput(i => i.slice(0, -1)); return; }
    if (e.key.length !== 1) return;
    setInput(i => i + e.key);
  }

  if (!item) return null;

  const parts = item.stem.split('___');
  const score = results.filter(r => r.correct).length;

  return (
    <div ref={containerRef} tabIndex={0} onKeyDown={onKey}
      style={{ outline: 'none', display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 11, color: 'var(--t2)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          cloze
        </span>
        <span style={{ fontSize: 11, color: 'var(--t3)' }}>
          {idx + 1} / {items.length}
          {results.length > 0 && (
            <span style={{ marginLeft: 10, color: 'var(--green)' }}>
              {score} correct
            </span>
          )}
        </span>
      </div>

      {/* Progress bar */}
      <div style={{ height: 1, background: 'var(--b-inner)', overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${(idx / items.length) * 100}%`,
          background: 'var(--green)',
          transition: 'width 0.3s ease',
        }} />
      </div>

      {/* Sentence with blank */}
      <div style={{ fontSize: 16, lineHeight: 2.0, color: 'var(--t2)', wordBreak: 'break-word' }}>
        {parts.map((part, i) => (
          <span key={i}>
            {part}
            {i < parts.length - 1 && (
              <span style={{
                color: itemState === 'correct' ? 'var(--green)'
                     : itemState === 'wrong'   ? 'var(--red)'
                     : 'var(--t1)',
                fontWeight: 600,
                borderBottom: itemState === 'idle' ? '1px solid var(--t3)' : 'none',
                paddingBottom: 1,
                minWidth: 40,
                display: 'inline-block',
              }}>
                {itemState === 'idle'   ? (input || '     ')
                 : item.answer}
              </span>
            )}
          </span>
        ))}
      </div>

      {/* Wrong feedback */}
      {itemState === 'wrong' && (
        <div style={{ fontSize: 13, color: 'var(--red)' }}>
          the answer was &ldquo;{item.answer}&rdquo;
        </div>
      )}

      {/* Penalty */}
      {itemState === 'penalty' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ fontSize: 12, color: 'var(--t3)' }}>
            type it to lock it in:{' '}
            <span style={{ color: 'var(--t2)', fontWeight: 600 }}>{item.answer}</span>
          </div>
          <div style={{ fontSize: 15, letterSpacing: '0.05em' }}>
            {item.answer.split('').map((char, i) => {
              const t = penaltyInput[i];
              return (
                <span key={i} style={{
                  color: t
                    ? (t.toLowerCase() === char.toLowerCase() ? 'var(--green)' : 'var(--red)')
                    : 'var(--t3)',
                  borderBottom: i === penaltyInput.length ? '2px solid var(--t1)' : 'none',
                }}>
                  {t ?? char}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Input indicator */}
      {itemState === 'idle' && (
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--t3)' }}>&gt;</span>
          <span style={{ fontSize: 14, color: 'var(--t1)' }}>
            {input}
            <span style={{ borderRight: '1px solid var(--t1)', animation: 'blink 1s step-end infinite' }}>&nbsp;</span>
          </span>
        </div>
      )}

      <div style={{ fontSize: 11, color: 'var(--t3)' }}>
        {itemState === 'idle'
          ? 'type the missing word · Enter to check'
          : itemState === 'correct'
          ? 'correct!'
          : ''}
      </div>
    </div>
  );
}
