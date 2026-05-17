/**
 * This is not a production server yet!
 * This is only a minimal backend to get started.
 */

import { Logger } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app/app.module';
import { RedisIoAdapter } from './app/redis-io.adapter';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const globalPrefix = 'api';
  app.setGlobalPrefix(globalPrefix);
  
  // Activer CORS pour permettre au Frontend (Next.js) de se connecter en WebSocket
  app.enableCors({
    origin: '*', // En prod, mettre l'URL du frontend
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS',
    credentials: true,
  });

  // NOUVEAU : Initialisation de l'adaptateur Redis pour le scaling Socket.io
  const redisIoAdapter = new RedisIoAdapter(app);
  await redisIoAdapter.connectToRedis();
  app.useWebSocketAdapter(redisIoAdapter);

  // Le port 3004 sera dédié au Virtual Lab Service
  const port = process.env.PORT || 3004;
  await app.listen(port);
  Logger.log(
    `🚀 Virtual Lab Service is running on: http://localhost:${port}/${globalPrefix}`
  );
}

bootstrap();
