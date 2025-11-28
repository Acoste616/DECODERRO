
import React, { useState, useEffect } from 'react';
import { useStore } from '../store';
import {
   Sword,
   Database,
   Star,
   LayoutDashboard,
   Terminal,
   Play,
   Save,
   RefreshCw,
   Search,
   Folder,
   Plus,
   Upload,
   Trash2,
   ChevronRight,
   MapPin,
   MousePointerClick,
   Tag,
   Globe,
   Calendar,
   MessageSquareWarning,
   AlertCircle
} from 'lucide-react';
import { RagNugget, GoldenStandard, Session } from '../types';

const DEFAULT_PROMPT = `You are "JARVIS" - The ULTRA v3.0 Sales Engine for Tesla.
Your goal is to assist a salesperson in closing a deal.
Tone: Confident, Brief, Professional, Strategic.`;

type DojoTab = 'feedback' | 'rag' | 'standards' | 'prompting';

interface NegativeFeedbackItem {
   sessionId: string;
   messageId: string;
   content: string;
   feedbackDetails?: string;
   timestamp: number;
}

const Dojo: React.FC = () => {
   const { knowledgeBase, addNugget, removeNugget, addStandard, removeStandard, sessions } = useStore();
   const [activeTab, setActiveTab] = useState<DojoTab>('standards');

   // RAG State
   const [ragTitle, setRagTitle] = useState('');
   const [ragContent, setRagContent] = useState('');
   const [ragKeywords, setRagKeywords] = useState('');
   const [ragNuggets, setRagNuggets] = useState<any[]>([]);
   const [isEditModalOpen, setIsEditModalOpen] = useState(false);
   const [editingNugget, setEditingNugget] = useState<any>(null);

   // Prompting State
   const [systemPrompt, setSystemPrompt] = useState(DEFAULT_PROMPT);
   const [testInput, setTestInput] = useState("Klient twierdzi, że elektryki palą się częściej niż spalinowe.");
   const [testOutput, setTestOutput] = useState<string | null>(null);
   const [isLoading, setIsLoading] = useState(false);

   // Feedback State
   const [negativeFeedbackItems, setNegativeFeedbackItems] = useState<NegativeFeedbackItem[]>([]);
   const [selectedFeedback, setSelectedFeedback] = useState<NegativeFeedbackItem | null>(null);

   // Golden Standards State
   const [isGoldenModalOpen, setIsGoldenModalOpen] = useState(false);
   const [goldenForm, setGoldenForm] = useState({
      trigger_context: '',
      golden_response: '',
      category: 'price',
      language: 'PL'
   });

   // Load RAG nuggets from backend on mount and tab change
   useEffect(() => {
      if (activeTab === 'rag') {
         fetchRagNuggets();
      }
   }, [activeTab]);

   const fetchRagNuggets = async () => {
      try {
         const response = await fetch('http://localhost:8000/api/admin/rag/list');
         const data = await response.json();
         setRagNuggets(data.nuggets || []);
      } catch (error) {
         console.error('Error fetching RAG nuggets:', error);
      }
   };

   // Load negative feedback from sessions on mount or sessions update
   useEffect(() => {
      const items: NegativeFeedbackItem[] = [];
      Object.values(sessions).forEach((session: Session) => {
         session.messages.forEach(msg => {
            if (msg.feedback === 'negative') {
               items.push({
                  sessionId: session.id,
                  messageId: msg.id,
                  content: msg.content,
                  feedbackDetails: msg.feedbackDetails,
                  timestamp: msg.timestamp
               });
            }
         });
      });
      setNegativeFeedbackItems(items.sort((a, b) => b.timestamp - a.timestamp));
   }, [sessions, activeTab]);

   const handleAddNugget = async () => {
      if (!ragTitle || !ragContent) return;

      const newNugget = {
         title: ragTitle,
         content: ragContent,
         keywords: ragKeywords.split(',').map(k => k.trim()).filter(k => k),
         language: 'PL'
      };

      try {
         const response = await fetch('http://localhost:8000/api/admin/rag/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newNugget)
         });
         if (response.ok) {
            setRagTitle('');
            setRagContent('');
            setRagKeywords('');
            await fetchRagNuggets(); // Refresh list
         }
      } catch (error) {
         console.error('Error adding nugget:', error);
         // Fallback to local store if backend fails
         const localNugget: RagNugget = {
            id: crypto.randomUUID(),
            ...newNugget
         };
         addNugget(localNugget);
         setRagTitle('');
         setRagContent('');
         setRagKeywords('');
      }
   };

   const handleEditNugget = (nugget: any) => {
      setEditingNugget({ ...nugget });
      setIsEditModalOpen(true);
   };

   const handleSaveEdit = async () => {
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
            setIsEditModalOpen(false);
            setEditingNugget(null);
            await fetchRagNuggets(); // Refresh list
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
            await fetchRagNuggets(); // Refresh to show new golden standard in RAG
         }
      } catch (error) {
         console.error('Error adding golden standard:', error);
      }
   };

   const runSimulation = () => {
      setIsLoading(true);
      setTimeout(() => {
         setTestOutput(JSON.stringify({
            content: "Statystyki straży pożarnej pokazują, że samochody spalinowe palą się 60x częściej. Tesla ma zaawansowany system zarządzania temperaturą.",
            confidence: 0.95,
            clientStyle: "Sceptyk"
         }, null, 2));
         setIsLoading(false);
      }, 1500);
   };

   const renderTabContent = () => {
      switch (activeTab) {
         case 'feedback':
            return (
               <div className="flex flex-1 h-full overflow-hidden animate-in fade-in duration-300">
                  {/* Left Column: Feedback Topics */}
                  <div className="w-1/3 border-r border-zinc-800 bg-zinc-950 p-4 flex flex-col overflow-y-auto">
                     <div className="mb-4 p-3 bg-red-900/10 border border-red-800/30 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                           <MessageSquareWarning size={16} className="text-red-500" />
                           <h3 className="text-sm font-bold text-zinc-200">Tablica Feedbacku</h3>
                        </div>
                        <p className="text-xs text-zinc-500">Lista odpowiedzi ocenionych negatywnie przez sprzedawców.</p>
                     </div>

                     <div className="space-y-2">
                        {negativeFeedbackItems.length > 0 ? (
                           negativeFeedbackItems.map((item) => (
                              <button
                                 key={item.messageId}
                                 onClick={() => setSelectedFeedback(item)}
                                 className={`w-full text-left p-3 rounded border flex items-center justify-between group transition-colors ${selectedFeedback?.messageId === item.messageId
                                    ? 'bg-zinc-900 border-red-500/50'
                                    : 'bg-zinc-900/50 border-zinc-800 hover:bg-zinc-900 hover:border-zinc-700'
                                    }`}
                              >
                                 <div className="min-w-0">
                                    <div className="text-xs font-mono text-zinc-500 mb-1">{item.sessionId}</div>
                                    <div className="text-sm font-medium text-zinc-300 group-hover:text-white truncate">
                                       {item.feedbackDetails || "Brak szczegółów"}
                                    </div>
                                    <div className="text-[10px] text-zinc-600 mt-1 truncate max-w-[200px]">
                                       "{item.content.substring(0, 30)}..."
                                    </div>
                                 </div>
                                 <ChevronRight size={14} className="text-zinc-600 group-hover:text-tesla-red shrink-0" />
                              </button>
                           ))
                        ) : (
                           <div className="text-center py-10 text-zinc-600 text-xs italic">
                              Brak negatywnego feedbacku. Dobra robota!
                           </div>
                        )}
                     </div>
                  </div>

                  {/* Right Column: Details & Action */}
                  <div className="w-2/3 bg-black flex flex-col p-0">
                     {selectedFeedback ? (
                        <div className="flex flex-col h-full">
                           <div className="p-6 border-b border-zinc-800 bg-zinc-950/50">
                              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                 <AlertCircle size={18} className="text-red-500" />
                                 Analiza Zgłoszenia
                              </h3>

                              <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 mb-4">
                                 <span className="text-[10px] uppercase tracking-wider text-zinc-500 block mb-2">Odpowiedź AI (Odrzucona)</span>
                                 <p className="text-sm text-zinc-300 leading-relaxed italic">"{selectedFeedback.content}"</p>
                              </div>

                              <div className="bg-red-900/10 rounded-lg p-4 border border-red-900/30">
                                 <span className="text-[10px] uppercase tracking-wider text-red-400 block mb-2">Komentarz Sprzedawcy</span>
                                 <p className="text-sm text-white font-medium">
                                    {selectedFeedback.feedbackDetails || "Sprzedawca nie podał szczegółów, ale oznaczył odpowiedź jako nieprzydatną."}
                                 </p>
                              </div>
                           </div>

                           <div className="flex-1 p-6 flex flex-col items-center justify-center text-center">
                              <div className="max-w-md">
                                 <h4 className="text-zinc-300 font-bold mb-2">Skoryguj Model Mentalny</h4>
                                 <p className="text-xs text-zinc-500 mb-6">
                                    Utwórz nowy "Złoty Standard" na podstawie tego błędu, aby AI nie popełniło go ponownie.
                                 </p>
                                 <button
                                    onClick={() => {
                                       setRagTitle(`Korekta: ${selectedFeedback.feedbackDetails || 'Błąd logiczny'}`);
                                       setRagContent(`UNIKAJ: ${selectedFeedback.content}\n\nZAMIAST TEGO STOSUJ: [Wpisz poprawną argumentację]`);
                                       setActiveTab('rag');
                                    }}
                                    className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-lg text-sm font-bold transition-colors flex items-center gap-2 mx-auto"
                                 >
                                    <Plus size={16} />
                                    Utwórz Regułę Naprawczą (RAG)
                                 </button>
                              </div>
                           </div>
                        </div>
                     ) : (
                        <div className="h-full flex flex-col items-center justify-center text-zinc-500">
                           <div className="bg-zinc-900 p-6 rounded-full mb-4">
                              <MousePointerClick size={32} className="text-zinc-700" />
                           </div>
                           <h3 className="text-zinc-300 font-medium mb-2">Wybierz zgłoszenie z listy</h3>
                           <p className="text-sm max-w-xs text-center">Kliknij na element po lewej stronie, aby zobaczyć dlaczego AI otrzymało negatywną ocenę.</p>
                        </div>
                     )}
                  </div>
               </div>
            );

         case 'rag':
            return (
               <div className="flex flex-1 h-full overflow-hidden animate-in fade-in duration-300">
                  {/* Left Column: Nuggets List */}
                  <div className="w-5/12 border-r border-zinc-800 bg-zinc-950 p-6 overflow-y-auto">
                     <div className="flex justify-between items-center mb-4">
                        <div>
                           <h3 className="text-sm font-bold text-zinc-200">Baza Wiedzy (RAG)</h3>
                           <p className="text-[10px] text-zinc-500">Kontekst dla modelu AI</p>
                        </div>
                        <button className="bg-blue-600 hover:bg-blue-500 text-white text-xs px-3 py-1.5 rounded flex items-center gap-1 transition-colors">
                           <Upload size={12} />
                           Import
                        </button>
                     </div>

                     <div className="space-y-4">
                        {ragNuggets.map(nugget => (
                           <div key={nugget.id} className="bg-zinc-900/50 border border-zinc-800 hover:border-blue-500/30 rounded-lg p-4 transition-all group relative hover:bg-zinc-900">
                              <div className="absolute top-4 right-4 flex gap-2">
                                 <button
                                    onClick={() => handleEditNugget(nugget)}
                                    className="text-zinc-600 hover:text-blue-500 transition-colors"
                                    title="Edit nugget"
                                 >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                                 </button>
                                 <button
                                    onClick={() => removeNugget(nugget.id)}
                                    className="text-zinc-600 hover:text-red-500 transition-colors"
                                 >
                                    <Trash2 size={14} />
                                 </button>
                              </div>
                              <h4 className="text-sm font-bold text-zinc-200 mb-2 pr-6">{nugget.title}</h4>
                              <div className="flex items-center gap-2 mb-2 text-[10px] font-mono text-zinc-500">
                                 <span className="bg-blue-900/20 text-blue-400 px-1.5 rounded uppercase">{nugget.language}</span>
                                 <span className="truncate max-w-[120px]">{nugget.id.substring(0, 8)}...</span>
                              </div>
                              <p className="text-xs text-zinc-400 leading-relaxed line-clamp-3 mb-3">
                                 {nugget.content}
                              </p>
                              <div className="flex flex-wrap gap-1">
                                 {nugget.keywords.map((kw, i) => (
                                    <span key={i} className="text-[9px] bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded">
                                       {kw}
                                    </span>
                                 ))}
                              </div>
                           </div>
                        ))}
                     </div>
                  </div>

                  {/* Right Column: Add Form */}
                  <div className="w-7/12 bg-black p-8 overflow-y-auto">
                     <div className="max-w-2xl mx-auto">
                        <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                           <Plus size={18} />
                           Nowy Nugget Wiedzy
                        </h3>

                        <div className="space-y-6">
                           <div>
                              <label className="block text-xs font-bold text-zinc-400 mb-2 uppercase tracking-wider">Tytuł *</label>
                              <input
                                 type="text"
                                 value={ragTitle}
                                 onChange={(e) => setRagTitle(e.target.value)}
                                 placeholder="np. Model 3 Long Range - zasięg WLTP"
                                 className="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-3 text-sm text-white focus:border-blue-500 focus:outline-none transition-colors"
                              />
                           </div>

                           <div>
                              <label className="block text-xs font-bold text-zinc-400 mb-2 uppercase tracking-wider">Treść merytoryczna *</label>
                              <textarea
                                 value={ragContent}
                                 onChange={(e) => setRagContent(e.target.value)}
                                 placeholder="Wprowadź pełną treść faktu, specyfikacji lub procedury..."
                                 className="w-full h-48 bg-zinc-900 border border-zinc-800 rounded-lg p-3 text-sm text-white focus:border-blue-500 focus:outline-none transition-colors resize-none leading-relaxed"
                              />
                           </div>

                           <div>
                              <label className="block text-xs font-bold text-zinc-400 mb-2 uppercase tracking-wider">Słowa Kluczowe (Tagi)</label>
                              <input
                                 type="text"
                                 value={ragKeywords}
                                 onChange={(e) => setRagKeywords(e.target.value)}
                                 placeholder="model 3, zasięg, wltp, zima"
                                 className="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-3 text-sm text-white focus:border-blue-500 focus:outline-none transition-colors"
                              />
                           </div>

                           <div className="pt-4">
                              <button
                                 onClick={handleAddNugget}
                                 disabled={!ragTitle || !ragContent}
                                 className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-3 rounded-lg transition-all shadow-lg shadow-blue-900/20 border border-blue-500"
                              >
                                 Dodaj do Bazy Wiedzy
                              </button>
                           </div>
                        </div>
                     </div>
                  </div>
               </div>
            );

         case 'standards':
            return (
               <div className="p-6 h-full overflow-y-auto bg-zinc-50/5 animate-in fade-in duration-300">
                  {/* Top Bar */}
                  <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6 mb-6 flex flex-col md:flex-row items-center justify-between gap-4">
                     <div>
                        <div className="flex items-center gap-2 text-amber-400 font-bold text-lg mb-1">
                           <Star size={20} className="fill-amber-400" />
                           <h2>Złote Standardy Odpowiedzi</h2>
                        </div>
                        <p className="text-xs text-zinc-400">Przeglądaj i analizuj wzorcowe odpowiedzi zaimportowane do systemu</p>
                     </div>
                     <button
                        onClick={() => setIsGoldenModalOpen(true)}
                        className="bg-amber-600 hover:bg-amber-500 text-black font-bold px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition-colors"
                     >
                        <Plus size={16} />
                        Dodaj Złoty Standard
                     </button>
                     <div className="flex-1 w-full md:max-w-xl flex gap-3">
                        <div className="relative flex-1">
                           <Search size={16} className="absolute left-3 top-3 text-zinc-500" />
                           <input
                              type="text"
                              placeholder="Szukaj w kontekście, odpowiedziach..."
                              className="w-full pl-10 pr-4 py-2.5 bg-black border border-zinc-800 rounded-lg text-sm text-white focus:border-amber-500 focus:outline-none"
                           />
                        </div>
                        <button className="bg-black border border-zinc-800 text-zinc-300 px-4 py-2 rounded-lg text-sm flex items-center gap-2 hover:border-zinc-600 transition-colors whitespace-nowrap">
                           <Folder size={16} className="text-amber-500" />
                           Wszystkie kategorie
                        </button>
                     </div>
                     <div className="text-right hidden lg:block">
                        <div className="text-2xl font-bold text-blue-400">{knowledgeBase.standards.length}</div>
                        <div className="text-[10px] text-zinc-500 uppercase tracking-wider">Total Standards</div>
                     </div>
                  </div>

                  {/* Standards List */}
                  <div className="space-y-6 max-w-5xl mx-auto">
                     {knowledgeBase.standards.map(std => (
                        <div key={std.id} className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden shadow-sm hover:border-zinc-600 transition-all group">
                           {/* Header */}
                           <div className="px-6 py-3 border-b border-zinc-800 bg-zinc-950/50 flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                 <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded flex items-center gap-1 ${std.category === 'financial' ? 'bg-blue-900/20 text-blue-400' :
                                    std.category === 'competitive' ? 'bg-purple-900/20 text-purple-400' :
                                       'bg-zinc-800 text-zinc-400'
                                    }`}>
                                    <Folder size={10} />
                                    {std.category}
                                 </span>
                                 <span className="text-[10px] font-mono text-zinc-600">ID: {std.id}</span>
                              </div>
                              <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                                 <button
                                    onClick={() => removeStandard(std.id)}
                                    className="text-zinc-500 hover:text-white p-1"
                                 >
                                    <Trash2 size={14} />
                                 </button>
                              </div>
                           </div>

                           <div className="p-6 space-y-4">
                              {/* Context */}
                              <div>
                                 <div className="flex items-center gap-2 text-xs font-bold text-red-400 uppercase tracking-wider mb-1">
                                    <MapPin size={12} className="fill-red-400" />
                                    Kontekst wyzwalacza:
                                 </div>
                                 <p className="text-base font-medium text-zinc-100">{std.context}</p>
                              </div>

                              {/* Response */}
                              <div className="bg-amber-950/10 border border-amber-900/20 rounded-lg p-4 relative">
                                 <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider mb-2">
                                    <Star size={12} className="fill-amber-400" />
                                    Wzorcowa odpowiedź:
                                 </div>
                                 <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">{std.response}</p>
                              </div>
                           </div>

                           {/* Footer */}
                           <div className="px-6 py-3 bg-zinc-950 border-t border-zinc-800 flex items-center justify-between">
                              <div className="flex gap-2">
                                 {std.tags.map(tag => (
                                    <span key={tag} className="text-[10px] bg-blue-500/10 text-blue-300 px-2 py-0.5 rounded-full flex items-center gap-1">
                                       <Tag size={8} /> {tag}
                                    </span>
                                 ))}
                              </div>
                              <div className="flex items-center gap-4 text-[10px] text-zinc-500 font-mono">
                                 <div className="flex items-center gap-1">
                                    <Globe size={10} /> {std.language}
                                 </div>
                                 <div className="flex items-center gap-1">
                                    <Calendar size={10} /> {std.date}
                                 </div>
                              </div>
                           </div>
                        </div>
                     ))}
                  </div>
               </div>
            );

         case 'prompting':
            return (
               <div className="flex flex-1 h-full overflow-hidden animate-in fade-in duration-300">
                  {/* Left Panel: Config */}
                  <div className="w-1/2 border-r border-zinc-800 p-6 flex flex-col bg-zinc-950">
                     <h2 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Terminal size={14} />
                        System Prompt Configuration
                     </h2>
                     <textarea
                        className="flex-1 bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 text-sm font-mono text-green-400 focus:outline-none focus:border-green-500 resize-none leading-relaxed"
                        value={systemPrompt}
                        onChange={(e) => setSystemPrompt(e.target.value)}
                     />
                  </div>

                  {/* Right Panel: Simulation */}
                  <div className="w-1/2 p-6 flex flex-col bg-black">
                     <h2 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Play size={14} />
                        Simulation Output
                     </h2>

                     <div className="mb-4">
                        <label className="block text-xs text-zinc-500 mb-2">Test Input (User Role)</label>
                        <input
                           type="text"
                           value={testInput}
                           onChange={(e) => setTestInput(e.target.value)}
                           className="w-full bg-zinc-900 border border-zinc-800 text-white px-3 py-2 rounded text-sm focus:border-green-500 focus:outline-none"
                        />
                     </div>

                     <button
                        onClick={runSimulation}
                        disabled={isLoading}
                        className="bg-zinc-800 hover:bg-zinc-700 text-white py-2 rounded text-xs font-bold tracking-wide mb-6 border border-zinc-700 hover:border-zinc-500 transition-all"
                     >
                        {isLoading ? "PROCESSING..." : "RUN SIMULATION"}
                     </button>

                     <div className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg p-4 relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-green-600 to-transparent"></div>
                        {testOutput ? (
                           <pre className="text-xs font-mono text-zinc-300 whitespace-pre-wrap">{testOutput}</pre>
                        ) : (
                           <div className="h-full flex items-center justify-center text-zinc-700 text-xs font-mono italic">
                              WAITING FOR OUTPUT...
                           </div>
                        )}
                     </div>
                  </div>
               </div>
            );
      }
   };

   return (
      <div className="flex flex-col h-screen bg-black">
         {/* Edit Modal */}
         {isEditModalOpen && editingNugget && (
            <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
               <div className="bg-zinc-900 border border-zinc-700 rounded-xl max-w-2xl w-full p-6">
                  <h2 className="text-lg font-bold text-white mb-4">Edit RAG Nugget</h2>
                  <div className="space-y-4">
                     <div>
                        <label className="block text-xs font-bold text-zinc-400 mb-2">TYTUŁ</label>
                        <input
                           type="text"
                           value={editingNugget.title}
                           onChange={(e) => setEditingNugget({ ...editingNugget, title: e.target.value })}
                           className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-white text-sm"
                        />
                     </div>
                     <div>
                        <label className="block text-xs font-bold text-zinc-400 mb-2">TREŚĆ</label>
                        <textarea
                           value={editingNugget.content}
                           onChange={(e) => setEditingNugget({ ...editingNugget, content: e.target.value })}
                           className="w-full h-32 bg-zinc-800 border border-zinc-700 rounded p-2 text-white text-sm resize-none"
                        />
                     </div>
                     <div>
                        <label className="block text-xs font-bold text-zinc-400 mb-2">KEYWORDS (comma separated)</label>
                        <input
                           type="text"
                           value={Array.isArray(editingNugget.keywords) ? editingNugget.keywords.join(', ') : editingNugget.keywords}
                           onChange={(e) => setEditingNugget({ ...editingNugget, keywords: e.target.value.split(',').map(k => k.trim()) })}
                           className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-white text-sm"
                        />
                     </div>
                     <div className="flex gap-3 pt-4">
                        <button onClick={handleSaveEdit} className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 rounded">
                           Save Changes
                        </button>
                        <button onClick={() => setIsEditModalOpen(false)} className="px-6 bg-zinc-800 hover:bg-zinc-700 text-white py-2 rounded">
                           Cancel
                        </button>
                     </div>
                  </div>
               </div>
            </div>
         )}

         {/* Golden Standards Modal */}
         {isGoldenModalOpen && (
            <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
               <div className="bg-zinc-900 border border-zinc-700 rounded-xl max-w-2xl w-full p-6">
                  <h2 className="text-lg font-bold text-amber-400 mb-4 flex items-center gap-2">
                     <Star size={20} className="fill-amber-400" />
                     Dodaj Złoty Standard
                  </h2>
                  <div className="space-y-4">
                     <div>
                        <label className="block text-xs font-bold text-zinc-400 mb-2">KONTEKST WYZWALACZA (pytanie klienta)</label>
                        <input
                           type="text"
                           placeholder="np. Klient porównuje Teslę z BMW i4"
                           value={goldenForm.trigger_context}
                           onChange={(e) => setGoldenForm({ ...goldenForm, trigger_context: e.target.value })}
                           className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-white text-sm"
                        />
                     </div>
                     <div>
                        <label className="block text-xs font-bold text-zinc-400 mb-2">WZORCOWA ODPOWIEDŹ</label>
                        <textarea
                           placeholder="Wprowadź idealną odpowiedź AI na ten kontekst..."
                           value={goldenForm.golden_response}
                           onChange={(e) => setGoldenForm({ ...goldenForm, golden_response: e.target.value })}
                           className="w-full h-32 bg-zinc-800 border border-zinc-700 rounded p-2 text-white text-sm resize-none"
                        />
                     </div>
                     <div>
                        <label className="block text-xs font-bold text-zinc-400 mb-2">KATEGORIA</label>
                        <select
                           value={goldenForm.category}
                           onChange={(e) => setGoldenForm({ ...goldenForm, category: e.target.value })}
                           className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-white text-sm"
                        >
                           <option value="price">Price</option>
                           <option value="objections">Objections</option>
                           <option value="features">Features</option>
                           <option value="closing">Closing</option>
                        </select>
                     </div>
                     <div className="flex gap-3 pt-4">
                        <button onClick={handleAddGoldenStandard} className="flex-1 bg-amber-600 hover:bg-amber-500 text-black font-bold py-2 rounded">
                           Dodaj do Systemu
                        </button>
                        <button onClick={() => setIsGoldenModalOpen(false)} className="px-6 bg-zinc-800 hover:bg-zinc-700 text-white py-2 rounded">
                           Anuluj
                        </button>
                     </div>
                  </div>
               </div>
            </div>
         )}

         {/* Top Header */}
         <div className="h-16 border-b border-zinc-800 flex items-center px-6 bg-zinc-900/80 justify-between shrink-0 z-10">
            <div className="flex items-center gap-3">
               <Sword className="text-tesla-red" size={20} />
               <div>
                  <h1 className="text-white font-bold text-sm tracking-wide">AI DOJO LAB</h1>
                  <p className="text-zinc-500 text-[10px] font-mono">TRAINING & KNOWLEDGE CENTER</p>
               </div>
            </div>
            <div className="flex gap-2">
               {activeTab === 'prompting' && (
                  <button className="bg-green-600 hover:bg-green-500 text-black font-bold px-4 py-1.5 rounded text-xs flex items-center gap-2 transition-colors">
                     <Save size={12} /> Save Config
                  </button>
               )}
            </div>
         </div>

         {/* Tab Navigation */}
         <div className="bg-zinc-950 border-b border-zinc-800 px-6 flex gap-8 overflow-x-auto">
            <button
               onClick={() => setActiveTab('standards')}
               className={`py-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'standards' ? 'border-amber-500 text-amber-400' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}
            >
               <Star size={14} />
               Złote Standardy
            </button>
            <button
               onClick={() => setActiveTab('rag')}
               className={`py-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'rag' ? 'border-blue-500 text-blue-400' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}
            >
               <Database size={14} />
               Baza Wiedzy (RAG)
            </button>
            <button
               onClick={() => setActiveTab('feedback')}
               className={`py-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'feedback' ? 'border-red-500 text-red-400' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}
            >
               <LayoutDashboard size={14} />
               Tablica Feedbacku
            </button>
            <button
               onClick={() => setActiveTab('prompting')}
               className={`py-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'prompting' ? 'border-green-500 text-green-400' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}
            >
               <Terminal size={14} />
               Prompt Engineering
            </button>
         </div>

         {/* Main Content Area */}
         <div className="flex-1 overflow-hidden">
            {renderTabContent()}
         </div>
      </div>
   );
};

export default Dojo;
