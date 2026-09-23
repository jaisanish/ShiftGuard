import React from 'react';
import { BookOpen, Clock, CheckCircle2, PlayCircle, Shield, Award } from 'lucide-react';

/**
 * TrainingLibrary
 * Curriculum module grid displaying available coaching lessons.
 */
export default function TrainingLibrary({
  lessons = [],
  completedLessonIds = [],
  onSelectLesson,
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-emerald-400" />
          <h2 className="text-xs font-mono font-bold tracking-wider text-zinc-200 uppercase">
            CURRICULUM MODULES
          </h2>
        </div>
        <span className="text-[10px] font-mono text-zinc-400">
          {lessons.length} MODULES AVAILABLE
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {lessons.map((lesson) => {
          const isCompleted = completedLessonIds.includes(lesson.lesson_id);

          return (
            <div
              key={lesson.lesson_id}
              className="glass-panel p-4 rounded-xs border border-white/[0.08] hover:border-emerald-500/40 transition-colors flex flex-col justify-between space-y-4 group"
            >
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-xs bg-zinc-800 text-zinc-300 border border-white/[0.06] uppercase">
                    {lesson.category}
                  </span>
                  <div className="flex items-center gap-1.5 text-[11px] font-mono text-zinc-400">
                    <Clock className="w-3 h-3 text-zinc-400" />
                    <span>{lesson.duration_min} MIN</span>
                  </div>
                </div>

                <h3 className="text-sm font-semibold text-white group-hover:text-emerald-300 transition-colors">
                  {lesson.title}
                </h3>

                <p className="text-xs text-zinc-300 font-mono line-clamp-2">
                  {lesson.description}
                </p>
              </div>

              <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between">
                {isCompleted ? (
                  <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-400 font-semibold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    COMPLETED
                  </span>
                ) : (
                  <span className="text-[11px] font-mono text-zinc-400">
                    STATUS: READY
                  </span>
                )}

                <button
                  onClick={() => onSelectLesson?.(lesson.lesson_id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xs text-xs font-mono font-semibold bg-white/[0.05] hover:bg-emerald-500/20 text-zinc-200 hover:text-emerald-300 border border-white/[0.08] hover:border-emerald-500/40 transition-colors cursor-pointer"
                >
                  <PlayCircle className="w-3.5 h-3.5" />
                  <span>{isCompleted ? 'REVIEW' : 'LAUNCH'}</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
