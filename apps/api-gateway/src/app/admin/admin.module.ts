import { Module } from '@nestjs/common';
import { AdminController } from './admin.controller';
import { AdminEmailService } from './admin.email.service';

@Module({
  controllers: [AdminController],
  providers: [AdminEmailService],
})
export class AdminModule {}
