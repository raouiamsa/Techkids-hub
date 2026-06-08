'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/auth.context';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  BookOpen, ChevronDown, CheckCircle2, Lock, PlayCircle,
  ArrowLeft, Star, Trophy, BookText, AlertCircle, Clock,
  Lightbulb, Settings, Search, Rocket, Target
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { Button } from '@org/ui-components';
import ReactMarkdown from 'react-markdown';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

interface Module {
  id: string;
  title: string;
  order: number;
  content?: string;
  exercises?: Exercise[];
}

interface Exercise {
  id: string;
  title: string;
  instructions: string;
  exerciseType: 'QUIZ' | 'CIRCUIT_BUILD' | 'CODE_CHALLENGE';
}

interface Progression {
  moduleId: string;
  completionPercent: number;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
}

interface CourseViewProps {
  courseId: string;
  courseTitle: string;
  modules: Module[];
  sidebar?: React.ReactNode;
}

const splitMarkdownIntoCards = (content: string) => {
  if (!content) return [];
  // Découper le markdown avant chaque titre H2 ou H3
  const parts = content.split(/(?=(?:^|\n)#{2,3} )/);
  return parts.filter(p => p.trim().length > 0);
};

export function CourseEnrolledView({ courseId, courseTitle, modules, sidebar }: CourseViewProps) {
  const { user, token } = useAuth();
  const router = useRouter();
  const [isEnrolled, setIsEnrolled] = useState<boolean | null>(null);
  const [progressions, setProgressions] = useState<Progression[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [enrollError, setEnrollError] = useState<string | null>(null);
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [expandedModuleId, setExpandedModuleId] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !token) {
      setIsEnrolled(false);
      setIsLoading(false);
      return;
    }

    const checkEnrollment = async () => {
      try {
        const [enrollRes, progRes] = await Promise.all([
          fetch(`${API_URL}/enrollments/my`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${API_URL}/progression/my`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

        if (enrollRes.ok) {
          const enrollments = await enrollRes.json();
          const enrolled = enrollments.some((e: any) => e.courseId === courseId);
          setIsEnrolled(enrolled);
        } else {
          setIsEnrolled(false);
        }

        if (progRes.ok) {
          const progs = await progRes.json();
          setProgressions(progs.filter((p: any) =>
            modules.some(m => m.id === p.moduleId)
          ));
        }
      } catch (err) {
        setIsEnrolled(false);
      } finally {
        setIsLoading(false);
      }
    };
    checkEnrollment();
  }, [courseId, user, token, modules]);

  const handleEnroll = async () => {
    if (!user) {
      router.push(`/login?returnUrl=/courses/${courseId}`);
      return;
    }
    if (user.role !== 'STUDENT' && user.role !== 'PARENT') {
      setEnrollError("Seuls les étudiants ou parents peuvent s'inscrire.");
      return;
    }
    try {
      setIsEnrolling(true);
      setEnrollError(null);
      const res = await fetch(`${API_URL}/enrollments`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ courseId }),
      });
      if (res.ok) {
        setIsEnrolled(true);
      } else {
        const data = await res.json();
        setEnrollError(data.message || 'Erreur lors de l\'inscription');
      }
    } catch (err) {
      setEnrollError('Erreur de connexion serveur');
    } finally {
      setIsEnrolling(false);
    }
  };

  const getModuleProgress = (moduleId: string) => {
    return progressions.find((p) => p.moduleId === moduleId);
  };

  if (isLoading) {
    return <div className="h-40 flex items-center justify-center">Chargement...</div>;
  }

  // Calculate global progress
  let overallProgress = 0;
  if (modules.length > 0) {
    const totalPercent = modules.reduce((sum, mod) => {
      const p = getModuleProgress(mod.id);
      return sum + (p?.completionPercent || 0);
    }, 0);
    overallProgress = Math.round(totalPercent / modules.length);
  }

  const sortedModules = [...modules].sort((a, b) => a.order - b.order);

  if (!isEnrolled) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm text-center py-16">
        <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
          <Lock className="h-10 w-10 text-blue-500" />
        </div>
        <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
          Prêt à commencer l'aventure ?
        </h2>
        <p className="text-lg text-slate-600 dark:text-slate-400 mb-8 max-w-lg mx-auto">
          Inscrivez-vous à ce cours pour accéder aux leçons interactives, réaliser des circuits et écrire du code.
        </p>
        <Button size="lg" onClick={handleEnroll} disabled={isEnrolling} className="px-8 py-6 text-lg rounded-xl">
          {isEnrolling ? 'Inscription...' : 'Commencer ce cours gratuitement'}
        </Button>
        {enrollError && (
          <div className="mt-4 flex items-center justify-center gap-2 text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg w-fit mx-auto">
            <AlertCircle className="h-4 w-4" />
            <p className="text-red-700 dark:text-red-400 text-sm">{enrollError}</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="w-full space-y-8">
      {/* Overall Progress Bar */}
      {user?.role !== 'TEACHER' && user?.role !== 'ADMIN' && !expandedModuleId && (
        <div className="p-6 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-3xl text-white shadow-xl">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-yellow-300" />
              <span className="font-semibold">Ta progression dans ce cours</span>
              <span className="text-2xl font-extrabold">{overallProgress}%</span>
            </div>
          </div>
          <div className="h-3 bg-white/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-white rounded-full transition-all duration-1000"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Modules Area (Master / Detail) */}
      {!expandedModuleId ? (
        /* VUE MAITRE : Grille avec Sidebar */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <BookText className="h-5 w-5 text-blue-500" />
              Modules du cours ({modules.length})
            </h2>

            {modules.length === 0 ? (
              <div className="p-8 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 text-center text-slate-500">
                Les modules de ce cours sont en cours de rédaction.
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {sortedModules.map((module, idx) => {
                  const prog = getModuleProgress(module.id);
                  const percent = prog?.completionPercent ?? 0;
                  const status = prog?.status ?? 'NOT_STARTED';

                  return (
                    <button
                      key={module.id}
                      onClick={() => {
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                        setExpandedModuleId(module.id);
                      }}
                      className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 flex flex-col sm:flex-row items-start sm:items-center gap-5 hover:shadow-lg hover:border-blue-300 transition-all text-left group"
                    >
                      <div className="shrink-0">
                        {status === 'COMPLETED' ? (
                          <div className="h-12 w-12 rounded-xl bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center">
                            <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                          </div>
                        ) : status === 'IN_PROGRESS' ? (
                          <div className="h-12 w-12 rounded-xl bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center group-hover:scale-110 transition-transform">
                            <PlayCircle className="h-6 w-6 text-blue-600" />
                          </div>
                        ) : (
                          <div className="h-12 w-12 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center font-bold text-slate-500 text-xl group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors">
                            {idx + 1}
                          </div>
                        )}
                      </div>
                      <div className="flex-1 w-full">
                        <h3 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                          {module.title}
                        </h3>
                        {module.content && (
                          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                            {module.content.replace(/[#*`>\[\]]/g, '')}
                          </p>
                        )}
                        {percent > 0 && (
                          <div className="mt-3 h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden w-full max-w-sm">
                            <div
                              className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"
                              style={{ width: `${percent}%` }}
                            />
                          </div>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
            
            {/* Section Test Final */}
            <div className="mt-12 pt-8 border-t border-slate-200 dark:border-slate-800">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-6">
                <Trophy className="h-5 w-5 text-yellow-500" />
                Certification
              </h2>
              
              <button
                onClick={() => {
                  if (overallProgress < 100) return;
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                  setExpandedModuleId('final-test');
                }}
                disabled={overallProgress < 100}
                className={`w-full bg-gradient-to-r from-yellow-500 to-amber-500 rounded-2xl p-1 transition-all hover:scale-[1.02] hover:shadow-xl hover:shadow-yellow-500/20 group ${
                  overallProgress < 100 ? 'opacity-50 cursor-not-allowed grayscale' : ''
                }`}
              >
                <div className="bg-white dark:bg-slate-900 rounded-xl p-6 sm:p-8 flex flex-col sm:flex-row items-center gap-6 text-left w-full">
                  <div className="shrink-0 h-20 w-20 bg-yellow-100 dark:bg-yellow-900/40 rounded-full flex items-center justify-center shadow-inner group-hover:scale-110 transition-transform">
                    <Trophy className="h-10 w-10 text-yellow-500" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-3 py-1 bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400 text-xs font-bold uppercase tracking-widest rounded-full">
                        Examen Final
                      </span>
                      {overallProgress < 100 && (
                        <span className="text-sm font-semibold text-slate-500 flex items-center gap-1">
                          <Lock className="h-3 w-3" /> Requis : 100% du cours
                        </span>
                      )}
                    </div>
                    <h3 className="text-2xl font-black text-slate-900 dark:text-white mb-2 group-hover:text-amber-500 transition-colors">
                      Test de Validation du Cours
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400">
                      Validez vos acquis à travers un défi complet pour débloquer votre certificat d'accomplissement.
                    </p>
                  </div>
                </div>
              </button>
            </div>
            
            {/* Go to Dashboard */}
            <div className="text-center pt-8">
              <Link
                href="/student/dashboard"
                className="text-sm text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors inline-flex items-center gap-1"
              >
                <ArrowLeft className="h-4 w-4" />
                Voir tout mon tableau de bord
              </Link>
            </div>
          </div>
          
          <div className="lg:col-span-1">
            {sidebar}
          </div>
        </div>
      ) : (
        /* VUE DÉTAIL : Pleine largeur (Mode Étape par Étape / Gamifié) */
        <div className="animate-fade-in w-full max-w-4xl mx-auto px-4 min-h-[80vh] flex flex-col">
          {(() => {
            if (expandedModuleId === 'final-test') {
              return (
                <div className="animate-fade-in-up w-full flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
                  <div className="inline-flex items-center justify-center h-32 w-32 bg-yellow-100 dark:bg-yellow-900/40 rounded-full mb-8 shadow-inner relative">
                    <Trophy className="h-16 w-16 text-yellow-500" />
                    <div className="absolute -top-4 -right-4 h-12 w-12 bg-white dark:bg-slate-800 rounded-full flex items-center justify-center shadow-lg animate-pulse">
                      <Star className="h-6 w-6 text-yellow-400" fill="currentColor" />
                    </div>
                  </div>
                  <h2 className="text-4xl md:text-6xl font-black text-slate-900 dark:text-white mb-6">
                    Test de Certification
                  </h2>
                  <p className="text-xl text-slate-600 dark:text-slate-400 mb-12 max-w-2xl mx-auto">
                    Le véritable test interactif sera généré par l'IA lors de la Release 2. Pour le moment, simulez la réussite du test pour voir l'animation !
                  </p>
                  <button
                    onClick={() => {
                      if (overallProgress < 100) return;
                      // 1. Envoyer la requête au backend pour terminer le cours (status = COMPLETED)
                      fetch(`${API_URL}/enrollments/${courseId}/complete`, {
                         method: 'POST',
                         headers: { 
                           'Content-Type': 'application/json',
                           Authorization: `Bearer ${token}` 
                         }
                      }).then(() => {
                        // Mettre à jour l'état local pour refléter la complétion si besoin
                      });

                      // 2. Afficher les confettis
                      import('canvas-confetti').then((confetti) => {
                        const end = Date.now() + 3 * 1000; // 3 seconds of massive fireworks
                        const colors = ['#f59e0b', '#ef4444', '#3b82f6', '#10b981', '#8b5cf6'];

                        (function frame() {
                          confetti.default({
                            particleCount: 5,
                            angle: 60,
                            spread: 55,
                            origin: { x: 0 },
                            colors: colors,
                            zIndex: 100
                          });
                          confetti.default({
                            particleCount: 5,
                            angle: 120,
                            spread: 55,
                            origin: { x: 1 },
                            colors: colors,
                            zIndex: 100
                          });

                          if (Date.now() < end) {
                            requestAnimationFrame(frame);
                          } else {
                            // Optionnel: Rediriger vers le dashboard après les confettis
                            setTimeout(() => {
                              window.location.href = '/student/certifications';
                            }, 1000);
                          }
                        }());
                      });
                    }}
                    disabled={overallProgress < 100}
                    className={`px-10 py-5 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-black text-2xl rounded-2xl shadow-xl hover:shadow-2xl hover:scale-105 transition-all ${
                      overallProgress < 100 ? 'opacity-50 cursor-not-allowed grayscale' : ''
                    }`}
                  >
                    🚀 Valider mon diplôme !
                  </button>
                </div>
              );
            }

            const currentModuleIndex = sortedModules.findIndex((m) => m.id === expandedModuleId);
            if (currentModuleIndex === -1) return null;
            
            const module = sortedModules[currentModuleIndex];
            const nextModule = currentModuleIndex < sortedModules.length - 1 ? sortedModules[currentModuleIndex + 1] : null;

            const chunks = splitMarkdownIntoCards(module.content || '');
            
            // Total steps = 1 (Header) + chunks.length + 1 (Exercises)
            const totalSteps = chunks.length > 0 ? chunks.length + 2 : 2;
            
            // We need a local state for the current step inside this render block.
            // Since we can't easily use hooks inside an IIFE returning JSX cleanly without 
            // a sub-component, we should ideally move this to a sub-component, 
            // but we can also use a small trick: we define the state at the top of the main component!
            return <ModulePlayer 
              key={module.id}
              module={module} 
              chunks={chunks} 
              courseId={courseId}
              nextModule={nextModule}
              onClose={() => {
                setExpandedModuleId(null);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              onNextModule={(id) => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
                setExpandedModuleId(id);
              }}
            />;
          })()}
        </div>
      )}
    </div>
  );
}

// Sub-component for the Interactive Module Player (Duolingo Style)
function ModulePlayer({ module, chunks, courseId, nextModule, onClose, onNextModule }: { 
  module: Module, 
  chunks: string[], 
  courseId: string, 
  nextModule: Module | null,
  onClose: () => void,
  onNextModule: (id: string) => void
}) {
  const [currentStep, setCurrentStep] = useState(0);
  const totalSteps = chunks.length > 0 ? chunks.length + 2 : 2; // 0=Intro, 1..N=Chunks, N+1=Exercises
  const progressPercent = currentStep > 0 ? Math.round(((currentStep - 1) / chunks.length) * 100) : 0;

  const colors = [
    'from-blue-50 to-indigo-100 dark:from-blue-900/40 dark:to-indigo-900/40 text-blue-950 dark:text-blue-50',
    'from-emerald-50 to-teal-100 dark:from-emerald-900/40 dark:to-teal-900/40 text-emerald-950 dark:text-emerald-50',
    'from-purple-50 to-fuchsia-100 dark:from-purple-900/40 dark:to-fuchsia-900/40 text-purple-950 dark:text-purple-50',
    'from-amber-50 to-orange-100 dark:from-amber-900/40 dark:to-orange-900/40 text-amber-950 dark:text-amber-50',
    'from-rose-50 to-pink-100 dark:from-rose-900/40 dark:to-pink-900/40 text-rose-950 dark:text-rose-50'
  ];
  const borderColors = [
    'border-blue-200 dark:border-blue-800',
    'border-emerald-200 dark:border-emerald-800',
    'border-purple-200 dark:border-purple-800',
    'border-amber-200 dark:border-amber-800',
    'border-rose-200 dark:border-rose-800'
  ];

  // Inspiration from Benchmarking JSON Schema for icons
  const icons = [
    <BookOpen key="1" className="h-10 w-10 text-slate-800 dark:text-white opacity-80" />, 
    <Lightbulb key="2" className="h-10 w-10 text-slate-800 dark:text-white opacity-80" />, 
    <Settings key="3" className="h-10 w-10 text-slate-800 dark:text-white opacity-80" />, 
    <Search key="4" className="h-10 w-10 text-slate-800 dark:text-white opacity-80" />, 
    <Rocket key="5" className="h-10 w-10 text-slate-800 dark:text-white opacity-80" />, 
    <Target key="6" className="h-10 w-10 text-slate-800 dark:text-white opacity-80" />
  ];

  // Fonction pour calculer le temps de lecture estimé (basé sur ~100 mots/minute pour un enfant)
  const calculateReadingTime = (text: string) => {
    if (!text) return 1;
    const wordCount = text.trim().split(/\s+/).length;
    const minutes = Math.ceil(wordCount / 100);
    return Math.max(1, minutes); // Au moins 1 minute
  };

  const totalReadingTime = calculateReadingTime(module.content || '');

  useEffect(() => {
    if (currentStep === totalSteps - 1 && chunks.length > 0) {
      confetti({
        particleCount: 150,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'],
        disableForReducedMotion: true
      });
    }
  }, [currentStep, totalSteps, chunks.length]);

  return (
    <div className="flex-1 flex flex-col pt-4">
      {/* Header with Progress Bar */}
      <div className="flex items-center gap-4 mb-8">
        <button onClick={onClose} className="p-3 bg-white dark:bg-slate-800 rounded-xl hover:bg-slate-100 text-slate-500 shadow-sm border border-slate-200 dark:border-slate-700 transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex-1 h-4 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden shadow-inner">
          <div 
            className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="font-bold text-emerald-600 dark:text-emerald-400 text-sm bg-emerald-50 dark:bg-emerald-900/30 px-3 py-1.5 rounded-lg border border-emerald-200 dark:border-emerald-800">
          {progressPercent}%
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col justify-center items-center py-4 relative">
        
        {currentStep === 0 && (
          <div className="w-full animate-fade-in-up bg-gradient-to-br from-indigo-600 to-purple-600 dark:from-indigo-900 dark:to-purple-900 rounded-[2.5rem] p-10 md:p-16 shadow-2xl relative overflow-hidden text-center border border-indigo-400/30">
            <div className="inline-flex items-center justify-center h-20 w-20 bg-white/20 rounded-3xl mb-8 backdrop-blur-md shadow-lg border border-white/30 text-4xl">
              🎯
            </div>
            <h2 className="text-4xl md:text-6xl font-black text-white leading-tight mb-6">
              {module.title}
            </h2>
            
            {/* Metadata Badges inspired by JSON schema */}
            <div className="flex flex-wrap justify-center gap-3 mb-10">
              <span className="px-4 py-2 bg-white/10 text-white rounded-xl text-sm font-semibold backdrop-blur-md flex items-center gap-2 border border-white/20">
                <Clock className="h-4 w-4" /> {totalReadingTime} min estimées
              </span>
              <span className="px-4 py-2 bg-emerald-500/20 text-emerald-100 rounded-xl text-sm font-semibold backdrop-blur-md flex items-center gap-2 border border-emerald-400/30">
                Niveau : Adaptatif
              </span>
            </div>

            <p className="text-indigo-100 text-lg max-w-xl mx-auto mb-10">
              Prêt à découvrir de nouvelles notions ? Avance étape par étape pour ne rien rater !
            </p>
          </div>
        )}

        {currentStep > 0 && currentStep <= chunks.length && (
          <div key={currentStep} className={`w-full animate-fade-in-up bg-gradient-to-br ${colors[(currentStep-1) % colors.length]} rounded-[2.5rem] p-8 md:p-14 border ${borderColors[(currentStep-1) % borderColors.length]} shadow-xl relative`}>
            
            {/* Concept Card Header (Inspired by JSON Schema) */}
            <div className="flex items-center justify-between mb-8 pb-6 border-b border-black/10 dark:border-white/10">
              <div className="flex items-center gap-4">
                <div>{icons[(currentStep-1) % icons.length]}</div>
                <div>
                  <span className="text-sm font-bold opacity-60 uppercase tracking-widest">
                    Section {currentStep} sur {chunks.length}
                  </span>
                  <div className="text-xl font-bold opacity-90 mt-1">
                    Notion Clé
                  </div>
                </div>
              </div>
              <div className="hidden sm:flex items-center gap-2 px-4 py-2 bg-white/40 dark:bg-black/20 rounded-full text-sm font-semibold opacity-80">
                <Clock className="h-4 w-4" /> {calculateReadingTime(chunks[currentStep - 1])} min
              </div>
            </div>

            <div className={`prose prose-lg md:prose-xl dark:prose-invert prose-headings:font-black prose-h2:text-3xl prose-h3:text-2xl prose-a:text-blue-600 prose-img:rounded-3xl prose-img:shadow-lg max-w-none`}>
              <ReactMarkdown>{chunks[currentStep - 1]}</ReactMarkdown>
            </div>
          </div>
        )}

        {currentStep === totalSteps - 1 && (
          <div className="w-full animate-fade-in-up bg-white dark:bg-slate-800 rounded-[2.5rem] p-8 md:p-16 border border-slate-200 dark:border-slate-700 shadow-2xl text-center">
            <div className="inline-flex items-center justify-center h-24 w-24 bg-yellow-100 dark:bg-yellow-900/40 rounded-full mb-8 shadow-inner">
              <Trophy className="h-12 w-12 text-yellow-500" />
            </div>
            <h2 className="text-4xl font-black text-slate-900 dark:text-white mb-4">
              Bravo, leçon terminée ! 🎉
            </h2>
            <p className="text-lg text-slate-500 dark:text-slate-400 mb-10 max-w-lg mx-auto">
              Il est temps de valider tes connaissances. Prêt à relever les défis de ce module ?
            </p>

            {module.exercises && module.exercises.length > 0 ? (
              <div className="grid grid-cols-1 gap-4 text-left max-w-2xl mx-auto mb-10">
                {module.exercises.map((exercise) => (
                  <Link
                    key={exercise.id}
                    href={`/courses/${courseId}/modules/${module.id}/exercises/${exercise.id}`}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-6 rounded-2xl bg-slate-50 dark:bg-slate-900 hover:bg-blue-50 dark:hover:bg-slate-800/80 border border-slate-200 dark:border-slate-700 transition-all hover:scale-[1.02] hover:shadow-lg group"
                  >
                    <div className="flex items-center gap-4">
                      <div className="h-12 w-12 rounded-xl bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center shrink-0">
                        <Lock className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div>
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-1">
                          Défi : {exercise.exerciseType.replace('_', ' ')}
                        </span>
                        <h4 className="text-lg font-bold text-slate-800 dark:text-white group-hover:text-blue-600 transition-colors">
                          {exercise.title}
                        </h4>
                      </div>
                    </div>
                    <div className="mt-4 sm:mt-0 flex items-center justify-center gap-2 px-6 py-3 bg-white dark:bg-slate-700 rounded-xl text-sm font-bold text-blue-600 dark:text-blue-400 group-hover:bg-blue-600 group-hover:text-white transition-all shadow-sm">
                      Jouer <ArrowLeft className="h-4 w-4 rotate-180" />
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="p-6 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 text-slate-500 italic mb-10 max-w-2xl mx-auto">
                Aucun exercice disponible pour l'instant.
              </div>
            )}
            
            {nextModule && (
              <div className="pt-8 border-t border-slate-100 dark:border-slate-700">
                <button
                  onClick={() => onNextModule(nextModule.id)}
                  className="inline-flex items-center justify-center w-full sm:w-auto px-10 py-5 bg-slate-900 dark:bg-slate-700 hover:bg-slate-800 dark:hover:bg-slate-600 text-white font-bold text-lg rounded-2xl shadow-lg transition-all hover:-translate-y-1"
                >
                  Passer au module suivant
                  <ArrowLeft className="h-6 w-6 ml-3 rotate-180" />
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Navigation Footer */}
      <div className="mt-8 mb-12 flex justify-between items-center px-2">
        <button
          onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
          className={`px-6 py-4 rounded-2xl font-bold transition-all ${
            currentStep > 0 
              ? 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 shadow-sm border border-slate-200 dark:border-slate-700 hover:shadow-md'
              : 'opacity-0 pointer-events-none'
          }`}
        >
          Précédent
        </button>

        {currentStep < totalSteps - 1 && (
          <button
            onClick={() => setCurrentStep(Math.min(totalSteps - 1, currentStep + 1))}
            className="flex-1 max-w-sm flex items-center justify-center gap-3 px-8 py-5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-black text-xl rounded-2xl shadow-[0_8px_0_rgb(37,99,235)] hover:shadow-[0_6px_0_rgb(37,99,235)] hover:translate-y-[2px] active:shadow-[0_0px_0_rgb(37,99,235)] active:translate-y-[8px] transition-all"
          >
            Continuer <ArrowLeft className="h-6 w-6 rotate-180" />
          </button>
        )}
      </div>
    </div>
  );
}
