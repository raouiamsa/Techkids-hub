import { Controller, Get, UseGuards, Req } from '@nestjs/common';
import { AppService } from './app.service';
import { JwtAuthGuard } from '@org/auth';

@Controller()
export class AppController {
  constructor(private readonly appService: AppService) { }

  // Route PUBLIQUE (accessible sans token)
  @Get()
  getData() {
    return this.appService.getData();
  }

  // Route requiert juste un token valide (tous les rôles)
  @UseGuards(JwtAuthGuard)
  @Get('profile')
  getProfile(@Req() req: any) {
    return { message: ' Connecté !', user: req.user };
  }

}
