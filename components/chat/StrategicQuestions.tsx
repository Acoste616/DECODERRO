
import React from 'react';
import { Lightbulb, ChevronRight } from 'lucide-react';

interface Props {
  questions: string[];
  onSelect: (question: string) => void;
}

const StrategicQuestions: React.FC<Props> = ({ questions, onSelect }) => {
  if (!questions || questions.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-zinc-800/50">
      <div className="flex items-center gap-2 text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-2">
        <Lightbulb size={12} className="text-yellow-500" />
        <span>Strategic Questions (SPIN)</span>
      </div>
      <div className="space-y-1">
        {questions.map((q, i) => (
          <button
            key={i}
            onClick={() => onSelect(q)}
            className="w-full text-left text-xs text-zinc-400 hover:text-tesla-red hover:bg-zinc-900/50 py-1.5 px-2 rounded transition-colors flex items-center justify-between group"
          >
            <span>{q}</span>
            <ChevronRight size={12} className="opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
        ))}
      </div>
    </div>
  );
};

export default StrategicQuestions;
