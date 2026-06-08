import { Controller, Get, Post, Body, Param, Inject, UseGuards, Req, Delete } from '@nestjs/common';
import { ClientProxy } from '@nestjs/microservices';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { firstValueFrom } from 'rxjs';
import { EDU_PATTERNS, CreateCourseDto } from '@org/shared-types';
import { JwtAuthGuard, RolesGuard, Roles } from '@org/auth';
import { UserRole } from '@prisma/client';
import { throwRpcError } from '../shared/rpc-error.helper';

@ApiTags('Edu-Tracker - Courses')
@Controller('courses')
export class CoursesController {
  constructor(@Inject('EDU_SERVICE') private readonly eduClient: ClientProxy) {}

  @Get()
  @ApiOperation({ summary: 'Liste tous les cours publiés (public)' })
  async getPublishedCourses() {
    try {
      return await firstValueFrom(this.eduClient.send(EDU_PATTERNS.COURSES_LIST, {}));
    } catch (err) { throwRpcError(err); }
  }
  @Get('drafts')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles(UserRole.TEACHER)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Liste les cours non publiés (brouillons manuels) pour le TEACHER' })
  async getDraftCourses(@Req() req: any) {
    try {
      return await firstValueFrom(this.eduClient.send(EDU_PATTERNS.COURSES_DRAFTS, req.user.userId));
    } catch (err) { throwRpcError(err); }
  }
  @Get(':id')
  @ApiOperation({ summary: "Détail d'un cours par ID (public)" })
  async getCourseById(@Param('id') id: string) {
    try {
      return await firstValueFrom(this.eduClient.send(EDU_PATTERNS.COURSES_GET, id));
    } catch (err) { throwRpcError(err); }
  }

  @Post()
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles(UserRole.TEACHER)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Créer un cours (TEACHER uniquement)' })
  async createCourse(@Body() data: CreateCourseDto, @Req() req: any) {
    try {
      const payload = { ...data, teacherId: req.user.userId };
      return await firstValueFrom(this.eduClient.send(EDU_PATTERNS.COURSES_CREATE, payload));
    } catch (err) { throwRpcError(err); }
  }

  @Post(':id') // using POST or PATCH, let's stick to PATCH for updates. Wait, nestjs common has Patch. Let me import it.
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles(UserRole.TEACHER)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Mettre à jour un cours (TEACHER uniquement)' })
  async updateCourse(@Param('id') id: string, @Body() data: any) {
    try {
      return await firstValueFrom(this.eduClient.send(EDU_PATTERNS.COURSES_UPDATE, { id, data }));
    } catch (err) { throwRpcError(err); }
  }

  @Delete(':id')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles(UserRole.TEACHER)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Supprimer un cours (TEACHER uniquement)' })
  async deleteCourse(@Param('id') id: string) {
    try {
      return await firstValueFrom(this.eduClient.send(EDU_PATTERNS.COURSES_DELETE, id));
    } catch (err) { throwRpcError(err); }
  }
}
