'use client';
import { useEffect, useState } from 'react';

export default function LoadingDots() {
  const [n, setN] = useState(1);
  useEffect(() => {
    const t = setInterval(() => setN(d => d === 3 ? 1 : d + 1), 350);
    return () => clearInterval(t);
  }, []);
  return (
    <span style={{ fontSize: 13, color: 'var(--t3)', letterSpacing: '0.1em' }}>
      {'·'.repeat(n)}
    </span>
  );
}
