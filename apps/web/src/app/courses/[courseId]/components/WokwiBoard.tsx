'use client';

import React, { useEffect, useRef, useState } from 'react';
import '@wokwi/elements';
import { CPU, avrInstruction, AVRIOPort, portBConfig } from 'avr8js';
import { Play, Square, Activity, AlertTriangle, Zap } from 'lucide-react';
import { io, Socket } from 'socket.io-client';



// Un programme "Blink" précompilé en HEX (Pin 13 clignote) pour la démo
const BLINK_HEX = `
:100000000C9434000C9449000C9449000C944900A9
:100010000C9449000C9449000C9449000C94490090
:100020000C9449000C9449000C9449000C94490080
:100030000C9449000C9449000C9449000C94490070
:100040000C9449000C9449000C9449000C94490060
:100050000C9449000C9449000C9449000C94490050
:100060000C9449000C94490011241FBECFEFD8E0DE
:10007000DEBFCDBF11E0A0E0B1E001C01D92A930B1
:10008000B107E1F710E0C9E0D1E003C02297FE01E5
:100090003196E8F720910001283020F491E020E0FC
:1000A000A0E0B0E0EC0102C020930001089584B5D0
:1000B000806284BD85B5806285BD82E098E001C0AA
:1000C0001D9289308107E1F7089585B58F7D85BDF9
:1000D00082E098E001C01D9289308107E1F7089531
:1000E000CF93DF930E9455000E945C000E946500F8
:1000F000F9CFF894FFCF0000000000000000000024
:020100000000FD
:00000001FF
`.trim();

// Fonction utilitaire pour parser le fichier intel HEX
function parseHex(hex: string) {
  const data = new Uint8Array(32768);
  let bytes = 0;
  hex.split('\n').forEach((line) => {
    if (line[0] !== ':') return;
    const count = parseInt(line.substring(1, 3), 16);
    const address = parseInt(line.substring(3, 7), 16);
    const type = parseInt(line.substring(7, 9), 16);
    if (type === 0) {
      for (let i = 0; i < count; i++) {
        data[address + i] = parseInt(line.substring(9 + i * 2, 11 + i * 2), 16);
      }
      bytes += count;
    }
  });
  const progData = new Uint16Array(data.buffer);
  return { progData, bytes };
}

interface WokwiBoardProps {
  exerciseId: string;
  studentId: string;
}

export default function WokwiBoard({ exerciseId, studentId }: WokwiBoardProps) {
  const ledRef = useRef<any>(null);
  const [isRunning, setIsRunning] = useState(false);
  const cpuRef = useRef<CPU | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const [physicsResult, setPhysicsResult] = useState<any>(null);
  const [activeWires, setActiveWires] = useState<string[]>([]);

  // Initialisation Socket & PySpice (Backend)
  useEffect(() => {
    const socket = io('http://localhost:3004', {
      transports: ['websocket'],
      upgrade: false,
    });
    socketRef.current = socket;

    socket.on('circuit-result', (data: any) => {
      setPhysicsResult(data);
    });

    return () => {
      socket.disconnect();
      stopSimulation();
    };
  }, []);

  const generateCircuitJson = () => {
    // La source 5V représente l'Arduino Pin 13 (actif)
    const comps: any[] = [
      { id: 'v1', type: 'battery', nodes: ['pin13', '0'], value: 5 }
    ];

    let ledAnode = 'unconnected_a';
    let ledCathode = 'unconnected_c';
    let resNode1 = 'unconnected_r1';
    let resNode2 = 'unconnected_r2';

    if (activeWires.includes('pin13-led_anode')) ledAnode = 'pin13';
    if (activeWires.includes('gnd-led_cathode')) ledCathode = '0';
    if (activeWires.includes('led_cathode-resistor')) {
      ledCathode = 'node_mid';
      resNode1 = 'node_mid';
    }
    if (activeWires.includes('resistor-gnd')) resNode2 = '0';

    comps.push({ id: 'd1', type: 'led', nodes: [ledAnode, ledCathode] });
    
    // On ajoute la résistance au schéma si elle a au moins un fil
    if (activeWires.includes('led_cathode-resistor') || activeWires.includes('resistor-gnd')) {
      comps.push({ id: 'r1', type: 'resistor', nodes: [resNode1, resNode2], value: 220 });
    }

    return comps;
  };

  const runSimulation = () => {
    if (isRunning) return;
    setIsRunning(true);
    setPhysicsResult(null);

    // 1. Démarrer la vérification physique (PySpice)
    socketRef.current?.emit('simulate-circuit', {
      room: `lab-${exerciseId}`,
      components: generateCircuitJson()
    });

    // 2. Démarrer l'émulation Logique (AVR8js)
    const { progData } = parseHex(BLINK_HEX);
    const cpu = new CPU(progData);
    cpuRef.current = cpu;

    // Configurer le Port B (La Pin 13 de l'Arduino Uno est PB5)
    const portB = new AVRIOPort(cpu, portBConfig);
    portB.addListener((value) => {
      // PB5 est le 5ème bit (1 << 5)
      const pin13State = (value & (1 << 5)) !== 0;
      if (ledRef.current) {
        ledRef.current.value = pin13State; // Allume ou éteint la LED Wokwi
      }
    });

    // Boucle d'exécution non-bloquante
    const executeInstructions = () => {
      if (!cpuRef.current) return;
      // Exécute 500k cycles par frame (environ 16MHz pour 60fps)
      for (let i = 0; i < 500000; i++) {
        avrInstruction(cpuRef.current);
      }
      requestAnimationFrame(executeInstructions);
    };

    requestAnimationFrame(executeInstructions);
  };

  const stopSimulation = () => {
    setIsRunning(false);
    cpuRef.current = null; // Stoppe la boucle requestAnimationFrame
    if (ledRef.current) {
      ledRef.current.value = false;
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl relative">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-slate-800/50 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Zap className="w-5 h-5 text-blue-500" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Laboratoire Électronique (Wokwi)</h3>
            <p className="text-xs text-slate-400">Powered by AVR8js & PySpice</p>
          </div>
        </div>

        <div className="flex gap-2">
          {!isRunning ? (
            <button
              onClick={runSimulation}
              className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-400 hover:to-green-500 text-white font-medium rounded-xl transition shadow-lg shadow-emerald-500/20"
            >
              <Play className="w-4 h-4 fill-current" /> Démarrer (Blink)
            </button>
          ) : (
            <button
              onClick={stopSimulation}
              className="flex items-center gap-2 px-6 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/50 font-medium rounded-xl transition"
            >
              <Square className="w-4 h-4 fill-current" /> Arrêter
            </button>
          )}
        </div>
      </div>

      {/* Wokwi Canvas Area */}
      <div className="flex-1 flex items-center justify-center bg-[url('/grid-dark.svg')] relative p-8">

        {/* Composants Web Wokwi */}
        <div className="relative flex gap-16 items-center transform scale-110">
          {/* @ts-ignore : Les custom elements Wokwi ne sont pas nativement typés pour React */}
          <wokwi-arduino-uno></wokwi-arduino-uno>

          <div className="flex flex-col items-center gap-12 relative">
            <div className="flex flex-col items-center">
              {/* @ts-ignore */}
              <wokwi-led ref={ledRef} color="red"></wokwi-led>
              <p className="text-slate-500 text-xs font-mono mt-2">LED</p>
            </div>
            
            <div className="flex flex-col items-center">
              {/* @ts-ignore */}
              <wokwi-resistor value="220"></wokwi-resistor>
              <p className="text-slate-500 text-xs font-mono mt-2">Résistance (220Ω)</p>
            </div>
          </div>

          {/* Câblage dynamique (SVG) */}
          <svg className="absolute inset-0 pointer-events-none" style={{ width: '100%', height: '100%', overflow: 'visible' }}>
            {activeWires.includes('pin13-led_anode') && <path d="M 220 80 Q 280 80 320 60" fill="none" stroke="#ef4444" strokeWidth="4" className="animate-pulse" />}
            {activeWires.includes('gnd-led_cathode') && <path d="M 220 100 Q 280 100 320 90" fill="none" stroke="#000000" strokeWidth="4" />}
            {activeWires.includes('led_cathode-resistor') && <path d="M 330 90 Q 360 120 330 150" fill="none" stroke="#eab308" strokeWidth="4" />}
            {activeWires.includes('resistor-gnd') && <path d="M 310 150 Q 250 150 220 100" fill="none" stroke="#000000" strokeWidth="4" />}
          </svg>
        </div>

        {/* Panneau de Câblage (UI) */}
        <div className="absolute top-4 right-4 bg-slate-800/90 backdrop-blur border border-slate-700 p-4 rounded-xl shadow-xl w-64">
          <h4 className="text-white font-semibold mb-3 flex items-center gap-2"><Activity className="w-4 h-4 text-emerald-400" /> Câblage du Circuit</h4>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer hover:bg-slate-700/50 p-2 rounded transition">
              <input type="checkbox" className="accent-emerald-500" checked={activeWires.includes('pin13-led_anode')} onChange={(e) => setActiveWires(prev => e.target.checked ? [...prev, 'pin13-led_anode'] : prev.filter(w => w !== 'pin13-led_anode'))} />
              Arduino Pin 13 ➔ LED (+)
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer hover:bg-slate-700/50 p-2 rounded transition">
              <input type="checkbox" className="accent-slate-500" checked={activeWires.includes('gnd-led_cathode')} onChange={(e) => setActiveWires(prev => e.target.checked ? [...prev, 'gnd-led_cathode'] : prev.filter(w => w !== 'gnd-led_cathode'))} />
              Arduino GND ➔ LED (-)
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer hover:bg-slate-700/50 p-2 rounded transition">
              <input type="checkbox" className="accent-amber-500" checked={activeWires.includes('led_cathode-resistor')} onChange={(e) => setActiveWires(prev => e.target.checked ? [...prev, 'led_cathode-resistor'] : prev.filter(w => w !== 'led_cathode-resistor'))} />
              LED (-) ➔ Résistance
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer hover:bg-slate-700/50 p-2 rounded transition">
              <input type="checkbox" className="accent-slate-500" checked={activeWires.includes('resistor-gnd')} onChange={(e) => setActiveWires(prev => e.target.checked ? [...prev, 'resistor-gnd'] : prev.filter(w => w !== 'resistor-gnd'))} />
              Résistance ➔ Arduino GND
            </label>
          </div>
        </div>

        {/* Rapport PySpice (Backend Physics) */}
        {physicsResult && (
          <div className={`absolute bottom-8 left-1/2 -translate-x-1/2 px-8 py-6 rounded-2xl shadow-2xl backdrop-blur-md border border-white/10 w-[90%] max-w-lg ${physicsResult.led_status === 'EXPLODED' ? 'bg-red-900/90' :
              physicsResult.led_status === 'ON' ? 'bg-emerald-900/90' : 'bg-slate-800/90'
            }`}>
            <div className="flex items-start gap-4">
              {physicsResult.led_status === 'EXPLODED' ? <AlertTriangle className="w-8 h-8 text-red-400 shrink-0" /> :
                physicsResult.led_status === 'ON' ? <Activity className="w-8 h-8 text-emerald-400 shrink-0" /> :
                  <Zap className="w-8 h-8 text-slate-400 shrink-0" />}

              <div>
                <h4 className="text-lg font-bold text-white mb-1">Rapport Physique (PySpice)</h4>
                <p className="text-white/80">{physicsResult.message}</p>
                <div className="mt-2 text-xs text-red-200 bg-red-950/50 p-2 rounded-lg border border-red-500/20">
                  <b>Tuteur IA :</b> « Je vois que ton Arduino fonctionne, mais tu n'as pas mis de résistance sur ton circuit virtuel. Ta LED va griller ! »
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
