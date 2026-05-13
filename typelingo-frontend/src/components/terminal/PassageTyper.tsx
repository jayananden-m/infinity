'use client';

import { useEffect, useRef, useState } from 'react';

interface Props {
  passage: string;
  blankWord?: string;
  minimal?: boolean;
  onComplete: (typed: string, durationMs: number) => void;
}

export default function PassageTyper({ passage, blankWord, minimal, onComplete }: Props) {
  const wordStart = blankWord
    ? passage.toLowerCase().indexOf(blankWord.toLowerCase())
    : -1;
  const wordEnd = wordStart >= 0 ? wordStart + blankWord!.length : -1;
  const [typed,   setTyped]   = useState('');
  const [liveWpm, setLiveWpm] = useState<number | null>(null);
  // startedTyping is set on the first keystroke, not on mount, so WPM reflects
  // actual typing speed rather than time spent reading the passage.
  const startedTyping  = useRef<number | null>(null);
  const typedRef       = useRef('');
  const completedRef   = useRef(false);
  const ref            = useRef<HTMLDivElement>(null);

  useEffect(() => { ref.current?.focus(); }, []);

  useEffect(() => {
    const t = setInterval(() => {
      if (startedTyping.current === null || typedRef.current.length === 0) return;
      const mins  = (Date.now() - startedTyping.current) / 60000;
      const words = typedRef.current.trim().split(/\s+/).filter(Boolean).length;
      setLiveWpm(mins > 0 ? Math.round(words / mins) : 0);
    }, 400);
    return () => clearInterval(t);
  }, []);

  function onKey(e: React.KeyboardEvent) {
    if (e.key === 'Tab' || e.key === 'Enter') { e.preventDefault(); return; }
    if (e.key === 'Backspace') {
      const n = typedRef.current.slice(0, -1);
      typedRef.current = n; setTyped(n); return;
    }
    if (e.key.length !== 1) return;
    if (startedTyping.current === null) startedTyping.current = Date.now();
    const n = typedRef.current + e.key;
    typedRef.current = n; setTyped(n);
    if (n.length >= passage.length && !completedRef.current) {
      completedRef.current = true;
      const duration = Date.now() - startedTyping.current;
      setTimeout(() => onComplete(n, duration), 80);
    }
  }

  const errors   = typed.split('').filter((c, i) => c !== passage[i]).length;
  const progress = passage.length > 0 ? typed.length / passage.length : 0;

  return (
    <div
      ref={ref}
      tabIndex={0}
      onKeyDown={onKey}
      style={{ outline: 'none', display: 'flex', flexDirection: 'column', gap: 14 }}
    >
      {!minimal && (
        <div style={{ display: 'flex', gap: 20, fontSize: 12, color: 'var(--t3)', alignItems: 'center' }}>
          <span style={{ color: 'var(--t2)', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            session active
          </span>
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
            <span style={{ color: 'var(--t3)', fontSize: 11 }}>{typed.length}/{passage.length}</span>
          </span>
        </div>
      )}

      <div style={{ height: 1, background: 'var(--b-inner)', overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${progress * 100}%`,
          background: errors > 4 ? 'var(--red)' : 'var(--t3)',
          transition: 'width 0.1s linear',
        }} />
      </div>

      <div style={{ fontSize: 15, lineHeight: 2.1, letterSpacing: '0.01em', userSelect: 'none', wordBreak: 'break-word' }}>
        {passage.split('').map((char, i) => {
          if (i < typed.length) {
            const ok = typed[i] === char;
            return (
              <span key={i} style={{
                color: ok ? 'var(--t1)' : 'var(--red)',
                background: ok ? 'transparent' : 'rgba(255,85,85,0.08)',
                textDecoration: ok ? 'none' : 'underline',
                textDecorationColor: 'rgba(255,85,85,0.4)',
                transition: 'color 0.1s',
              }}>{char}</span>
            );
          }
          const inBlank = wordStart >= 0 && i >= wordStart && i < wordEnd;
          if (i === typed.length) {
            return (
              <span key={i} style={{ position: 'relative', display: 'inline' }}>
                <span style={{
                  position: 'absolute', left: 0, top: '0.1em',
                  borderLeft: '2px solid var(--t1)', height: '1em',
                  animation: 'blink 1s step-end infinite',
                }} />
                <span style={{ color: inBlank ? 'var(--t3)' : 'var(--t2)' }}>
                  {inBlank ? '_' : char}
                </span>
              </span>
            );
          }
          const dist = i - typed.length;
          const op   = Math.max(0.32, 0.58 - dist * 0.011);
          return (
            <span key={i} style={{ color: inBlank ? 'var(--t3)' : 'var(--t1)', opacity: op, transition: 'opacity 0.25s' }}>
              {inBlank ? '_' : char}
            </span>
          );
        })}
      </div>

      <div style={{ fontSize: 11, color: 'var(--t3)' }}>
        type to the end · Backspace to correct · Esc to cancel
      </div>
    </div>
  );
}
