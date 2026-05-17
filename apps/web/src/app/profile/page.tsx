'use client';

import { useState } from 'react';
import { useAuth } from '../contexts/auth.context';
import { useRouter } from 'next/navigation';
import { Card, CardContent, Button } from '@org/ui-components';
import { User, Lock, Mail, Save, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

export default function ProfilePage() {
  const { user, token, logout } = useAuth();
  const router = useRouter();

  const [firstName, setFirstName] = useState(user?.firstName || '');
  const [lastName, setLastName] = useState(user?.lastName || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const [isSavingInfo, setIsSavingInfo] = useState(false);
  const [isSavingPass, setIsSavingPass] = useState(false);
  
  const [infoMessage, setInfoMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [passMessage, setPassMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  if (!user) {
    if (typeof window !== 'undefined') router.push('/login');
    return null;
  }

  const handleUpdateInfo = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingInfo(true);
    setInfoMessage(null);
    try {
      const res = await fetch(`${API_URL}/users/profile`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ firstName, lastName })
      });
      
      if (!res.ok) throw new Error("Erreur de mise à jour");
      
      // Update local storage user (minimalistic refresh approach)
      const updatedUser = { ...user, firstName, lastName };
      localStorage.setItem('tk_user', JSON.stringify(updatedUser));
      
      setInfoMessage({ type: 'success', text: 'Informations mises à jour avec succès. Veuillez vous reconnecter pour voir les changements partout.' });
    } catch (err: any) {
      setInfoMessage({ type: 'error', text: err.message || 'Erreur lors de la mise à jour' });
    } finally {
      setIsSavingInfo(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword) return;
    
    setIsSavingPass(true);
    setPassMessage(null);
    try {
      const res = await fetch(`${API_URL}/users/password`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ currentPassword, newPassword })
      });
      
      if (!res.ok) throw new Error("Mot de passe actuel incorrect ou erreur serveur");
      
      setPassMessage({ type: 'success', text: 'Mot de passe mis à jour !' });
      setCurrentPassword('');
      setNewPassword('');
    } catch (err: any) {
      setPassMessage({ type: 'error', text: err.message || 'Erreur lors du changement de mot de passe' });
    } finally {
      setIsSavingPass(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 py-12 px-6">
      <div className="max-w-4xl mx-auto space-y-8">
        
        <div className="flex items-center gap-4 mb-8">
          <div className="h-16 w-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold">
            {user.firstName ? user.firstName[0].toUpperCase() : user.email[0].toUpperCase()}
          </div>
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white">Mon Profil</h1>
            <p className="text-slate-500 dark:text-slate-400">Gérez vos informations personnelles et votre sécurité.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Informations Personnelles */}
          <Card className="rounded-3xl border-slate-200 dark:border-slate-800 shadow-sm">
            <CardContent className="p-6">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                <User className="h-5 w-5 text-blue-500" />
                Informations Personnelles
              </h2>

              <form onSubmit={handleUpdateInfo} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email</label>
                  <div className="flex items-center gap-3 px-4 py-3 bg-slate-100 dark:bg-slate-800/50 rounded-xl text-slate-500">
                    <Mail className="h-5 w-5" />
                    {user.email}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Prénom</label>
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nom</label>
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition"
                  />
                </div>

                {infoMessage && (
                  <div className={`p-3 rounded-xl flex items-center gap-2 text-sm ${infoMessage.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                    {infoMessage.type === 'success' ? <CheckCircle2 className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
                    {infoMessage.text}
                  </div>
                )}

                <Button type="submit" disabled={isSavingInfo} className="w-full rounded-xl bg-blue-600 hover:bg-blue-700 h-12">
                  {isSavingInfo ? <Loader2 className="h-5 w-5 animate-spin" /> : <Save className="h-5 w-5 mr-2" />}
                  Enregistrer les modifications
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Sécurité */}
          <Card className="rounded-3xl border-slate-200 dark:border-slate-800 shadow-sm">
            <CardContent className="p-6">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                <Lock className="h-5 w-5 text-indigo-500" />
                Sécurité & Mot de passe
              </h2>

              <form onSubmit={handleUpdatePassword} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Mot de passe actuel</label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nouveau mot de passe</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition"
                    required
                  />
                </div>

                {passMessage && (
                  <div className={`p-3 rounded-xl flex items-center gap-2 text-sm ${passMessage.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                    {passMessage.type === 'success' ? <CheckCircle2 className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
                    {passMessage.text}
                  </div>
                )}

                <Button type="submit" disabled={isSavingPass || !currentPassword || !newPassword} className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-700 h-12">
                  {isSavingPass ? <Loader2 className="h-5 w-5 animate-spin" /> : <Lock className="h-5 w-5 mr-2" />}
                  Mettre à jour le mot de passe
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
