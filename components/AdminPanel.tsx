
import React, { useState, useEffect } from 'react';
import {
    Server, Shield, Activity, Cpu, ArrowLeft, Database, Edit2, Plus, Save, X
} from 'lucide-react';
import { useStore } from '../store';
import { Session } from '../types';

interface RAGNugget {
    id: string;
    title: string;
    content: string;
    keywords: string[];
    language: string;
}

const AdminPanel: React.FC = () => {
    const { setView, systemLogs, sessions } = useStore();
    const [ragNuggets, setRagNuggets] = useState<RAGNugget[]>([]);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isGoldenModalOpen, setIsGoldenModalOpen] = useState(false);
    const [editingNugget, setEditingNugget] = useState<RAGNugget | null>(null);
    const [goldenForm, setGoldenForm] = useState({
        trigger_context: '', golden_response: '', category: 'price', language: 'PL'
    });

    const sessionList = Object.values(sessions) as Session[];
    const closedSessions = sessionList.filter(s => s.status === 'closed');
    const wonSessions = closedSessions.filter(s => s.outcome === 'sale');
    const winRate = closedSessions.length > 0 ? Math.round((wonSessions.length / closedSessions.length) * 100) : 0;

    useEffect(() => {
        fetch('http://localhost:8000/api/admin/rag/list')
            .then(res => res.json())
            .then(data => setRagNuggets(data.nuggets || []))
            .catch(err => console.error('Failed to load RAG nuggets:', err));
    }, []);

    const handleEditNugget = (nugget: RAGNugget) => {
        setEditingNugget({ ...nugget });
        setIsEditModalOpen(true);
    };

    const handleSaveNugget = async () => {
        if (!editingNugget) return;
        try {
            const response = await fetch(`http://localhost:8000/api/admin/rag/edit/${editingNugget.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: editingNugget.title,
                    content: editingNugget.content,
                    keywords: editingNugget.keywords,
                    language: editingNugget.language
                })
            });
            if (response.ok) {
                setRagNuggets(prev => prev.map(n => n.id === editingNugget.id ? editingNugget : n));
                setIsEditModalOpen(false);
                setEditingNugget(null);
            }
        } catch (error) {
            console.error('Error saving nugget:', error);
        }
    };

    const handleAddGoldenStandard = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/admin/golden-standards/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(goldenForm)
            });
            if (response.ok) {
                setIsGoldenModalOpen(false);
                setGoldenForm({ trigger_context: '', golden_response: '', category: 'price', language: 'PL' });
                const data = await fetch('http://localhost:8000/api/admin/rag/list').then(r => r.json());
                setRagNuggets(data.nuggets || []);
            }
        } catch (error) {
            console.error('Error adding golden standard:', error);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-black text-zinc-300 p-8 overflow-y-auto">
            <div className="flex items-center gap-4 mb-8">
                <button onClick={() => setView('dashboard')} className="hover:text-white transition-colors">
                    <ArrowLeft size={20} />
                </button>
                <h1 className="text-2xl font-bold text-white">System Administration</h1>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-4 text-white font-bold">
                        <Server size={20} className="text-green-500" />
                        <h2>Global Operations</h2>
                    </div>
                    <div className="space-y-4">
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-500">Total Sessions</span>
                            <span className="font-mono text-white">{sessionList.length}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-500">Active Now</span>
                            <span className="font-mono text-green-400">{sessionList.filter(s => s.status === 'active').length}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-500">Win Rate (Closed)</span>
                            <span className="font-mono text-blue-400">{winRate}%</span>
                        </div>
                    </div>
                </div>

                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-4 text-white font-bold">
                        <Cpu size={20} className="text-blue-500" />
                        <h2>LLM Connection</h2>
                    </div>
                    <div className="space-y-4">
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-500">Provider</span>
                            <span className="font-mono">Google Gemini</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-500">Model</span>
                            <span className="font-mono">gemini-2.5-flash</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-500">Status</span>
                            <span className="font-mono text-green-400 flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                                Operational
                            </span>
                        </div>
                    </div>
                </div>

                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-4 text-white font-bold">
                        <Shield size={20} className="text-tesla-red" />
                        <h2>Security & Privacy</h2>
                    </div>
                    <div className="space-y-4">
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-500">PII Stripping</span>
                            <span className="font-mono text-green-400">ACTIVE</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-500">Encryption</span>
                            <span className="font-mono text-green-400">AES-256</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-500">Session Audit</span>
                            <span className="font-mono">Enabled</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* RAG Knowledge Base */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-8">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3 text-white font-bold">
                        <Database size={20} className="text-blue-500" />
                        <h2>Baza Wiedzy (RAG)</h2>
                    </div>
                    <button onClick={() => setIsGoldenModalOpen(true)} className="flex items-center gap-2 bg-tesla-red hover:bg-tesla-red/80 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium">
                        <Plus size={16} />Dodaj Złoty Standard
                    </button>
                </div>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                    {ragNuggets.map((nugget) => (
                        <div key={nugget.id} className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 hover:border-zinc-700 transition-colors">
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-2">
                                        <h3 className="text-white font-medium text-sm truncate">{nugget.title}</h3>
                                        <span className="text-[10px] text-zinc-500 font-mono bg-zinc-800 px-2 py-0.5 rounded">{nugget.id.slice(0, 8)}...</span>
                                    </div>
                                    <p className="text-zinc-400 text-xs line-clamp-2 mb-2">{nugget.content}</p>
                                    <div className="flex flex-wrap gap-1">
                                        {nugget.keywords.slice(0, 4).map((kw, i) => (
                                            <span key={i} className="text-[10px] bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded-full">{kw}</span>
                                        ))}
                                    </div>
                                </div>
                                <button onClick={() => handleEditNugget(nugget)} className="p-2 hover:bg-zinc-800 rounded-lg transition-colors text-blue-400 hover:text-blue-300" title="Edit">
                                    <Edit2 size={16} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
                <div className="mt-4 text-xs text-zinc-600 text-center">Total Nuggets: {ragNuggets.length}</div>
            </div>

            {/* Edit Modal */}
            {isEditModalOpen && editingNugget && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-white">Edytuj Nugget</h2>
                            <button onClick={() => setIsEditModalOpen(false)} className="text-zinc-400 hover:text-white"><X size={20} /></button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-zinc-400 mb-2">Title</label>
                                <input type="text" value={editingNugget.title} onChange={(e) => setEditingNugget({ ...editingNugget, title: e.target.value })} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-zinc-400 mb-2">Content</label>
                                <textarea value={editingNugget.content} onChange={(e) => setEditingNugget({ ...editingNugget, content: e.target.value })} rows={6} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500 resize-none" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-zinc-400 mb-2">Keywords (comma-separated)</label>
                                <input type="text" value={editingNugget.keywords.join(', ')} onChange={(e) => setEditingNugget({ ...editingNugget, keywords: e.target.value.split(',').map(k => k.trim()) })} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-zinc-400 mb-2">Language</label>
                                <select value={editingNugget.language} onChange={(e) => setEditingNugget({ ...editingNugget, language: e.target.value })} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500">
                                    <option value="PL">Polish (PL)</option>
                                    <option value="EN">English (EN)</option>
                                </select>
                            </div>
                        </div>
                        <div className="flex gap-3 mt-6">
                            <button onClick={handleSaveNugget} className="flex-1 flex items-center justify-center gap-2 bg-tesla-red hover:bg-tesla-red/80 text-white px-4 py-3 rounded-lg transition-colors font-medium">
                                <Save size={18} />Save Changes
                            </button>
                            <button onClick={() => setIsEditModalOpen(false)} className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg transition-colors">Cancel</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Golden Standard Modal */}
            {isGoldenModalOpen && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 w-full max-w-2xl">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-white">Dodaj Złoty Standard</h2>
                            <button onClick={() => setIsGoldenModalOpen(false)} className="text-zinc-400 hover:text-white"><X size={20} /></button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-zinc-400 mb-2">Trigger Context (pytanie klienta)</label>
                                <input type="text" value={goldenForm.trigger_context} onChange={(e) => setGoldenForm({ ...goldenForm, trigger_context: e.target.value })} placeholder="np. Klient pyta o cenę Model 3 Long Range" className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white placeholder-zinc-600 focus:outline-none focus:border-blue-500" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-zinc-400 mb-2">Golden Response (idealna odpowiedź)</label>
                                <textarea value={goldenForm.golden_response} onChange={(e) => setGoldenForm({ ...goldenForm, golden_response: e.target.value })} placeholder="Model 3 Long Range w Polsce kosztuje 229,990 PLN katalogowo..." rows={5} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white placeholder-zinc-600 focus:outline-none focus:border-blue-500 resize-none" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-zinc-400 mb-2">Category</label>
                                    <select value={goldenForm.category} onChange={(e) => setGoldenForm({ ...goldenForm, category: e.target.value })} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500">
                                        <option value="price">Price</option>
                                        <option value="objections">Objections</option>
                                        <option value="features">Features</option>
                                        <option value="closing">Closing</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-zinc-400 mb-2">Language</label>
                                    <select value={goldenForm.language} onChange={(e) => setGoldenForm({ ...goldenForm, language: e.target.value })} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500">
                                        <option value="PL">Polish (PL)</option>
                                        <option value="EN">English (EN)</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div className="flex gap-3 mt-6">
                            <button onClick={handleAddGoldenStandard} className="flex-1 flex items-center justify-center gap-2 bg-tesla-red hover:bg-tesla-red/80 text-white px-4 py-3 rounded-lg transition-colors font-medium">
                                <Plus size={18} />Dodaj Standard
                            </button>
                            <button onClick={() => setIsGoldenModalOpen(false)} className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg transition-colors">Cancel</button>
                        </div>
                    </div>
                </div>
            )}

            {/* System Logs */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 flex-1 min-h-[300px] flex flex-col">
                <div className="flex items-center gap-3 mb-4 text-white font-bold">
                    <Activity size={20} className="text-zinc-500" />
                    <h2>System Logs</h2>
                </div>
                <div className="font-mono text-xs space-y-1 h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-700">
                    {systemLogs.length > 0 ? systemLogs.map((log) => (
                        <div key={log.id} className="flex gap-4 hover:bg-zinc-800/50 p-1 rounded">
                            <span className="text-zinc-500 w-20 shrink-0">{new Date(log.timestamp).toLocaleTimeString()}</span>
                            <span className={`w-16 shrink-0 font-bold ${log.type === 'INFO' ? 'text-blue-500' : log.type === 'WARN' ? 'text-amber-500' : log.type === 'ERROR' ? 'text-red-500' : 'text-green-500'}`}>[{log.type}]</span>
                            <span className="text-zinc-300">{log.message}</span>
                        </div>
                    )) : (
                        <div className="text-zinc-600 italic p-4">Waiting for system events...</div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AdminPanel;
