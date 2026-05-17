import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { VirtualLabGateway } from './virtual-lab.gateway';

@Module({
  imports: [],
  controllers: [AppController],
  providers: [AppService, VirtualLabGateway],
})
export class AppModule {}
