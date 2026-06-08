import { Injectable, NotFoundException, Logger } from '@nestjs/common';
import { PrismaService } from '@org/database';
import { CreateCourseDto } from '@org/shared-types';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

@Injectable()
export class CoursesService {
  private readonly logger = new Logger(CoursesService.name);

  constructor(private prisma: PrismaService) {}

  async getPublishedCourses() {
    return this.prisma.course.findMany({
      where: { isPublished: true },
      include: {
        teacher: {
          select: { id: true, email: true, profile: true },
        },
      },
    });
  }

  async getDraftCourses(teacherId: string) {
    return this.prisma.course.findMany({
      where: { 
        isPublished: false,
        teacherId: teacherId 
      },
      include: {
        modules: true
      },
      orderBy: { updatedAt: 'desc' }
    });
  }

  async getCourseById(id: string) {
    const course = await this.prisma.course.findUnique({
      where: { id },
      include: {
        modules: {
          orderBy: { order: 'asc' },
          include: {
            exercises: true,
          },
        },
        teacher: {
          select: { id: true, email: true, profile: true },
        },
      },
    });

    if (!course) {
      throw new NotFoundException(`Course with ID ${id} not found`);
    }

    return course;
  }

  async createCourse(data: CreateCourseDto & { teacherId: string }) {
    // 1. Sauvegarder le cours
    const course = await this.prisma.course.create({
      data: {
        title: data.title,
        description: data.description,
        level: data.level,
        language: data.language, // Nouveau champ ajouté
        teacherId: data.teacherId,
        isPublished: false, // Default to unpublished
      },
    });

    // 2. Automatisation : Si un langage est défini, ordonner à Piston de l'installer en arrière-plan
    if (data.language) {
      this.logger.log(`Langage détecté (${data.language}). Lancement de l'installation silencieuse dans Piston...`);
      execAsync(`docker exec techkids-piston cli packages install ${data.language}`).then(() => {
        this.logger.log(`✅ Langage '${data.language}' installé avec succès dans Piston !`);
      }).catch((err) => {
        this.logger.error(`❌ Échec de l'installation automatique du langage '${data.language}' dans Piston.`, err);
      });
    }

    return course;
  }

  async updateCourse(id: string, data: any) {
    const course = await this.prisma.course.findUnique({ where: { id } });
    if (!course) {
      throw new NotFoundException(`Course with ID ${id} not found`);
    }

    const { modules, ...courseData } = data;

    // Mise à jour du cours et de ses modules/exercices imbriqués
    return this.prisma.course.update({
      where: { id },
      data: {
        ...courseData,
        ...(modules && {
          modules: {
            deleteMany: {}, // Réinitialise les modules existants
            create: modules.map((m: any, index: number) => ({
              title: m.title,
              content: m.content || '',
              order: index,
              exercises: {
                create: (m.exercises || []).map((e: any) => ({
                  title: e.title,
                  instructions: e.instructions || '',
                  exerciseType: e.exerciseType || 'QUIZ',
                  options: e.options || [],
                  solution: e.solution || '',
                })),
              },
            })),
          },
        }),
      },
      include: {
        modules: {
          include: { exercises: true }
        }
      }
    });
  }
}
