
import React from 'react';
import { MessageSquarePlus } from 'lucide-react';

interface Props {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
}

const SuggestedResponses: React.FC<Props> = ({ suggestions, onSelect }) => {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {suggestions.map((suggestion, i) => (
        <button 
          key={i}
          onClick={() => onSelect(suggestion)}
          className="text-xs text-left text-zinc-300 hover:text-white bg-zinc-900/80 hover:bg-tesla-red/10 border border-zinc-800 hover:border-tesla-red/50 px-3 py-2 rounded-lg transition-all flex items-start gap-2 group/suggestion max-w-md"
        >
          <MessageSquarePlus size={14} className="shrink-0 mt-0.5 text-tesla-red opacity-70 group-hover/suggestion:opacity-100" />
          <span className="line-clamp-2">{suggestion}</span>
        </button>
      ))}
    </div>
  );
};

export default SuggestedResponses;
