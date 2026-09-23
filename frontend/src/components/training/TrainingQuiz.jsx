import React, { useState } from 'react';
import { HelpCircle, CheckCircle2, XCircle, ArrowLeft, RefreshCw, Award } from 'lucide-react';

/**
 * TrainingQuiz
 * 3-question comprehension check with immediate feedback,
 * score calculation, and persistent completion recording.
 */
export default function TrainingQuiz({
  lesson,
  operatorId = 'OP-101',
  onBack,
  onComplete,
}) {
  const questions = lesson?.quiz || [];
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [scorePct, setScorePct] = useState(0);
  const [passed, setPassed] = useState(false);

  const handleSelectOption = (questionIndex, optionIndex) => {
    if (submitted) return;
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionIndex]: optionIndex,
    }));
  };

  const allAnswered = questions.length > 0 && Object.keys(selectedAnswers).length === questions.length;

  const handleSubmit = () => {
    if (!allAnswered || submitted) return;

    let correctCount = 0;
    questions.forEach((q, idx) => {
      if (selectedAnswers[idx] === q.correct_index) {
        correctCount += 1;
      }
    });

    const calculatedPct = Math.round((correctCount / questions.length) * 100);
    const hasPassed = calculatedPct >= 66; // 2 out of 3 = 67%

    setScorePct(calculatedPct);
    setPassed(hasPassed);
    setSubmitted(true);

    onComplete?.({
      lesson_id: lesson.lesson_id,
      operator_id: operatorId,
      score_pct: calculatedPct,
      passed: hasPassed,
    });
  };

  const handleRetake = () => {
    setSelectedAnswers({});
    setSubmitted(false);
    setScorePct(0);
    setPassed(false);
  };

  return (
    <div className="glass-panel hud-corner p-5 sm:p-6 rounded-sm space-y-6">
      {/* Quiz Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.08] pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xs text-xs font-mono text-zinc-300 hover:text-white bg-zinc-900 border border-white/[0.08] hover:border-white/[0.2] transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>BACK TO LESSON</span>
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold">
                COMPREHENSION CHECK
              </span>
              <span className="text-xs font-mono text-zinc-400">
                {questions.length} QUESTIONS • PASS: 66%
              </span>
            </div>
            <h1 className="display-heading text-lg sm:text-xl font-bold text-white tracking-tight uppercase pt-1">
              {lesson.title} — QUIZ
            </h1>
          </div>
        </div>

        {submitted && (
          <div className={`px-4 py-2 rounded-xs border font-mono text-xs font-bold uppercase tracking-wider flex items-center gap-2 ${
            passed 
              ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.2)]'
              : 'bg-red-950/60 border-red-500/40 text-red-300'
          }`}>
            <Award className="w-4 h-4" />
            <span>SCORE: {scorePct}% — {passed ? 'PASSED' : 'NOT PASSED'}</span>
          </div>
        )}
      </div>

      {/* Questions Stack */}
      <div className="space-y-6">
        {questions.map((q, qIdx) => {
          const isSelected = selectedAnswers[qIdx] !== undefined;
          const selectedOption = selectedAnswers[qIdx];
          const isCorrect = selectedOption === q.correct_index;

          return (
            <div
              key={q.id || qIdx}
              className="p-4 sm:p-5 rounded-xs bg-[#12151d] border border-white/[0.08] space-y-3.5"
            >
              <div className="flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-xs bg-zinc-800 text-zinc-300 border border-white/[0.06] flex items-center justify-center shrink-0 text-xs font-mono font-bold">
                  {qIdx + 1}
                </span>
                <h3 className="text-sm font-semibold text-white">
                  {q.question}
                </h3>
              </div>

              {/* Options */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                {q.options.map((opt, optIdx) => {
                  const isThisSelected = selectedOption === optIdx;
                  const isThisCorrect = optIdx === q.correct_index;

                  let borderClass = 'border-white/[0.08] hover:border-emerald-500/30';
                  let bgClass = 'bg-[#151822]/80';
                  let textClass = 'text-zinc-300';

                  if (submitted) {
                    if (isThisCorrect) {
                      borderClass = 'border-emerald-500/60';
                      bgClass = 'bg-emerald-950/40';
                      textClass = 'text-emerald-300 font-semibold';
                    } else if (isThisSelected && !isThisCorrect) {
                      borderClass = 'border-red-500/60';
                      bgClass = 'bg-red-950/40';
                      textClass = 'text-red-300 line-through';
                    }
                  } else if (isThisSelected) {
                    borderClass = 'border-emerald-500/60';
                    bgClass = 'bg-emerald-950/30';
                    textClass = 'text-emerald-300 font-semibold';
                  }

                  return (
                    <button
                      key={optIdx}
                      type="button"
                      disabled={submitted}
                      onClick={() => handleSelectOption(qIdx, optIdx)}
                      className={`p-3 rounded-xs border text-left text-xs font-mono transition-all cursor-pointer flex items-center justify-between gap-3 ${borderClass} ${bgClass} ${textClass}`}
                    >
                      <span>{opt}</span>
                      {submitted && isThisCorrect && (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      )}
                      {submitted && isThisSelected && !isThisCorrect && (
                        <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Technical Explanation on Submission */}
              {submitted && q.explanation && (
                <div className="mt-2.5 p-2.5 rounded-xs bg-black/40 border border-white/[0.05] text-[11px] font-mono text-zinc-300">
                  <strong className="text-emerald-400 block uppercase text-[10px]">Reference:</strong>
                  {q.explanation}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Action Footer */}
      <div className="pt-4 border-t border-white/[0.08] flex flex-wrap items-center justify-between gap-4">
        <span className="text-xs font-mono text-zinc-400">
          {!submitted
            ? `${Object.keys(selectedAnswers).length} of ${questions.length} answered`
            : passed
            ? 'Lesson complete. Record committed to SQLite log.'
            : 'Review procedure key points and retake quiz to attain certification.'}
        </span>

        <div className="flex items-center gap-3">
          {submitted ? (
            <>
              {!passed && (
                <button
                  onClick={handleRetake}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-mono text-xs uppercase font-bold tracking-wider transition-colors cursor-pointer"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>RETAKE QUIZ</span>
                </button>
              )}
              <button
                onClick={onBack}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xs bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-mono text-xs uppercase font-bold tracking-wider transition-colors shadow-[0_0_12px_rgba(16,185,129,0.3)] cursor-pointer"
              >
                <span>RETURN TO HUB</span>
              </button>
            </>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!allAnswered}
              className={`flex items-center gap-2 px-6 py-2.5 rounded-xs font-mono text-xs uppercase font-bold tracking-wider transition-colors shadow-[0_0_12px_rgba(16,185,129,0.2)] ${
                allAnswered
                  ? 'bg-emerald-500 hover:bg-emerald-400 text-zinc-950 cursor-pointer'
                  : 'bg-zinc-800 text-zinc-500 border border-white/[0.05] cursor-not-allowed'
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>SUBMIT ANSWERS</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
