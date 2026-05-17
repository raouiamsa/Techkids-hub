import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayConnection,
  OnGatewayDisconnect,
  MessageBody,
  ConnectedSocket,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { Logger } from '@nestjs/common';

@WebSocketGateway({
  cors: {
    origin: '*',
  },
  // Optimisation PFE : on force le transport websocket
  transports: ['websocket'],
})
export class VirtualLabGateway
  implements OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer()
  server!: Server;

  private readonly logger = new Logger(VirtualLabGateway.name);

  handleConnection(client: Socket) {
    this.logger.log(` Client connecté: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    this.logger.log(` Client déconnecté: ${client.id}`);
  }

  @SubscribeMessage('join-lab')
  handleJoinLab(
    @MessageBody() data: { exerciseId: string; studentId: string },
    @ConnectedSocket() client: Socket
  ) {
    const room = `lab-${data.exerciseId}-${data.studentId}`;
    client.join(room);
    this.logger.log(`Client ${client.id} a rejoint le lab: ${room}`);
    return { event: 'joined', data: room };
  }

  // Utilisation de volatile (comme discuté pour optimiser la charge)
  @SubscribeMessage('code-draft')
  handleCodeDraft(
    @MessageBody() data: { room: string; code: string },
    @ConnectedSocket() client: Socket
  ) {
    // Dans le vrai PFE, ici on enverra vers Redis pour la sauvegarde de session
    // Pour l'instant, on broadcast "volatile" à ceux dans la room (le tuteur IA par ex)
    client.volatile.to(data.room).emit('code-update', data.code);

    // Log réduit pour éviter de spammer la console à chaque frappe
    // this.logger.log(`Draft reçu pour ${data.room} (Volatile)`);
  }

  @SubscribeMessage('ask-tutor')
  async handleAskTutor(
    @MessageBody() data: { room: string; code: string; question: string; instructions: string },
    @ConnectedSocket() client: Socket
  ) {
    this.logger.log(`Demande d'aide IA Socratique dans la room ${data.room}`);

    try {
      // Appel HTTP vers le cerveau IA (Python FastAPI sur le port 8000)
      const response = await fetch('http://127.0.0.1:8000/tutor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: data.code,
          question: data.question,
          language: 'python', // TODO: Rendre dynamique si on ajoute d'autres langages
          exercise_instructions: data.instructions || 'Aide l\'enfant à corriger son code.',
        }),
      });

      if (!response.ok) {
        throw new Error('Erreur de connexion avec le cerveau IA');
      }

      const result = (await response.json()) as { reply: string };

      // Renvoi de la réponse Socratique générée par LangChain/Groq
      client.emit('tutor-reply', ` Tuteur: ${result.reply}`);

    } catch (error: any) {
      this.logger.error(`Erreur Socratique: ${error.message}`);
      client.emit('tutor-reply', ' Tuteur: Mince, j\'ai eu un moment d\'inattention. Peux-tu répéter ?');
    }
  }

  // --- NOUVEAU : Exécution de code via Piston API ---
  @SubscribeMessage('run-code')
  async handleRunCode(
    @MessageBody() data: { code: string; language: string },
    @ConnectedSocket() client: Socket
  ) {
    this.logger.log(`Demande d'exécution de code (${data.language}) par le client ${client.id}`);

    try {
      // 1. Appel à l'API Piston (identique à la logique de validator.py)
      const response = await fetch('https://emkc.org/api/v2/piston/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language: data.language.toLowerCase(),
          version: '*', // Prendre la dernière version du langage
          files: [{ content: data.code }],
        }),
      });

      if (!response.ok) {
        throw new Error(`Piston API Error: ${response.statusText}`);
      }

      const result = (await response.json()) as any;

      // 2. Formatage du résultat (on récupère stdout ou stderr)
      const output = result.run?.stdout || result.run?.stderr || 'Exécution terminée sans sortie console.';
      const isError = result.run?.code !== 0;

      // 3. Renvoi du résultat au client
      client.emit('run-result', { output, isError });

    } catch (error: any) {
      this.logger.error(`Erreur lors de l'exécution Piston: ${error.message}`);
      client.emit('run-result', {
        output: ` Erreur du serveur d'exécution : ${error.message}`,
        isError: true
      });
    }
  }

  // --- NOUVEAU : Simulation de Circuits avec PySpice ---
  @SubscribeMessage('simulate-circuit')
  async handleSimulateCircuit(
    @MessageBody() data: { room: string; components: any[] },
    @ConnectedSocket() client: Socket
  ) {
    this.logger.log(`Demande de simulation de circuit par le client ${client.id}`);
    try {
      const response = await fetch('http://127.0.0.1:8000/simulate-circuit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ components: data.components }),
      });

      if (!response.ok) {
        throw new Error('Erreur de connexion avec le simulateur IA');
      }

      const result = await response.json();
      client.emit('circuit-result', result);
    } catch (error: any) {
      this.logger.error(`Erreur Simulation Circuit: ${error.message}`);
      client.emit('circuit-result', {
        status: 'error',
        message: `Erreur du serveur : ${error.message}`
      });
    }
  }
}
