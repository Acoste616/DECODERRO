import React, { useState } from 'react';
import { AlertTriangle, CheckSquare, Square } from 'lucide-react';

interface ContextNeedsProps {
  needs?: string[];
}

const ContextNeeds: React.FC<ContextNeedsProps> = ({ needs = [] }) => {
  // Lokalny stan do odhaczania zadań
  const [completed, setCompleted] = useState<Set<number>>(new Set());

  const toggleTask = (index: number) => {
    const newCompleted = new Set(completed);
    if (newCompleted.has(index)) {
      newCompleted.delete(index);
    } else {
      newCompleted.add(index);
    }
    setCompleted(newCompleted);
  };

  if (!needs || needs.length === 0) return null;

  return (
    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-4">
      <div className="flex items-center gap-2 mb-3 text-yellow-500">
        <AlertTriangle className="w-5 h-5" />
        <h3 className="font-semibold uppercase text-sm tracking-wider">
          Taktyczne Następne Kroki
        </h3>
      </div>

      <ul className="space-y-2">
        {needs.map((need, i) => {
          const isDone = completed.has(i);
          return (
            <li
              key={i}
              onClick={() => toggleTask(i)}
              className={`
                flex items-start gap-3 p-2 rounded cursor-pointer transition-all
                ${isDone ? 'opacity-50 line-through bg-yellow-500/5' : 'hover:bg-yellow-500/10'}
              `}
            >
              <div className="mt-1 min-w-[16px]">
                {isDone ? (
                  <CheckSquare className="w-4 h-4 text-yellow-500" />
                ) : (
                  <Square className="w-4 h-4 text-yellow-600/50" />
                )}
              </div>
              <span className="text-sm text-yellow-100/90 leading-relaxed">
                {need}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default ContextNeeds;