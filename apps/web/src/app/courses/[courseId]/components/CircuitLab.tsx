'use client';

import React, { useState, useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { Cpu, Lightbulb, Activity, Zap, Play, CheckCircle2, XCircle, Plus, Trash2, Link as LinkIcon } from 'lucide-react';
import { Button } from '@org/ui-components';

interface Connection {
  fromComponent: string;
  fromPin: string;
  toComponent: string;
  toPin: string;
}

interface CircuitLabProps {
  exerciseId: string;
  studentId: string;
  allowedComponents?: string[]; // Ajout de la prop dynamique
  onChange?: (value: string) => void;
}

// Composants disponibles et leurs broches (Pins)
const COMPONENT_CATALOG: Record<string, { label: string; icon: React.ReactNode; pins: string[]; color: string }> = {
  'Arduino_Uno': { 
    label: 'Arduino Uno', 
    icon: <Cpu className="w-6 h-6" />, 
    pins: ['Pin13', 'Pin12', 'Pin11', '5V', 'GND'],
    color: 'bg-teal-500'
  },
  'Breadboard': {
    label: 'Breadboard',
    icon: <div className="grid grid-cols-3 gap-0.5 w-6 h-6 p-0.5"><div className="bg-white/50 rounded-full"/><div className="bg-white/50 rounded-full"/><div className="bg-white/50 rounded-full"/><div className="bg-white/50 rounded-full"/><div className="bg-white/50 rounded-full"/><div className="bg-white/50 rounded-full"/></div>,
    pins: ['Ligne +', 'Ligne -', 'A1', 'B1', 'C1'],
    color: 'bg-slate-500'
  },
  'LED_Rouge': { 
    label: 'LED Rouge', 
    icon: <Lightbulb className="w-6 h-6" />, 
    pins: ['Anode (+)', 'Cathode (GND)'],
    color: 'bg-red-500' 
  },
  'Resistor_220': { 
    label: 'Résistance 220Ω', 
    icon: <Activity className="w-6 h-6" />, 
    pins: ['Borne 1', 'Borne 2'],
    color: 'bg-amber-500'
  },
  'Bouton_Poussoir': {
    label: 'Bouton Poussoir',
    icon: <div className="w-6 h-6 rounded-full border-2 border-white/50 bg-white/20 flex items-center justify-center"><div className="w-3 h-3 rounded-full bg-white"/></div>,
    pins: ['Borne A', 'Borne B'],
    color: 'bg-indigo-500'
  },
  'Buzzer': {
    label: 'Buzzer (Piezo)',
    icon: <div className="w-6 h-6 rounded-full bg-white/20 border-2 border-white/50 relative"><div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-white rounded-full"/></div>,
    pins: ['Positif (+)', 'Négatif (-)'],
    color: 'bg-pink-500'
  },
  'Capteur_DHT11': {
    label: 'Capteur Temp.',
    icon: <Zap className="w-6 h-6" />,
    pins: ['VCC', 'DATA', 'GND'],
    color: 'bg-blue-500'
  },
  'Pile_9V': {
    label: 'Pile 9V',
    icon: <div className="w-6 h-6 border-2 border-white/50 rounded-sm flex flex-col"><div className="h-1.5 w-3 bg-white/50 mx-auto rounded-t-sm"/><div className="flex-1 bg-white/20"/></div>,
    pins: ['VCC (+)', 'GND (-)'],
    color: 'bg-emerald-500'
  }
};

export function CircuitLab({ exerciseId, studentId, allowedComponents, onChange }: CircuitLabProps) {
  const [components, setComponents] = useState<string[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  
  // États pour le constructeur de connexion
  const [isConnecting, setIsConnecting] = useState(false);
  const [connFrom, setConnFrom] = useState<{ comp: string; pin: string } | null>(null);

  const [isSimulating, setIsSimulating] = useState(false);
  const [result, setResult] = useState<any>(null);

  const socketRef = useRef<Socket | null>(null);

  // Mettre à jour le parent (formulaire) quand le circuit change
  useEffect(() => {
    if (onChange) {
      onChange(JSON.stringify({ components, connections }, null, 2));
    }
  }, [components, connections, onChange]);

  useEffect(() => {
    // Connexion au Virtual Lab Service (NestJS)
    const socketUrl = process.env.NEXT_PUBLIC_VIRTUAL_LAB_URL || 'http://localhost:3004';
    const socket = io(socketUrl, {
      transports: ['websocket'],
      upgrade: false,
    });
    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('🔗 Connecté au Virtual Lab Service');
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

      // Création du graphe JSON exact attendu par le backend (NestJS -> Python)
      const studentGraph = {
        components: components,
        connections: connections.map(c => ({
          from: `${c.fromComponent}:${c.fromPin}`,
          to: `${c.toComponent}:${c.toPin}`
        }))
      };

      // Événement corrigé : validate-circuit au lieu de simulate-circuit
      socketRef.current.emit('validate-circuit', { exerciseId, studentGraph });
    }
  };

  const addComponent = (typeKey: string) => {
    // Génère un ID unique, ex: "Arduino_Uno_1"
    const count = components.filter(c => c.startsWith(typeKey)).length + 1;
    setComponents([...components, `${typeKey}_${count}`]);
  };

  const removeComponent = (compId: string) => {
    setComponents(components.filter(c => c !== compId));
    setConnections(connections.filter(c => c.fromComponent !== compId && c.toComponent !== compId));
  };

  const removeConnection = (index: number) => {
    setConnections(connections.filter((_, i) => i !== index));
  };

  const handlePinClick = (comp: string, pin: string) => {
    if (!isConnecting) {
      setIsConnecting(true);
      setConnFrom({ comp, pin });
      setConnTo(null);
    } else {
      if (connFrom && (connFrom.comp !== comp || connFrom.pin !== pin)) {
        setConnections([...connections, {
          fromComponent: connFrom.comp,
          fromPin: connFrom.pin,
          toComponent: comp,
          toPin: pin
        }]);
      }
      setIsConnecting(false);
      setConnFrom(null);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900 rounded-3xl overflow-hidden border-2 border-slate-200 dark:border-slate-800 shadow-xl font-sans">
      
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-2xl">
            <Cpu className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="font-black text-slate-900 dark:text-white text-lg">Laboratoire IoT</h3>
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Assemble tes composants virtuels !</p>
          </div>
        </div>
        <Button
          onClick={handleSimulate}
          disabled={isSimulating || components.length === 0}
          className="rounded-full shadow-lg font-bold px-8"
        >
          {isSimulating ? <Activity className="w-5 h-5 animate-spin mr-2" /> : <Play className="w-5 h-5 mr-2 fill-current" />}
          Vérifier mon Circuit
        </Button>
      </div>

      <div className="flex-1 flex flex-col md:flex-row bg-slate-50 dark:bg-slate-950/50">
        
        {/* Boîte à outils (Composants) */}
        <div className="w-full md:w-72 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 flex flex-col gap-3 overflow-y-auto">
          <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-2 pl-2">Boîte à outils</h4>
          {Object.entries(COMPONENT_CATALOG)
            .filter(([key]) => !allowedComponents || allowedComponents.includes(key))
            .map(([key, def]) => (
            <button 
              key={key} 
              type="button"
              onClick={() => addComponent(key)} 
              className="flex items-center gap-4 p-4 rounded-2xl transition-all border-2 border-transparent hover:border-slate-200 dark:hover:border-slate-700 bg-slate-50 dark:bg-slate-800/50 hover:bg-white dark:hover:bg-slate-800 group text-left shadow-sm hover:shadow-md"
            >
              <div className={`p-2 rounded-xl text-white shadow-inner ${def.color}`}>
                {def.icon}
              </div>
              <div className="flex-1">
                <p className="font-bold text-slate-800 dark:text-slate-200">{def.label}</p>
              </div>
              <Plus className="w-5 h-5 text-slate-300 group-hover:text-blue-500 transition-colors" />
            </button>
          ))}
        </div>

        {/* Espace de travail (Table de montage) */}
        <div className="flex-1 p-6 relative flex flex-col overflow-y-auto">
          
          {/* Guide visuel de connexion */}
          {isConnecting && connFrom && (
            <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-800 rounded-2xl flex items-center justify-between shadow-sm animate-pulse">
              <p className="text-blue-700 dark:text-blue-300 font-bold flex items-center gap-2">
                <LinkIcon className="w-5 h-5" /> 
                Connecte <b>{connFrom.pin}</b> de <b>{connFrom.comp.replace(/_/g, ' ')}</b> vers un autre composant...
              </p>
              <Button variant="ghost" size="sm" onClick={() => setIsConnecting(false)} className="text-blue-600 hover:bg-blue-100">
                Annuler
              </Button>
            </div>
          )}

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">
            
            {/* Liste des Composants posés */}
            <div className="space-y-4">
              <h4 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-2">Composants placés</h4>
              {components.length === 0 && (
                <div className="p-8 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-3xl text-center">
                  <p className="text-slate-500 dark:text-slate-400 font-medium">Ajoute des composants depuis la boîte à outils.</p>
                </div>
              )}
              {components.map((compId) => {
                const baseType = compId.substring(0, compId.lastIndexOf('_'));
                const def = COMPONENT_CATALOG[baseType];
                return (
                  <div key={compId} className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden transition-all hover:shadow-md">
                    <div className="flex items-center justify-between p-4 border-b border-slate-100 dark:border-slate-700/50 bg-slate-50/50 dark:bg-slate-800/80">
                      <div className="flex items-center gap-3">
                        <div className={`p-1.5 rounded-lg text-white shadow-sm ${def.color}`}>
                          {def.icon}
                        </div>
                        <span className="font-bold text-slate-800 dark:text-slate-200 text-lg">{compId.replace(/_/g, ' ')}</span>
                      </div>
                      <button type="button" onClick={() => removeComponent(compId)} className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition">
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                    {/* Pins du composant */}
                    <div className="p-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {def.pins.map(pin => {
                        const isSelected = connFrom?.comp === compId && connFrom?.pin === pin;
                        return (
                          <button
                            key={pin}
                            type="button"
                            onClick={() => handlePinClick(compId, pin)}
                            className={`px-3 py-2 text-xs font-black uppercase rounded-xl border-2 transition-all flex items-center justify-center gap-2
                              ${isSelected 
                                ? 'bg-blue-500 border-blue-500 text-white shadow-lg scale-105' 
                                : 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-blue-400 hover:text-blue-500'}`}
                          >
                            <div className={`w-2 h-2 rounded-full ${isSelected ? 'bg-white' : 'bg-slate-300 dark:bg-slate-600'}`} />
                            {pin}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Fils / Connexions établies */}
            <div className="space-y-4">
              <h4 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-2">Fils de connexion</h4>
              {connections.length === 0 && (
                <div className="p-8 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-3xl text-center">
                  <p className="text-slate-500 dark:text-slate-400 font-medium">Clique sur deux broches (pins) pour les relier par un fil.</p>
                </div>
              )}
              {connections.map((conn, idx) => (
                <div key={idx} className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-2xl">
                  <div className="flex flex-1 items-center gap-2 text-sm font-medium">
                    <span className="text-slate-700 dark:text-slate-300 truncate max-w-[120px]">{conn.fromComponent.replace(/_/g, ' ')}</span>
                    <span className="px-2 py-1 bg-slate-200 dark:bg-slate-700 rounded font-black text-xs text-slate-500 dark:text-slate-400">{conn.fromPin}</span>
                    <div className="flex-1 h-0.5 bg-gradient-to-r from-blue-400 to-emerald-400 mx-2 relative">
                      <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
                    </div>
                    <span className="text-slate-700 dark:text-slate-300 truncate max-w-[120px]">{conn.toComponent.replace(/_/g, ' ')}</span>
                    <span className="px-2 py-1 bg-slate-200 dark:bg-slate-700 rounded font-black text-xs text-slate-500 dark:text-slate-400">{conn.toPin}</span>
                  </div>
                  <button type="button" onClick={() => removeConnection(idx)} className="ml-4 p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition">
                    <XCircle className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>

          </div>

          {/* Result Alert - Centered Absolute */}
          {result && (
            <div className={`absolute bottom-6 left-1/2 -translate-x-1/2 w-[90%] max-w-xl p-1 rounded-3xl shadow-2xl z-50 animate-in slide-in-from-bottom-10 fade-in duration-300 ${
              result.status === 'success' ? 'bg-gradient-to-r from-emerald-400 to-green-500' : 'bg-gradient-to-r from-red-500 to-rose-600'
            }`}>
              <div className="bg-white dark:bg-slate-900 rounded-[22px] p-6 flex items-start gap-4">
                {result.status === 'success' ? (
                  <div className="p-3 bg-emerald-100 dark:bg-emerald-900/30 rounded-2xl shrink-0">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                  </div>
                ) : (
                  <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-2xl shrink-0">
                    <XCircle className="w-8 h-8 text-red-500" />
                  </div>
                )}
                <div className="flex-1">
                  <h4 className={`text-xl font-black mb-1 ${result.status === 'success' ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
                    {result.status === 'success' ? 'Super Travail !' : 'Oups, il y a une erreur...'}
                  </h4>
                  <p className="text-slate-600 dark:text-slate-300 font-medium text-lg leading-relaxed">{result.message}</p>
                </div>
                <button onClick={() => setResult(null)} className="text-slate-400 hover:text-slate-600 transition">
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
