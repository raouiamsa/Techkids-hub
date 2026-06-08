import { Controller, Get, Post, Delete, Param, Body, UseGuards, HttpException, HttpStatus } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth, ApiBody } from '@nestjs/swagger';
import { JwtAuthGuard, RolesGuard, Roles } from '@org/auth';
import { UserRole } from '@prisma/client';
import { PrismaService } from '@org/database';
import * as bcrypt from 'bcrypt';
import { AdminEmailService } from './admin.email.service';

@ApiTags('Admin')
@Controller('admin')
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles(UserRole.ADMIN)
@ApiBearerAuth()
export class AdminController {
  constructor(
    private readonly prisma: PrismaService,
    private readonly adminEmailService: AdminEmailService
  ) {}

  @Get('stats')
  @ApiOperation({ summary: 'Obtenir les statistiques globales (ADMIN)' })
  async getStats() {
    const totalUsers = await this.prisma.user.count();
    const totalStudents = await this.prisma.user.count({ where: { role: 'STUDENT' } });
    const totalParents = await this.prisma.user.count({ where: { role: 'PARENT' } });
    const totalTeachers = await this.prisma.user.count({ where: { role: 'TEACHER' } });
    const totalCourses = await this.prisma.course.count();

    return {
      totalUsers,
      totalStudents,
      totalParents,
      totalTeachers,
      totalCourses,
    };
  }

  @Get('users')
  @ApiOperation({ summary: 'Liste de tous les utilisateurs (ADMIN)' })
  async getAllUsers() {
    return await this.prisma.user.findMany({
      select: {
        id: true,
        email: true,
        role: true,
        createdAt: true,
        profile: {
          select: { firstName: true, lastName: true },
        },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  @Delete('users/:id')
  @ApiOperation({ summary: 'Supprimer un utilisateur (ADMIN)' })
  async deleteUser(@Param('id') id: string) {
    const user = await this.prisma.user.findUnique({ where: { id } });
    if (!user) throw new HttpException('Utilisateur introuvable', HttpStatus.NOT_FOUND);
    if (user.role === 'ADMIN') throw new HttpException('Impossible de supprimer un autre administrateur', HttpStatus.FORBIDDEN);

    await this.prisma.user.delete({ where: { id } });
    return { message: 'Utilisateur supprimé avec succès' };
  }

  @Post('teachers/add')
  @ApiOperation({ summary: 'Ajouter un nouveau professeur (ADMIN)' })
  @ApiBody({
    schema: {
      type: 'object',
      properties: {
        email: { type: 'string' },
        firstName: { type: 'string' },
        lastName: { type: 'string' },
      },
    },
  })
  async addTeacher(@Body() body: { email: string; firstName: string; lastName: string }) {
    if (!body.email || !body.firstName || !body.lastName) {
      throw new HttpException('Veuillez fournir un email, prénom et nom', HttpStatus.BAD_REQUEST);
    }

    const existing = await this.prisma.user.findUnique({ where: { email: body.email } });
    if (existing) {
      throw new HttpException('Un compte avec cet email existe déjà', HttpStatus.CONFLICT);
    }

    // Générer un mot de passe aléatoire de 8 caractères
    const randomPassword = Math.random().toString(36).slice(-8);
    const passwordHash = await bcrypt.hash(randomPassword, 10);

    const newTeacher = await this.prisma.user.create({
      data: {
        email: body.email.toLowerCase().trim(),
        passwordHash,
        role: 'TEACHER',
        isEmailVerified: true, // Auto-vérifié car créé par un admin
        profile: {
          create: {
            firstName: body.firstName,
            lastName: body.lastName,
          },
        },
      },
    });

    // Envoi de l'email via le service de messagerie (Mailtrap)
    await this.adminEmailService.sendTeacherCredentials(body.email, body.firstName, randomPassword);

    return {
      message: 'Compte professeur créé. Un email contenant le mot de passe a été envoyé.',
      teacher: { id: newTeacher.id, email: newTeacher.email }
    };
  }
}
