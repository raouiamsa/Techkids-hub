'use client';

import { useAuth } from '../../contexts/auth.context';
import { Trophy, Star, ChevronRight, Lock, Medal, Download } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function CertificationsPage() {
  const { user } = useAuth();
  const [enrollments, setEnrollments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEnrollments = async () => {
      try {
        const token = localStorage.getItem('tk_token'); // Fixed token key
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';
        
        const res = await fetch(`${API_URL}/enrollments/my`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (res.ok) {
          const data = await res.json();
          setEnrollments(data || []);
        } else {
          console.error("Error from API:", res.status);
        }
      } catch (err) {
        console.error("Failed to fetch enrollments", err);
      } finally {
        setLoading(false);
      }
    };
    fetchEnrollments();
  }, []);

  const completedCourses = enrollments.filter(e => e.status === 'COMPLETED');
  const activeCourses = enrollments.filter(e => e.status === 'ACTIVE');

  return (
    <div className="min-h-screen bg-[#020617] relative overflow-hidden p-4 md:p-8 font-sans selection:bg-amber-500/30">
      
      {/* Background Ornaments */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-gradient-to-b from-amber-500/10 via-amber-900/5 to-transparent blur-3xl pointer-events-none" />
      <div className="absolute -top-40 -right-40 w-96 h-96 bg-amber-600/20 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-0 -left-20 w-80 h-80 bg-blue-600/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-6xl mx-auto space-y-12 relative z-10 pt-8">
        
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center p-3 bg-amber-500/10 rounded-2xl border border-amber-500/20 mb-4 ring-1 ring-amber-500/50 shadow-[0_0_30px_rgba(245,158,11,0.2)]">
            <Trophy className="h-8 w-8 text-amber-400" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight">
            Mur des <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-yellow-400 to-amber-500">Légendes</span>
          </h1>
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            Collectionne les trophées et prouve tes compétences au monde entier. Ton parcours d'excellence commence ici.
          </p>
        </div>

        {loading ? (
          <div className="text-center text-amber-500 animate-pulse mt-20">Chargement de tes exploits...</div>
        ) : enrollments.length === 0 ? (
          <div className="text-center mt-20 p-10 bg-slate-900/50 border border-slate-800 rounded-3xl backdrop-blur-sm">
            <Trophy className="h-16 w-16 text-slate-700 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-slate-300 mb-2">Aucun parcours commencé</h2>
            <p className="text-slate-500 mb-6">Inscris-toi à un cours pour commencer à collectionner des certificats !</p>
            <Link href="/courses" className="inline-block px-8 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold rounded-xl shadow-lg hover:shadow-orange-500/25 transition-all hover:-translate-y-1">
              Explorer les cours
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-12">
            
            {/* 🌟 COMPLETED COURSES (GOLDEN CARDS) */}
            {completedCourses.map((enrollment: any) => (
              <div key={enrollment.id} className="group relative w-full perspective-1000">
                <div className="absolute -inset-1 bg-gradient-to-br from-amber-400 via-yellow-300 to-orange-500 rounded-3xl blur-xl opacity-30 group-hover:opacity-60 transition duration-700 min-h-[550px]" />
                <div id={`cert-${enrollment.id}`} className="relative min-h-[550px] w-full bg-gradient-to-b from-slate-800 to-slate-900 border border-slate-700/50 rounded-3xl p-1 overflow-hidden transition-all duration-500 hover:scale-[1.02] hover:-translate-y-2 shadow-2xl">
                  <div className="absolute inset-[2px] bg-slate-900 rounded-[22px] overflow-hidden flex flex-col">
                    <div className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-black/50 pointer-events-none" />
                    <div className="absolute -inset-[100%] bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-[30deg] translate-x-[-150%] group-hover:translate-x-[150%] transition-transform duration-1000 ease-out" />
                    <div className="p-8 flex flex-col items-center text-center h-full relative z-10">
                      <div className="relative mb-6">
                        <div className="absolute inset-0 bg-amber-500 blur-2xl opacity-40 rounded-full" />
                        <div className="relative w-28 h-28 bg-gradient-to-br from-amber-100 to-amber-300 rounded-full flex items-center justify-center shadow-[inset_0_-4px_10px_rgba(0,0,0,0.2),0_10px_20px_rgba(245,158,11,0.4)] border-4 border-amber-400/50">
                          <Medal className="h-14 w-14 text-amber-600 drop-shadow-md" />
                        </div>
                      </div>
                      <h2 className="text-2xl font-black text-white mb-1 tracking-wide uppercase">
                        Certificat d'Initiation
                      </h2>
                      <p className="text-amber-400 font-bold mb-2">Cours : {enrollment.course?.title || 'Cours inconnu'}</p>
                      <div className="h-1 w-12 bg-amber-500 rounded-full mb-4" />
                      <p className="text-slate-300 text-sm mb-auto">
                        Décerné avec les honneurs à <span className="font-bold text-white text-lg block mt-1">{user?.firstName || ''} {user?.lastName || ''}</span> 
                        <br/>pour avoir complété ce parcours sur la plateforme <span className="font-bold text-amber-400">TechKids Hub</span>.
                      </p>
                      <div className="w-full bg-slate-950/50 rounded-xl p-4 border border-slate-800 backdrop-blur-sm mt-6">
                        <div className="flex items-center justify-between">
                          <div className="text-left">
                            <p className="text-[10px] text-slate-500 uppercase font-black tracking-widest">Délivré le</p>
                            <p className="text-sm font-bold text-slate-300">{new Date(enrollment.updatedAt || enrollment.enrolledAt).toLocaleDateString('fr-FR')}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-[10px] text-slate-500 uppercase font-black tracking-widest">Plateforme</p>
                            <p className="text-sm font-bold text-amber-500">TechKids Hub</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 flex justify-center relative z-20">
                  <button 
                    onClick={(e) => {
                      const btn = e.currentTarget;
                      const originalText = btn.innerHTML;
                      btn.innerHTML = '<span class="animate-pulse">Génération du PDF...</span>';
                      
                      const el = document.getElementById(`cert-${enrollment.id}`);
                      if (!el) return;
                      
                      const originalTransform = el.style.transform;
                      el.style.transform = 'none';
                      
                      Promise.all([
                        import('html2canvas'),
                        import('jspdf')
                      ]).then(([html2canvas, jsPDF]) => {
                        html2canvas.default(el, { scale: 3, useCORS: true, backgroundColor: '#0f172a' }).then((canvas) => {
                          const imgData = canvas.toDataURL('image/png');
                          const pdf = new jsPDF.default('p', 'mm', 'a4');
                          
                          const pdfWidth = pdf.internal.pageSize.getWidth();
                          const margin = 20;
                          const printWidth = pdfWidth - (margin * 2);
                          const printHeight = (canvas.height * printWidth) / canvas.width;
                          
                          pdf.addImage(imgData, 'PNG', margin, margin, printWidth, printHeight);
                          
                          const safeTitle = (enrollment.course?.title || 'Cours').replace(/[^a-zA-Z0-9]/g, '_');
                          pdf.save(`Certificat_${safeTitle}.pdf`);
                          
                          el.style.transform = originalTransform;
                          btn.innerHTML = originalText;
                        });
                      });
                    }}
                    className="flex items-center gap-2 px-6 py-3 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 rounded-xl transition-all font-bold shadow-lg hover:shadow-amber-500/20"
                  >
                    <Download className="w-5 h-5" /> Télécharger en PDF
                  </button>
                </div>
              </div>
            ))}

            {/* 🔒 ACTIVE COURSES (LOCKED CARDS) */}
            {activeCourses.map((enrollment: any) => (
              <div key={enrollment.id} className="group relative h-[450px] w-full">
                <div className="relative h-full w-full bg-slate-900/50 border border-slate-800/80 rounded-3xl p-1 overflow-hidden transition-all duration-300 hover:border-slate-700 backdrop-blur-sm">
                  <div className="absolute inset-[2px] bg-slate-950/80 rounded-[22px] flex flex-col items-center justify-center text-center p-8">
                    <div className="w-24 h-24 bg-slate-900 rounded-full flex items-center justify-center mb-6 border border-slate-800 shadow-inner">
                      <Lock className="h-10 w-10 text-slate-600" />
                    </div>
                    <h2 className="text-xl font-bold text-slate-500 mb-2 uppercase tracking-widest">
                      Certificat Bloqué
                    </h2>
                    <p className="text-slate-600 text-sm mb-8 px-4">
                      Termine le cours <span className="font-bold">"{enrollment.course?.title || 'Cours inconnu'}"</span> à 100% pour briser ce cadenas et réclamer ton certificat.
                    </p>
                    <Link href={`/courses/${enrollment.courseId}`} className="inline-flex items-center gap-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-bold transition-all hover:gap-3 border border-slate-700 shadow-lg">
                      Continuer le cours <ChevronRight className="h-4 w-4" />
                    </Link>
                  </div>
                </div>
              </div>
            ))}

          </div>
        )}
      </div>
    </div>
  );
}
