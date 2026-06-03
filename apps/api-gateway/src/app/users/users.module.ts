import { Module } from '@nestjs/common';
import { UsersController } from './users.controller';
import { DatabaseModule } from '@org/database';

@Module({
  imports: [DatabaseModule],
  controllers: [UsersController],
})
export class UsersModule {}
