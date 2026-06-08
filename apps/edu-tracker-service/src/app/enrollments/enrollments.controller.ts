import { Controller } from '@nestjs/common';
import { MessagePattern, Payload } from '@nestjs/microservices';
import { EnrollmentsService } from './enrollments.service';
import { EDU_PATTERNS } from '@org/shared-types';

@Controller()
export class EnrollmentsController {
  constructor(private readonly enrollmentsService: EnrollmentsService) { }

  @MessagePattern(EDU_PATTERNS.ENROLL)
  async enrollStudent(
    @Payload() data: { studentId: string; courseId: string }
  ) {
    console.log('EDU-SERVICE: ENROLL', data);
    return this.enrollmentsService.enrollStudent(data.studentId, data.courseId);
  }

  @MessagePattern(EDU_PATTERNS.MY_ENROLLMENTS)
  async getMyEnrollments(@Payload() studentId: string) {
    console.log('EDU-SERVICE: MY_ENROLLMENTS', studentId);
    return this.enrollmentsService.getMyEnrollments(studentId);
  }

  @MessagePattern('edu.enrollments.complete')
  async completeEnrollment(@Payload() data: { studentId: string; courseId: string }) {
    console.log('EDU-SERVICE: ENROLL_COMPLETE', data);
    return this.enrollmentsService.completeCourse(data.studentId, data.courseId);
  }
}
