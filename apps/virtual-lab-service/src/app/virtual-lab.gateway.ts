import { spawn } from 'child_process';
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

  @SubscribeMessage('code-draft')
  handleCodeDraft(
    @MessageBody() data: { room: string; code: string },
    @ConnectedSocket() client: Socket
  ) {
    client.volatile.to(data.room).emit('code-update', data.code);
  }

  // --- Exécution de code via conteneurs Docker locaux (Sans Piston) ---
  @SubscribeMessage('run-code')
  async handleRunCode(
    @MessageBody() data: { code: string; language: string },
    @ConnectedSocket() client: Socket
  ) {
    this.logger.log(`Demande d'exécution de code (${data.language}) par le client ${client.id}`);

    try {
      const language = data.language.toLowerCase();
      let dockerCmd = '';
      let dockerArgs: string[] = [];

      if (language === 'python') {
        dockerCmd = 'docker';
        dockerArgs = ['run', '--rm', '-i', 'python:3-alpine', 'python', '-'];
      } else if (language === 'c++' || language === 'cpp') {
        dockerCmd = 'docker';
        dockerArgs = ['run', '--rm', '-i', 'gcc:latest', 'sh', '-c', 'cat > main.cpp && g++ main.cpp && ./a.out'];
      } else {
        throw new Error(`Langage non supporté: ${language}`);
      }

      const child = spawn(dockerCmd, dockerArgs);
      
      let output = '';
      let errorOutput = '';

      child.stdout.on('data', (chunk) => { output += chunk.toString(); });
      child.stderr.on('data', (chunk) => { errorOutput += chunk.toString(); });

      child.stdin.write(data.code);
      child.stdin.end();

      child.on('close', (code) => {
        const isError = code !== 0;
        const finalOutput = (output + '\n' + errorOutput).trim() || 'Exécution terminée sans sortie console.';
        client.emit('run-result', { output: finalOutput, isError });
      });

      child.on('error', (error) => {
        client.emit('run-result', { output: `Erreur d'exécution: ${error.message}`, isError: true });
      });

    } catch (error: any) {
      this.logger.error(`Erreur lors de l'exécution: ${error.message}`);
      client.emit('run-result', {
        output: ` Erreur du serveur d'exécution : ${error.message}`,
        isError: true
      });
    }
  }

  // --- Validation de Circuits (Release 1 - Web Seulement) ---
  @SubscribeMessage('validate-circuit')
  async handleValidateCircuit(
    @MessageBody() data: { exerciseId: string; studentGraph: any },
    @ConnectedSocket() client: Socket
  ) {
    this.logger.log(`Validation logique du circuit pour le client ${client.id}`);
    
    try {
      // 1. Récupération de la solution en BDD (Simulation)
      // Solution exacte attendue : LED(+) → 220Ω → pin13 | LED(-) → GND
      const expectedSolution = {
        connections: [
          // On peut accepter différents ordres, mais restons stricts pour la démo
          { from: "Arduino_Uno_1:Pin13", to: "Resistor_220_1:Borne 1" },
          { from: "Resistor_220_1:Borne 2", to: "LED_Rouge_1:Anode (+)" },
          { from: "Arduino_Uno_1:GND", to: "LED_Rouge_1:Cathode (GND)" }
        ]
      };

      const studentGraph = data.studentGraph;
      
      let result;

      // Vérifier si le circuit est fermé basiquement (pour les alertes simples)
      if (studentGraph.connections.length < 3) {
        result = {
          status: 'error',
          message: 'Ton circuit n\'est pas complet. Vérifie l\'énoncé (LED, Résistance, Pin 13).'
        };
      } else {
        // Validation Stricte par Graph Matching
        let matchCount = 0;
        
        expectedSolution.connections.forEach(expectedConn => {
          const hasMatch = studentGraph.connections.some((studentConn: any) => {
            // studentConn is { from: "Comp:Pin", to: "Comp:Pin" }
            const matchForward = 
              studentConn.from === expectedConn.from &&
              studentConn.to === expectedConn.to;
              
            const matchBackward = 
              studentConn.from === expectedConn.to &&
              studentConn.to === expectedConn.from;

            return matchForward || matchBackward;
          });
          
          if (hasMatch) matchCount++;
        });

        if (matchCount === expectedSolution.connections.length) {
          result = {
            status: 'success',
            message: 'Bravo ! Ton circuit est parfaitement valide.'
          };
        } else {
          result = {
            status: 'error',
            message: 'Oups ! Le câblage est incorrect. Vérifie bien l\'énoncé (Pin 13, Anode, Cathode, Résistance).'
          };
        }
      }
      
      // Renvoi du résultat d'analyse au frontend
      client.emit('circuit-result', result);

    } catch (error: any) {
      this.logger.error(`Erreur Validation Circuit: ${error.message}`);
      client.emit('circuit-result', {
        status: 'error',
        message: `Erreur interne du serveur lors de la validation.`
      });
    }
  }
}
