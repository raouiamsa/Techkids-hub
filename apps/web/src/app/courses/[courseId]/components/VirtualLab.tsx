import React, { useState, useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { io, Socket } from 'socket.io-client';
import { Play, AlertCircle, Cpu, Zap, Settings, RefreshCw, Layers } from 'lucide-react';
import { Button } from '@org/ui-components';

interface VirtualLabProps {
  exerciseId: string;
  studentId: string;
  exerciseType?: 'CODE_CHALLENGE' | 'CIRCUIT_BUILD' | 'QUIZ';
  language?: string;
  starterCode: string;
  instructions: string;
  value: string;
  onChange: (value: string) => void;
}

export function VirtualLab({ 
  exerciseId, 
  studentId, 
  exerciseType = 'CODE_CHALLENGE', 
  language = 'python',
  starterCode, 
  instructions, 
  value, 
  onChange 
}: VirtualLabProps) {
  const [output, setOutput] = useState<string>('');
  const [isExecuting, setIsExecuting] = useState(false);
  
  const socketRef = useRef<Socket | null>(null);

  // Initialiser avec starterCode si la valeur est vide
  useEffect(() => {
    if (!value && starterCode) {
      onChange(starterCode);
    }
  }, [starterCode, value, onChange]);

  useEffect(() => {
    // Connexion au Virtual Lab Service (Port 3004)
    // IMPORTANT: Ceci utilise votre architecture locale (Redis + RabbitMQ)
    import('socket.io-client').then(({ io }) => {
      const socket = io('http://localhost:3004', {
        transports: ['websocket'],
        upgrade: false,
      });
      
      socketRef.current = socket;

      socket.on('connect', () => {
        console.log('Connecté au Virtual Lab Service');
        socket.emit('join-lab', { exerciseId, studentId });
      });

      socket.on('run-result', (data: { output: string; isError: boolean }) => {
        setIsExecuting(false);
        setOutput((prev) => prev + `\n${data.output}`);
      });

      return () => {
        socket.disconnect();
      };
    });
  }, [exerciseId, studentId]);

  const throttleTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleEditorChange = (v: string | undefined) => {
    if (v !== undefined) {
      onChange(v);
      
      // Sauvegarde automatique (Redis) via WebSocket
      if (throttleTimeoutRef.current) {
        clearTimeout(throttleTimeoutRef.current);
      }
      
      throttleTimeoutRef.current = setTimeout(() => {
        if (socketRef.current) {
          const room = `lab-${exerciseId}-${studentId}`;
          socketRef.current.volatile.emit('code-draft', { room, code: v });
        }
      }, 300);
    }
  };

  const handleRunCode = async () => {
    setIsExecuting(true);
    setOutput('> Exécution en cours via votre serveur Piston local (RabbitMQ)...\n');
    
    if (socketRef.current) {
      // On envoie le code au backend qui va l'envoyer à RabbitMQ puis Piston
      socketRef.current.emit('run-code', { code: value, language });
    } else {
      setOutput('> Erreur : Non connecté au serveur de laboratoire (Port 3004).\n');
      setIsExecuting(false);
    }
  };

  // ─── RENDU DU MODE CODE CHALLENGE ──────────────────────────────────────────
  if (exerciseType === 'CODE_CHALLENGE') {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-0 bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl my-8">
        {/* Colonne de Gauche : Instructions (1/4) */}
        <div className="bg-slate-900 p-6 border-r border-slate-800 flex flex-col h-[600px] overflow-y-auto">
          <h3 className="text-lg font-black text-white mb-6 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-blue-400" /> 
            Mission
          </h3>
          <div className="prose prose-invert prose-sm text-slate-300 leading-relaxed">
            {instructions}
          </div>
        </div>

        {/* Colonne de Droite : Editeur & Console (3/4) */}
        <div className="lg:col-span-3 flex flex-col h-[600px]">
          <div className="flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <div className="w-3 h-3 rounded-full bg-amber-500" />
              <div className="w-3 h-3 rounded-full bg-emerald-500" />
              <span className="ml-3 text-xs font-mono text-slate-400">
                main.{language === 'python' ? 'py' : language === 'javascript' ? 'js' : language === 'c++' || language === 'cpp' ? 'cpp' : language}
              </span>
            </div>
            <Button 
              type="button"
              size="sm" 
              className="bg-emerald-600 hover:bg-emerald-700 h-8"
              onClick={handleRunCode}
              disabled={isExecuting}
            >
              <Play className="w-4 h-4 mr-2" /> Exécuter le code
            </Button>
          </div>

          <div className="flex-1 relative border-b border-slate-800">
            <Editor
              height="100%"
              defaultLanguage={language === 'c++' ? 'cpp' : language}
              theme="vs-dark"
              value={value}
              onChange={handleEditorChange}
              options={{ 
                minimap: { enabled: false }, 
                fontSize: 14, 
                padding: { top: 16 },
                scrollBeyondLastLine: false,
              }}
            />
          </div>

          <div className="h-48 bg-[#0d1117] p-4 font-mono text-xs overflow-y-auto">
            <div className="text-slate-500 mb-2 font-bold uppercase tracking-wider">Terminal -- bash</div>
            <pre className="text-emerald-400 whitespace-pre-wrap">{output}</pre>
          </div>
        </div>
      </div>
    );
  }

  // ─── RENDU DU MODE CIRCUIT BUILD ───────────────────────────────────────────
  if (exerciseType === 'CIRCUIT_BUILD') {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-0 bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl my-8 h-[650px]">
        {/* Barre d'outils (Toute la largeur) */}
        <div className="lg:col-span-4 bg-slate-900 border-b border-slate-800 p-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h3 className="text-white font-bold flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-400" /> Laboratoire IoT
            </h3>
            <div className="h-4 w-px bg-slate-700" />
            <p className="text-sm text-slate-400 max-w-xl truncate">{instructions}</p>
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="outline" size="sm" className="border-slate-700 text-slate-300 hover:bg-slate-800 h-9">
              <RefreshCw className="w-4 h-4 mr-2" /> Réinitialiser
            </Button>
            <Button type="button" size="sm" className="bg-indigo-600 hover:bg-indigo-700 h-9 shadow-lg shadow-indigo-900/50">
              <Zap className="w-4 h-4 mr-2" /> Lancer la simulation
            </Button>
          </div>
        </div>

        {/* Palette de Composants (Sidebar Gauche 1/4) */}
        <div className="bg-[#0f111a] border-r border-slate-800 p-4 overflow-y-auto hidden lg:block">
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Composants disponibles</h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/50 hover:bg-slate-800 cursor-grab transition-all group">
              <div className="w-12 h-12 mx-auto bg-slate-900 rounded-lg shadow-inner mb-2 flex items-center justify-center group-hover:scale-105 transition-transform">
                <Cpu className="w-6 h-6 text-emerald-400" />
              </div>
              <p className="text-[10px] text-center text-slate-300 font-medium leading-tight">Arduino Uno</p>
            </div>
            
            <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/50 hover:bg-slate-800 cursor-grab transition-all group">
              <div className="w-12 h-12 mx-auto bg-slate-900 rounded-lg shadow-inner mb-2 flex items-center justify-center group-hover:scale-105 transition-transform">
                <div className="w-3 h-3 rounded-full bg-red-500 shadow-[0_0_15px_rgba(239,68,68,0.6)]" />
              </div>
              <p className="text-[10px] text-center text-slate-300 font-medium leading-tight">LED Rouge</p>
            </div>

            <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/50 hover:bg-slate-800 cursor-grab transition-all group">
              <div className="w-12 h-12 mx-auto bg-slate-900 rounded-lg shadow-inner mb-2 flex items-center justify-center group-hover:scale-105 transition-transform">
                <div className="w-8 h-2 bg-amber-700/80 rounded-sm flex items-center justify-between px-1">
                  <div className="w-1 h-2 bg-slate-900" /><div className="w-1 h-2 bg-slate-900" />
                </div>
              </div>
              <p className="text-[10px] text-center text-slate-300 font-medium leading-tight">Résistance</p>
            </div>

            <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/50 hover:bg-slate-800 cursor-grab transition-all group">
              <div className="w-12 h-12 mx-auto bg-slate-900 rounded-lg shadow-inner mb-2 flex items-center justify-center group-hover:scale-105 transition-transform">
                <Layers className="w-6 h-6 text-blue-400" />
              </div>
              <p className="text-[10px] text-center text-slate-300 font-medium leading-tight">Capteur DHT11</p>
            </div>
          </div>
        </div>

        {/* Grille de Travail Principale (Canvas 3/4) */}
        <div className="lg:col-span-3 bg-[#13151f] relative overflow-hidden">
          {/* Grille de fond SVG stylisée */}
          <div className="absolute inset-0 opacity-20" style={{ 
            backgroundImage: `linear-gradient(#334155 1px, transparent 1px), linear-gradient(90deg, #334155 1px, transparent 1px)`, 
            backgroundSize: '20px 20px' 
          }} />
          
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center bg-slate-950/80 backdrop-blur-sm p-6 rounded-2xl border border-slate-800/50">
              <div className="w-16 h-16 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-4">
                <Settings className="w-8 h-8 text-indigo-400 animate-[spin_8s_linear_infinite]" />
              </div>
              <p className="text-slate-300 font-bold text-lg">Espace d'assemblage</p>
              <p className="text-sm text-slate-400 mt-2">Glissez-déposez des composants de la palette vers la grille.</p>
              <p className="text-xs text-indigo-400/70 mt-4 font-mono">[ Graph-based Validation Ready ]</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Fallback de sécurité
  return (
    <div className="p-8 bg-slate-900 border border-slate-800 rounded-2xl text-center">
      <AlertCircle className="w-8 h-8 text-slate-500 mx-auto mb-4" />
      <h3 className="text-slate-300 font-bold">Mode d'exercice non supporté</h3>
      <p className="text-slate-500 text-sm mt-2">Le Virtual Lab ne supporte pas encore ce type d'exercice.</p>
    </div>
  );
}
