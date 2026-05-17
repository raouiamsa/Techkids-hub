import { IoAdapter } from '@nestjs/platform-socket.io';
import { ServerOptions } from 'socket.io';
import { createAdapter } from '@socket.io/redis-adapter';
import { createClient } from 'redis';
import { Logger } from '@nestjs/common';

export class RedisIoAdapter extends IoAdapter {
  private adapterConstructor!: ReturnType<typeof createAdapter>;
  private logger = new Logger('RedisIoAdapter');

  async connectToRedis(): Promise<void> {
    const pubClient = createClient({ url: 'redis://localhost:6379' });
    const subClient = pubClient.duplicate();

    pubClient.on('error', (err) => this.logger.error(`Erreur Redis Pub: ${err.message}`));
    subClient.on('error', (err) => this.logger.error(`Erreur Redis Sub: ${err.message}`));

    await Promise.all([pubClient.connect(), subClient.connect()]);

    this.adapterConstructor = createAdapter(pubClient, subClient);
    this.logger.log(' Connecté à Redis Pub/Sub pour Socket.io');
  }

  override createIOServer(port: number, options?: ServerOptions): any {
    const server = super.createIOServer(port, options);

    // On attache l'adaptateur Redis au serveur Socket.io
    if (this.adapterConstructor) {
      server.adapter(this.adapterConstructor);
    } else {
      this.logger.warn(' L\'adaptateur Redis n\'est pas initialisé.');
    }

    return server;
  }
}
