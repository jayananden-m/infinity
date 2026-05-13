'use client';

import { useEffect, useState } from 'react';
import Terminal, { type Layout, type Theme, type Verbosity } from '@/components/terminal/Terminal';

// Persisted tweaks — stored in localStorage so they survive refresh
const TWEAK_KEY = 'tl_tweaks';
const defaults = { theme: 'void' as Theme, layout: 'focused' as Layout, verbosity: 'normal' as Verbosity };

export default function Home() {
  const [tweaks, setTweaks] = useState(defaults);

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(TWEAK_KEY) || '{}');
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTweaks(t => ({ ...t, ...saved }));
    } catch { /* ignore */ }
  }, []);

  return (
    <main style={{ height: '100vh', position: 'relative', zIndex: 1 }}>
      <Terminal
        theme={tweaks.theme}
        layout={tweaks.layout}
        verbosity={tweaks.verbosity}
      />
    </main>
  );
}
