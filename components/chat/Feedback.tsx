
import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Send } from 'lucide-react';

interface Props {
  feedback: 'positive' | 'negative' | null;
  feedbackDetails?: string;
  onFeedback: (type: 'positive' | 'negative', details?: string) => void;
}

const Feedback: React.FC<Props> = ({ feedback, feedbackDetails, onFeedback }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [detailsText, setDetailsText] = useState(feedbackDetails || '');

  const handleNegativeClick = () => {
    if (feedback === 'negative') {
      setShowDetails(!showDetails);
    } else {
      onFeedback('negative');
      setShowDetails(true);
    }
  };

  const handleSubmitDetails = () => {
    onFeedback('negative', detailsText);
    setShowDetails(false);
  };

  return (
    <div className="flex items-center gap-2">
      {/* Feedback Buttons Group */}
      <div className="flex items-center bg-zinc-900/50 rounded-full border border-zinc-800 p-0.5">
        <button 
          onClick={() => {
              onFeedback('positive');
              setShowDetails(false);
          }}
          className={`p-1.5 rounded-full transition-colors ${
            feedback === 'positive' ? 'text-green-400 bg-green-500/10' : 'text-zinc-600 hover:text-zinc-300 hover:bg-zinc-800'
          }`}
          title="Dobra odpowiedź"
        >
          <ThumbsUp size={12} />
        </button>
        <div className="w-px h-3 bg-zinc-800 mx-0.5" />
        <button 
          onClick={handleNegativeClick}
          className={`p-1.5 rounded-full transition-colors ${
            feedback === 'negative' ? 'text-red-400 bg-red-500/10' : 'text-zinc-600 hover:text-zinc-300 hover:bg-zinc-800'
          }`}
          title="Zła odpowiedź"
        >
          <ThumbsDown size={12} />
        </button>
      </div>

      {/* Quick Input for Negative Feedback */}
      {showDetails && (
        <div className="absolute bottom-14 right-4 z-10 w-64 animate-in slide-in-from-bottom-2 fade-in duration-200">
            <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-2 shadow-xl flex gap-2">
                <input 
                    type="text" 
                    value={detailsText}
                    onChange={(e) => setDetailsText(e.target.value)}
                    placeholder="Co poprawić?"
                    className="bg-black border border-zinc-800 rounded px-2 py-1 text-xs text-zinc-200 focus:border-tesla-red focus:outline-none flex-1 min-w-0"
                    autoFocus
                />
                <button 
                    onClick={handleSubmitDetails}
                    className="bg-zinc-800 hover:bg-tesla-red text-zinc-300 hover:text-white rounded px-2 py-1 transition-colors"
                >
                    <Send size={12} />
                </button>
            </div>
        </div>
      )}
    </div>
  );
};

export default Feedback;
