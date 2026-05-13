'use client';

import type { VocabWordResponse } from '@/lib/api';

interface Props {
  word: VocabWordResponse;
}

const LABEL: React.CSSProperties = {
  fontSize: 10,
  color: 'var(--t3)',
  letterSpacing: '0.12em',
  marginBottom: 10,
};

const CELL: React.CSSProperties = {
  padding: '14px 18px',
};

export default function VocabCard({ word }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Word + meta */}
      <div>
        <div className="shimmer" style={{
          fontSize: 46, fontWeight: 700,
          lineHeight: 1.1, letterSpacing: '-0.02em',
          fontFamily: 'var(--font)',
        }}>
          {word.word}
        </div>
        <div style={{
          marginTop: 10, fontSize: 11, color: 'var(--t3)',
          letterSpacing: '0.12em', display: 'flex', gap: 10, alignItems: 'center',
        }}>
          <span>{word.pos.toUpperCase()}</span>
          <span>·</span>
          <span>{word.cefr_level}</span>
        </div>
      </div>

      {/* Card grid */}
      <div style={{ border: '1px solid var(--b-inner)' }}>

        {/* Definition */}
        <div style={{ ...CELL, borderBottom: '1px solid var(--b-inner)' }}>
          <div style={LABEL}>DEFINITION</div>
          <div style={{ fontSize: 14, color: 'var(--t1)', lineHeight: 1.65 }}>
            {word.definition}
          </div>
        </div>

        {/* Etymology | Register | Contrast */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
          borderBottom: '1px solid var(--b-inner)',
        }}>
          <div style={{ ...CELL, borderRight: '1px solid var(--b-inner)' }}>
            <div style={LABEL}>ETYMOLOGY</div>
            <div style={{ fontSize: 13, color: 'var(--t1)', lineHeight: 1.6 }}>
              {word.etymology}
            </div>
          </div>
          <div style={{ ...CELL, borderRight: '1px solid var(--b-inner)' }}>
            <div style={LABEL}>REGISTER</div>
            <div style={{ fontSize: 13, color: 'var(--t2)', lineHeight: 1.6, fontStyle: 'italic' }}>
              {word.register}
            </div>
          </div>
          <div style={CELL}>
            <div style={LABEL}>CONTRAST</div>
            <div style={{ fontSize: 13, color: 'var(--t2)', lineHeight: 1.6, fontStyle: 'italic' }}>
              {word.contrast_note}
            </div>
          </div>
        </div>

        {/* Example */}
        <div style={{ ...CELL, borderBottom: '1px solid var(--b-inner)' }}>
          <div style={LABEL}>EXAMPLE</div>
          <div style={{ fontSize: 14, color: 'var(--t2)', lineHeight: 1.65, fontStyle: 'italic' }}>
            &ldquo;{word.examples[0]}&rdquo;
          </div>
        </div>

        {/* Memory hook */}
        <div style={{ ...CELL, display: 'flex', gap: 20, alignItems: 'baseline' }}>
          <div style={{ ...LABEL, marginBottom: 0, flexShrink: 0 }}>MEMORY HOOK</div>
          <div style={{ fontSize: 13, color: 'var(--t2)', lineHeight: 1.6, fontStyle: 'italic' }}>
            {word.memory_hook}
          </div>
        </div>

      </div>
    </div>
  );
}
