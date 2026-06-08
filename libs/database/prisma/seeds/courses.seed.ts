/**
 * seeds/courses.seed.ts
 * Création des données de test détaillées (Rich Content Ready).
 * Cours testables de bout-en-bout (Code Challenges fonctionnels).
 */

import { PrismaClient, CourseLevel, ExerciseType } from '@prisma/client';

const coursesData = [
    {
        title: 'Apprendre Python en s\'amusant',
        description: "Découverte de Python pas à pas ! Des variables aux conditions, deviens un as du code.",
        level: CourseLevel.BEGINNER,
        language: 'python',
        placementBank: [],
        certificationBank: [],
        finalProject: {
            title: "Créer un calculateur magique",
            description: "Applique tout ce que tu as appris pour créer un calculateur qui demande l'âge de l'utilisateur et lui dit s'il est majeur.",
            steps: ["Créer la variable age", "Utiliser input() pour lire la valeur", "Faire un if/else pour afficher le bon message"],
            solution: "age = 18\nif age >= 18:\n    print('Majeur')\nelse:\n    print('Mineur')"
        },
        modules: [
            {
                title: 'Variables et Affichage',
                order: 1,
                content: '# Variables et Affichage\n\nEn Python, on utilise `print()` pour afficher du texte et on peut stocker des informations dans des *variables*.',
                exercises: [
                    {
                        title: 'Quiz : La fonction magique',
                        instructions: 'Quelle fonction utilise-t-on en Python pour afficher du texte à l\'écran ?',
                        exerciseType: ExerciseType.QUIZ,
                        options: ["echo()", "print()", "show()", "display()"],
                        solution: "print()",
                    },
                    {
                        title: 'Défi : Ton premier message',
                        instructions: 'Écris un programme Python qui affiche exactement le message "Bonjour le monde !". Attention aux majuscules et à l\'orthographe.',
                        exerciseType: ExerciseType.CODE_CHALLENGE,
                        solution: 'print("Bonjour le monde !")',
                    },
                ],
            },
            {
                title: 'Conditions et Choix',
                order: 2,
                content: "# Les Conditions\n\nParfois, le programme doit prendre des décisions. C'est le rôle de `if` et `else` !",
                exercises: [
                    {
                        title: 'Quiz : Les comparaisons',
                        instructions: 'Quel symbole utilise-t-on en Python pour vérifier si deux variables sont égales ?',
                        exerciseType: ExerciseType.QUIZ,
                        options: ["=", "==", "===", "=>"],
                        solution: "==",
                    },
                    {
                        title: 'Défi : Majeur ou Mineur ?',
                        instructions: 'Crée une variable `age` égale à 18. Ensuite, utilise `if` pour afficher "Majeur". (Attention à l\'indentation !)',
                        exerciseType: ExerciseType.CODE_CHALLENGE,
                        solution: 'age = 18\nif age >= 18:\n    print("Majeur")',
                    },
                ],
            },
        ],
    },
    {
        title: 'Les Secrets du C++',
        description: 'Plonge dans les fondations de la programmation avec le langage C++. Parfait pour préparer Arduino !',
        level: CourseLevel.INTERMEDIATE,
        language: 'cpp',
        placementBank: [],
        certificationBank: [],
        finalProject: {
            title: "Le Compteur Intelligent",
            description: "Crée un programme C++ complet qui utilise une boucle pour compter de 1 à 5, puis qui affiche 'Terminé !'.",
            steps: ["Déclarer la boucle for", "Afficher chaque nombre", "Afficher Terminé à la fin"],
            solution: "#include <iostream>\nusing namespace std;\nint main() {\n  for(int i=1; i<=5; i++) cout << i << endl;\n  cout << \"Termine !\" << endl;\n  return 0;\n}"
        },
        modules: [
            {
                title: 'Introduction et Syntaxe',
                order: 1,
                content: '# Introduction au C++\n\nEn C++, chaque programme doit contenir une fonction `main()`. Et surtout, chaque instruction se termine par un point-virgule `;` !',
                exercises: [
                    {
                        title: "Quiz : La fin d'une ligne",
                        instructions: "Par quel caractère doit obligatoirement se terminer une instruction en C++ ?",
                        exerciseType: ExerciseType.QUIZ,
                        options: ["Un point (.)", "Deux points (:)", "Un point-virgule (;)", "Une virgule (,)"],
                        solution: "Un point-virgule (;)",
                    },
                    {
                        title: 'Défi : Hello World en C++',
                        instructions: 'Complète ce programme pour qu\'il affiche "Hello" avec cout. N\'oublie pas le std::endl et le point-virgule !',
                        exerciseType: ExerciseType.CODE_CHALLENGE,
                        solution: '#include <iostream>\n\nint main() {\n    std::cout << "Hello" << std::endl;\n    return 0;\n}',
                    },
                ],
            },
            {
                title: 'Mathématiques et Variables',
                order: 2,
                content: '# Les Variables\n\nEn C++, il faut toujours préciser le *type* de la variable (par exemple, `int` pour un entier).',
                exercises: [
                    {
                        title: 'Quiz : Le type des nombres',
                        instructions: "Quel type de variable utilise-t-on pour stocker un nombre entier comme 42 en C++ ?",
                        exerciseType: ExerciseType.QUIZ,
                        options: ["string", "int", "float", "bool"],
                        solution: "int",
                    },
                    {
                        title: 'Défi : Addition',
                        instructions: 'Crée deux variables `int a = 5;` et `int b = 3;`. Affiche leur somme avec cout.',
                        exerciseType: ExerciseType.CODE_CHALLENGE,
                        solution: '#include <iostream>\n\nint main() {\n    int a = 5;\n    int b = 3;\n    std::cout << a + b << std::endl;\n    return 0;\n}',
                    },
                ],
            },
        ],
    },
];

export async function seedCourses(prisma: PrismaClient) {
    console.log('\n── Cours, Modules et Exercices de test (Seed Riche & AI Ready) ──');

    const teacher = await prisma.user.findUnique({ where: { email: 'teacher@techkids.com' } });
    if (!teacher) throw new Error('Teacher introuvable — seedUsers() doit être lancé avant seedCourses()');

    for (const courseData of coursesData) {
        // 1. Créer ou mettre à jour le cours (Idempotency)
        let course = await prisma.course.findFirst({
            where: { title: courseData.title, teacherId: teacher.id },
        });

        if (!course) {
            course = await prisma.course.create({
                data: {
                    title: courseData.title,
                    description: courseData.description,
                    level: courseData.level,
                    isPublished: true,
                    teacherId: teacher.id,
                    language: courseData.language,
                    placementBank: courseData.placementBank,
                    certificationBank: courseData.certificationBank,
                    finalProject: courseData.finalProject
                },
            });
        } else {
            course = await prisma.course.update({
                where: { id: course.id },
                data: {
                    language: courseData.language,
                    placementBank: course.placementBank ?? [],
                    certificationBank: course.certificationBank ?? [],
                    finalProject: course.finalProject ?? courseData.finalProject
                }
            });
        }

        console.log(`\n"${course.title}"`);

        for (const moduleData of courseData.modules) {
            let module = await prisma.module.findFirst({
                where: { title: moduleData.title, courseId: course.id },
            });
            if (!module) {
                module = await prisma.module.create({
                    data: {
                        title: moduleData.title,
                        order: moduleData.order,
                        content: moduleData.content,
                        courseId: course.id,
                    },
                });
            }
            console.log(`Module ${moduleData.order} : "${module.title}"`);

            for (const ex of moduleData.exercises) {
                const existing = await prisma.exercise.findFirst({
                    where: { title: ex.title, moduleId: module.id },
                });
                if (!existing) {
                    await prisma.exercise.create({
                        data: {
                            title: ex.title,
                            instructions: ex.instructions,
                            exerciseType: ex.exerciseType,
                            options: (ex as any).options || [],
                            solution: ex.solution,
                            moduleId: module.id,
                        },
                    });
                } else {
                    await prisma.exercise.update({
                        where: { id: existing.id },
                        data: {
                            instructions: ex.instructions,
                            options: (ex as any).options || [],
                            solution: ex.solution,
                        }
                    });
                }
            }
        }
    }
}