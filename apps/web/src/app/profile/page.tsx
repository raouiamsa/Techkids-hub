'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/auth.context';
import { useRouter } from 'next/navigation';
import { Card, CardContent, Button } from '@org/ui-components';
import { User, Lock, Mail, Save, Loader2, CheckCircle2, AlertCircle, Camera, Trash2, ShieldX } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

function buildAvatarUrl(avatarPath?: string | null) {
  if (!avatarPath) return null;
  if (avatarPath.startsWith('http')) return avatarPath;
  // Le backend retourne /uploads/filename
  const base = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api').replace(/\/api\/?$/, '');
  const path = avatarPath.startsWith('/') ? avatarPath : `/${avatarPath}`;
  return `${base}${path}`;
}

export default function ProfilePage() {
  const { user, token, logout, updateUser, isLoading } = useAuth();
  const router = useRouter();

  const [firstName, setFirstName] = useState(user?.firstName || '');
  const [lastName, setLastName] = useState(user?.lastName || '');
  const [phoneNumber, setPhoneNumber] = useState(user?.phoneNumber || '');
  const [address, setAddress] = useState(user?.address || '');
  const [avatarUrl, setAvatarUrl] = useState<string | null>(buildAvatarUrl(user?.avatar));
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const [isSavingInfo, setIsSavingInfo] = useState(false);
  const [isSavingPass, setIsSavingPass] = useState(false);
  
  const [infoMessage, setInfoMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [passMessage, setPassMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_URL}/users/profile`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const data = await res.json();
        setFirstName(data.firstName || '');
        setLastName(data.lastName || '');
        setPhoneNumber(data.phoneNumber || '');
        setAddress(data.address || '');
        setAvatarUrl(buildAvatarUrl(data.avatar));

        const stored = localStorage.getItem('tk_user');
        const parsed = stored ? JSON.parse(stored) : {};
        const merged = { ...parsed, firstName: data.firstName, lastName: data.lastName, avatar: data.avatar, phoneNumber: data.phoneNumber, address: data.address };
        localStorage.setItem('tk_user', JSON.stringify(merged));
      } catch {
        // ignore
      }
    })();
  }, [token]);

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
        body: JSON.stringify({ firstName, lastName, phoneNumber, address })
      });
      
      if (!res.ok) throw new Error("Erreur de mise à jour");
      
      updateUser({ firstName, lastName, phoneNumber, address });
      setInfoMessage({ type: 'success', text: 'Informations mises à jour avec succès !' });
    } catch (err: any) {
      setInfoMessage({ type: 'error', text: err.message || 'Erreur lors de la mise à jour' });
    } finally {
      setIsSavingInfo(false);
    }
  };

  const handleAvatarUpload = async (file?: File) => {
    if (!file) return;
    setInfoMessage(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`${API_URL}/users/avatar`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      });
      if (!res.ok) throw new Error('Erreur upload avatar');
      const data = await res.json();
      // Le backend retourne avatarUrl: '/uploads/filename'
      const newAvatarPath: string = data.avatarUrl || data.profile?.avatar;
      const newAvatarAbsoluteUrl = buildAvatarUrl(newAvatarPath);
      setAvatarUrl(newAvatarAbsoluteUrl);
      updateUser({ avatar: newAvatarPath });
      setInfoMessage({ type: 'success', text: 'Avatar mis à jour.' });
    } catch (err: any) {
      setInfoMessage({ type: 'error', text: err.message || 'Erreur lors de l’upload' });
    }
  };

  const handleDeleteAvatar = async () => {
    if (!confirm('Supprimer votre avatar ?')) return;
    try {
      const res = await fetch(`${API_URL}/users/avatar`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error('Erreur suppression avatar');
      setAvatarUrl(null);
      updateUser({ avatar: undefined });
      setInfoMessage({ type: 'success', text: 'Avatar supprimé.' });
    } catch (err: any) {
      setInfoMessage({ type: 'error', text: err.message || 'Erreur lors de la suppression' });
    }
  };

  const handleAccountDelete = async () => {
    if (!confirm('Cette action supprimera définitivement votre compte. Continuer ?')) return;
    try {
      const res = await fetch(`${API_URL}/users`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error('Erreur lors de la suppression du compte');
      logout();
      router.push('/register');
    } catch (err: any) {
      setInfoMessage({ type: 'error', text: err.message || 'Erreur lors de la suppression du compte' });
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
    <div className="min-h-screen bg-[#f7f8fc] dark:bg-slate-950 pb-20">
      {/* Top Banner */}
      <div className="h-64 w-full bg-[url('https://images.unsplash.com/photo-1557683316-973673baf926?q=80&w=2000&auto=format&fit=crop')] bg-cover bg-center relative">
        <div className="absolute inset-0 bg-gradient-to-b from-black/20 to-black/60" />
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-24 relative z-10">
        <div className="flex flex-col md:flex-row gap-8">
          
          {/* Left Column (Avatar & Quick Info) */}
          <div className="w-full md:w-1/3">
            <Card className="rounded-[2rem] border-white/70 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl shadow-[0_20px_60px_-15px_rgba(15,23,42,0.1)] border-t border-l sticky top-24 overflow-hidden">
              <div className="h-24 bg-gradient-to-br from-sky-400 via-blue-500 to-indigo-600 relative">
                {/* Decorative circles */}
                <div className="absolute -bottom-6 -right-6 w-24 h-24 rounded-full bg-white/20 blur-xl" />
                <div className="absolute top-4 left-4 w-12 h-12 rounded-full bg-white/20 blur-lg" />
              </div>
              <CardContent className="px-6 pb-8 -mt-12 text-center">
                <div className="relative inline-block">
                  <div className="h-28 w-28 rounded-full border-4 border-white dark:border-slate-900 overflow-hidden bg-white shadow-xl mx-auto flex items-center justify-center text-3xl font-black text-indigo-600">
                    {avatarUrl ? (
                      <img src={avatarUrl} alt="avatar" className="h-full w-full object-cover" />
                    ) : (
                      user.firstName ? user.firstName[0].toUpperCase() : user.email[0].toUpperCase()
                    )}
                  </div>
                  <label className="absolute bottom-1 right-1 h-8 w-8 bg-indigo-600 hover:bg-indigo-700 rounded-full text-white flex items-center justify-center shadow-lg cursor-pointer transition-transform hover:scale-110">
                    <Camera className="h-4 w-4" />
                    <input type="file" accept="image/*, .png, .jpg, .jpeg, .gif, .webp" className="hidden" onChange={(e) => {
                      const file = e.target.files?.[0] || null;
                      if (file) handleAvatarUpload(file);
                    }} />
                  </label>
                </div>
                
                <h1 className="mt-4 text-2xl font-black tracking-tight text-slate-900 dark:text-white">
                  {firstName || 'Mon Profil'} {lastName}
                </h1>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mt-1 uppercase tracking-widest">{user.role}</p>

                <div className="mt-6 flex flex-col gap-3">
                  <div className="flex items-center gap-3 px-4 py-3 bg-slate-50 dark:bg-slate-800/50 rounded-2xl text-slate-600 dark:text-slate-300 text-sm font-medium">
                    <Mail className="h-5 w-5 text-slate-400" />
                    <span className="truncate">{user.email}</span>
                  </div>
                  
                  {avatarUrl && (
                    <Button variant="ghost" onClick={handleDeleteAvatar} className="w-full rounded-2xl text-red-600 hover:bg-red-50 hover:text-red-700">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Retirer la photo
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column (Forms) */}
          <div className="w-full md:w-2/3 space-y-6">
            
            {/* Infos Perso */}
            <Card className="rounded-[2rem] border-white/70 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl shadow-[0_20px_60px_-15px_rgba(15,23,42,0.1)] border-t border-l">
              <CardContent className="p-8">
                <div className="flex items-center gap-3 mb-8">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-400">
                    <User className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Informations Personnelles</h2>
                    <p className="text-sm text-slate-500">Mettez à jour vos informations de contact.</p>
                  </div>
                </div>

                <form onSubmit={handleUpdateInfo} className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Prénom</label>
                      <input
                        type="text"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-slate-900 dark:text-white font-medium"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Nom</label>
                      <input
                        type="text"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-slate-900 dark:text-white font-medium"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Téléphone</label>
                      <input
                        type="text"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-slate-900 dark:text-white font-medium"
                        placeholder="+216 20 000 000"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Adresse</label>
                      <input
                        type="text"
                        value={address}
                        onChange={(e) => setAddress(e.target.value)}
                        className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-slate-900 dark:text-white font-medium"
                        placeholder="Votre adresse"
                      />
                    </div>
                  </div>

                  {infoMessage && (
                    <div className={`p-4 rounded-2xl flex items-center gap-3 text-sm font-medium animate-fade-in ${infoMessage.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : 'bg-red-50 text-red-700 border border-red-100'}`}>
                      {infoMessage.type === 'success' ? <CheckCircle2 className="h-5 w-5 shrink-0" /> : <AlertCircle className="h-5 w-5 shrink-0" />}
                      {infoMessage.text}
                    </div>
                  )}

                  <div className="pt-2">
                    <Button type="submit" disabled={isSavingInfo} className="w-full sm:w-auto rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white h-12 px-8 font-bold">
                      {isSavingInfo ? <Loader2 className="h-5 w-5 animate-spin" /> : <Save className="h-5 w-5 mr-2" />}
                      Enregistrer les modifications
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            {/* Sécurité */}
            <Card className="rounded-[2rem] border-white/70 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl shadow-[0_20px_60px_-15px_rgba(15,23,42,0.1)] border-t border-l">
              <CardContent className="p-8">
                <div className="flex items-center gap-3 mb-8">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-400">
                    <Lock className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Sécurité & Mot de passe</h2>
                    <p className="text-sm text-slate-500">Protégez l'accès à votre compte.</p>
                  </div>
                </div>

                <form onSubmit={handleUpdatePassword} className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Mot de passe actuel</label>
                      <input
                        type="password"
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-slate-900 dark:text-white font-medium"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Nouveau mot de passe</label>
                      <input
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-slate-900 dark:text-white font-medium"
                        required
                      />
                    </div>
                  </div>

                  {passMessage && (
                    <div className={`p-4 rounded-2xl flex items-center gap-3 text-sm font-medium animate-fade-in ${passMessage.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : 'bg-red-50 text-red-700 border border-red-100'}`}>
                      {passMessage.type === 'success' ? <CheckCircle2 className="h-5 w-5 shrink-0" /> : <AlertCircle className="h-5 w-5 shrink-0" />}
                      {passMessage.text}
                    </div>
                  )}

                  <div className="pt-2">
                    <Button type="submit" disabled={isSavingPass || !currentPassword || !newPassword} className="w-full sm:w-auto rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white h-12 px-8 font-bold">
                      {isSavingPass ? <Loader2 className="h-5 w-5 animate-spin" /> : <Lock className="h-5 w-5 mr-2" />}
                      Modifier le mot de passe
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            {/* Zone Dangereuse */}
            <Card className="rounded-[2rem] border-red-100 dark:border-red-900/30 bg-red-50/50 dark:bg-red-950/10">
              <CardContent className="p-8 flex flex-col sm:flex-row items-center justify-between gap-6">
                <div>
                  <h3 className="text-lg font-bold text-red-600 dark:text-red-400">Zone dangereuse</h3>
                  <p className="text-sm text-red-600/70 dark:text-red-400/70 mt-1">La suppression du compte est irréversible et efface toutes vos données.</p>
                </div>
                <Button type="button" onClick={handleAccountDelete} className="w-full sm:w-auto shrink-0 rounded-2xl bg-red-100 hover:bg-red-200 text-red-700 dark:bg-red-900/30 dark:hover:bg-red-900/50 dark:text-red-400 font-bold h-12 px-6">
                  <ShieldX className="h-5 w-5 mr-2" />
                  Supprimer le compte
                </Button>
              </CardContent>
            </Card>

          </div>
        </div>
      </div>
    </div>
  );
}
