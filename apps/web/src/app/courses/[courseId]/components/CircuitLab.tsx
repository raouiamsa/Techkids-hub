import React, { useState, useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { Battery, Lightbulb, Activity, Zap, Play, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface CircuitComponent {
  id: string;
  type: 'battery' | 'resistor' | 'led';
  nodes: string[];
  value?: number;
}

interface CircuitLabProps {
  exerciseId: string;
  studentId: string;
}

export function CircuitLab({ exerciseId, studentId }: CircuitLabProps) {
  const [components, setComponents] = useState<CircuitComponent[]>([
    { id: 'v1', type: 'battery', nodes: ['n1', '0'], value: 9 }
  ]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [result, setResult] = useState<any>(null);

  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Connexion au Virtual Lab Service
    const socket = io('http://localhost:3004', {
      transports: ['websocket'],
      upgrade: false,
    });
    socketRef.current = socket;

    socket.on('connect', () => {
      console.log(' Connecté au Circuit Lab');
    });

    socket.on('circuit-result', (data: any) => {
      setIsSimulating(false);
      setResult(data);
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const handleSimulate = () => {
    if (socketRef.current) {
      setIsSimulating(true);
      setResult(null);
      const room = `lab-circuit-${exerciseId}-${studentId}`;
      socketRef.current.emit('simulate-circuit', { room, components });
    }
  };

  const addComponent = (type: 'battery' | 'resistor' | 'led') => {
    const newId = `${type[0]}${components.length + 1}`;
    
    // Le courant part du pôle positif de la pile (n1)
    let lastNode = '0';
    if (components.length === 1 && components[0].type === 'battery') {
      lastNode = components[0].nodes[0]; // 'n1'
    } else if (components.length > 1) {
      lastNode = components[components.length - 1].nodes[1];
    }

    const nextNode = `n${components.length + 1}`;

    let value = 0;
    if (type === 'battery') value = 9;
    if (type === 'resistor') value = 330;

    // Fermeture du circuit si c'est la fin (la LED retourne à 0)
    const finalNodes = [lastNode, type === 'led' ? '0' : nextNode];

    setComponents([...components, { id: newId, type, nodes: finalNodes, value }]);
  };

  const removeComponent = (id: string) => {
    setComponents(components.filter(c => c.id !== id));
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-slate-800/50 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-yellow-500/20 rounded-lg">
            <Zap className="w-5 h-5 text-yellow-500" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Laboratoire d'Électronique</h3>
            <p className="text-xs text-slate-400">Simulateur PySpice</p>
          </div>
        </div>
        <button
          onClick={handleSimulate}
          disabled={isSimulating}
          className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-400 hover:to-green-500 text-white font-medium rounded-xl transition shadow-lg shadow-emerald-500/20 disabled:opacity-50"
        >
          {isSimulating ? <Activity className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
          Lancer la Simulation
        </button>
      </div>

      {/* Main Workspace */}
      <div className="flex-1 flex bg-[url('/grid-dark.svg')]">

        {/* Toolbox */}
        <div className="w-64 border-r border-slate-800 bg-slate-900/80 p-4 flex flex-col gap-3">
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Composants</h4>

          <button onClick={() => addComponent('battery')} className="flex items-center gap-3 p-3 bg-slate-800 hover:bg-slate-700 rounded-xl transition text-left group">
            <Battery className="w-6 h-6 text-emerald-400" />
            <div>
              <p className="text-sm font-medium text-white group-hover:text-emerald-400 transition">Pile (9V)</p>
              <p className="text-xs text-slate-400">Source d'énergie</p>
            </div>
          </button>

          <button onClick={() => addComponent('resistor')} className="flex items-center gap-3 p-3 bg-slate-800 hover:bg-slate-700 rounded-xl transition text-left group">
            <Activity className="w-6 h-6 text-amber-400" />
            <div>
              <p className="text-sm font-medium text-white group-hover:text-amber-400 transition">Résistance</p>
              <p className="text-xs text-slate-400">330 Ohms</p>
            </div>
          </button>

          <button onClick={() => addComponent('led')} className="flex items-center gap-3 p-3 bg-slate-800 hover:bg-slate-700 rounded-xl transition text-left group">
            <Lightbulb className="w-6 h-6 text-red-400" />
            <div>
              <p className="text-sm font-medium text-white group-hover:text-red-400 transition">LED Rouge</p>
              <p className="text-xs text-slate-400">Diode lumineuse</p>
            </div>
          </button>
        </div>

        {/* Breadboard View (Simplified List for MVP) */}
        <div className="flex-1 p-8 relative">
          <div className="max-w-2xl mx-auto space-y-4">
            {components.map((comp, idx) => (
              <div key={comp.id} className="flex items-center gap-4 p-4 bg-slate-800/80 backdrop-blur-sm border border-slate-700 rounded-2xl">
                <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center font-mono text-slate-400 text-sm">
                  #{idx + 1}
                </div>
                <div className="flex-1">
                  <p className="text-white font-medium capitalize flex items-center gap-2">
                    {comp.type === 'battery' && <Battery className="w-4 h-4 text-emerald-400" />}
                    {comp.type === 'resistor' && <Activity className="w-4 h-4 text-amber-400" />}
                    {comp.type === 'led' && <Lightbulb className="w-4 h-4 text-red-400" />}
                    {comp.type}
                  </p>
                  <p className="text-sm text-slate-400 font-mono">Noeuds: {comp.nodes.join(' → ')} {comp.value ? `| Val: ${comp.value}` : ''}</p>
                </div>
                <button onClick={() => removeComponent(comp.id)} className="p-2 text-slate-500 hover:text-red-400 transition rounded-lg hover:bg-slate-700">
                  Retirer
                </button>
              </div>
            ))}
          </div>

          {/* Result Overlay */}
          {result && (
            <div className={`absolute bottom-8 left-1/2 -translate-x-1/2 px-8 py-6 rounded-2xl shadow-2xl backdrop-blur-md border border-white/10 w-[90%] max-w-lg ${result.led_status === 'EXPLODED' ? 'bg-red-900/90' :
                result.led_status === 'ON' ? 'bg-emerald-900/90' : 'bg-slate-800/90'
              }`}>
              <div className="flex items-start gap-4">
                {result.led_status === 'EXPLODED' ? <AlertTriangle className="w-8 h-8 text-red-400 shrink-0" /> :
                  result.led_status === 'ON' ? <CheckCircle2 className="w-8 h-8 text-emerald-400 shrink-0" /> :
                    <Lightbulb className="w-8 h-8 text-slate-400 shrink-0" />}

                <div>
                  <h4 className="text-lg font-bold text-white mb-1">Résultat de la Simulation</h4>
                  <p className="text-white/80">{result.message}</p>

                  {result.current_mA !== undefined && (
                    <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 bg-black/30 rounded-lg font-mono text-sm text-white">
                      Courant mesuré : {result.current_mA} mA
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
