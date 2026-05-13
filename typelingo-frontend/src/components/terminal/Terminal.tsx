'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { COMMANDS, useTerminal, type OutputLine } from './useTerminal';
import PassageTyper from './PassageTyper';
import MineTyper from './MineTyper';
import ClozeTyper from './ClozeTyper';
import type { ClozeItemData } from './ClozeTyper';
import DrillTyper from './DrillTyper';
import type { DrillRoundData } from './DrillTyper';
import Suggestions from './Suggestions';
import VocabCard from './VocabCard';
import LoadingDots from './LoadingDots';
import DashboardView from './DashboardView';
import VocabCloud from './VocabCloud';
import { fetchWordSuggestions } from '@/lib/api';

export type Theme      = 'void' | 'phosphor' | 'amber';
export type Layout     = 'focused' | 'terminal';
export type Verbosity  = 'terse' | 'normal' | 'verbose';

interface Props {
  theme?:     Theme;
  layout?:    Layout;
  verbosity?: Verbosity;
}

function promptLabel(mode: string): string {
  return ({
    idle:                '>',
    login_email:         'email',
    login_password:      'password',
    reg_email:           'email',
    reg_name:            'name',
    reg_password:        'password',
    level_select:        'level',
    vocab_type_word:     'word',
    vocab_type_sentence: 'answer',
  } as Record<string, string>)[mode] ?? '>';
}

const LINE_STYLE: Record<string, React.CSSProperties> = {
  cmd:     { color: 'var(--t1)', fontWeight: 600 },
  out:     { color: 'var(--t2)' },
  success: { color: 'var(--green)' },
  error:   { color: 'var(--red)' },
  muted:   { color: 'var(--t3)' },
  blank:   { color: 'transparent', lineHeight: '0.55', userSelect: 'none' },
  div:     { color: 'var(--b-inner)', userSelect: 'none', letterSpacing: '0.04em' },
  hero:    { color: 'var(--t1)', fontWeight: 700, fontSize: 36, lineHeight: '1.1', letterSpacing: '-0.01em' },
  label:   { color: 'var(--t3)', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase' },
};

export default function Terminal({
  theme     = 'void',
  layout    = 'focused',
  verbosity = 'normal',
}: Props) {
  const {
    output, input, setInput, mode, ctx, auth, history,
    vocabWord, vocabLoading, vocabCloudWords, submit, startVocabPractice,
    sessionComplete, vocabSessionComplete,
    sessionMineComplete, sessionClozeComplete, sessionDrillComplete,
    vocabCloudWordClick,
  } = useTerminal(verbosity);

  const inputRef      = useRef<HTMLInputElement>(null);
  const outputRef     = useRef<HTMLDivElement>(null);
  const [wordSuggestions, setWordSuggestions] = useState<string[]>([]);

  const isPassword       = mode === 'login_password' || mode === 'reg_password';
  const isSession        = mode === 'session';
  const isSessionMine    = mode === 'session_mine';
  const isSessionCloze   = mode === 'session_cloze';
  const isSessionDrill   = mode === 'session_drill';
  const isAnySession     = isSession || isSessionMine || isSessionCloze || isSessionDrill;
  const isVocabCard      = mode === 'vocab_card';
  const isVocabSession   = mode === 'vocab_session';
  const isVocabCloud     = mode === 'vocab_cloud';
  const isDashboard      = mode === 'dashboard';
  const isAuthFlow       = mode === 'login_email' || mode === 'login_password' ||
                           mode === 'reg_email'   || mode === 'reg_name' || mode === 'reg_password';
  const isFlow           = mode !== 'idle';
  const [inputVisible, setInputVisible] = useState(false);
  const cmdMode        = mode === 'idle' && input.startsWith('/') && input.length > 1;
  const showInputBar   = !isAnySession && !isVocabSession && !isVocabCard && !isDashboard && !isVocabCloud && (isFlow || inputVisible);
  const showOutput     = !isAnySession && !isAuthFlow && !isVocabCard && !isVocabSession && !isDashboard && !isVocabCloud && !cmdMode;
  const isTerminalLayout = layout === 'terminal';
  const panelBorder      = cmdMode || isFlow ? 'var(--b-cmd)' : 'var(--b-idle)';
  const visibleOutput    = useMemo(() => output.slice(-30), [output]);

  // Apply theme
  useEffect(() => {
    document.body.className = theme === 'void' ? '' : `theme-${theme}`;
  }, [theme]);

  // vocab_card: Enter starts practice, Esc skips
  useEffect(() => {
    if (!isVocabCard) return;
    function onCardKey(e: KeyboardEvent) {
      if (e.key === 'Enter') { e.preventDefault(); startVocabPractice(); }
      if (e.key === 'Escape' || (e.key === 'c' && e.ctrlKey)) { e.preventDefault(); submit(''); }
    }
    document.addEventListener('keydown', onCardKey);
    return () => document.removeEventListener('keydown', onCardKey);
  }, [isVocabCard, startVocabPractice, submit]);

  // Global '/' to summon input bar; Escape/Ctrl+C to cancel any active mode
  useEffect(() => {
    function onDocKey(e: KeyboardEvent) {
      // Cancel session or vocab session with Escape or Ctrl+C
      if ((isAnySession || isVocabSession) && (e.key === 'Escape' || (e.key === 'c' && e.ctrlKey))) {
        e.preventDefault();
        submit('');
        return;
      }
      // Dismiss dashboard or vocab cloud with Esc, Enter, or Ctrl+C
      if ((isDashboard || isVocabCloud) && (e.key === 'Escape' || e.key === 'Enter' || (e.key === 'c' && e.ctrlKey))) {
        e.preventDefault();
        submit('');
        return;
      }
      if (isAnySession || isVocabSession || isVocabCard || isDashboard || isVocabCloud) return;
      if (e.key === '/' && mode === 'idle' && !inputVisible) {
        e.preventDefault();
        setInputVisible(true);
        setInput('/');
        setTimeout(() => inputRef.current?.focus(), 30);
      }
      if (e.key === 'Escape' && mode === 'idle') {
        setInputVisible(false);
        setInput('');
      }
    }
    document.addEventListener('keydown', onDocKey);
    return () => document.removeEventListener('keydown', onDocKey);
  }, [isAnySession, isVocabCloud, isSession, isVocabSession, isVocabCard, isDashboard, mode, inputVisible, setInput, submit]);

  // Auto-focus input bar
  useEffect(() => {
    if (showInputBar && !isSession && !isVocabSession) setTimeout(() => inputRef.current?.focus(), 30);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showInputBar, isSession]);

  // Scroll to bottom for output, top for card/panel views
  useEffect(() => {
    if (!outputRef.current) return;
    if (isVocabCard || isVocabSession || isDashboard) {
      outputRef.current.scrollTop = 0;
    } else {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [visibleOutput, mode, isVocabCard, isVocabSession, isDashboard]);

  // Hide input bar when idle + empty
  useEffect(() => {
    if (mode === 'idle' && input === '') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setInputVisible(false);
    }
  }, [mode, input]);

  // Debounced word suggestions for /vocab <word>
  useEffect(() => {
    const query = input.startsWith('/vocab ') ? input.slice(7).trim() : '';
    if (query.length < 2) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setWordSuggestions([]);
      return;
    }
    const id = setTimeout(() => {
      fetchWordSuggestions(query).then(setWordSuggestions).catch(() => setWordSuggestions([]));
    }, 280);
    return () => clearTimeout(id);
  }, [input]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter')          { e.preventDefault(); submit(input); }
    if (e.key === 'c' && e.ctrlKey) { e.preventDefault(); submit(''); }
    if (e.key === 'Escape' && mode === 'idle') { setInputVisible(false); setInput(''); }
    if (e.key === 'Tab' && cmdMode) {
      e.preventDefault();
      if (input.startsWith('/vocab ') && wordSuggestions.length > 0) {
        setInput(`/vocab ${wordSuggestions[0]}`);
      } else {
        const m = COMMANDS.find(c => c.cmd.startsWith(input));
        if (m) setInput(m.cmd);
      }
    }
  }

  /* ── Vocab practice header: word + definition only (etymology/hooks revealed after) ── */
  const vocabHeaderJSX = vocabWord ? (
    <div style={{ marginBottom: 20 }}>
      <div style={{
        fontSize: 56, fontWeight: 700, color: 'var(--t1)',
        lineHeight: 1, letterSpacing: '-0.02em', fontFamily: 'var(--font)',
      }}>
        {vocabWord.word}
      </div>
      <div style={{
        marginTop: 8, fontSize: 11, color: 'var(--t3)',
        letterSpacing: '0.12em', display: 'flex', gap: 8, alignItems: 'center',
      }}>
        <span>{vocabWord.pos.toUpperCase()}</span>
        <span>·</span>
        <span>{vocabWord.cefr_level}</span>
      </div>
      {vocabWord.definition && (
        <div style={{
          marginTop: 16, fontSize: 14, color: 'var(--t2)',
          lineHeight: 1.65, maxWidth: 520,
        }}>
          {vocabWord.definition}
        </div>
      )}
    </div>
  ) : null;

  /* ── Shared pieces ── */

  const outputLinesJSX = (
    <>
      {visibleOutput.map((line: OutputLine, i: number) => {
        const s = LINE_STYLE[line.type] ?? LINE_STYLE.out;
        return (
          <div
            key={line.id}
            className={i === visibleOutput.length - 1 ? 'fade-up' : undefined}
            style={{
              fontSize: 13,
              lineHeight: line.type === 'blank' ? '0.55' : '1.75',
              whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              ...s,
            }}
          >
            {line.text || ' '}
          </div>
        );
      })}
      {vocabLoading && <LoadingDots />}
    </>
  );

  const inputBarJSX = showInputBar ? (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: isTerminalLayout ? '14px 0' : '14px 20px',
      borderTop:    isTerminalLayout ? '1px solid var(--b-inner)' : 'none',
      borderBottom: isTerminalLayout ? 'none' : '1px solid var(--b-inner)',
      flexShrink: 0,
      animation: 'fadeUp 0.18s cubic-bezier(0.16,1,0.3,1) both',
    }}>
      <span style={{
        flexShrink: 0,
        fontSize: isFlow ? 11 : 16,
        color: 'var(--t3)',
        letterSpacing: '0.06em',
        textTransform: isFlow && !mode.startsWith('vocab') ? 'uppercase' : 'none',
      }}>
        {promptLabel(mode)}
      </span>
      <input
        ref={inputRef}
        type={isPassword ? 'password' : 'text'}
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        autoComplete="off" autoCorrect="off" autoCapitalize="off" spellCheck={false}
        placeholder={mode === 'idle' ? 'type a command…' : ''}
        style={{
          flex: 1, background: 'transparent', border: 'none', outline: 'none',
          fontFamily: 'var(--font)', fontSize: 15, color: 'var(--t1)', caretColor: 'var(--t1)',
        }}
      />
    </div>
  ) : null;

  const hintBarJSX = showInputBar || isAnySession || isVocabSession || isVocabCard || isDashboard || isVocabCloud ? (
    <div style={{
      padding: isTerminalLayout ? '6px 0 20px' : '8px 20px',
      flexShrink: 0,
      borderTop: isTerminalLayout ? 'none' : '1px solid var(--b-inner)',
    }}>
      <span style={{ fontSize: 10, color: 'var(--t3)' }}>
        {isDashboard || isVocabCloud
          ? 'Esc to dismiss'
          : isVocabCard
            ? 'Enter to practice · Esc to skip'
            : (isAnySession || isVocabSession)
              ? 'Esc or Ctrl+C to cancel'
              : isFlow
                ? 'Ctrl+C to cancel'
                : '/ for commands · Tab to complete · Esc to dismiss'}
      </span>
    </div>
  ) : null;

  const wordmark = (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span className="shimmer" style={{ fontSize: 12, fontWeight: 700, letterSpacing: '0.16em' }}>
        TYPELINGO
      </span>
      {auth && (
        <span style={{ fontSize: 10, color: 'var(--t3)', letterSpacing: '0.04em' }}>
          · {auth.isGuest
            ? <span style={{ color: 'var(--t3)', fontStyle: 'italic' }}>guest</span>
            : auth.name}
        </span>
      )}
    </div>
  );

  /* ── TERMINAL layout ── */
  if (isTerminalLayout) return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column',
      maxWidth: 860, margin: '0 auto', padding: '0 28px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 0', borderBottom: '1px solid var(--b-inner)', flexShrink: 0 }}>
        {wordmark}
        {!auth && <span style={{ fontSize: 10, color: 'var(--t3)' }}>not signed in</span>}
      </div>

      {showOutput && (
        <div ref={outputRef} style={{ flex: 1, overflowY: 'auto',
          padding: '16px 0', display: 'flex', flexDirection: 'column', gap: 0 }}>
          {outputLinesJSX}
        </div>
      )}

      {isVocabCard && vocabWord && (
        <div ref={outputRef} style={{ flex: 1, overflowY: 'auto', padding: '24px 0' }}>
          <div className="fade-up">
            <VocabCard word={vocabWord} />
          </div>
        </div>
      )}

      {isVocabSession && vocabWord && (
        <div ref={outputRef} style={{ flex: 1, overflowY: 'auto', padding: '24px 0' }}>
          <div className="fade-up">
            {vocabHeaderJSX}
            <div style={{ borderTop: '1px solid var(--b-inner)', paddingTop: 20 }}>
              <PassageTyper passage={ctx.passage} blankWord={ctx.blankWord} minimal onComplete={vocabSessionComplete} />
            </div>
          </div>
        </div>
      )}

      {isSession && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column',
          justifyContent: 'center', padding: '32px 0' }}>
          <div className="fade-up">
            <PassageTyper passage={ctx.passage} onComplete={sessionComplete} />
          </div>
        </div>
      )}

      {isSessionMine && (
        <div style={{ flex: 1, overflowY: 'auto', padding: '32px 0' }}>
          <div className="fade-up">
            <MineTyper
              passage={ctx.passage}
              targetWords={JSON.parse(ctx.targetWords || '[]') as string[]}
              onComplete={sessionMineComplete}
            />
          </div>
        </div>
      )}

      {isSessionCloze && (
        <div style={{ flex: 1, overflowY: 'auto', padding: '32px 0' }}>
          <div className="fade-up">
            <ClozeTyper
              items={JSON.parse(ctx.items || '[]') as ClozeItemData[]}
              onComplete={sessionClozeComplete}
            />
          </div>
        </div>
      )}

      {isSessionDrill && (
        <div style={{ flex: 1, overflowY: 'auto', padding: '32px 0' }}>
          <div className="fade-up">
            <DrillTyper
              rounds={JSON.parse(ctx.rounds || '[]') as DrillRoundData[]}
              grammarTarget={ctx.grammarTarget ?? ''}
              onComplete={sessionDrillComplete}
            />
          </div>
        </div>
      )}

      {isDashboard && auth && (
        <div ref={outputRef} style={{ flex: 1, overflowY: 'auto', padding: '24px 0' }}>
          <div className="fade-up">
            <DashboardView email={auth.email} history={history} />
          </div>
        </div>
      )}

      {isVocabCloud && (
        <div ref={outputRef} style={{ flex: 1, overflowY: 'auto', padding: '24px 0' }}>
          <div className="fade-up">
            <VocabCloud words={vocabCloudWords} onWordClick={vocabCloudWordClick} />
          </div>
        </div>
      )}

      {inputBarJSX}
      {hintBarJSX}
    </div>
  );

  /* ── FOCUSED (spotlight) layout ── */
  return (
    <div style={{ height: '100%', display: 'flex', alignItems: 'center',
      justifyContent: 'center', padding: '24px' }}>
      <div className="panel-in" style={{
        width: '100%', maxWidth: 660,
        display: 'flex', flexDirection: 'column',
        background: 'var(--panel)',
        border: `1px solid ${panelBorder}`,
        transition: 'border-color 0.2s ease',
        boxShadow: '0 24px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.03)',
        position: 'relative', maxHeight: isVocabCard || isVocabSession || isAnySession || isVocabCloud ? '94vh' : '80vh',
      }}>
        {/* Top bar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 20px', borderBottom: '1px solid var(--b-inner)', flexShrink: 0 }}>
          {wordmark}
          {!auth && <span style={{ fontSize: 10, color: 'var(--t3)' }}>not signed in</span>}
        </div>

        {/* Input bar + suggestions */}
        {inputBarJSX}
        {cmdMode && showInputBar && (
          <Suggestions input={input} wordSuggestions={wordSuggestions} onSelect={v => { setInput(v); inputRef.current?.focus(); }} />
        )}

        {/* Output — hidden during session, auth flows, vocab card/session, dashboard */}
        {showOutput && (
          <div ref={outputRef} style={{ flex: 1, overflowY: 'auto',
            padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 0,
            minHeight: 120 }}>
            {outputLinesJSX}
          </div>
        )}

        {/* Vocab card — full card shown immediately, user chooses practice or skip */}
        {isVocabCard && vocabWord && (
          <div ref={outputRef} style={{ flex: 1, overflowY: 'auto', padding: '20px 20px' }}>
            <div className="fade-up">
              <VocabCard word={vocabWord} />
            </div>
          </div>
        )}

        {/* Vocab practice — word + definition + blank sentence to type */}
        {isVocabSession && vocabWord && (
          <div ref={outputRef} style={{ flex: 1, overflowY: 'auto', padding: '20px 20px' }}>
            <div className="fade-up">
              {vocabHeaderJSX}
              <div style={{ borderTop: '1px solid var(--b-inner)', paddingTop: 16 }}>
                <PassageTyper passage={ctx.passage} blankWord={ctx.blankWord} minimal onComplete={vocabSessionComplete} />
              </div>
            </div>
          </div>
        )}

        {/* Dashboard */}
        {isDashboard && auth && (
          <div ref={outputRef} style={{ flex: 1, overflowY: 'auto', padding: '20px 20px' }}>
            <div className="fade-up">
              <DashboardView email={auth.email} history={history} />
            </div>
          </div>
        )}

        {/* Vocab cloud */}
        {isVocabCloud && (
          <div ref={outputRef} style={{ flex: 1, overflowY: 'auto', padding: '20px 20px' }}>
            <div className="fade-up">
              <VocabCloud words={vocabCloudWords} onWordClick={vocabCloudWordClick} />
            </div>
          </div>
        )}

        {/* Regular session passage — centered overlay */}
        {isSession && (
          <div style={{ flex: 1, padding: '24px 20px', display: 'flex',
            flexDirection: 'column', justifyContent: 'center' }}>
            <div className="fade-up">
              <PassageTyper passage={ctx.passage} onComplete={sessionComplete} />
            </div>
          </div>
        )}

        {/* Mine session */}
        {isSessionMine && (
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px 20px' }}>
            <div className="fade-up">
              <MineTyper
                passage={ctx.passage}
                targetWords={JSON.parse(ctx.targetWords || '[]') as string[]}
                onComplete={sessionMineComplete}
              />
            </div>
          </div>
        )}

        {/* Cloze session */}
        {isSessionCloze && (
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px 20px' }}>
            <div className="fade-up">
              <ClozeTyper
                items={JSON.parse(ctx.items || '[]') as ClozeItemData[]}
                onComplete={sessionClozeComplete}
              />
            </div>
          </div>
        )}

        {/* Drill session */}
        {isSessionDrill && (
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px 20px' }}>
            <div className="fade-up">
              <DrillTyper
                rounds={JSON.parse(ctx.rounds || '[]') as DrillRoundData[]}
                grammarTarget={ctx.grammarTarget ?? ''}
                onComplete={sessionDrillComplete}
              />
            </div>
          </div>
        )}

        {/* Hint footer */}
        {hintBarJSX}
      </div>
    </div>
  );
}
