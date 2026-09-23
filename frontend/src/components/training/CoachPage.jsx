import React, { useState, useEffect } from 'react';
import { 
  fetchTrainingRecommendations, 
  fetchTrainingLessons, 
  fetchTrainingLessonById,
  fetchTrainingHistory,
  completeTrainingLesson
} from '../../services/api';

import TrainingRecommendation from './TrainingRecommendation';
import TrainingLibrary from './TrainingLibrary';
import TrainingLesson from './TrainingLesson';
import TrainingQuiz from './TrainingQuiz';
import TrainingHistory from './TrainingHistory';
import { GraduationCap, ArrowLeft, RefreshCw } from 'lucide-react';

/**
 * CoachPage
 * Top-level Operator Training Hub view.
 * Orchestrates coaching recommendations, interactive curriculum,
 * video/slide instructions, comprehension quizzes, and certified histories.
 */
export default function CoachPage({
  operatorId = 'OP-101',
  initialLessonId = null,
  onReturnToCockpit,
}) {
  const [viewState, setViewState] = useState('hub'); // 'hub', 'lesson', 'quiz'
  const [recommendations, setRecommendations] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedLesson, setSelectedLesson] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load curriculum, active recommendations, and operator history
  const loadCoachData = async () => {
    setLoading(true);
    try {
      const [recs, allLessons, hist] = await Promise.all([
        fetchTrainingRecommendations(operatorId),
        fetchTrainingLessons(),
        fetchTrainingHistory(operatorId),
      ]);
      setRecommendations(recs || []);
      setLessons(allLessons || []);
      setHistory(hist || []);

      // If initialLessonId specified (e.g. from Coaching Moment click), open directly
      if (initialLessonId) {
        const target = (allLessons || []).find((l) => l.lesson_id.toUpperCase() === initialLessonId.toUpperCase());
        if (target) {
          setSelectedLesson(target);
          setViewState('lesson');
        }
      }
    } catch (err) {
      console.error('[CoachPage] Failed to load training hub data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCoachData();
  }, [operatorId, initialLessonId]);

  const handleStartLesson = async (lessonId) => {
    let target = lessons.find((l) => l.lesson_id.toUpperCase() === lessonId.toUpperCase());
    if (!target) {
      target = await fetchTrainingLessonById(lessonId);
    }
    if (target) {
      setSelectedLesson(target);
      setViewState('lesson');
    }
  };

  const handleTakeQuiz = () => {
    setViewState('quiz');
  };

  const handleQuizComplete = async (completionPayload) => {
    try {
      await completeTrainingLesson(completionPayload);
      // Reload history
      const updatedHistory = await fetchTrainingHistory(operatorId);
      setHistory(updatedHistory || []);
    } catch (err) {
      console.error('[CoachPage] Failed to save completion:', err);
    }
  };

  const completedLessonIds = history.filter((h) => h.passed).map((h) => h.lesson_id);
  const primaryRecommendation = recommendations.length > 0 ? recommendations[0] : null;

  return (
    <div className="space-y-6">
      {/* Page Context Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.08] pb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xs bg-emerald-500/10 border border-emerald-500/40 text-emerald-400 flex items-center justify-center">
            <GraduationCap className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="display-heading text-xl font-bold tracking-tight text-white uppercase">
                OPERATOR COACH & TRAINING HUB
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-xs bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 font-semibold">
                SYSTEM ACTIVE
              </span>
            </div>
            <p className="text-xs font-mono text-zinc-300">
              Interactive procedural coaching, safety certifications, and telemetry recommendations.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={onReturnToCockpit}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xs text-xs font-mono text-zinc-300 hover:text-white bg-zinc-900 border border-white/[0.08] hover:border-white/[0.2] transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>RETURN TO COCKPIT</span>
          </button>
        </div>
      </div>

      {/* View Switcher: Hub vs Lesson vs Quiz */}
      {viewState === 'hub' && (
        <div className="space-y-8">
          {/* 1. Hero Recommendation (if active) */}
          {primaryRecommendation && (
            <TrainingRecommendation
              recommendation={primaryRecommendation}
              onStartLesson={handleStartLesson}
            />
          )}

          {/* 2. Curriculum Library Grid */}
          <TrainingLibrary
            lessons={lessons}
            completedLessonIds={completedLessonIds}
            onSelectLesson={handleStartLesson}
          />

          {/* 3. History of Completed Lessons */}
          <TrainingHistory history={history} />
        </div>
      )}

      {viewState === 'lesson' && selectedLesson && (
        <TrainingLesson
          lesson={selectedLesson}
          onBack={() => setViewState('hub')}
          onTakeQuiz={handleTakeQuiz}
        />
      )}

      {viewState === 'quiz' && selectedLesson && (
        <TrainingQuiz
          lesson={selectedLesson}
          operatorId={operatorId}
          onBack={() => setViewState('lesson')}
          onComplete={handleQuizComplete}
        />
      )}
    </div>
  );
}
