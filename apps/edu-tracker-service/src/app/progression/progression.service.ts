import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '@org/database';
import { SubmitExerciseDto, UpdateProgressionDto } from '@org/shared-types';

@Injectable()
export class ProgressionService {
  constructor(private prisma: PrismaService) {}

  async getMyProgress(studentId: string) {
    return this.prisma.progression.findMany({
      where: { studentId },
      include: {
        module: {
          select: { id: true, title: true, courseId: true },
        },
      },
    });
  }

  async getChildProgress(parentId: string, childId: string) {
    // 1. Verify that 'childId' actually belongs to 'parentId'
    // By convention in the User schema, a student has a 'parentId' linking them to their parent
    const child = await this.prisma.user.findUnique({
      where: { id: childId },
      select: { parentId: true },
    });

    if (!child || child.parentId !== parentId) {
      // Throw access denied HTTP-like error compatible with our handleRpcError
      throw new NotFoundException(`Enfant non trouvé ou n'appartient pas à ce parent`);
    }

    // 2. Return progression (same query as getMyProgress)
    return this.getMyProgress(childId);
  }

  async submitExercise(data: SubmitExerciseDto & { studentId: string }) {
    // 1. Verify exercise exists
    const exercise = await this.prisma.exercise.findUnique({
      where: { id: data.exerciseId },
    });
    if (!exercise) {
      throw new NotFoundException(`Exercise not found`);
    }

    // 2. Évaluation (AI Grading pour le MVP)
    let score = 0;
    if (exercise.exerciseType === 'CODE_CHALLENGE') {
      let executionOutput = "Aucune exécution effectuée.";
      const code = data.answer || "";
      
      try {
        // A. Tenter d'exécuter le code via Piston pour donner du contexte à l'IA
        try {
          // On utilise python par défaut pour tolérer les algorithmes et pseudo-codes
          const pistonRes = await fetch('https://emkc.org/api/v2/piston/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              language: 'python',
              version: '*',
              files: [{ content: code }],
            }),
          });
          if (pistonRes.ok) {
            const pistonData = await pistonRes.json() as any;
            executionOutput = pistonData.run?.stdout || pistonData.run?.stderr || "Exécution réussie sans erreur.";
          } else {
            executionOutput = `Erreur d'exécution: ${pistonRes.statusText}`;
          }
        } catch (e: any) {
          executionOutput = `Erreur Piston: ${e.message}`;
        }

        // B. Demander la correction à l'IA Socratique (ai-brain)
        const aiRes = await fetch('http://127.0.0.1:8000/grade-code', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_code: code,
            execution_output: executionOutput,
            instructions: exercise.instructions || "Évaluer le code.",
          }),
        });

        if (aiRes.ok) {
          const aiData = await aiRes.json() as any;
          score = typeof aiData.score === 'number' ? aiData.score : 0;
          console.log(`IA Grading - Score: ${score}, Feedback: ${aiData.feedback}`);
        } else {
          score = 50; // Score par défaut si le cerveau IA ne répond pas
        }
      } catch (error) {
        console.error("Erreur lors du grading IA (probablement serveur éteint):", error);
        
        // --- Fallback Démo (Sans IA) ---
        // 1. Si on attend une solution exacte et que le code correspond (en ignorant les espaces)
        if (exercise.solution && code.replace(/\s/g, '') === exercise.solution.replace(/\s/g, '')) {
          score = 100;
        } 
        // 2. Si le code s'exécute sans générer d'erreur de syntaxe ou d'exécution
        else if (executionOutput && !executionOutput.toLowerCase().includes("error") && !executionOutput.toLowerCase().includes("erreur")) {
          score = 100;
        } 
        // 3. Sinon, la réponse est fausse
        else {
          score = 0;
        }
      }
    } else if (exercise.exerciseType === 'CIRCUIT_BUILD') {
      try {
        const studentGraph = JSON.parse(data.answer);
        
        // Mock Validation pour Sprint 2 (Même logique que le Gateway)
        const expectedSolution = {
          connections: [
            { from: "Arduino_Uno_1:Pin13", to: "Resistor_220_1:Borne 1" },
            { from: "Resistor_220_1:Borne 2", to: "LED_Rouge_1:Anode (+)" },
            { from: "Arduino_Uno_1:GND", to: "LED_Rouge_1:Cathode (GND)" }
          ]
        };

        if (!studentGraph.connections || studentGraph.connections.length < 3) {
          score = 0;
        } else {
          let matchCount = 0;
          expectedSolution.connections.forEach(expectedConn => {
            const hasMatch = studentGraph.connections.some((studentConn: any) => {
              const matchForward = 
                studentConn.fromComponent === expectedConn.from.split(':')[0] &&
                studentConn.fromPin === expectedConn.from.split(':')[1] &&
                studentConn.toComponent === expectedConn.to.split(':')[0] &&
                studentConn.toPin === expectedConn.to.split(':')[1];
              
              const matchBackward = 
                studentConn.fromComponent === expectedConn.to.split(':')[0] &&
                studentConn.fromPin === expectedConn.to.split(':')[1] &&
                studentConn.toComponent === expectedConn.from.split(':')[0] &&
                studentConn.toPin === expectedConn.from.split(':')[1];

              return matchForward || matchBackward;
            });
            if (hasMatch) matchCount++;
          });
          
          score = matchCount === expectedSolution.connections.length ? 100 : 0;
        }
      } catch (e) {
        score = 0; // JSON invalide ou vide
      }
    } else if (exercise.exerciseType === 'QUIZ') {
      if (exercise.solution && data.answer) {
        // Compare answer exactly (or case-insensitive) to solution
        score = data.answer.trim().toLowerCase() === exercise.solution.trim().toLowerCase() ? 100 : 0;
      } else {
        score = 0;
      }
    } else {
      score = 100; // Default fallback for other potential types
    }
    // 3. Find current attempt count
    const previousSubmissions = await this.prisma.submission.count({
      where: { studentId: data.studentId, exerciseId: data.exerciseId },
    });

    // 4. Create submission
    const submission = await this.prisma.submission.create({
      data: {
        studentId: data.studentId,
        exerciseId: data.exerciseId,
        answer: data.answer,
        score,
        attempt: previousSubmissions + 1,
      },
    });

    // 5. Optionally recalculate module progression here
    await this.recalculateModuleProgression(data.studentId, exercise.moduleId);

    return submission;
  }

  async updateProgress(data: UpdateProgressionDto & { studentId: string }) {
    // Compute status automatically based on percent
    const status =
      data.completionPercent === 0
        ? 'NOT_STARTED'
        : data.completionPercent === 100
          ? 'COMPLETED'
          : 'IN_PROGRESS';

    return this.prisma.progression.upsert({
      where: {
        studentId_moduleId: {
          studentId: data.studentId,
          moduleId: data.moduleId,
        },
      },
      update: {
        completionPercent: data.completionPercent,
        status,
        completedAt: data.completionPercent === 100 ? new Date() : null,
      },
      create: {
        studentId: data.studentId,
        moduleId: data.moduleId,
        completionPercent: data.completionPercent,
        status,
        completedAt: data.completionPercent === 100 ? new Date() : null,
      },
    });
  }

  async getMySubmissionForExercise(studentId: string, exerciseId: string) {
    // Return the last submission for this student+exercise
    return this.prisma.submission.findFirst({
      where: { studentId, exerciseId },
      orderBy: { submittedAt: 'desc' },
      select: {
        id: true,
        answer: true,
        score: true,
        attempt: true,
        submittedAt: true,
      },
    });
  }

  private async recalculateModuleProgression(studentId: string, moduleId: string) {
    // 1. Count total exercises in the module
    const totalExercises = await this.prisma.exercise.count({
      where: { moduleId },
    });

    if (totalExercises === 0) return; // Nothing to calculate

    // 2. Count distinct exercises that the student has submitted at least once
    const submittedExercises = await this.prisma.submission.findMany({
      where: {
        studentId,
        exercise: { moduleId },
      },
      select: { exerciseId: true },
      distinct: ['exerciseId'],
    });

    const solvedCount = submittedExercises.length;

    // 3. Compute progression percentage (rounded to nearest integer)
    const completionPercent = Math.round((solvedCount / totalExercises) * 100);

    // 4. Derive status from the percentage
    const status =
      completionPercent === 0
        ? 'NOT_STARTED'
        : completionPercent === 100
          ? 'COMPLETED'
          : 'IN_PROGRESS';

    // 5. Upsert the Progression record
    await this.prisma.progression.upsert({
      where: {
        studentId_moduleId: { studentId, moduleId },
      },
      update: {
        completionPercent,
        status,
        completedAt: completionPercent === 100 ? new Date() : null,
      },
      create: {
        studentId,
        moduleId,
        completionPercent,
        status,
        completedAt: completionPercent === 100 ? new Date() : null,
      },
    });
  }
}
