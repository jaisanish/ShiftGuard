import React, { useState } from 'react';
import { Mic, Send, Sparkles } from 'lucide-react';

/**
 * CopilotEntry
 * Compact in-cab voice & text assistant entry point on the Command Center console.
 * Strictly non-chatty, operator-focused interaction shortcut.
 */
export default function CopilotEntry() {
  const [query, setQuery] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [isListening, setIsListening] = useState(false);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!query.trim()) return;

    const q = query.trim().toLowerCase();
    if (q.includes('next task')) {
      setFeedback('Next queued assignment: ORE HAULING & DUMP (Scheduled in 15m).');
    } else if (q.includes('status') || q.includes('operating')) {
      setFeedback('Machine operational state nominal. All edge safety interlocks active.');
    } else {
      setFeedback(`Query received: "${query}". Co-Pilot diagnostic subsystem is on STANDBY.`);
    }
    setQuery('');
  };

  const handleMicClick = () => {
    setIsListening(true);
    setFeedback('Listening for in-cab voice query...');
    setTimeout(() => {
      setIsListening(false);
      setFeedback('Voice query: "What\'s my next task?" -> Next queued: ORE HAULING & DUMP.');
    }, 2000);
  };

  return (
    <div className="glass-panel hud-corner p-4 rounded-sm space-y-3 font-mono">
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-2 text-xs">
        <div className="flex items-center gap-2 font-bold uppercase text-zinc-200">
          <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
          <span>ASK SHIFTGUARD</span>
        </div>
        <span className="text-[10px] text-zinc-400">
          IN-CAB VOICE & QUERY ENTRY
        </span>
      </div>

      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
        <button
          onClick={handleMicClick}
          className={`px-3 py-2 rounded-xs border text-xs font-bold flex items-center justify-center gap-2 transition-all cursor-pointer ${
            isListening
              ? 'bg-rose-600/30 border-rose-500 text-rose-300 animate-pulse'
              : 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/25'
          }`}
          title="Activate cab microphone"
        >
          <Mic className={`w-3.5 h-3.5 ${isListening ? 'animate-bounce' : ''}`} />
          <span>{isListening ? 'LISTENING...' : 'VOICE'}</span>
        </button>

        <form onSubmit={handleSubmit} className="flex-1 flex items-center gap-1.5 min-w-0">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder='Ask: "What&apos;s my next task?" or "Check proximity clearance"'
            className="flex-1 bg-[#12151e] border border-white/[0.08] px-3 py-2 rounded-xs text-xs text-zinc-200 placeholder-zinc-500 focus:outline-hidden focus:border-emerald-500/50"
          />
          <button
            type="submit"
            disabled={!query.trim()}
            className="px-3 py-2 rounded-xs bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 text-zinc-200 border border-white/[0.08] transition-colors cursor-pointer text-xs"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>

      {/* Suggested Quick Queries */}
      <div className="flex flex-wrap items-center gap-2 text-[11px]">
        <span className="text-zinc-500">QUICK:</span>
        <button
          onClick={() => {
            setQuery("What's my next task?");
            setFeedback('Next queued assignment: ORE HAULING & DUMP (Auto-dispatched).');
          }}
          className="px-2 py-0.5 rounded-xs bg-white/[0.03] hover:bg-white/[0.08] text-zinc-300 border border-white/[0.05] transition-colors cursor-pointer"
        >
          &quot;What&apos;s my next task?&quot;
        </button>
        <button
          onClick={() => {
            setQuery("Check machine health");
            setFeedback('Engine RPM nominal. Hydraulic temperature within operating envelope.');
          }}
          className="px-2 py-0.5 rounded-xs bg-white/[0.03] hover:bg-white/[0.08] text-zinc-300 border border-white/[0.05] transition-colors cursor-pointer"
        >
          &quot;Check machine health&quot;
        </button>
      </div>

      {feedback && (
        <div className="p-2.5 rounded-xs bg-[#121620] border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between gap-2">
          <span>{feedback}</span>
          <button
            onClick={() => setFeedback(null)}
            className="text-zinc-400 hover:text-zinc-200 cursor-pointer"
          >
            &times;
          </button>
        </div>
      )}
    </div>
  );
}
