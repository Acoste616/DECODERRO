import React from 'react';
import { Lightbulb, ArrowRight, BrainCircuit } from 'lucide-react';

interface SuggestedActionsProps {
  actions?: string[];
  onSelect?: (action: string) => void;
}

const SuggestedActions: React.FC<SuggestedActionsProps> = ({ actions = [], onSelect }) => {
  if (!actions || actions.length === 0) return null;

  return (
    <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center justify-between mb-3 text-purple-400">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-5 h-5" />
          <h3 className="font-semibold uppercase text-sm tracking-wider">
            Luka Wiedzy AI (Uzupełnij)
          </h3>
        </div>
        <span className="text-xs px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">
          Wymagany Input
        </span>
      </div>

      <div className="space-y-2">
        {actions.map((action, i) => (
          <button
            key={i}
            onClick={() => onSelect?.(action)}
            className="w-full text-left group flex items-center justify-between p-3 rounded-md bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/10 hover:border-purple-500/40 transition-all duration-200"
          >
            <div className="flex items-start gap-3">
              <Lightbulb className="w-4 h-4 text-purple-400 mt-0.5 shrink-0" />
              <span className="text-sm text-purple-100 font-medium leading-relaxed">
                {action}
              </span>
            </div>
            <ArrowRight className="w-4 h-4 text-purple-500 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
          </button>
        ))}
      </div>

      <div className="mt-3 text-center">
        <p className="text-[10px] text-purple-400/60 uppercase tracking-widest">
          Kliknij pytanie, aby odpowiedzieć
        </p>
      </div>
    </div>
  );
};

export default SuggestedActions;