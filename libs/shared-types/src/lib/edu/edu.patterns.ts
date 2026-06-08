// Patterns TCP pour l'edu-tracker-service
export const EDU_PATTERNS = {
    // Cours
    COURSES_LIST: { cmd: 'edu.courses.list' },
    COURSES_TEACHER_LIST: { cmd: 'edu.courses.teacher.list' },
    COURSES_GET: { cmd: 'edu.courses.get' },
    COURSES_CREATE: { cmd: 'edu.courses.create' },
    COURSES_UPDATE: { cmd: 'edu.courses.update' },
    COURSES_DELETE: { cmd: 'edu.courses.delete' },
    COURSES_DRAFTS: { cmd: 'edu.courses.drafts' },
    // Modules
    MODULES_LIST: { cmd: 'edu.modules.list' },
    MODULES_GET: { cmd: 'edu.modules.get' },
    MODULES_CREATE: { cmd: 'edu.modules.create' },
    MODULES_UPDATE: { cmd: 'edu.modules.update' },
    MODULES_DELETE: { cmd: 'edu.modules.delete' },
    // Exercices (CRUD)
    EXERCISES_CREATE: { cmd: 'edu.exercises.create' },
    EXERCISES_UPDATE: { cmd: 'edu.exercises.update' },
    EXERCISES_DELETE: { cmd: 'edu.exercises.delete' },
    // Inscriptions
    ENROLL: { cmd: 'edu.enroll' },
    MY_ENROLLMENTS: { cmd: 'edu.enrollments.my' },
    // Progression
    UPDATE_PROGRESS: { cmd: 'edu.progress.update' },
    MY_PROGRESS: { cmd: 'edu.progress.my' },
    CHILD_PROGRESS: { cmd: 'edu.progress.child' }, // Pour les parents (progression enfant)
    // Exercices
    SUBMIT_EXERCISE: { cmd: 'edu.exercise.submit' },
    MY_SUBMISSIONS: { cmd: 'edu.submissions.my' },
    // Brouillons IA (Drafts)
    DRAFTS_CREATE: { cmd: 'edu.drafts.create' },
    DRAFTS_LIST: { cmd: 'edu.drafts.list' },
    DRAFTS_PUBLISH: { cmd: 'edu.drafts.publish' },
    DRAFTS_DELETE: { cmd: 'edu.drafts.delete' },
    // Bibliothèque de Contenus (ContentSources)
    CONTENT_SOURCES_CREATE: { cmd: 'edu.content_sources.create' },
    CONTENT_SOURCES_LIST: { cmd: 'edu.content_sources.list' },
    CONTENT_SOURCES_DELETE: { cmd: 'edu.content_sources.delete' },
    CONTENT_SOURCES_UPDATE_STATUS: { cmd: 'edu.content_sources.update_status' },
} as const;

