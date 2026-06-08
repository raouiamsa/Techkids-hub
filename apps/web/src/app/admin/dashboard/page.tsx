'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/auth.context';
import { useRouter } from 'next/navigation';
import {
  ShieldAlert, Users, BookOpen, GraduationCap, Trash2, 
  UserPlus, X, Loader2, CheckCircle2, AlertCircle, Mail, Key
} from 'lucide-react';
import { Button, Card, CardContent, Input } from '@org/ui-components';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

interface Stats {
  totalUsers: number;
  totalStudents: number;
  totalParents: number;
  totalTeachers: number;
  totalCourses: number;
}

interface UserProfile {
  id: string;
  email: string;
  role: string;
  createdAt: string;
  profile: { firstName: string; lastName: string } | null;
}

export default function AdminDashboardPage() {
  const { user, token, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();

  const [stats, setStats] = useState<Stats | null>(null);
  const [usersList, setUsersList] = useState<UserProfile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState('');
  
  // Add Teacher State
  const [showAddTeacher, setShowAddTeacher] = useState(false);
  const [teacherEmail, setTeacherEmail] = useState('');
  const [teacherFirstName, setTeacherFirstName] = useState('');
  const [teacherLastName, setTeacherLastName] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [addResult, setAddResult] = useState<{success: boolean, msg: string, pwd?: string} | null>(null);

  // Delete State
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push('/login?returnUrl=/admin/dashboard');
    } else if (user && user.role !== 'ADMIN') {
      router.push('/');
    }
  }, [user, isAuthLoading, router]);

  const fetchData = async () => {
    if (!token) return;
    try {
      const [statsRes, usersRes] = await Promise.all([
        fetch(`${API_URL}/admin/stats`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/admin/users`, { headers: { Authorization: `Bearer ${token}` } })
      ]);

      if (!statsRes.ok || !usersRes.ok) throw new Error("Erreur de chargement des données");
      
      const statsData = await statsRes.json();
      const usersData = await usersRes.json();

      setStats(statsData);
      setUsersList(usersData);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  const handleDeleteUser = async (id: string) => {
    if (!confirm("Voulez-vous vraiment supprimer cet utilisateur définitivement ?")) return;
    setDeletingId(id);
    try {
      const res = await fetch(`${API_URL}/admin/users/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Erreur lors de la suppression");
      
      setUsersList(prev => prev.filter(u => u.id !== id));
      setStats(prev => prev ? { ...prev, totalUsers: prev.totalUsers - 1 } : null);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleAddTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teacherEmail || !teacherFirstName || !teacherLastName) return;
    
    setIsAdding(true);
    setAddResult(null);

    try {
      const res = await fetch(`${API_URL}/admin/teachers/add`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ 
          email: teacherEmail, 
          firstName: teacherFirstName, 
          lastName: teacherLastName 
        })
      });
      const data = await res.json();
      
      if (!res.ok) throw new Error(data.message || "Erreur inconnue");
      
      setAddResult({ success: true, msg: data.message, pwd: data.generatedPassword });
      setTeacherEmail('');
      setTeacherFirstName('');
      setTeacherLastName('');
      fetchData(); // Refresh list
    } catch (err: any) {
      setAddResult({ success: false, msg: err.message });
    } finally {
      setIsAdding(false);
    }
  };

  const filteredUsers = usersList.filter(u => 
    u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (u.profile?.firstName + ' ' + u.profile?.lastName).toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'ADMIN': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 border-red-200 dark:border-red-800';
      case 'TEACHER': return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 border-amber-200 dark:border-amber-800';
      case 'PARENT': return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 border-purple-200 dark:border-purple-800';
      default: return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800';
    }
  };

  if (isAuthLoading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-12 w-12 text-teal-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white pb-20">
      
      {/* Admin Header (Teal/Cyan Theme) */}
      <div className="bg-gradient-to-r from-teal-800 to-cyan-900 pt-16 pb-24 px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
        <div className="max-w-7xl mx-auto relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <h1 className="text-4xl font-black text-white flex items-center gap-3 tracking-tight">
              <ShieldAlert className="h-8 w-8 text-teal-300" />
              Console d'Administration
            </h1>
            <p className="text-teal-100 mt-2 text-lg">
              Supervision de la plateforme TechKids Hub
            </p>
          </div>
          <Button 
            onClick={() => { setShowAddTeacher(true); setAddResult(null); }}
            className="bg-white text-teal-900 hover:bg-teal-50 font-bold shadow-xl rounded-xl"
          >
            <UserPlus className="h-4 w-4 mr-2" />
            Ajouter un Professeur
          </Button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 -mt-12 relative z-20 space-y-8">
        
        {/* KPI Cards */}
        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="rounded-2xl border-none shadow-lg bg-white dark:bg-slate-900 overflow-hidden relative">
              <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
              <CardContent className="p-6">
                <p className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-1">Total Inscrits</p>
                <div className="flex items-center justify-between">
                  <p className="text-4xl font-black text-slate-800 dark:text-white">{stats.totalUsers}</p>
                  <Users className="h-8 w-8 text-blue-100 dark:text-blue-900/50" />
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-none shadow-lg bg-white dark:bg-slate-900 overflow-hidden relative">
              <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
              <CardContent className="p-6">
                <p className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-1">Étudiants</p>
                <div className="flex items-center justify-between">
                  <p className="text-4xl font-black text-slate-800 dark:text-white">{stats.totalStudents}</p>
                  <GraduationCap className="h-8 w-8 text-indigo-100 dark:text-indigo-900/50" />
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-none shadow-lg bg-white dark:bg-slate-900 overflow-hidden relative">
              <div className="absolute top-0 left-0 w-1 h-full bg-amber-500"></div>
              <CardContent className="p-6">
                <p className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-1">Enseignants</p>
                <div className="flex items-center justify-between">
                  <p className="text-4xl font-black text-slate-800 dark:text-white">{stats.totalTeachers}</p>
                  <BookOpen className="h-8 w-8 text-amber-100 dark:text-amber-900/50" />
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-none shadow-lg bg-white dark:bg-slate-900 overflow-hidden relative">
              <div className="absolute top-0 left-0 w-1 h-full bg-teal-500"></div>
              <CardContent className="p-6">
                <p className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-1">Cours Actifs</p>
                <div className="flex items-center justify-between">
                  <p className="text-4xl font-black text-slate-800 dark:text-white">{stats.totalCourses}</p>
                  <BookOpen className="h-8 w-8 text-teal-100 dark:text-teal-900/50" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Users Table */}
        <div className="bg-white dark:bg-slate-900 rounded-3xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <h2 className="text-xl font-bold">Gestion des Utilisateurs</h2>
            <Input 
              type="text" 
              placeholder="Rechercher un email ou un nom..." 
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full sm:w-72 bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800"
            />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 font-semibold uppercase tracking-wider text-xs">
                <tr>
                  <th className="px-6 py-4">Utilisateur</th>
                  <th className="px-6 py-4">Rôle</th>
                  <th className="px-6 py-4">Date d'inscription</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
                {filteredUsers.map(u => (
                  <tr key={u.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/20 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-900 dark:text-white">
                        {u.profile?.firstName} {u.profile?.lastName}
                        {!u.profile?.firstName && <span className="text-slate-400 italic">Profil incomplet</span>}
                      </div>
                      <div className="text-slate-500 text-xs mt-0.5 flex items-center gap-1">
                        <Mail className="h-3 w-3" />
                        {u.email}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getRoleColor(u.role)}`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {new Date(u.createdAt).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {u.role !== 'ADMIN' && (
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => handleDeleteUser(u.id)}
                          disabled={deletingId === u.id}
                          className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-full"
                        >
                          {deletingId === u.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {filteredUsers.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center text-slate-500">
                      Aucun utilisateur trouvé.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>

      {/* Add Teacher Modal */}
      {showAddTeacher && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-900 w-full max-w-md rounded-3xl shadow-2xl overflow-hidden border border-slate-200 dark:border-slate-800 animate-in fade-in zoom-in-95 duration-200">
            <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <UserPlus className="h-5 w-5 text-teal-600" />
                Nouveau Professeur
              </h3>
              <button onClick={() => setShowAddTeacher(false)} className="text-slate-400 hover:text-slate-500">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <form onSubmit={handleAddTeacher} className="p-6 space-y-4">
              {addResult?.success ? (
                <div className="bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-800 p-4 rounded-2xl">
                  <div className="flex items-center gap-2 text-teal-700 dark:text-teal-400 font-bold mb-2">
                    <CheckCircle2 className="h-5 w-5" />
                    Professeur créé avec succès !
                  </div>
                  <p className="text-sm text-teal-600/80 dark:text-teal-300/80 mb-4">
                    Un email contenant les identifiants a été envoyé au professeur.
                  </p>
                  <div className="bg-white dark:bg-slate-950 rounded-xl p-3 border border-teal-100 dark:border-teal-800/50 flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                      <Mail className="h-4 w-4 text-slate-400" /> {teacherEmail}
                    </div>
                  </div>
                  <Button 
                    type="button"
                    onClick={() => { setShowAddTeacher(false); setAddResult(null); }}
                    className="w-full mt-4 bg-teal-600 hover:bg-teal-700 text-white rounded-xl"
                  >
                    Fermer
                  </Button>
                </div>
              ) : (
                <>
                  {addResult?.success === false && (
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 text-red-600 p-3 rounded-xl flex items-start gap-2 text-sm">
                      <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                      {addResult.msg}
                    </div>
                  )}
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Prénom</label>
                      <Input required value={teacherFirstName} onChange={e => setTeacherFirstName(e.target.value)} placeholder="Jean" className="bg-slate-50 dark:bg-slate-950" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Nom</label>
                      <Input required value={teacherLastName} onChange={e => setTeacherLastName(e.target.value)} placeholder="Dupont" className="bg-slate-50 dark:bg-slate-950" />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Adresse Email</label>
                    <Input required type="email" value={teacherEmail} onChange={e => setTeacherEmail(e.target.value)} placeholder="jean.dupont@ecole.fr" className="bg-slate-50 dark:bg-slate-950" />
                  </div>
                  <p className="text-xs text-slate-500 flex items-center gap-1.5">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    Un mot de passe aléatoire sera généré et envoyé à cette adresse.
                  </p>
                  
                  <div className="pt-2 flex gap-3">
                    <Button type="button" variant="outline" onClick={() => setShowAddTeacher(false)} className="flex-1 rounded-xl">Annuler</Button>
                    <Button type="submit" disabled={isAdding} className="flex-1 bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow-lg shadow-teal-500/20">
                      {isAdding ? <Loader2 className="h-4 w-4 animate-spin" /> : "Créer le compte"}
                    </Button>
                  </div>
                </>
              )}
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
