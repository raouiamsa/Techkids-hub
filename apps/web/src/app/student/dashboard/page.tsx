'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/auth.context';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { BookOpen, Trophy, PlayCircle, CheckCircle2, Flame, Star, Code, Library, Shield } from 'lucide-react';
import { Button, Card, CardContent } from '@org/ui-components';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

export default function StudentDashboardPage() {
  const { user, token, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();

  const [enrolledCourses, setEnrolledCourses] = useState<any[]>([]);
  const [learningProgressions, setLearningProgressions] = useState<any[]>([]);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(true);

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push('/login?returnUrl=/student/dashboard');
    } else if (user && user.role !== 'STUDENT') {
      router.push('/');
    }
  }, [user, isAuthLoading, router]);

  useEffect(() => {
    if (!token) return;

    const fetchDashboardData = async () => {
      try {
        const [enrollRes, progRes] = await Promise.all([
          fetch(`${API_URL}/enrollments/my`, { headers: { Authorization: `Bearer ${token}` } }),
          fetch(`${API_URL}/progression/my`, { headers: { Authorization: `Bearer ${token}` } })
        ]);

        if (enrollRes.ok && progRes.ok) {
          setEnrolledCourses(await enrollRes.json());
          setLearningProgressions(await progRes.json());
        }
      } catch (error) {
        console.error("Erreur chargement dashboard", error);
      } finally {
        setIsLoadingDashboard(false);
      }
    };

    fetchDashboardData();
  }, [token]);

  if (isAuthLoading || isLoadingDashboard) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-950">
        <Library className="h-12 w-12 text-blue-500 animate-bounce mb-4" />
        <p className="text-slate-500 font-bold animate-pulse">Chargement de ton espace...</p>
      </div>
    );
  }

  // Calcul global (Pour la Gamification)
  let totalModulesCompleted = 0;
  let totalModulesStarted = 0;

  const totalCompletion = enrolledCourses.length > 0
    ? Math.round(
        enrolledCourses.reduce((acc, enrollment) => {
          const courseModules = enrollment.course?.modules ?? [];
          if (courseModules.length === 0) return acc;
          const completed = courseModules.filter((m: any) => {
            const prog = learningProgressions.find((p: any) => p.moduleId === m.id);
            if (prog) totalModulesStarted++;
            if (prog?.completionPercent === 100 || prog?.status === 'COMPLETED') {
              totalModulesCompleted++;
              return true;
            }
            return false;
          }).length;
          return acc + Math.round((completed / courseModules.length) * 100);
        }, 0) / enrolledCourses.length
      )
    : 0;

  // -- GAMIFICATION LOGIC --
  // 1 module complété = 50 XP. Inscription à un cours = 10 XP.
  const xp = (totalModulesCompleted * 50) + (enrolledCourses.length * 10) + (totalModulesStarted * 5);
  const currentLevel = Math.floor(xp / 100) + 1;
  const xpToNextLevel = (currentLevel * 100) - xp;
  const xpProgressPercent = ((xp % 100) / 100) * 100;
  
  // Simulation d'une série (Streak)
  const streakDays = totalModulesStarted > 0 ? 3 : 0; 

  return (
    <div className="min-h-screen bg-[#f8fafc] dark:bg-[#0f111a] p-4 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-10">

        {/* ─── EN-TÊTE : CARTE DE PROFIL JOUEUR ────────────────────────────────── */}
        <div className="relative rounded-3xl overflow-hidden bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 shadow-2xl p-1">
          {/* Décoration de fond */}
          <div className="absolute top-0 left-0 w-full h-full opacity-10 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] mix-blend-overlay" />
          
          <div className="bg-slate-900/40 backdrop-blur-md rounded-[22px] p-6 md:p-8 flex flex-col md:flex-row items-center gap-8 relative z-10">
            
            {/* Avatar & Niveau */}
            <div className="flex flex-col items-center">
              <div className="relative">
                <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-yellow-400 to-orange-500 p-1 flex items-center justify-center shadow-lg shadow-orange-500/50">
                  <div className="w-full h-full rounded-full bg-slate-900 flex items-center justify-center text-4xl">
                    🦊
                  </div>
                </div>
                <div className="absolute -bottom-3 -right-2 bg-gradient-to-r from-pink-500 to-red-500 text-white text-xs font-black px-3 py-1 rounded-full shadow-lg border-2 border-slate-900">
                  NIV {currentLevel}
                </div>
              </div>
            </div>

            {/* Infos Joueur */}
            <div className="flex-1 text-center md:text-left text-white">
              <h1 className="text-3xl md:text-4xl font-black tracking-tight mb-2">
                Salut, {user?.firstName || 'Champion'} !
              </h1>
              <p className="text-blue-100 font-medium text-lg mb-4 flex items-center justify-center md:justify-start gap-2">
                Prêt pour une nouvelle aventure ? <Code className="w-5 h-5 text-yellow-400" />
              </p>

              {/* Jauge d'XP */}
              <div className="max-w-md w-full">
                <div className="flex justify-between text-xs font-bold text-blue-200 mb-1 px-1 uppercase tracking-wider">
                  <span>{xp} XP</span>
                  <span>Plus que {xpToNextLevel} XP pour le niveau {currentLevel + 1} !</span>
                </div>
                <div className="h-4 w-full bg-slate-900/50 rounded-full overflow-hidden border border-white/10 p-0.5">
                  <div
                    className="h-full bg-gradient-to-r from-green-400 to-emerald-500 rounded-full relative"
                    style={{ width: `${xpProgressPercent}%` }}
                  >
                    <div className="absolute top-0 right-0 bottom-0 left-0 bg-[linear-gradient(45deg,rgba(255,255,255,.2)_25%,transparent_25%,transparent_50%,rgba(255,255,255,.2)_50%,rgba(255,255,255,.2)_75%,transparent_75%,transparent)] bg-[length:1rem_1rem] animate-[progress_1s_linear_infinite]" />
                  </div>
                </div>
              </div>
            </div>

            {/* Statistiques Rapides */}
            <div className="flex gap-4 w-full md:w-auto">
              <div className="flex-1 md:flex-none bg-slate-900/60 rounded-2xl p-4 flex flex-col items-center justify-center border border-white/10 backdrop-blur-md">
                <Flame className="w-8 h-8 text-orange-500 mb-1 drop-shadow-[0_0_8px_rgba(249,115,22,0.8)]" />
                <span className="text-2xl font-black text-white">{streakDays}</span>
                <span className="text-[10px] uppercase font-bold text-slate-300">Jours de suite</span>
              </div>
              <div className="flex-1 md:flex-none bg-slate-900/60 rounded-2xl p-4 flex flex-col items-center justify-center border border-white/10 backdrop-blur-md">
                <Star className="w-8 h-8 text-yellow-400 mb-1 drop-shadow-[0_0_8px_rgba(250,204,21,0.8)]" />
                <span className="text-2xl font-black text-white">{totalCompletion}%</span>
                <span className="text-[10px] uppercase font-bold text-slate-300">Complétion</span>
              </div>
            </div>
          </div>
        </div>

        {/* ─── MES TROPHÉES (BADGES) ────────────────────────────────────────────── */}
        <section>
          <h2 className="text-xl font-black text-slate-800 dark:text-white flex items-center gap-2 mb-4">
            <Trophy className="h-6 w-6 text-yellow-500" /> Mes Trophées
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className={`p-4 rounded-2xl border-2 flex flex-col items-center text-center transition-all ${enrolledCourses.length > 0 ? 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-200 dark:border-indigo-800' : 'bg-slate-100 dark:bg-slate-900/50 border-transparent opacity-50 grayscale'}`}>
              <div className="w-12 h-12 rounded-full bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center mb-3 text-2xl">🎒</div>
              <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">Premier Pas</h4>
              <p className="text-[10px] text-slate-500 mt-1">Inscrit à ton 1er cours</p>
            </div>
            
            <div className={`p-4 rounded-2xl border-2 flex flex-col items-center text-center transition-all ${totalModulesCompleted > 0 ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800' : 'bg-slate-100 dark:bg-slate-900/50 border-transparent opacity-50 grayscale'}`}>
              <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-900/50 flex items-center justify-center mb-3 text-2xl">⚡</div>
              <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">Étincelle</h4>
              <p className="text-[10px] text-slate-500 mt-1">Fini ton 1er module</p>
            </div>

            <div className={`p-4 rounded-2xl border-2 flex flex-col items-center text-center transition-all ${streakDays >= 3 ? 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800' : 'bg-slate-100 dark:bg-slate-900/50 border-transparent opacity-50 grayscale'}`}>
              <div className="w-12 h-12 rounded-full bg-orange-100 dark:bg-orange-900/50 flex items-center justify-center mb-3 text-2xl">🔥</div>
              <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">En Feu</h4>
              <p className="text-[10px] text-slate-500 mt-1">3 jours consécutifs</p>
            </div>

            <div className={`p-4 rounded-2xl border-2 flex flex-col items-center text-center transition-all ${currentLevel >= 5 ? 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800' : 'bg-slate-100 dark:bg-slate-900/50 border-transparent opacity-50 grayscale'}`}>
              <div className="w-12 h-12 rounded-full bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center mb-3"><Shield className="w-6 h-6 text-purple-500" /></div>
              <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">Vétéran</h4>
              <p className="text-[10px] text-slate-500 mt-1">Atteint le Niveau 5</p>
            </div>
          </div>
        </section>

        {/* ─── MES AVENTURES (COURS) ────────────────────────────────────────────── */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2">
              <Code className="h-6 w-6 text-blue-500" /> Mes Aventures
            </h2>
            <Button variant="ghost" size="sm" asChild className="font-bold text-blue-600 dark:text-blue-400 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/20 dark:hover:bg-blue-900/40 rounded-full">
              <Link href="/courses">Trouver une mission</Link>
            </Button>
          </div>

          {enrolledCourses.length === 0 ? (
            <div className="text-center py-16 bg-white dark:bg-slate-900 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-3xl">
              <div className="w-24 h-24 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <BookOpen className="h-10 w-10 text-slate-400" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">Aucune aventure en cours</h3>
              <p className="text-slate-500 dark:text-slate-400 mb-8 mt-2 max-w-sm mx-auto">
                Le laboratoire t'attend ! Choisis ton premier cours pour commencer à gagner de l'XP.
              </p>
              <Button asChild className="rounded-full shadow-lg shadow-blue-500/30 px-8 py-6 text-lg font-bold">
                <Link href="/courses">Explorer le catalogue</Link>
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {enrolledCourses.map((enrollment) => {
                const courseModules = enrollment.course?.modules ?? [];
                const completedCount = courseModules.filter((m: any) => {
                  const prog = learningProgressions.find((p: any) => p.moduleId === m.id);
                  return prog?.completionPercent === 100 || prog?.status === 'COMPLETED';
                }).length;
                const avgProgress = courseModules.length > 0
                  ? Math.round((completedCount / courseModules.length) * 100)
                  : 0;

                return (
                  <Card key={enrollment.id} className="group flex flex-col rounded-[2rem] overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-2 border-transparent hover:border-blue-500/50 bg-white dark:bg-slate-900">
                    
                    {/* Badge de Progression Circulaire */}
                    <div className="absolute top-4 right-4 z-10 flex items-center justify-center w-14 h-14 rounded-full bg-white dark:bg-slate-800 shadow-xl border-4 border-slate-50 dark:border-slate-900">
                      <svg className="w-12 h-12 transform -rotate-90">
                        <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-slate-100 dark:text-slate-700" />
                        <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="4" fill="transparent"
                                strokeDasharray={125.6}
                                strokeDashoffset={125.6 - (125.6 * avgProgress) / 100}
                                className="text-blue-500 transition-all duration-1000 ease-out" />
                      </svg>
                      <span className="absolute text-xs font-black text-slate-800 dark:text-white">{avgProgress}%</span>
                    </div>

                    <CardContent className="p-0 flex-1 flex flex-col">
                      {/* Image ou Décoration Haut de carte */}
                      <div className="h-32 bg-gradient-to-br from-indigo-500 to-cyan-500 relative">
                        <div className="absolute inset-0 bg-black/10" />
                        <div className="absolute bottom-4 left-6 text-4xl shadow-sm">💻</div>
                      </div>

                      <div className="p-6 flex flex-col flex-1">
                        <h3 className="text-xl font-black text-slate-800 dark:text-white mb-2 pr-12 leading-tight">
                          {enrollment.course?.title || "Cours inconnu"}
                        </h3>
                        
                        <div className="space-y-2 mt-auto pt-6">
                          <div className="h-3 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden shadow-inner">
                            <div
                              className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-1000 ease-out"
                              style={{ width: `${avgProgress}%` }}
                            />
                          </div>
                        </div>

                        <div className="pt-6 mt-4">
                          <Button asChild className="w-full rounded-2xl font-bold py-6 text-md shadow-md group-hover:shadow-blue-500/25 transition-all">
                            <Link href={`/courses/${enrollment.courseId}`}>
                              {avgProgress === 100
                                ? <><CheckCircle2 className="h-5 w-5 mr-2" /> Mission Accomplie</>
                                : <><PlayCircle className="h-5 w-5 mr-2" /> Reprendre la mission</>
                              }
                            </Link>
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
