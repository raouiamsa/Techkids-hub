import { Controller } from '@nestjs/common';
import { MessagePattern, Payload } from '@nestjs/microservices';
import { CoursesService } from './courses.service';
import { EDU_PATTERNS, CreateCourseDto } from '@org/shared-types';

@Controller()
export class CoursesController {
  constructor(private readonly coursesService: CoursesService) { }

  @MessagePattern(EDU_PATTERNS.COURSES_LIST)
  async getPublishedCourses() {
    return this.coursesService.getPublishedCourses();
  }

  @MessagePattern(EDU_PATTERNS.COURSES_GET)
  async getCourseById(@Payload() id: string) {
    return this.coursesService.getCourseById(id);
  }

  @MessagePattern(EDU_PATTERNS.COURSES_CREATE)
  async createCourse(@Payload() data: CreateCourseDto & { teacherId: string }) {
    return this.coursesService.createCourse(data);
  }

  @MessagePattern(EDU_PATTERNS.COURSES_UPDATE)
  async updateCourse(@Payload() payload: { id: string; data: any }) {
    return this.coursesService.updateCourse(payload.id, payload.data);
  }

  @MessagePattern(EDU_PATTERNS.COURSES_DRAFTS)
  async getDraftCourses(@Payload() teacherId: string) {
    return this.coursesService.getDraftCourses(teacherId);
  }
}
