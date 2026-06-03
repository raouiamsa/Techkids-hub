import Link from 'next/link';
import Image from 'next/image';
import {
  ArrowRight,
  BadgeCheck,
  BookOpen,
  CircuitBoard,
  ChevronRight,
  GraduationCap,
  Rocket,
  ShieldCheck,
  Sparkles,
  Users,
  Zap,
} from 'lucide-react';

const pillars = [
  {
    title: 'Parcours guidés',
    description: 'Des modules courts, concrets et progressifs pour apprendre sans se perdre.',
    icon: BookOpen,
    accent: 'from-sky-500 to-cyan-400',
  },
  {
    title: 'Atelier collectif',
    description: 'Des défis à deux, des projets d’équipe et des retours visuels pour rester motivé.',
    icon: Users,
    accent: 'from-indigo-500 to-violet-400',
  },
  {
    title: 'Repères rassurants',
    description: 'Un suivi simple pour les parents, avec des jalons clairs et des résultats visibles.',
    icon: ShieldCheck,
    accent: 'from-amber-500 to-orange-400',
  },
];

const milestones = [
  {
    step: '01',
    title: 'On découvre',
    text: 'L’enfant suit une intro ultra visuelle avec des objectifs très courts.',
  },
  {
    step: '02',
    title: 'On construit',
    text: 'Chaque séance produit quelque chose de concret: une carte, un montage, un résultat.',
  },
  {
    step: '03',
    title: 'On partage',
    text: 'Le projet final devient une petite vitrine fière à montrer à la famille.',
  },
];

function HeroScene() {
  return (
    <div className="hero-float relative mx-auto w-full max-w-[720px]">
      <div className="absolute -inset-6 rounded-[2rem] bg-gradient-to-br from-sky-500/12 via-indigo-500/8 to-violet-500/12 blur-3xl" />

      <div className="relative overflow-hidden rounded-[2rem] border border-white/70 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl shadow-[0_30px_80px_-30px_rgba(15,23,42,0.45)] hero-glow">
        <div className="relative">
          <div className="relative h-[420px] sm:h-[520px] lg:h-[640px]">
            <Image src="/hero-techkids.png" alt="Enfants construisant un robot dans un atelier TechKids Hub" fill className="object-cover" priority />

            <div className="absolute inset-0 bg-gradient-to-t from-black/35 via-transparent to-transparent" />

            <div className="absolute left-5 top-5 flex flex-wrap gap-2 sm:left-6 sm:top-6">
              <span className="animate-float-slow rounded-full bg-white px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-slate-900 shadow-xl shadow-black/20 ring-1 ring-black/5">                Code
              </span>
              <span className="animate-float-medium rounded-full bg-sky-100/95 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-sky-800 shadow-lg shadow-sky-900/10 backdrop-blur-sm">
                IA
              </span>
              <span className="animate-float-slow rounded-full bg-indigo-100/95 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-indigo-800 shadow-lg shadow-indigo-900/10 backdrop-blur-sm">
                Web
              </span>
              <span className="animate-float-medium rounded-full bg-emerald-100/95 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-emerald-800 shadow-lg shadow-emerald-900/10 backdrop-blur-sm">
                Data
              </span>
            </div>
          

            <div className="absolute right-5 bottom-5 flex flex-wrap justify-end gap-2 sm:right-6 sm:bottom-6">
              <span className="animate-float-medium rounded-full bg-white/90 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-slate-900 shadow-lg shadow-black/10 backdrop-blur-sm">
                Robotique
              </span>
              <span className="animate-float-slow rounded-full bg-amber-100/95 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-amber-800 shadow-lg shadow-amber-900/10 backdrop-blur-sm">
                Électronique
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen overflow-hidden bg-[#f7f8fc] font-sans text-slate-900 selection:bg-sky-500/30 dark:bg-slate-950 dark:text-white">
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-white/70 bg-white/70 backdrop-blur-2xl dark:border-slate-800/80 dark:bg-slate-950/70">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 via-blue-500 to-indigo-600 text-white shadow-lg shadow-sky-500/20">
              <Zap className="h-4 w-4" fill="currentColor" />
            </div>
            <div>
              <p className="text-sm font-extrabold tracking-tight sm:text-base">TechKids Hub</p>
              <p className="text-[11px] font-medium uppercase tracking-[0.28em] text-slate-400">Apprendre en créant</p>
            </div>
          </Link>

          <div className="hidden items-center gap-8 md:flex">
            <Link href="#pillars" className="text-sm font-medium text-slate-600 transition-colors hover:text-sky-600 dark:text-slate-300 dark:hover:text-sky-400">
              Découvrir
            </Link>
            <Link href="#journey" className="text-sm font-medium text-slate-600 transition-colors hover:text-sky-600 dark:text-slate-300 dark:hover:text-sky-400">
              Le parcours
            </Link>
            <Link href="/courses" className="text-sm font-medium text-slate-600 transition-colors hover:text-sky-600 dark:text-slate-300 dark:hover:text-sky-400">
              Catalogue de cours
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/login" className="rounded-xl px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-900">
              Se connecter
            </Link>
            <Link href="/register" className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-slate-900/15 transition-transform hover:-translate-y-0.5 dark:bg-white dark:text-slate-900">
              Rejoindre
            </Link>
          </div>
        </div>
      </nav>

      <main className="pt-24">
        <section className="relative overflow-hidden px-6 pb-24 pt-14 sm:pb-28 lg:pb-36 lg:pt-20">
          <div className="absolute inset-0 -z-20 bg-[radial-gradient(circle_at_top_left,rgba(56,189,248,0.16),transparent_26%),radial-gradient(circle_at_80%_20%,rgba(99,102,241,0.14),transparent_24%),radial-gradient(circle_at_bottom,rgba(251,191,36,0.10),transparent_28%)]" />
          <div className="absolute inset-0 -z-10 bg-[linear-gradient(to_right,rgba(148,163,184,0.10)_1px,transparent_1px),linear-gradient(to_bottom,rgba(148,163,184,0.10)_1px,transparent_1px)] bg-[size:32px_32px] opacity-70" />

          <div className="mx-auto grid max-w-7xl items-center gap-14 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="max-w-2xl animate-fade-in">
              <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-white/80 px-4 py-2 text-sm font-semibold text-sky-700 shadow-sm shadow-sky-200/30 backdrop-blur dark:border-sky-500/20 dark:bg-sky-500/10 dark:text-sky-300">
                <Rocket className="h-4 w-4" />
                L’atelier numérique pensé pour les enfants curieux
              </div>

              <h1 className="mt-6 text-5xl font-black leading-[1.02] tracking-tight text-slate-950 sm:text-6xl lg:text-7xl dark:text-white">
                Une plateforme qui donne envie de{' '}
                <span className="bg-gradient-to-r from-sky-500 via-blue-500 to-indigo-500 bg-clip-text text-transparent">
                  coder, créer et explorer
                </span>{' '}
                la technologie.
              </h1>

              <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600 sm:text-xl dark:text-slate-300">
                TechKids Hub propose des projets pratiques autour du code, de la robotique, de l'électronique et de l'IA — des expériences tangibles qui développent la curiosité et les compétences techniques.
              </p>

              <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center">
                <Link href="/courses" className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-950 px-7 py-4 text-base font-bold text-white shadow-xl shadow-slate-900/15 transition-transform hover:-translate-y-0.5 dark:bg-white dark:text-slate-950">
                  Explorer le catalogue
                  <ChevronRight className="h-5 w-5" />
                </Link>
                <Link href="/register" className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-7 py-4 text-base font-bold text-slate-900 shadow-sm transition-colors hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-white dark:hover:bg-slate-800">
                  Créer un compte parent
                  <ArrowRight className="h-5 w-5" />
                </Link>
              </div>

              <div className="mt-10 grid max-w-xl grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-3xl border border-white/80 bg-white/85 p-4 shadow-[0_20px_60px_-40px_rgba(15,23,42,0.45)] backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
                  <p className="text-3xl font-black tracking-tight text-slate-950 dark:text-white">+40</p>
                  <p className="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">activités et mini-projets</p>
                </div>
                <div className="rounded-3xl border border-white/80 bg-white/85 p-4 shadow-[0_20px_60px_-40px_rgba(15,23,42,0.45)] backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
                  <p className="text-3xl font-black tracking-tight text-slate-950 dark:text-white">3</p>
                  <p className="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">rythmes d’apprentissage</p>
                </div>
                <div className="rounded-3xl border border-white/80 bg-white/85 p-4 shadow-[0_20px_60px_-40px_rgba(15,23,42,0.45)] backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
                  <p className="text-3xl font-black tracking-tight text-slate-950 dark:text-white">1</p>
                  <p className="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">parcours suivi pour les parents</p>
                </div>
              </div>
            </div>

            <div className="relative">
              <HeroScene />
            </div>
          </div>
        </section>

        <section id="pillars" className="border-y border-slate-200/80 bg-white/70 py-24 backdrop-blur dark:border-slate-800 dark:bg-slate-950/60">
          <div className="mx-auto max-w-7xl px-6">
            <div className="mx-auto mb-14 max-w-2xl text-center">
              <p className="text-sm font-bold uppercase tracking-[0.28em] text-sky-600 dark:text-sky-400">Pourquoi ça donne envie</p>
              <h2 className="mt-4 text-3xl font-black tracking-tight text-slate-950 sm:text-4xl dark:text-white">
                Une expérience plus proche d’un atelier vivant que d’un simple site de cours.
              </h2>
              <p className="mt-4 text-slate-600 dark:text-slate-300">
                On garde la pédagogie, mais on ajoute du relief visuel, des repères simples et des micro-moments de surprise.
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              {pillars.map((pillar) => {
                const Icon = pillar.icon;
                return (
                  <article key={pillar.title} className="group rounded-[2rem] border border-slate-200/80 bg-white p-6 shadow-[0_25px_60px_-35px_rgba(15,23,42,0.35)] transition-transform duration-300 hover:-translate-y-1 dark:border-slate-800 dark:bg-slate-900/80">
                    <div className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${pillar.accent} text-white shadow-lg`}>
                      <Icon className="h-6 w-6" />
                    </div>
                    <h3 className="mt-5 text-xl font-bold text-slate-950 dark:text-white">{pillar.title}</h3>
                    <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">{pillar.description}</p>
                    <div className="mt-6 h-px bg-gradient-to-r from-slate-200 via-slate-200 to-transparent dark:from-slate-700 dark:via-slate-700" />
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section id="journey" className="py-24">
          <div className="mx-auto max-w-7xl px-6">
            <div className="grid gap-10 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
              <div>
                <p className="text-sm font-bold uppercase tracking-[0.28em] text-sky-600 dark:text-sky-400">Le parcours</p>
                <h2 className="mt-4 text-3xl font-black tracking-tight text-slate-950 sm:text-4xl dark:text-white">
                  Trois étapes simples, beaucoup de plaisir visuel, et un vrai résultat à la fin.
                </h2>
                <p className="mt-4 max-w-xl text-slate-600 dark:text-slate-300">
                  L’idée n’est pas d’empiler des blocs, mais d’installer une progression qui rassure les parents et valorise l’enfant à chaque étape.
                </p>

                <div className="mt-8 space-y-4">
                  {milestones.map((milestone) => (
                    <div key={milestone.step} className="flex gap-4 rounded-[1.5rem] border border-slate-200/80 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white dark:bg-white dark:text-slate-950">
                        {milestone.step}
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-slate-950 dark:text-white">{milestone.title}</h3>
                        <p className="mt-1 leading-7 text-slate-600 dark:text-slate-300">{milestone.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="relative">
                <div className="absolute -inset-4 rounded-[2.2rem] bg-gradient-to-br from-sky-500/10 via-indigo-500/10 to-amber-500/10 blur-2xl" />
                <div className="relative rounded-[2rem] border border-slate-200/80 bg-white p-6 shadow-[0_25px_70px_-30px_rgba(15,23,42,0.4)] dark:border-slate-800 dark:bg-slate-900/90">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Tableau de bord</p>
                      <h3 className="mt-1 text-xl font-bold text-slate-950 dark:text-white">Vue d’ensemble</h3>
                    </div>
                    <div className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300">
                      92% de complétion
                    </div>
                  </div>

                  <div className="mt-6 grid gap-4 sm:grid-cols-2">
                    <div className="rounded-[1.5rem] bg-slate-50 p-4 dark:bg-slate-950/60">
                      <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">Projet de la semaine</p>
                      <div className="mt-4 rounded-[1.5rem] bg-gradient-to-br from-slate-950 to-slate-800 p-5 text-white">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs uppercase tracking-[0.18em] text-white/50">Challenge</p>
                            <p className="mt-1 text-lg font-bold">Boîte qui s’allume</p>
                          </div>
                          <div className="rounded-2xl bg-white/10 p-3">
                            <CircuitBoard className="h-5 w-5" />
                          </div>
                        </div>
                        <div className="mt-5 h-2 rounded-full bg-white/10">
                          <div className="h-2 w-[68%] rounded-full bg-gradient-to-r from-sky-400 to-indigo-400" />
                        </div>
                      </div>
                    </div>

                    <div className="rounded-[1.5rem] bg-slate-50 p-4 dark:bg-slate-950/60">
                      <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">Énergie du jour</p>
                      <div className="mt-4 grid grid-cols-2 gap-3">
                        <div className="rounded-2xl bg-sky-100 p-4 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300">
                          <p className="text-2xl font-black">8</p>
                          <p className="mt-1 text-xs font-semibold uppercase tracking-[0.18em]">défis</p>
                        </div>
                        <div className="rounded-2xl bg-amber-100 p-4 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">
                          <p className="text-2xl font-black">4</p>
                          <p className="mt-1 text-xs font-semibold uppercase tracking-[0.18em]">projets</p>
                        </div>
                      </div>

                      <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
                        <p className="font-semibold text-slate-900 dark:text-white">Ambiance atelier</p>
                        <p className="mt-1">Des couleurs franches, des cartes courtes et une progression qu’on voit tout de suite.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="px-6 pb-24">
          <div className="mx-auto max-w-7xl rounded-[2.25rem] border border-slate-200/80 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-6 py-10 text-white shadow-[0_35px_90px_-35px_rgba(15,23,42,0.65)] dark:border-slate-800">
            <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-sky-300/80">Prêt à commencer ?</p>
                <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
                  Un écran qui donne envie d’entrer dedans, pas juste de le regarder.
                </h2>
                <p className="mt-4 max-w-2xl text-slate-300">
                  Le prochain pas est simple: on s’inscrit, on choisit un parcours, et on lance le premier projet sans friction.
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <Link href="/courses" className="inline-flex items-center justify-center gap-2 rounded-2xl bg-white px-6 py-4 text-sm font-bold text-slate-950 transition-transform hover:-translate-y-0.5">
                  Voir les cours
                  <ChevronRight className="h-4 w-4" />
                </Link>
                <Link href="/register" className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/15 bg-white/10 px-6 py-4 text-sm font-bold text-white transition-colors hover:bg-white/15">
                  Créer un compte parent
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
