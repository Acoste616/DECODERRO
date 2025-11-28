
import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  question: string;
  onClose: () => void;
  onSubmit: (answer: string) => void;
}

const StrategicModal: React.FC<Props> = ({ isOpen, question, onClose, onSubmit }) => {
  const [answer, setAnswer] = useState('');

  // Reset answer when modal opens with a new question
  useEffect(() => {
    if (isOpen) {
      setAnswer('');
    }
  }, [isOpen, question]);

  if (!isOpen) return null;

  const handleSubmit = () => {
    if (!answer.trim()) return;
    onSubmit(answer);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-zinc-900 border border-zinc-800 w-full max-w-lg rounded-xl shadow-2xl p-6 relative animate-in zoom-in-95 duration-200">
        <button 
            onClick={onClose}
            className="absolute top-4 right-4 text-zinc-500 hover:text-white transition-colors"
        >
            <X size={20} />
        </button>
        
        <div className="mb-4">
            <h3 className="text-purple-400 font-bold uppercase tracking-wider text-xs mb-1">Tactical Action: Deep Probe</h3>
            <p className="text-lg text-zinc-100 font-medium leading-relaxed">{question}</p>
        </div>

        <div className="space-y-4">
            <div>
                <label className="block text-xs text-zinc-400 mb-2">Client Response (Outcome):</label>
                <textarea
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder="Record what the client said..."
                    className="w-full h-32 bg-black border border-zinc-700 rounded-lg p-3 text-sm text-zinc-200 focus:border-purple-500 focus:outline-none resize-none"
                    autoFocus
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSubmit();
                        }
                    }}
                />
            </div>
            <div className="flex justify-end gap-3">
                <button 
                    onClick={onClose}
                    className="px-4 py-2 text-sm text-zinc-400 hover:text-white transition-colors"
                >
                    Cancel
                </button>
                <button 
                    onClick={handleSubmit}
                    disabled={!answer.trim()}
                    className="px-6 py-2 bg-purple-600 text-white text-sm font-medium rounded hover:bg-purple-500 disabled:opacity-50 transition-colors"
                >
                    Continue Analysis
                </button>
            </div>
        </div>
      </div>
    </div>
  );
};

export default StrategicModal;
