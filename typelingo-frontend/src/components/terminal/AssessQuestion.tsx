'use client';

import type { AssessmentQuestionResponse } from '@/lib/api';

export interface AssessFeedback {
  correct: boolean;
  explanation: string;
  correctAnswer: string;
}

interface Props {
  question: AssessmentQuestionResponse;
  index: number;
  total: number;
  selectedOption: number;
  feedback: AssessFeedback | null;
}

export default function AssessQuestion({ question, index, total, selectedOption, feedback }: Props) {
  return (
    <div>
      {/* Progress header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: 24,
      }}>
        <span style={{ fontSize: 10, color: 'var(--t3)', letterSpacing: '0.13em', textTransform: 'uppercase' }}>
          english level
        </span>
        <span style={{ fontSize: 10, color: 'var(--t3)' }}>
          {index + 1} / {total}
        </span>
      </div>

      {/* Sentence */}
      <div style={{
        fontSize: 16, color: 'var(--t1)', lineHeight: 1.8,
        marginBottom: 20, letterSpacing: '0.01em',
      }}>
        {question.sentence}
      </div>

      {/* Options */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 5, marginBottom: 16 }}>
        {question.options.map((opt, i) => {
          const isSelected = i === selectedOption;
          const isCorrectAns = !!feedback && i === question.correct_index;
          const isWrongChosen = !!feedback && !feedback.correct && isSelected;

          let borderColor = isSelected ? 'var(--b-cmd)' : 'var(--b-inner)';
          let color = isSelected ? 'var(--t1)' : 'var(--t2)';
          let bg = isSelected ? 'rgba(255,255,255,0.02)' : 'transparent';

          if (feedback) {
            if (isCorrectAns)  { borderColor = 'var(--green)'; color = 'var(--green)'; bg = 'transparent'; }
            else if (isWrongChosen) { borderColor = 'var(--red)';   color = 'var(--red)';   bg = 'transparent'; }
            else               { borderColor = 'var(--b-inner)'; color = 'var(--t3)';    bg = 'transparent'; }
          }

          return (
            <div
              key={i}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 14px',
                border: `1px solid ${borderColor}`,
                color, background: bg,
                fontSize: 13,
                transition: 'border-color 0.15s, color 0.15s',
              }}
            >
              <span style={{ fontSize: 10, color: 'var(--t3)', minWidth: 14, flexShrink: 0 }}>
                {String.fromCharCode(97 + i)}
              </span>
              {opt}
            </div>
          );
        })}
      </div>

      {/* Feedback */}
      {feedback && (
        <div style={{
          padding: '12px 14px',
          border: `1px solid ${feedback.correct ? 'var(--green)' : 'var(--red)'}`,
          animation: 'fadeUp 0.15s ease both',
        }}>
          <div style={{
            fontSize: 11,
            color: feedback.correct ? 'var(--green)' : 'var(--red)',
            letterSpacing: '0.04em',
            marginBottom: feedback.explanation ? 6 : 0,
          }}>
            {feedback.correct ? '✓ correct' : `✗ correct: "${feedback.correctAnswer}"`}
          </div>
          {feedback.explanation && (
            <div style={{ fontSize: 12, color: 'var(--t3)', lineHeight: 1.65 }}>
              {feedback.explanation}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
