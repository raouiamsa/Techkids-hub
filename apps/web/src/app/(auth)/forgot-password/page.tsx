'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { KeyRound, Mail, ArrowLeft, ShieldCheck, Eye, EyeOff } from 'lucide-react';
import { Button, Input, Label } from '@org/ui-components';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

type Step = 'email' | 'reset';

export default function ForgotPasswordPage() {
    const router = useRouter();
    const [step, setStep] = useState<Step>('email');

    // Étape 1
    const [email, setEmail] = useState('');
    const [loadingEmail, setLoadingEmail] = useState(false);
    const [emailError, setEmailError] = useState('');

    // Étape 2
    const [code, setCode] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loadingReset, setLoadingReset] = useState(false);
    const [resetError, setResetError] = useState('');

    const handleSendCode = async (e: React.FormEvent) => {
        e.preventDefault();
        setEmailError('');
        setLoadingEmail(true);
        try {
            const res = await fetch(`${API_URL}/auth/forgot-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.message || 'Erreur lors de l\'envoi');
            }
            setStep('reset');
        } catch (err: unknown) {
            setEmailError(err instanceof Error ? err.message : 'Erreur inattendue');
        } finally {
            setLoadingEmail(false);
        }
    };

    const handleResetPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setResetError('');

        if (newPassword !== confirmPassword) {
            setResetError('Les mots de passe ne correspondent pas.');
            return;
        }
        if (newPassword.length < 6) {
            setResetError('Le mot de passe doit contenir au moins 6 caractères.');
            return;
        }

        setLoadingReset(true);
        try {
            const res = await fetch(`${API_URL}/auth/reset-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, code, newPassword }),
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.message || 'Code invalide ou expiré');
            }
            router.push('/login?reset=success');
        } catch (err: unknown) {
            setResetError(err instanceof Error ? err.message : 'Erreur inattendue');
        } finally {
            setLoadingReset(false);
        }
    };

    return (
        <>
            {/* Header */}
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
                    {step === 'email' ? (
                        <KeyRound className="w-5 h-5 text-primary" />
                    ) : (
                        <ShieldCheck className="w-5 h-5 text-primary" />
                    )}
                </div>
                <div>
                    <h1 className="text-xl font-bold text-white">
                        {step === 'email' ? 'Mot de passe oublié' : 'Nouveau mot de passe'}
                    </h1>
                    <p className="text-sm text-dark-muted">
                        {step === 'email'
                            ? 'Entrez votre email pour recevoir un code.'
                            : `Code envoyé à ${email}`}
                    </p>
                </div>
            </div>

            {/* Indicateur d'étapes */}
            <div className="flex items-center gap-2 mb-6">
                <div className={`flex-1 h-1.5 rounded-full transition-all ${step === 'email' ? 'bg-primary' : 'bg-primary'}`} />
                <div className={`flex-1 h-1.5 rounded-full transition-all ${step === 'reset' ? 'bg-primary' : 'bg-white/10'}`} />
            </div>

            {/* Étape 1 : Saisie de l'email */}
            {step === 'email' && (
                <form onSubmit={handleSendCode} className="space-y-4">
                    {emailError && (
                        <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                            {emailError}
                        </div>
                    )}

                    <div className="space-y-1.5">
                        <Label htmlFor="email">Adresse email</Label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                            <Input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="vous@exemple.com"
                                required
                                autoComplete="email"
                                className="pl-10 bg-dark-input border-dark-border text-white placeholder-gray-600 focus:ring-primary/50 focus:border-primary"
                            />
                        </div>
                    </div>

                    <Button
                        type="submit"
                        disabled={loadingEmail}
                        className="w-full bg-primary hover:bg-primary-hover shadow-lg shadow-primary/25 mt-2 normal-case tracking-normal font-semibold text-sm rounded-xl h-11"
                    >
                        {loadingEmail ? <span className="spinner" /> : 'Envoyer le code →'}
                    </Button>
                </form>
            )}

            {/* Étape 2 : OTP + nouveau mot de passe */}
            {step === 'reset' && (
                <form onSubmit={handleResetPassword} className="space-y-4">
                    {resetError && (
                        <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                            {resetError}
                        </div>
                    )}

                    <div className="space-y-1.5">
                        <Label htmlFor="code">Code de vérification (6 chiffres)</Label>
                        <Input
                            id="code"
                            type="text"
                            inputMode="numeric"
                            maxLength={6}
                            value={code}
                            onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                            placeholder="123456"
                            required
                            className="bg-dark-input border-dark-border text-white placeholder-gray-600 focus:ring-primary/50 focus:border-primary text-center text-xl tracking-[0.5em] font-bold"
                        />
                    </div>

                    <div className="space-y-1.5">
                        <Label htmlFor="newPassword">Nouveau mot de passe</Label>
                        <div className="relative">
                            <Input
                                id="newPassword"
                                type={showPassword ? 'text' : 'password'}
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                minLength={6}
                                className="pr-10 bg-dark-input border-dark-border text-white placeholder-gray-600 focus:ring-primary/50 focus:border-primary"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                            >
                                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                        </div>
                    </div>

                    <div className="space-y-1.5">
                        <Label htmlFor="confirmPassword">Confirmer le mot de passe</Label>
                        <Input
                            id="confirmPassword"
                            type={showPassword ? 'text' : 'password'}
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                            className="bg-dark-input border-dark-border text-white placeholder-gray-600 focus:ring-primary/50 focus:border-primary"
                        />
                    </div>

                    <div className="flex gap-2 mt-2">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => { setStep('email'); setResetError(''); setCode(''); }}
                            className="flex-1 border-dark-border text-dark-muted hover:text-white rounded-xl h-11 normal-case tracking-normal text-sm"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            Retour
                        </Button>
                        <Button
                            type="submit"
                            disabled={loadingReset}
                            className="flex-1 bg-primary hover:bg-primary-hover shadow-lg shadow-primary/25 normal-case tracking-normal font-semibold text-sm rounded-xl h-11"
                        >
                            {loadingReset ? <span className="spinner" /> : 'Réinitialiser'}
                        </Button>
                    </div>

                    <p className="text-center text-xs text-dark-muted">
                        Pas reçu le code ?{' '}
                        <button
                            type="button"
                            onClick={() => { setStep('email'); setCode(''); setResetError(''); }}
                            className="text-primary hover:text-primary-hover font-medium transition-colors"
                        >
                            Renvoyer
                        </button>
                    </p>
                </form>
            )}

            {/* Lien retour connexion */}
            <p className="text-center text-sm text-dark-muted mt-6">
                <Link href="/login" className="text-primary hover:text-primary-hover font-medium transition-colors flex items-center justify-center gap-1">
                    <ArrowLeft className="w-3 h-3" />
                    Retour à la connexion
                </Link>
            </p>
        </>
    );
}
