import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft, Signal, Clock, Users, BookText } from 'lucide-react';
import { CourseEnrolledView } from './course-enrolled-view';
import { Badge } from '@org/ui-components';

// Configuration URL API
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:3000/api';

// Types
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
interface Course {
  id: string;
  title: string;
  description: string;
  level: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
  isPublished: boolean;
  createdAt: string;
  teacherId: string;
  modules?: Module[];
}

// Fetch course details (Server Side)
async function fetchCourseDetails(courseId: string): Promise<Course | null> {
  try {
    const res = await fetch(`${API_URL}/courses/${courseId}`, {
      cache: 'no-store',
    });
    if (!res.ok) {
      if (res.status === 404) return null;
      throw new Error(`Failed to fetch course: ${res.statusText}`);
    }
    return res.json();
  } catch (error) {
    console.error('Error fetching course:', error);
    return null;
  }
}

const LevelBadge = ({ level }: { level: string }) => {
  const map: Record<string, { label: string; variant: 'default' | 'approved' | 'processing' | 'pending' }> = {
    BEGINNER: { label: 'Débutant', variant: 'default' },
    INTERMEDIATE: { label: 'Intermédiaire', variant: 'processing' },
    ADVANCED: { label: 'Avancé', variant: 'pending' },
  };
  const config = map[level] ?? map.BEGINNER;
  return (
    <Badge variant={config.variant} className="px-4 py-1.5 rounded-full text-sm font-medium">
      Niveau {config.label}
    </Badge>
  );
};

export default async function CourseDetailsPage({ params }: { params: Promise<{ courseId: string }> }) {
  const resolvedParams = await params;
  const course = await fetchCourseDetails(resolvedParams.courseId);

  if (!course) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 pb-20">
      {/* Hero Section */}
      <section className="relative px-6 py-20 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 overflow-hidden">
        <div className="absolute top-0 right-0 -mr-40 -mt-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 -ml-40 -mb-20 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl" />

        <div className="relative max-w-5xl mx-auto space-y-6">
          <Link href="/courses" className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-blue-600 transition-colors">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour au catalogue
          </Link>

          <div className="flex flex-wrap items-center gap-3">
            <LevelBadge level={course.level} />
            <span className="inline-flex items-center text-sm text-slate-500 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-full">
              <BookText className="h-4 w-4 mr-2" />
              {course.modules?.length ?? 0} modules
            </span>
          </div>

          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            {course.title}
          </h1>

          {course.description && (
            <p className="max-w-2xl text-lg text-slate-600 dark:text-slate-400">
              {course.description}
            </p>
          )}
        </div>
      </section>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-16">
        <CourseEnrolledView
          courseId={course.id}
          courseTitle={course.title}
          modules={course.modules ?? []}
          sidebar={
            <div className="sticky top-24 space-y-6">
              <div className="bg-white dark:bg-slate-900 p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-bl-[100px] -mr-10 -mt-10" />
                <h3 className="text-sm font-extrabold text-blue-600 dark:text-blue-400 uppercase tracking-widest mb-6">
                  Informations Clés
                </h3>
                <ul className="space-y-5 text-slate-700 dark:text-slate-300 font-medium">
                  <li className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-xl bg-slate-50 dark:bg-slate-800 flex items-center justify-center text-slate-400 shrink-0">
                      <Signal className="h-5 w-5 text-indigo-500" />
                    </div>
                    Niveau {course.level}
                  </li>
                  <li className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-xl bg-slate-50 dark:bg-slate-800 flex items-center justify-center text-slate-400 shrink-0">
                      <Clock className="h-5 w-5 text-blue-500" />
                    </div>
                    À votre rythme
                  </li>
                  <li className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-xl bg-slate-50 dark:bg-slate-800 flex items-center justify-center text-slate-400 shrink-0">
                      <Users className="h-5 w-5 text-emerald-500" />
                    </div>
                    Communauté d'apprenants
                  </li>
                </ul>
              </div>
            </div>
          }
        />
      </div>
    </div>
  );
}
