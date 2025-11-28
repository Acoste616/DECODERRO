
import React from 'react';
import { Bot, Key, ShieldCheck } from 'lucide-react';

interface Props {
  confidence: number;
  confidenceReason?: string;
  clientStyle?: string;
}

const JarvisMetadata: React.FC<Props> = ({ confidence, confidenceReason, clientStyle }) => {
  return (
    <div className="bg-blue-950/20 border border-blue-500/20 rounded-lg p-3 text-xs relative overflow-hidden">
      <div className="absolute top-0 left-0 w-1 h-full bg-blue-500/30"></div>
      
      <div className="flex flex-col sm:flex-row sm:items-start gap-4 pl-2">
        
        {/* Confidence Section */}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
             <div className="text-blue-400 font-bold uppercase tracking-wider text-[10px] flex items-center gap-1">
                <ShieldCheck size={12} />
                <span>Pewność AI</span>
             </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`font-mono font-bold text-sm ${
              confidence > 0.8 ? 'text-green-400' : confidence > 0.5 ? 'text-yellow-400' : 'text-red-400'
            }`}>
              {(confidence * 100).toFixed(0)}%
            </span>
            {confidenceReason && (
              <span className="text-zinc-400 leading-tight text-[10px]">
                {confidenceReason}
              </span>
            )}
          </div>
        </div>

        {/* Style Section */}
        {clientStyle && (
          <div className="min-w-[140px] shrink-0 pt-1 sm:pt-0 border-t sm:border-t-0 sm:border-l border-blue-500/20 sm:pl-4 mt-2 sm:mt-0">
             <div className="text-zinc-500 text-[10px] mb-1 uppercase tracking-wider">Styl klienta</div>
             <div className="flex items-center gap-1.5 text-blue-200 font-medium">
                <Key size={12} className="text-blue-400" />
                <span className="tracking-wide">{clientStyle}</span>
             </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default JarvisMetadata;
