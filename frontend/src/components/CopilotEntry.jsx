import React, { useRef, useState } from 'react';
import { Mic, Send, Sparkles, Volume2 } from 'lucide-react';
import { askCopilot } from '../services/api';
import { useRealtime } from '../context/RealtimeContext';

export default function CopilotEntry() {
  const { telemetry, currentTask, upcomingTask, etaPrediction } = useRealtime();
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  const submit = async (event, suppliedQuery = null) => {
    event?.preventDefault(); const question = (suppliedQuery || query).trim(); if (!question) return;
    setResponse({ answer: 'Checking edge context…', loading: true });
    try {
      const result = await askCopilot(question, { telemetry, task: currentTask, upcoming_task: upcomingTask, eta: etaPrediction });
      setResponse(result); setQuery('');
    } catch (error) { setResponse({ answer: `Copilot unavailable: ${error.message}`, error: true }); }
  };
  const speak = (text) => { if ('speechSynthesis' in window) { window.speechSynthesis.cancel(); window.speechSynthesis.speak(new SpeechSynthesisUtterance(text)); } };
  const listen = () => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) { setResponse({ answer: 'Voice recognition is not supported in this browser. Type your question instead.', error: true }); return; }
    const recognition = new Recognition(); recognition.lang = 'en-US'; recognition.interimResults = false;
    recognition.onstart = () => setIsListening(true); recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setResponse({ answer: 'Voice capture failed. Please try again or type your question.', error: true });
    recognition.onresult = (event) => { const spoken = event.results[0][0].transcript; setQuery(spoken); submit(null, spoken); };
    recognitionRef.current = recognition; recognition.start();
  };
  return <div className="glass-panel hud-corner p-4 rounded-sm space-y-3 font-mono">
    <div className="flex items-center justify-between border-b border-white/[0.06] pb-2 text-xs"><div className="flex items-center gap-2 font-bold uppercase text-zinc-200"><Sparkles className="w-3.5 h-3.5 text-emerald-400" />ASK SHIFTGUARD</div><span className="text-[10px] text-zinc-400">ADVISORY VOICE + RAG</span></div>
    <div className="flex gap-2"><button onClick={listen} className={`px-3 py-2 rounded-xs border text-xs font-bold ${isListening ? 'bg-rose-600/30 border-rose-500 text-rose-300 animate-pulse' : 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300'}`}><Mic className="w-3.5 h-3.5 inline mr-1" />{isListening ? 'LISTENING' : 'VOICE'}</button><form onSubmit={submit} className="flex-1 flex gap-1.5"><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Ask about ETA, health, task, or safety" className="flex-1 bg-[#12151e] border border-white/[0.08] px-3 py-2 rounded-xs text-xs" /><button disabled={!query.trim()} className="px-3 py-2 rounded-xs bg-zinc-800 disabled:opacity-40"><Send className="w-3.5 h-3.5" /></button></form></div>
    <div className="flex flex-wrap gap-2 text-[11px]"><button onClick={() => submit(null, "What's my next task?")}>NEXT TASK</button><button onClick={() => submit(null, 'What is my ETA?')}>ETA</button><button onClick={() => submit(null, 'Check machine health')}>HEALTH</button><button onClick={() => submit(null, 'What should I do about proximity safety?')}>SAFETY</button></div>
    {response && <div className={`p-2.5 rounded-xs border text-xs flex gap-2 ${response.error ? 'border-rose-500/30 text-rose-300' : 'border-emerald-500/30 text-emerald-300'}`}><span className="flex-1">{response.answer}</span>{!response.loading && !response.error && <button onClick={() => speak(response.answer)} title="Read response aloud"><Volume2 className="w-4 h-4" /></button>}</div>}
    <p className="text-[10px] text-zinc-500">Advisory only — edge safety alerts and controls remain authoritative.</p>
  </div>;
}
