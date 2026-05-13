import { useEffect, useState } from 'react';
import {
  abandonSession,
  completeSession,
  createGuestSession,
  fetchVocabList,
  fetchVocabWord,
  login,
  recordVocabPracticed,
  register,
  startSession,
  submitAssessResult,
} from '@/lib/api';
import type {
  SessionMode,
  VocabListItem,
  VocabWordResponse,
} from '@/lib/api';

/* ── Types ── */
export type LineType = 'cmd' | 'out' | 'success' | 'error' | 'muted' | 'blank' | 'div' | 'hero' | 'label';
export interface OutputLine { id: number; type: LineType; text: string; }
export type Mode =
  | 'idle'
  | 'login_email' | 'login_password'
  | 'reg_email'   | 'reg_name' | 'reg_password'
  | 'level_select'
  | 'session'
  | 'session_mine'
  | 'session_cloze'
  | 'session_drill'
  | 'vocab_card'
  | 'vocab_session'
  | 'vocab_cloud'
  | 'dashboard';

const CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] as const;
type CefrLevel = typeof CEFR_LEVELS[number];

export interface SessionResult {
  wpm: number;
  accuracy: number;
  passage: string;
  passageSnippet: string;
}

export interface AuthUser { email: string; name: string; token: string; isGuest?: boolean; }

export const COMMANDS = [
  { cmd: '/help',            desc: 'list all commands' },
  { cmd: '/guest',           desc: 'continue without an account' },
  { cmd: '/login',           desc: 'authenticate' },
  { cmd: '/register',        desc: 'create account' },
  { cmd: '/type',            desc: 'typing test — pure speed + accuracy' },
  { cmd: '/session',         desc: 'learning session (random: mine / cloze / drill)' },
  { cmd: '/session mine',    desc: 'sentence mining — type vocab words in context' },
  { cmd: '/session cloze',   desc: 'cloze recovery — fill in the blanks' },
  { cmd: '/session drill',   desc: 'grammar drill — 3-round targeted practice' },
  { cmd: '/vocab',           desc: 'learn a new word' },
  { cmd: '/words',           desc: 'browse your vocab library (word cloud)' },
  { cmd: '/dashboard',       desc: 'view your typing stats' },
  { cmd: '/logout',          desc: 'sign out' },
  { cmd: '/clear',           desc: 'clear output' },
];


let uid = 0;
const L = (type: LineType, text: string): OutputLine => ({ id: uid++, type, text });

const BOOT: OutputLine[] = [
  L('blank', ''),
  L('muted', 'Where English becomes muscle memory'),
  L('blank', ''),
  L('out',   'type /help to see available commands'),
  L('blank', ''),
];

const GUEST_BOOT: OutputLine[] = [
  L('blank', ''),
  L('muted', 'Where English becomes muscle memory'),
  L('blank', ''),
  L('out',   'you\'re in guest mode — progress is temporary')
];

const LEVEL_LINES: OutputLine[] = [
  L('blank', ''),
  L('out',   '  what\'s your English level?'),
  L('blank', ''),
  L('muted', '  A1  beginner'),
  L('muted', '  A2  elementary'),
  L('muted', '  B1  intermediate'),
  L('muted', '  B2  upper intermediate'),
  L('muted', '  C1  advanced'),
  L('muted', '  C2  mastery'),
  L('blank', ''),
];

export function useTerminal(verbosity: 'terse' | 'normal' | 'verbose' = 'normal') {
  const xtra = (...lines: OutputLine[]) => verbosity === 'verbose' ? lines : [];
  const hint = (...lines: OutputLine[]) => verbosity !== 'terse'  ? lines : [];

  const [output,  setOutput]  = useState<OutputLine[]>(BOOT);
  const [mode,    setMode]    = useState<Mode>('idle');
  const [ctx,     setCtx]     = useState<Record<string, string>>({});
  const [input,   setInput]   = useState('');

  const [auth, setAuth] = useState<AuthUser | null>(null);
  const [history, setHistory] = useState<SessionResult[]>([]);
  const [cefrLevel, setCefrLevel] = useState<CefrLevel | null>(null);

  // Load persisted state after hydration so server and client start identical.
  // Hydration-safe: localStorage is unavailable on the server, so we read it in an effect.
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('tl_auth') || 'null') as AuthUser | null;
      if (saved?.token) {
        setAuth(saved); // eslint-disable-line react-hooks/set-state-in-effect
        if (saved.isGuest) setOutput(GUEST_BOOT);
      }
    } catch { /* ignore */ }
    try {
      const saved = localStorage.getItem('tl_cefr');
      if (saved && (CEFR_LEVELS as readonly string[]).includes(saved)) {
        setCefrLevel(saved as CefrLevel);
      }
    } catch { /* ignore */ }

    try {
      const saved = JSON.parse(localStorage.getItem('tl_history') || '[]') as SessionResult[];
      if (Array.isArray(saved) && saved.length) {
        const valid = saved.filter(s => s.wpm >= 1 && s.wpm <= 300 && s.accuracy >= 0.05);
        setHistory(valid);
        if (valid.length !== saved.length) {
          localStorage.setItem('tl_history', JSON.stringify(valid));
        }
      }
    } catch { /* ignore */ }
  }, []);

  // Vocab state
  const [vocabWord,    setVocabWord]    = useState<VocabWordResponse | null>(null);
  const [vocabLoading, setVocabLoading] = useState(false);
  const [vocabCloudWords, setVocabCloudWords] = useState<VocabListItem[]>([]);

  function push(...lines: OutputLine[]) {
    setOutput(o => [...o, ...lines.map(l => ({ ...l, id: uid++ }))].slice(-60));
  }

  function _enterLevelSelect() {
    setOutput(LEVEL_LINES.map(l => ({ ...l, id: uid++ })));
    setMode('level_select');
  }

  function commitResult(result: SessionResult) {
    const updated = [...history, result];
    setHistory(updated);
    localStorage.setItem('tl_history', JSON.stringify(updated));
  }

  // ── Commands ────────────────────────────────────────────────────────────────

  async function run(raw: string) {
    const cmd = raw.trim().toLowerCase();

    if (cmd === '/clear') {
      setOutput([L('blank', ''), L('success', 'cleared.'), L('blank', '')]);
      setTimeout(() => setOutput(BOOT), 500);
      setInput(''); return;
    }

    if (cmd === '/help') {
      setOutput([
        L('blank', ''), L('muted', 'commands:'), L('blank', ''),
        ...COMMANDS.map(c => L('out', `  ${c.cmd.padEnd(18)}${c.desc}`)),
        L('blank', ''),
        ...xtra(L('muted', '  prefix every command with /'), L('muted', '  Tab to autocomplete · Ctrl+C to cancel'), L('blank', '')),
      ]);
      setInput(''); return;
    }

    if (cmd === '/login') {
      if (auth) { push(L('error', `already signed in as ${auth.email}`)); setInput(''); return; }
      push(L('blank', ''), L('out', '— login — Ctrl+C to cancel'), L('blank', ''), L('muted', 'email'));
      setMode('login_email'); setInput(''); return;
    }

    if (cmd === '/register') {
      if (auth) { push(L('error', 'already signed in. /logout first.')); setInput(''); return; }
      push(L('blank', ''), L('out', '— register — Ctrl+C to cancel'), L('blank', ''), L('muted', 'email'));
      setMode('reg_email'); setInput(''); return;
    }

    if (cmd === '/guest') {
      if (auth?.isGuest) { push(L('muted', 'already in guest mode.')); setInput(''); return; }
      push(L('muted', '  creating guest session…'));
      try {
        const { access_token } = await createGuestSession();
        const guest: AuthUser = { email: 'guest', name: 'guest', token: access_token, isGuest: true };
        setAuth(guest);
        localStorage.setItem('tl_auth', JSON.stringify(guest));
        setOutput(GUEST_BOOT.map(l => ({ ...l, id: uid++ })));
        if (!cefrLevel) { setTimeout(_enterLevelSelect, 600); }
      } catch {
        push(L('error', '  could not create guest session. is the backend running?'));
      }
      setInput(''); return;
    }

    if (cmd === '/logout') {
      if (!auth) { push(L('error', 'not signed in.')); setInput(''); return; }
      setAuth(null);
      localStorage.removeItem('tl_auth');
      push(L('blank', ''), L('success', 'signed out. goodbye.'), L('blank', ''));
      setInput(''); return;
    }

    if (cmd === '/dashboard') {
      if (!auth) { push(L('error', 'not signed in. /login first.')); setInput(''); return; }
      setMode('dashboard');
      setInput(''); return;
    }

    if (cmd === '/type') {
      if (!auth) { push(L('error', 'not signed in. /login first.')); setInput(''); return; }
      push(L('muted', '  loading passage…'));
      try {
        const session = await startSession(auth.token);
        const s = session as import('@/lib/api').SessionResponse;
        if (!s.passage_content) throw new Error('no passage');
        setCtx({ passage: s.passage_content, sessionId: s.id.toString() });
        setOutput([]);
        setMode('session');
      } catch (err) {
        const msg = String(err);
        if (msg.includes('503')) {
          push(L('error', '  no passages available yet — generation queued, try again shortly.'));
        } else {
          push(L('error', '  could not load passage. is the backend running?'));
        }
      }
      setInput(''); return;
    }

    if (cmd.startsWith('/session')) {
      const modeArg = raw.trim().slice(8).trim().toLowerCase();
      let sessionMode: SessionMode | undefined;
      if (modeArg === 'mine' || modeArg === 'cloze' || modeArg === 'drill') {
        sessionMode = modeArg as SessionMode;
      } else if (modeArg === '') {
        const pool: SessionMode[] = ['mine', 'cloze', 'drill'];
        sessionMode = pool[Math.floor(Math.random() * pool.length)];
      } else {
        push(L('error', '  usage: /session · /session mine · /session cloze · /session drill'));
        setInput(''); return;
      }
      if (!auth) { push(L('error', 'not signed in. /login first.')); setInput(''); return; }
      push(L('muted', `  loading ${sessionMode} session…`));
      try {
        const session = await startSession(auth.token, sessionMode);
        setOutput([]);
        if (session.mode === 'mine') {
          setCtx({
            sessionId: session.id.toString(),
            passage: session.passage,
            targetWords: JSON.stringify(session.target_words),
          });
          setMode('session_mine');
        } else if (session.mode === 'cloze') {
          setCtx({
            sessionId: session.id.toString(),
            items: JSON.stringify(session.items),
          });
          setMode('session_cloze');
        } else if (session.mode === 'drill') {
          setCtx({
            sessionId: session.id.toString(),
            rounds: JSON.stringify(session.rounds),
            grammarTarget: session.grammar_target,
          });
          setMode('session_drill');
        } else {
          push(L('error', '  unexpected session type returned. try /type for a typing test.'));
        }
      } catch (err) {
        const msg = String(err);
        if (msg.includes('400')) {
          push(L('error', '  practice some vocab words first (/vocab) before using this mode.'));
        } else if (msg.includes('503')) {
          push(L('error', '  no passages available yet — generation queued, try again shortly.'));
        } else {
          push(L('error', '  could not start session. is the backend running?'));
        }
      }
      setInput(''); return;
    }

    if (cmd === '/words') {
      if (!auth) { push(L('error', 'not signed in. /login first.')); setInput(''); return; }
      push(L('muted', '  loading vocab library…'));
      try {
        const words = await fetchVocabList(auth.token);
        setVocabCloudWords(words);
        setOutput([]);
        setMode('vocab_cloud');
      } catch {
        push(L('error', '  could not load vocab library. is the backend running?'));
      }
      setInput(''); return;
    }

    if (cmd.startsWith('/vocab')) {
      const targetWord = raw.trim().slice(6).trim() || undefined;
      if (!auth) { push(L('error', 'not signed in. /login first.')); setInput(''); return; }
      setOutput([]);
      setVocabLoading(true);
      try {
        const word = await fetchVocabWord(auth.token, targetWord);
        setVocabLoading(false);
        setVocabWord(word);
        const fullSentence = word.examples[0];
        setOutput([]);
        setCtx({ passage: fullSentence, blankWord: word.word });
        setMode('vocab_card');
      } catch (err) {
        setVocabLoading(false);
        const msg = String(err);
        if (msg.includes('401')) {
          setAuth(null);
          localStorage.removeItem('tl_auth');
          push(L('error', '  session expired. please /login again.'));
        } else if (msg.includes('422')) {
          const detail = msg.split(':').slice(1).join(':').trim();
          push(L('error', `  ${detail || 'word not recognised — check the spelling'}`));
        } else if (msg.includes('503')) {
          push(L('error', '  vocab pool empty — generation queued. try again in a moment.'));
        } else {
          push(L('error', '  could not fetch word. is the backend running?'));
        }
      }
      setInput(''); return;
    }

    if (!cmd.startsWith('/')) {
      push(L('muted', 'commands start with /  —  try /help'));
    } else {
      push(L('error', `unknown: ${cmd}`));
    }
    setInput('');
  }

  // ── Submit (all modes) ──────────────────────────────────────────────────────

  async function submit(val: string) {
    const isPassword = mode === 'login_password' || mode === 'reg_password';
    const display    = isPassword ? '•'.repeat(val.trim().length) : val.trim();

    if (mode === 'idle') {
      setOutput([L('cmd', `> ${display}`)]);
      await run(val);
      return;
    }

    // Ctrl+C / Escape cancel for any flow — replace output so stale cards don't persist
    if (!val.trim()) {
      if ((mode === 'session' || mode === 'session_mine' || mode === 'session_cloze' || mode === 'session_drill') && auth && ctx.sessionId) {
        abandonSession(auth.token, ctx.sessionId).catch(() => { /* best-effort */ });
      }
      setOutput(BOOT);
      setMode('idle'); setCtx({}); setVocabWord(null);
      setInput(''); return;
    }

    push(L('cmd', display));

    // ── Auth flows ────────────────────────────────────────────────────────────

    if (mode === 'login_email') {
      if (!val.includes('@')) { push(L('error', 'invalid email'), L('muted', 'email')); setInput(''); return; }
      setCtx(c => ({ ...c, email: val.trim() }));
      push(L('muted', 'password'));
      setMode('login_password'); setInput(''); return;
    }

    if (mode === 'login_password') {
      try {
        const { access_token } = await login(ctx.email, val.trim());
        const name = ctx.email.split('@')[0];
        const user: AuthUser = { email: ctx.email, name, token: access_token, isGuest: false };
        setAuth(user);
        localStorage.setItem('tl_auth', JSON.stringify(user));
        push(L('blank', ''), L('success', `welcome, ${name}.`), L('blank', ''));
        setCtx({});
        if (!cefrLevel) { _enterLevelSelect(); } else { setMode('idle'); }
      } catch {
        push(L('blank', ''), L('error', 'invalid credentials. try again.'), L('blank', ''));
        setMode('idle'); setCtx({});
      }
      setInput(''); return;
    }

    if (mode === 'reg_email') {
      if (!val.includes('@')) { push(L('error', 'invalid email'), L('muted', 'email')); setInput(''); return; }
      setCtx(c => ({ ...c, email: val.trim() }));
      push(L('muted', 'display name'));
      setMode('reg_name'); setInput(''); return;
    }

    if (mode === 'reg_name') {
      setCtx(c => ({ ...c, name: val.trim() }));
      push(L('muted', 'password'));
      setMode('reg_password'); setInput(''); return;
    }

    if (mode === 'reg_password') {
      try {
        const { access_token } = await register(ctx.email, ctx.name, val.trim());
        const user: AuthUser = { email: ctx.email, name: ctx.name, token: access_token, isGuest: false };
        setAuth(user);
        localStorage.setItem('tl_auth', JSON.stringify(user));
        push(L('blank', ''), L('success', `account created. welcome, ${ctx.name}.`), L('blank', ''));
        setCtx({});
        if (!cefrLevel) { _enterLevelSelect(); } else { setMode('idle'); }
      } catch {
        push(L('blank', ''), L('error', 'registration failed. email may already be taken.'), L('blank', ''));
        setMode('idle'); setCtx({});
      }
      setInput(''); return;
    }


    if (mode === 'level_select') {
      const lvl = val.trim().toUpperCase();
      if (!(CEFR_LEVELS as readonly string[]).includes(lvl)) {
        push(L('error', `  invalid level — choose one of: ${CEFR_LEVELS.join(', ')}`));
        setInput(''); return;
      }
      setCefrLevel(lvl as CefrLevel);
      try { localStorage.setItem('tl_cefr', lvl); } catch { /* ignore */ }
      if (auth) {
        submitAssessResult(auth.token, lvl).catch(() => { /* best-effort */ });
      }
      setOutput([
        L('blank', ''),
        L('success', `  level set to ${lvl}.`),
        ...hint(L('blank', ''), L('muted', 'type /session to start · /vocab to learn words')),
        L('blank', ''),
      ]);
      setMode('idle'); setInput(''); return;
    }

    setInput('');
  }

  // ── Vocab session complete ───────────────────────────────────────────────────

  function startVocabPractice() {
    setMode('vocab_session');
  }

  function vocabSessionComplete(_typed: string, _durationMs: number) {
    const word = vocabWord;
    if (word && auth) {
      recordVocabPracticed(auth.token, word.word, word.cefr_level, word.pos).catch(() => {/* best-effort */});
    }
    setOutput([
      L('blank', ''),
      L('success', `  "${word?.word}" committed to your vocab model.`),
      ...hint(L('blank', ''), L('muted', 'type /vocab for another word · /vocab list to review')),
      L('blank', ''),
    ]);
    setVocabWord(null);
    setMode('idle');
    setCtx({});
  }

  // ── Session complete ─────────────────────────────────────────────────────────

  function sessionComplete(typed: string, durationMs: number) {
    const passage  = ctx.passage;

    // Guard: passage must be substantially complete and duration must be real.
    // These should never fire now that Enter no longer submits early, but they
    // catch any future path that might call onComplete prematurely.
    const completionRate = passage.length > 0 ? typed.length / passage.length : 0;
    if (completionRate < 0.8 || durationMs < 3000) {
      setMode('idle'); setCtx({});
      return;
    }

    // WPM: word count / actual typing time (timer starts on first keystroke, not on /session)
    const mins     = Math.max(durationMs / 60000, 0.001);
    const wpm      = Math.min(passage.split(/\s+/).filter(Boolean).length / mins, 300);
    // Accuracy: correct chars out of total passage length (standard keystroke accuracy)
    let correct    = 0;
    for (let i = 0; i < Math.min(typed.length, passage.length); i++) {
      if (typed[i] === passage[i]) correct++;
    }
    const accuracy = passage.length > 0 ? correct / passage.length : 0;
    if (auth && ctx.sessionId) {
      completeSession(auth.token, ctx.sessionId, wpm, accuracy, durationMs / 1000).catch(() => { /* best-effort */ });
    }
    const grade    = accuracy > 0.97 ? 'S' : accuracy > 0.93 ? 'A' : accuracy > 0.85 ? 'B' : 'C';
    const note     = ({ S: 'Flawless', A: 'Excellent', B: 'Good', C: 'Keep going' } as Record<string, string>)[grade];
    commitResult({ wpm, accuracy, passage, passageSnippet: passage.slice(0, 18) + '…' });
    push(
      L('blank', ''), L('div', '  ────────────────────────────────────'), L('blank', ''),
      L('out',  `  wpm       ${wpm.toFixed(1)}`),
      L('out',  `  accuracy  ${(accuracy * 100).toFixed(2)}%`),
      L('out',  `  grade     ${grade} — ${note}`),
      L('blank', ''),
      L('success', wpm > 40 ? 'typing speed improving. model updated.' : 'model updated. keep going.'),
      ...xtra(
        L('blank', ''),
        L('muted', accuracy > 0.9 ? 'past_perfect: progressing — advancing grammar level' : 'past_perfect: needs work — flagged for next session'),
        L('muted', `motor delta: +${(Math.random() * 2.2).toFixed(1)} wpm`),
      ),
      ...hint(L('blank', ''), L('muted', 'type /session for another round')),
      L('blank', ''),
    );
    setMode('idle'); setCtx({});
  }

  // ── Mine session complete ──────────────────────────────────────────────────

  function sessionMineComplete(typed: string, durationMs: number) {
    const passage = ctx.passage;
    const completionRate = passage.length > 0 ? typed.length / passage.length : 0;
    if (completionRate < 0.8 || durationMs < 2000) { setMode('idle'); setCtx({}); return; }

    const mins     = Math.max(durationMs / 60000, 0.001);
    const wpm      = Math.min(passage.split(/\s+/).filter(Boolean).length / mins, 300);
    let correct    = 0;
    for (let i = 0; i < Math.min(typed.length, passage.length); i++) {
      if (typed[i] === passage[i]) correct++;
    }
    const accuracy = passage.length > 0 ? correct / passage.length : 0;
    if (auth && ctx.sessionId) {
      completeSession(auth.token, ctx.sessionId, wpm, accuracy, durationMs / 1000).catch(() => {});
    }
    const targetWords: string[] = JSON.parse(ctx.targetWords || '[]') as string[];
    push(
      L('blank', ''), L('div', '  ────────────────────────────────────'), L('blank', ''),
      L('out',  `  wpm         ${wpm.toFixed(1)}`),
      L('out',  `  accuracy    ${(accuracy * 100).toFixed(2)}%`),
      L('out',  `  words mined  ${targetWords.join(', ') || '—'}`),
      L('blank', ''),
      L('success', 'vocab reinforced. motor model updated.'),
      ...hint(L('blank', ''), L('muted', 'type /session mine for another · /vocab to learn more')),
      L('blank', ''),
    );
    setMode('idle'); setCtx({});
  }

  // ── Cloze session complete ─────────────────────────────────────────────────

  function sessionClozeComplete(
    results: { answer: string; correct: boolean }[],
    durationMs: number,
  ) {
    const score = results.filter(r => r.correct).length;
    const total = results.length;
    const totalChars = results.reduce((s, r) => s + r.answer.length, 0);
    const mins    = Math.max(durationMs / 60000, 0.001);
    const wpm     = Math.min((totalChars / 5) / mins, 300);
    const accuracy = total > 0 ? score / total : 0;
    if (auth && ctx.sessionId) {
      completeSession(auth.token, ctx.sessionId, wpm, accuracy, durationMs / 1000).catch(() => {});
    }
    const grade = accuracy >= 1 ? 'S' : accuracy >= 0.8 ? 'A' : accuracy >= 0.6 ? 'B' : 'C';
    push(
      L('blank', ''), L('div', '  ────────────────────────────────────'), L('blank', ''),
      L('out',  `  score    ${score} / ${total}`),
      L('out',  `  grade    ${grade}`),
      L('blank', ''),
      L('success', score === total ? 'perfect recall. vocab model updated.' : `${score}/${total} correct. keep practicing.`),
      ...hint(L('blank', ''), L('muted', 'type /session cloze for another · /vocab to learn more')),
      L('blank', ''),
    );
    setMode('idle'); setCtx({});
  }

  // ── Drill session complete ─────────────────────────────────────────────────

  function sessionDrillComplete(totalTyped: number, durationMs: number) {
    const mins    = Math.max(durationMs / 60000, 0.001);
    const wpm     = Math.min((totalTyped / 5) / mins, 300);
    const grammarTarget = ctx.grammarTarget ?? 'grammar';
    if (auth && ctx.sessionId) {
      completeSession(auth.token, ctx.sessionId, wpm, 1.0, durationMs / 1000).catch(() => {});
    }
    push(
      L('blank', ''), L('div', '  ────────────────────────────────────'), L('blank', ''),
      L('out',  `  focus     ${grammarTarget}`),
      L('out',  `  rounds    3 / 3 complete`),
      L('out',  `  wpm       ${wpm.toFixed(1)}`),
      L('blank', ''),
      L('success', 'grammar pattern encoded. model updated.'),
      ...hint(L('blank', ''), L('muted', 'type /session drill for another pattern')),
      L('blank', ''),
    );
    setMode('idle'); setCtx({});
  }

  function vocabCloudWordClick(word: string) {
    void run(`/vocab ${word}`);
  }

  return {
    output, input, setInput, mode, ctx, auth, history,
    vocabWord, vocabLoading, vocabCloudWords, submit,
    startVocabPractice, sessionComplete, vocabSessionComplete,
    sessionMineComplete, sessionClozeComplete, sessionDrillComplete,
    vocabCloudWordClick,
  };
}
