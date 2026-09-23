import React, { useState } from 'react';
import { ArrowLeft, PlayCircle, FileText, CheckCircle2, AlertCircle, HelpCircle, Video } from 'lucide-react';

/**
 * TrainingLesson
 * Interactive lesson viewer with video player, PDF slides fallback,
 * key procedural takeaways, and quiz trigger.
 */
export default function TrainingLesson({
  lesson,
  onBack,
  onTakeQuiz,
}) {
  const [videoError, setVideoError] = useState(false);
  const [activeTab, setActiveTab] = useState('video'); // 'video' or 'slides'

  if (!lesson) return null;

  return (
    <div className="glass-panel hud-corner p-5 sm:p-6 rounded-sm space-y-6">
      {/* Lesson Header Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.08] pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xs text-xs font-mono text-zinc-300 hover:text-white bg-zinc-900 border border-white/[0.08] hover:border-white/[0.2] transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>LIBRARY</span>
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold">
                {lesson.category}
              </span>
              <span className="text-xs font-mono text-zinc-400">
                {lesson.lesson_id} • {lesson.duration_min} MIN
              </span>
            </div>
            <h1 className="display-heading text-lg sm:text-xl font-bold text-white tracking-tight uppercase pt-1">
              {lesson.title}
            </h1>
          </div>
        </div>

        <button
          onClick={onTakeQuiz}
          className="flex items-center gap-2 px-4 py-2 rounded-xs bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-mono font-bold text-xs uppercase tracking-wider transition-colors shadow-[0_0_12px_rgba(16,185,129,0.25)] cursor-pointer"
        >
          <HelpCircle className="w-4 h-4" />
          <span>TAKE 3-QUESTION QUIZ</span>
        </button>
      </div>

      {/* Media Player Viewport */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs font-mono text-zinc-300">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('video')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-xs transition-colors cursor-pointer ${
                activeTab === 'video'
                  ? 'bg-white/[0.1] text-white border border-white/[0.15]'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Video className="w-3.5 h-3.5" />
              <span>COACHING VIDEO</span>
            </button>
            <button
              onClick={() => setActiveTab('slides')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-xs transition-colors cursor-pointer ${
                activeTab === 'slides'
                  ? 'bg-white/[0.1] text-white border border-white/[0.15]'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>PROCEDURAL SLIDES / PDF</span>
            </button>
          </div>

          <span className="text-[10px] text-zinc-300">
            AUDIO: CABIN COMM INTERCOM
          </span>
        </div>

        {/* Media Frame Container */}
        <div className="w-full bg-[#0a0c10] border border-white/[0.1] rounded-xs overflow-hidden aspect-video max-h-[420px] flex items-center justify-center relative">
          {activeTab === 'video' ? (
            !videoError ? (
              <video
                src={lesson.video_url}
                controls
                className="w-full h-full object-contain"
                onError={() => setVideoError(true)}
              >
                Your browser does not support the video tag.
              </video>
            ) : (
              <div className="text-center p-6 space-y-2.5 max-w-md">
                <AlertCircle className="w-8 h-8 text-amber-400 mx-auto" />
                <h4 className="text-sm font-mono font-semibold text-zinc-200">
                  Training media not configured
                </h4>
                <p className="text-xs font-mono text-zinc-300">
                  Place <code className="text-emerald-400">{lesson.video_url.replace('/training/', '')}</code> in <code className="text-zinc-200">frontend/public/training/</code> to enable full video playback.
                </p>
                <div className="pt-2">
                  <span className="inline-block text-[11px] font-mono px-3 py-1 rounded-xs bg-zinc-800 text-zinc-300 border border-white/[0.06]">
                    Proceeding with procedural key points and quiz
                  </span>
                </div>
              </div>
            )
          ) : (
            <div className="text-center p-6 space-y-2.5 max-w-md">
              <FileText className="w-8 h-8 text-emerald-400 mx-auto" />
              <h4 className="text-sm font-mono font-semibold text-zinc-200">
                Training slide deck / PDF reference
              </h4>
              <p className="text-xs font-mono text-zinc-300">
                Document <code className="text-emerald-400">{lesson.pdf_url.replace('/training/', '')}</code> ready for cab download.
              </p>
              <div className="pt-2">
                <a
                  href={lesson.pdf_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-block text-xs font-mono font-semibold px-3 py-1.5 rounded-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/30 transition-colors"
                >
                  OPEN REFERENCE MANUAL (PDF)
                </a>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Key Learning Takeaways */}
      <div className="space-y-3 pt-2">
        <h3 className="text-xs font-mono font-bold tracking-wider text-zinc-200 uppercase flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          KEY PROCEDURAL TAKEAWAYS
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
          {lesson.key_points.map((point, index) => (
            <div
              key={index}
              className="flex items-start gap-2.5 p-3 rounded-xs bg-[#12151d] border border-white/[0.06] text-xs font-mono text-zinc-300"
            >
              <span className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 text-[10px] font-bold">
                {index + 1}
              </span>
              <span>{point}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
