'use client';

import { useEffect, useRef, useState } from 'react';

interface Props {
  passage: string;
  targetWords: string[];
  onComplete: (typed: string, durationMs: number) => void;
}

type Phase = 'typing' | 'recall';
type RecallState = 'idle' | 'correct' | 'wrong' | 'penalty';

interface RecallItem { word: string; stem: string; }

function buildRecallItems(passage: string, words: string[]): RecallItem[] {
  const sentences = passage.match(/[^.!?]+[.!?]+\s*/g) ?? [passage];
  return words.map(word => {
    const sentence = sentences.find(s =>
      new RegExp(`\\b${word}\\b`, 'i').test(s)
    ) ?? passage;
    const stem = sentence.trim().replace(new RegExp(`\\b${word}\\b`, 'gi'), '___');
    return { word, stem };
  });
}

export default function MineTyper({ passage, targetWords, onComplete }: Props) {
  const [phase, setPhase] = useState<Phase>('typing');
  const [typed, setTyped] = useState('');
  const [liveWpm, setLiveWpm] = useState<number | null>(null);
  const [recallIdx, setRecallIdx] = useState(0);
  const [recallInput, setRecallInput] = useState('');
  const [recallState, setRecallState] = useState<RecallState>('idle');
  const [recallScore, setRecallScore] = useState(0);
  const [penaltyInput, setPenaltyInput] = useState('');

  const startedRef = useRef<number | null>(null);
  const typedRef = useRef('');
  const completedRef = useRef(false);
  const totalDurationRef = useRef(0);
  const recallStartRef = useRef(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const recallItems = buildRecallItems(passage, targetWords);

  useEffect(() => { containerRef.current?.focus(); }, [phase, recallIdx]);

  useEffect(() => {
    const t = setInterval(() => {
      if (startedRef.current === null || phase !== 'typing') return;
      const mins = (Date.now() - startedRef.current) / 60000;
      const words = typedRef.current.trim().split(/\s+/).filter(Boolean).length;
      setLiveWpm(mins > 0 ? Math.round(words / mins) : 0);
    }, 400);
    return () => clearInterval(t);
  }, [phase]);

  // Build set of char indices belonging to target words
  const targetRanges = new Set<number>();
  targetWords.forEach(word => {
    const lower = passage.toLowerCase();
    const wl = word.toLowerCase();
    let pos = 0;
    while ((pos = lower.indexOf(wl, pos)) !== -1) {
      for (let i = pos; i < pos + word.length; i++) targetRanges.add(i);
      pos++;
    }
  });

  function onTypingKey(e: React.KeyboardEvent) {
    if (e.key === 'Tab' || e.key === 'Enter') { e.preventDefault(); return; }
    if (e.key === 'Backspace') {
      const n = typedRef.current.slice(0, -1);
      typedRef.current = n; setTyped(n); return;
    }
    if (e.key.length !== 1) return;
    if (startedRef.current === null) startedRef.current = Date.now();
    const n = typedRef.current + e.key;
    typedRef.current = n; setTyped(n);
    if (n.length >= passage.length && !completedRef.current) {
      completedRef.current = true;
      totalDurationRef.current = Date.now() - startedRef.current!;
      if (recallItems.length === 0) {
        setTimeout(() => onComplete(n, totalDurationRef.current), 80);
      } else {
        setTimeout(() => { recallStartRef.current = Date.now(); setPhase('recall'); }, 80);
      }
    }
  }

  function onRecallKey(e: React.KeyboardEvent) {
    const item = recallItems[recallIdx];
    if (!item || recallState === 'correct') return;

    if (recallState === 'penalty') {
      if (e.key === 'Backspace') { setPenaltyInput(p => p.slice(0, -1)); return; }
      if (e.key.length !== 1) return;
      const n = penaltyInput + e.key;
      setPenaltyInput(n);
      if (n.toLowerCase() === item.word.toLowerCase()) advanceRecall(false);
      return;
    }

    if (e.key === 'Enter') {
      const correct = recallInput.toLowerCase().trim() === item.word.toLowerCase();
      if (correct) {
        setRecallScore(s => s + 1);
        setRecallState('correct');
        setTimeout(() => advanceRecall(true), 800);
      } else {
        setRecallState('wrong');
        setTimeout(() => { setRecallState('penalty'); setPenaltyInput(''); }, 900);
      }
      return;
    }
    if (e.key === 'Backspace') { setRecallInput(i => i.slice(0, -1)); return; }
    if (e.key.length !== 1) return;
    setRecallInput(i => i + e.key);
  }

  function advanceRecall(wasCorrect: boolean) {
    void wasCorrect;
    const next = recallIdx + 1;
    if (next >= recallItems.length) {
      // eslint-disable-next-line react-hooks/purity
      const recallMs = Date.now() - recallStartRef.current;
      onComplete(typedRef.current, totalDurationRef.current + recallMs);
    } else {
      setRecallIdx(next);
      setRecallInput('');
      setPenaltyInput('');
      setRecallState('idle');
    }
  }

  const errors = typed.split('').filter((c, i) => c !== passage[i]).length;
  const progress = passage.length > 0 ? typed.length / passage.length : 0;

  // ── Typing phase ─────────────────────────────────────────────────────────────
  if (phase === 'typing') {
    return (
      <div ref={containerRef} tabIndex={0} onKeyDown={onTypingKey}
        style={{ outline: 'none', display: 'flex', flexDirection: 'column', gap: 14 }}>

        <div style={{ display: 'flex', alignItems: 'center', gap: 20, fontSize: 12, color: 'var(--t3)' }}>
          <span style={{ fontSize: 11, color: 'var(--t2)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            mine
          </span>
          <span style={{ fontSize: 10, color: 'var(--t3)' }}>recall follows</span>
          <span style={{ marginLeft: 'auto', display: 'flex', gap: 20 }}>
            {liveWpm !== null && (
              <span>
                <span style={{ color: 'var(--t1)', fontWeight: 700, fontSize: 15 }}>{liveWpm}</span>
                <span style={{ color: 'var(--t3)', fontSize: 11 }}> wpm</span>
              </span>
            )}
            {errors > 0 && (
              <span>
                <span style={{ color: 'var(--red)', fontWeight: 700 }}>{errors}</span>
                <span style={{ color: 'var(--t3)', fontSize: 11 }}> err</span>
              </span>
            )}
          </span>
        </div>

        <div style={{ height: 1, background: 'var(--b-inner)', overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${progress * 100}%`,
            background: errors > 4 ? 'var(--red)' : 'var(--t3)',
            transition: 'width 0.1s linear',
          }} />
        </div>

        <div style={{ fontSize: 15, lineHeight: 2.1, letterSpacing: '0.01em', userSelect: 'none', wordBreak: 'break-word' }}>
          {passage.split('').map((char, i) => {
            const isT = targetRanges.has(i);
            if (i < typed.length) {
              const ok = typed[i] === char;
              return (
                <span key={i} style={{
                  color: ok ? (isT ? '#f59e0b' : 'var(--t1)') : 'var(--red)',
                  background: ok ? 'transparent' : 'rgba(255,85,85,0.08)',
                  textDecoration: ok ? 'none' : 'underline',
                  textDecorationColor: 'rgba(255,85,85,0.4)',
                }}>{char}</span>
              );
            }
            if (i === typed.length) {
              return (
                <span key={i} style={{ position: 'relative', display: 'inline' }}>
                  <span style={{
                    position: 'absolute', left: 0, top: '0.1em',
                    borderLeft: '2px solid var(--t1)', height: '1em',
                    animation: 'blink 1s step-end infinite',
                  }} />
                  <span style={{ color: isT ? 'rgba(245,158,11,0.55)' : 'var(--t2)' }}>{char}</span>
                </span>
              );
            }
            const op = Math.max(0.32, 0.58 - (i - typed.length) * 0.011);
            return (
              <span key={i} style={{ color: isT ? 'rgba(245,158,11,0.7)' : 'var(--t1)', opacity: op }}>{char}</span>
            );
          })}
        </div>

        {targetWords.length > 0 && (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {targetWords.map(w => (
              <span key={w} style={{
                fontSize: 10, padding: '2px 8px', borderRadius: 3,
                background: 'rgba(245,158,11,0.1)', color: 'rgba(245,158,11,0.85)',
                letterSpacing: '0.05em',
              }}>{w}</span>
            ))}
          </div>
        )}

        <div style={{ fontSize: 11, color: 'var(--t3)' }}>
          type the passage · recall phase follows · Esc to cancel
        </div>
      </div>
    );
  }

  // ── Recall phase ──────────────────────────────────────────────────────────────
  const item = recallItems[recallIdx];
  const parts = item.stem.split('___');

  return (
    <div ref={containerRef} tabIndex={0} onKeyDown={onRecallKey}
      style={{ outline: 'none', display: 'flex', flexDirection: 'column', gap: 20 }}>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 11, color: 'var(--t2)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          recall
        </span>
        <span style={{ fontSize: 11, color: 'var(--t3)' }}>{recallIdx + 1} / {recallItems.length}</span>
      </div>

      {/* Sentence with blank */}
      <div style={{ fontSize: 15, lineHeight: 1.9, color: 'var(--t2)', wordBreak: 'break-word' }}>
        {parts.map((part, i) => (
          <span key={i}>
            {part}
            {i < parts.length - 1 && (
              <span style={{
                color: recallState === 'correct' ? 'var(--green)'
                     : recallState === 'wrong'   ? 'var(--red)'
                     : '#f59e0b',
                fontWeight: 700,
              }}>
                {recallState === 'idle' ? (recallInput || '_'.repeat(item.word.length)) : item.word}
              </span>
            )}
          </span>
        ))}
      </div>

      {/* Penalty */}
      {recallState === 'wrong' && (
        <div style={{ fontSize: 13, color: 'var(--red)' }}>
          the word was &ldquo;{item.word}&rdquo;
        </div>
      )}
      {recallState === 'penalty' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ fontSize: 12, color: 'var(--t3)' }}>
            type it to continue:{' '}
            <span style={{ color: 'var(--t2)', fontWeight: 600 }}>{item.word}</span>
          </div>
          <div style={{ fontSize: 15, letterSpacing: '0.05em' }}>
            {item.word.split('').map((char, i) => {
              const t = penaltyInput[i];
              return (
                <span key={i} style={{
                  color: t ? (t.toLowerCase() === char.toLowerCase() ? 'var(--green)' : 'var(--red)') : 'var(--t3)',
                  borderBottom: i === penaltyInput.length ? '2px solid var(--t1)' : 'none',
                }}>{t ?? char}</span>
              );
            })}
          </div>
        </div>
      )}

      <div style={{ fontSize: 11, color: 'var(--t3)' }}>
        {recallState === 'idle'
          ? 'type the missing word · Enter to confirm'
          : recallState === 'correct'
          ? `correct · ${recallScore}/${recallItems.length} so far`
          : ''}
      </div>
    </div>
  );
}
