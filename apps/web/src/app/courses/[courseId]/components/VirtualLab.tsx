import React, { useState, useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { io, Socket } from 'socket.io-client';
import { Play, MessageCircle, AlertCircle, Sparkles } from 'lucide-react';
import { Button } from '@org/ui-components';

interface VirtualLabProps {
  exerciseId: string;
  studentId: string;
  starterCode: string;
  instructions: string;
  value: string;
  onChange: (value: string) => void;
}

export function VirtualLab({ exerciseId, studentId, starterCode, instructions, value, onChange }: VirtualLabProps) {
  const [output, setOutput] = useState<string>('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [tutorMessage, setTutorMessage] = useState<string>('Bonjour ! Je suis ton tuteur IA. As-tu besoin d\'aide avec cet exercice ?');
  
  const socketRef = useRef<Socket | null>(null);

  // Initialiser avec starterCode si la valeur est vide
  useEffect(() => {
    if (!value && starterCode) {
      onChange(starterCode);
    }
  }, [starterCode, value, onChange]);

  useEffect(() => {
    // Connexion au Virtual Lab Service (Port 3004)
    // On force le transport WebSocket pour optimiser la vitesse (comme discuté)
    const socket = io('http://localhost:3004', {
      transports: ['websocket'],
      upgrade: false,
    });
    
    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('Connecté au Virtual Lab Service');
      socket.emit('join-lab', { exerciseId, studentId });
    });

    socket.on('tutor-reply', (msg: string) => {
      setTutorMessage(msg);
    });

    // NOUVEAU : Écoute du résultat d'exécution Piston
    socket.on('run-result', (data: { output: string; isError: boolean }) => {
      setIsExecuting(false);
      setOutput((prev) => prev + `\n${data.output}`);
    });

    socket.on('code-update', (updatedCode: string) => {
      // Si quelqu'un d'autre modifiait le code (ex: mode collaboratif)
    });

    return () => {
      socket.disconnect();
    };
  }, [exerciseId, studentId]);

  const throttleTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleEditorChange = (v: string | undefined) => {
    if (v !== undefined) {
      onChange(v);
      
      // Optimisation 4 : Throttling (On attend 300ms avant d'envoyer)
      if (throttleTimeoutRef.current) {
        clearTimeout(throttleTimeoutRef.current);
      }
      
      throttleTimeoutRef.current = setTimeout(() => {
        if (socketRef.current) {
          const room = `lab-${exerciseId}-${studentId}`;
          // Optimisation 3 : Volatile Events
          socketRef.current.volatile.emit('code-draft', { room, code: v });
        }
      }, 300);
    }
  };

  const handleRunCode = async () => {
    setIsExecuting(true);
    setOutput('> Exécution en cours via Piston...\n');
    
    if (socketRef.current) {
      // On envoie le code au backend (NestJS) qui va l'envoyer à Piston
      // On suppose que l'éditeur est en Python pour l'instant
      socketRef.current.emit('run-code', { code: value, language: 'python' });
    }
  };

  const handleAskTutor = () => {
    if (socketRef.current) {
      setTutorMessage('...L\'IA réfléchit...');
      const room = `lab-${exerciseId}-${studentId}`;
      socketRef.current.emit('ask-tutor', { 
        room, 
        code: value, 
        question: 'Aide-moi s\'il te plaît',
        instructions // On passe la consigne de l'exercice pour le contexte de l'IA
      });
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl my-8">
      {/* Colonne de Gauche : Editeur & Console (Prend 2/3 de l'espace) */}
      <div className="lg:col-span-2 flex flex-col h-[600px] border-r border-slate-800">
        {/* Barre d'outils Éditeur */}
        <div className="flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <div className="w-3 h-3 rounded-full bg-emerald-500" />
            <span className="ml-3 text-xs font-mono text-slate-400">Virtual_Lab.py</span>
          </div>
          <Button 
            type="button"
            size="sm" 
            className="bg-emerald-600 hover:bg-emerald-700 h-8"
            onClick={handleRunCode}
            disabled={isExecuting}
          >
            <Play className="w-4 h-4 mr-2" /> Exécuter
          </Button>
        </div>

        {/* Éditeur Monaco */}
        <div className="flex-1 relative">
          <Editor
            height="100%"
            defaultLanguage="python"
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

        {/* Console de Sortie */}
        <div className="h-48 bg-[#0d1117] border-t border-slate-800 p-4 font-mono text-xs overflow-y-auto">
          <div className="text-slate-500 mb-2">Terminal -- bash</div>
          <pre className="text-emerald-400 whitespace-pre-wrap">{output}</pre>
        </div>
      </div>

      {/* Colonne de Droite : Instructions & Tuteur (Prend 1/3 de l'espace) */}
      <div className="flex flex-col h-[600px] bg-slate-900 p-6 space-y-6">
        {/* Instructions */}
        <div className="flex-1">
          <h3 className="text-lg font-black text-white mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-blue-400" /> 
            Mission
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed">
            {instructions}
          </p>
        </div>

        {/* Tuteur IA Socratique */}
        <div className="bg-slate-800 rounded-xl p-4 border border-blue-900/30">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-blue-600/20 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h4 className="font-bold text-white text-sm">Tuteur IA</h4>
              <p className="text-[10px] text-blue-400 font-bold uppercase tracking-widest">En ligne</p>
            </div>
          </div>
          
          <div className="bg-slate-900 rounded-lg p-3 text-sm text-slate-300 mb-4 min-h-[80px]">
            {tutorMessage}
          </div>

          <Button 
            type="button"
            variant="outline" 
            className="w-full bg-slate-900 hover:bg-slate-800 border-slate-700 text-slate-300"
            onClick={handleAskTutor}
          >
            <MessageCircle className="w-4 h-4 mr-2" />
            J'ai besoin d'un indice
          </Button>
        </div>
      </div>
    </div>
  );
}
