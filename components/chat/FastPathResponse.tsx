
import React from 'react';
import { Zap, Copy } from 'lucide-react';

interface Props {
  phrases: string[];
  onSelect: (phrase: string) => void;
}

const FastPathResponse: React.FC<Props> = ({ phrases, onSelect }) => {
  if (!phrases || phrases.length === 0) return null;

  return (
    <div className="bg-amber-950/20 border border-amber-500/30 rounded-lg p-3 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-amber-400 to-amber-600"></div>
      
      {/* Header */}
      <div className="flex items-center justify-between mb-3 pl-2">
        <div className="flex items-center gap-2 text-amber-400 font-bold uppercase tracking-wider text-[10px]">
          <Zap size={12} className="fill-amber-400" />
          <span>Fast Path: Golden Phrases</span>
        </div>
        <span className="text-[9px] text-amber-400/40 font-mono">CLICK TO INSERT</span>
      </div>

      {/* Phrases Grid */}
      <div className="space-y-2 pl-2">
        {phrases.map((phrase, i) => (
          <button
            key={i}
            onClick={() => onSelect(phrase)}
            className="w-full text-left bg-amber-500/5 hover:bg-amber-500/10 border border-amber-500/20 hover:border-amber-500/50 active:bg-amber-500/20 text-amber-100/90 p-2.5 rounded transition-all group flex items-start gap-3"
          >
            <span className="text-amber-500/50 font-serif italic text-lg leading-none">"</span>
            <span className="text-xs leading-relaxed flex-1 font-medium">{phrase}</span>
            <Copy size={12} className="text-amber-500 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 mt-0.5" />
          </button>
        ))}
      </div>
    </div>
  );
};

export default FastPathResponse;
