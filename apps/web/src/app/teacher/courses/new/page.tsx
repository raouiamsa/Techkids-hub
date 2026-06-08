"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/contexts/auth.context';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';
import { 
  Rocket, Code, Cpu, Gamepad2, Video, BookOpen,
  PlusCircle, Trash2, Save, Send, X, ShieldCheck
} from 'lucide-react';
import { Button, Card, CardContent } from '@org/ui-components';

const SYMBOLS = [
  { icon: Rocket, label: 'Espace', color: 'text-purple-500', bg: 'bg-purple-500/10' },
  { icon: Code, label: 'Code', color: 'text-blue-500', bg: 'bg-blue-500/10' },
  { icon: Cpu, label: 'Hardware', color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
  { icon: Gamepad2, label: 'Jeu', color: 'text-amber-500', bg: 'bg-amber-500/10' },
  { icon: Video, label: 'Média', color: 'text-pink-500', bg: 'bg-pink-500/10' },
  { icon: BookOpen, label: 'Théorie', color: 'text-slate-500', bg: 'bg-slate-500/10' },
];

export default function CourseBuilderPage() {
  const router = useRouter();
  const { token } = useAuth();
  
  const [course, setCourse] = useState({
    title: '',
    description: '',
    level: 'BEGINNER',
    language: '',
    modules: [] as any[],
    certificationBank: [] as any[],
  });

  const [saving, setSaving] = useState(false);

  const [showFinalTest, setShowFinalTest] = useState(false);

  const addModule = () => {
    setCourse(prev => ({
      ...prev,
      modules: [...prev.modules, { title: '', symbol: 'BookOpen', content: '', exercises: [] }]
    }));
  };

  const addCertQuestion = () => {
    setCourse(prev => ({
      ...prev,
      certificationBank: [
        ...(prev.certificationBank || []),
        { question: '', options: ['', '', '', ''], answer: '' }
      ]
    }));
  };

  const updateCertQuestion = (qIdx: number, field: string, value: any) => {
    const newQs = [...course.certificationBank];
    newQs[qIdx][field] = value;
    setCourse({ ...course, certificationBank: newQs });
  };

  const updateCertOption = (qIdx: number, optIdx: number, value: string) => {
    const newQs = [...course.certificationBank];
    newQs[qIdx].options[optIdx] = value;
    setCourse({ ...course, certificationBank: newQs });
  };

  const updateModule = (index: number, field: string, value: any) => {
    const newModules = [...course.modules];
    newModules[index][field] = value;
    setCourse({ ...course, modules: newModules });
  };

  const addExercise = (moduleIndex: number) => {
    const newModules = [...course.modules];
    newModules[moduleIndex].exercises.push({
      title: '',
      exerciseType: 'QUIZ',
      instructions: '',
      options: ['', '', '', ''],
      solution: ''
    });
    setCourse({ ...course, modules: newModules });
  };

  const updateExercise = (mIdx: number, eIdx: number, field: string, value: any) => {
    const newModules = [...course.modules];
    newModules[mIdx].exercises[eIdx][field] = value;
    setCourse({ ...course, modules: newModules });
  };

  const updateExerciseOption = (mIdx: number, eIdx: number, optIdx: number, value: string) => {
    const newModules = [...course.modules];
    newModules[mIdx].exercises[eIdx].options[optIdx] = value;
    setCourse({ ...course, modules: newModules });
  };

  const handleSave = async (isPublished: boolean) => {
    if (!token) return;
    setSaving(true);
    try {
      // 1. Create the base course
      const res = await fetch(`${API_URL}/courses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: course.title || 'Nouveau Cours',
          description: course.description,
          level: course.level,
          language: course.language
        })
      });
      
      if (!res.ok) throw new Error("Erreur HTTP création");
      const data = await res.json();
      const courseId = data?.id;
      
      if (!courseId) throw new Error("Erreur de création");

      // 2. Update with modules and exercises
      const updateRes = await fetch(`${API_URL}/courses/${courseId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          isPublished,
          modules: course.modules,
          certificationBank: course.certificationBank
        })
      });

      if (!updateRes.ok) throw new Error("Erreur sauvegarde modules");

      router.push('/teacher/dashboard');
    } catch (err) {
      console.error(err);
      alert("Erreur lors de la sauvegarde.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-20">
      {/* Header collant avec boutons */}
      <div className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800 p-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <span className="p-2 bg-teal-500/10 rounded-lg"><Code className="w-5 h-5 text-teal-500" /></span>
            Éditeur Créatif
          </h1>
          <div className="flex items-center gap-3">
            <Button variant="outline" className="border-slate-700 hover:bg-slate-800" onClick={() => router.push('/teacher/dashboard')}>
              <X className="w-4 h-4 mr-2" /> Annuler
            </Button>
            <Button variant="outline" className="border-amber-500/50 text-amber-500 hover:bg-amber-500/10" onClick={() => handleSave(false)} disabled={saving}>
              <Save className="w-4 h-4 mr-2" /> {saving ? '...' : 'Sauvegarder'}
            </Button>
            <Button className="bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold" onClick={() => handleSave(true)} disabled={saving}>
              <Send className="w-4 h-4 mr-2" /> {saving ? '...' : 'Publier'}
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto mt-8 px-4 space-y-8">
        
        {/* Info Générales */}
        <Card className="rounded-3xl border-slate-800 bg-slate-900/50">
          <CardContent className="p-8 space-y-6">
            <input 
              type="text" 
              placeholder="Titre du cours (ex: Découverte de Python)"
              className="w-full bg-transparent text-4xl font-black focus:outline-none placeholder:text-slate-700"
              value={course.title}
              onChange={(e) => setCourse({...course, title: e.target.value})}
            />
            <textarea 
              placeholder="Description engageante pour vos élèves..."
              className="w-full bg-slate-950 rounded-xl p-4 min-h-[100px] focus:outline-none focus:ring-2 focus:ring-teal-500/50 resize-none"
              value={course.description}
              onChange={(e) => setCourse({...course, description: e.target.value})}
            />
            <div className="flex gap-4">
              <select 
                className="bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 focus:outline-none focus:border-teal-500"
                value={course.level}
                onChange={(e) => setCourse({...course, level: e.target.value})}
              >
                <option value="BEGINNER">Débutant</option>
                <option value="INTERMEDIATE">Intermédiaire</option>
                <option value="ADVANCED">Avancé</option>
              </select>
              <input 
                type="text" 
                placeholder="Langage (ex: python, javascript)"
                className="bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 focus:outline-none focus:border-teal-500 flex-1"
                value={course.language}
                onChange={(e) => setCourse({...course, language: e.target.value})}
              />
            </div>
          </CardContent>
        </Card>

        {/* Modules */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold px-2">Parcours d'Apprentissage</h2>
          
          {course.modules.map((mod, mIdx) => (
            <Card key={mIdx} className="rounded-[2rem] border-slate-800 bg-slate-900 overflow-hidden relative group">
              <div className="absolute top-0 left-0 w-2 h-full bg-teal-500" />
              <CardContent className="p-6 pl-8">
                <div className="flex items-start justify-between mb-6">
                  <input 
                    type="text" 
                    placeholder="Titre du module"
                    className="bg-transparent text-2xl font-bold focus:outline-none placeholder:text-slate-700 w-full"
                    value={mod.title}
                    onChange={(e) => updateModule(mIdx, 'title', e.target.value)}
                  />
                  <button onClick={() => {
                    const newM = [...course.modules]; newM.splice(mIdx, 1); setCourse({...course, modules: newM});
                  }} className="text-slate-600 hover:text-red-500 transition-colors ml-4">
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>

                {/* Symbole Picker */}
                <div className="flex flex-wrap gap-3 mb-6">
                  {SYMBOLS.map((sym, sIdx) => {
                    const Icon = sym.icon;
                    const isActive = mod.symbol === sym.label;
                    return (
                      <button 
                        key={sIdx}
                        onClick={() => updateModule(mIdx, 'symbol', sym.label)}
                        className={`p-3 rounded-2xl flex flex-col items-center gap-2 transition-all ${isActive ? sym.bg + ' ring-2 ring-white/20 scale-105' : 'bg-slate-950 hover:bg-slate-800'}`}
                      >
                        <Icon className={`w-6 h-6 ${isActive ? sym.color : 'text-slate-500'}`} />
                        <span className="text-[10px] uppercase font-bold text-slate-400">{sym.label}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Contenu du Module */}
                <div className="mb-6">
                  <textarea 
                    placeholder="Contenu du cours pour ce module (Markdown accepté)..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 min-h-[120px] focus:outline-none focus:border-teal-500 resize-y text-sm"
                    value={mod.content}
                    onChange={(e) => updateModule(mIdx, 'content', e.target.value)}
                  />
                </div>

                {/* Exercices */}
                <div className="space-y-4 pl-4 border-l-2 border-slate-800">
                  {mod.exercises.map((ex: any, eIdx: number) => (
                    <div key={eIdx} className="bg-slate-950 rounded-xl p-4 space-y-4 border border-slate-800/50">
                      <div className="flex items-center gap-4">
                        <select
                          className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500 text-sm font-bold text-blue-400"
                          value={ex.exerciseType}
                          onChange={(e) => updateExercise(mIdx, eIdx, 'exerciseType', e.target.value)}
                        >
                          <option value="QUIZ">QUIZ (QCM)</option>
                          <option value="CODE_CHALLENGE">CODE_CHALLENGE</option>
                          <option value="CIRCUIT_BUILD">CIRCUIT_BUILD</option>
                        </select>
                        <input 
                          type="text" 
                          placeholder="Titre de l'exercice..."
                          className="bg-transparent font-bold flex-1 focus:outline-none text-base"
                          value={ex.title}
                          onChange={(e) => updateExercise(mIdx, eIdx, 'title', e.target.value)}
                        />
                      </div>
                      
                      <textarea 
                        placeholder="Énoncé de l'exercice..."
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 min-h-[80px] focus:outline-none focus:border-blue-500 resize-y text-sm"
                        value={ex.instructions}
                        onChange={(e) => updateExercise(mIdx, eIdx, 'instructions', e.target.value)}
                      />

                      {ex.exerciseType === 'QUIZ' && (
                        <div className="grid grid-cols-2 gap-3 mt-4">
                          {ex.options.map((opt: string, optIdx: number) => (
                            <div key={optIdx} className="flex items-center gap-2">
                              <input 
                                type="radio" 
                                name={`correct-${mIdx}-${eIdx}`}
                                checked={ex.solution === opt && opt !== ''}
                                onChange={() => updateExercise(mIdx, eIdx, 'solution', opt)}
                                className="w-4 h-4 accent-blue-500 cursor-pointer"
                              />
                              <input 
                                type="text" 
                                placeholder={`Option ${optIdx + 1}`}
                                className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500 flex-1 text-sm"
                                value={opt}
                                onChange={(e) => updateExerciseOption(mIdx, eIdx, optIdx, e.target.value)}
                              />
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                  <Button variant="ghost" size="sm" onClick={() => addExercise(mIdx)} className="text-slate-400 hover:text-teal-400">
                    <PlusCircle className="w-4 h-4 mr-2" /> Ajouter un exercice
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}

          <Button 
            onClick={addModule} 
            className="w-full py-8 border-2 border-dashed border-slate-800 hover:border-teal-500/50 hover:bg-teal-500/5 bg-transparent rounded-[2rem] text-slate-400 transition-all"
          >
            <PlusCircle className="w-6 h-6 mr-3" /> 
            <span className="font-bold text-lg">Ajouter une nouvelle étape (Module)</span>
          </Button>

          {/* Zone Test Final */}
          <Card className={`rounded-[2rem] border-amber-500/30 transition-all duration-300 ${showFinalTest ? 'bg-slate-900 border-amber-500/60' : 'bg-gradient-to-br from-amber-500/10 to-transparent'} mt-12`}>
            <CardContent className="p-8">
              {!showFinalTest ? (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-6">
                    <div className="p-4 bg-amber-500/20 rounded-2xl">
                      <ShieldCheck className="w-10 h-10 text-amber-500" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-amber-500 mb-2">Test Final & Certification</h3>
                      <p className="text-slate-400 text-sm">Ajoutez un examen final pour valider les acquis et délivrer le certificat.</p>
                    </div>
                  </div>
                  <Button onClick={() => setShowFinalTest(true)} className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-6 py-6 rounded-2xl shadow-lg shadow-amber-500/20">
                    Configurer l'examen
                  </Button>
                </div>
              ) : (
                <div className="space-y-6 animate-in fade-in zoom-in duration-300">
                  <div className="flex items-center justify-between border-b border-amber-500/20 pb-4">
                    <div className="flex items-center gap-4">
                      <ShieldCheck className="w-8 h-8 text-amber-500" />
                      <h3 className="text-xl font-black text-amber-500">Configuration du Test Final</h3>
                    </div>
                    <Button variant="ghost" onClick={() => setShowFinalTest(false)} className="text-slate-400 hover:text-red-400">
                      <X className="w-5 h-5" />
                    </Button>
                  </div>
                  
                  <div className="space-y-4">
                    <p className="text-sm text-amber-400/80 mb-4 font-medium">Configurez les questions du QCM final (recommandé: 20 à 40 questions).</p>
                    
                    {course.certificationBank?.map((q: any, qIdx: number) => (
                      <div key={qIdx} className="bg-slate-950 rounded-xl p-4 space-y-4 border border-amber-500/20">
                        <div className="flex items-center gap-4">
                          <span className="bg-amber-500 text-slate-900 font-black rounded-full min-w-[2rem] h-8 flex items-center justify-center">{qIdx + 1}</span>
                          <input 
                            type="text" 
                            placeholder="Énoncé de la question..."
                            className="bg-transparent font-bold flex-1 focus:outline-none text-base text-slate-200"
                            value={q.question}
                            onChange={(e) => updateCertQuestion(qIdx, 'question', e.target.value)}
                          />
                          <button onClick={() => {
                            const newQs = [...course.certificationBank]; newQs.splice(qIdx, 1); setCourse({...course, certificationBank: newQs});
                          }} className="text-slate-600 hover:text-red-500 transition-colors">
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-3 mt-4 pl-12">
                          {q.options.map((opt: string, optIdx: number) => (
                            <div key={optIdx} className="flex items-center gap-2">
                              <input 
                                type="radio" 
                                name={`cert-correct-${qIdx}`}
                                checked={q.answer === opt && opt !== ''}
                                onChange={() => updateCertQuestion(qIdx, 'answer', opt)}
                                className="w-4 h-4 accent-amber-500 cursor-pointer"
                              />
                              <input 
                                type="text" 
                                placeholder={`Option ${optIdx + 1}`}
                                className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 focus:outline-none focus:border-amber-500 flex-1 text-sm"
                                value={opt}
                                onChange={(e) => updateCertOption(qIdx, optIdx, e.target.value)}
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                    
                    <Button variant="ghost" onClick={addCertQuestion} className="w-full border border-dashed border-amber-500/30 text-amber-500 hover:bg-amber-500/10 hover:text-amber-400 py-6">
                      <PlusCircle className="w-5 h-5 mr-2" /> Ajouter une question au test
                    </Button>
                  </div>
                  
                  <div className="flex justify-end">
                    <Button onClick={() => setShowFinalTest(false)} className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-6">
                      Valider le test final
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

        </div>
      </div>
    </div>
  );
}
