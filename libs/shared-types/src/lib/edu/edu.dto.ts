import { IsString, IsOptional, IsIn, MaxLength, IsUUID, IsNumber, Min, Max, IsNotEmpty } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class CreateCourseDto {
    @ApiProperty({ example: 'Arduino pour débutants' })
    @IsNotEmpty()
    @IsString()
    @MaxLength(100)
    title!: string;

    @ApiPropertyOptional({ example: 'Un cours complet sur Arduino' })
    @IsOptional()
    @IsString()
    description?: string;

    @ApiPropertyOptional({ enum: ['BEGINNER', 'INTERMEDIATE', 'ADVANCED'], default: 'BEGINNER' })
    @IsOptional()
    @IsIn(['BEGINNER', 'INTERMEDIATE', 'ADVANCED'])
    level?: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';

    @ApiPropertyOptional({ example: 'python' })
    @IsOptional()
    @IsString()
    language?: string;
}

export class EnrollDto {
    @ApiProperty({ description: "ID du cours auquel s'inscrire", example: 'uuid-of-course' })
    @IsUUID()
    courseId!: string;

    // Injecté depuis le JWT côté serveur — ne doit PAS être envoyé par le client
    @ApiPropertyOptional({ description: "ID de l'étudiant (injecté depuis JWT)", example: 'uuid-of-student' })
    @IsOptional()
    @IsUUID()
    studentId?: string;
}

export class UpdateProgressionDto {
    @ApiProperty({ description: 'ID du module', example: 'uuid-of-module' })
    @IsUUID()
    moduleId!: string;

    @ApiProperty({ example: 75, description: 'Pourcentage de complétion (0–100)' })
    @IsNumber()
    @Min(0)
    @Max(100)
    completionPercent!: number;

    // Injecté depuis le JWT côté serveur — ne doit PAS être envoyé par le client
    @ApiPropertyOptional({ description: "ID de l'étudiant (injecté depuis JWT)", example: 'uuid-of-student' })
    @IsOptional()
    @IsUUID()
    studentId?: string;
}

export class SubmitExerciseDto {
    @ApiProperty({ description: "ID de l'exercice", example: 'uuid-of-exercise' })
    @IsUUID()
    exerciseId!: string;

    @ApiProperty({ example: "Ma réponse à l'exercice" })
    @IsNotEmpty()
    @IsString()
    answer!: string;

    // Injecté depuis le JWT côté serveur — ne doit PAS être envoyé par le client
    @ApiPropertyOptional({ description: "ID de l'étudiant (injecté depuis JWT)", example: 'uuid-of-student' })
    @IsOptional()
    @IsUUID()
    studentId?: string;
}

export class GetMyProgressDto {
    @ApiProperty({ description: "ID de l'étudiant", example: 'uuid-of-student' })
    @IsUUID()
    studentId!: string;
}

export class UpdateCourseDto {
    @ApiPropertyOptional() @IsOptional() @IsString() @MaxLength(100) title?: string;
    @ApiPropertyOptional() @IsOptional() @IsString() description?: string;
    @ApiPropertyOptional() @IsOptional() @IsIn(['BEGINNER', 'INTERMEDIATE', 'ADVANCED']) level?: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
    @ApiPropertyOptional() @IsOptional() @IsString() language?: string;
    @ApiPropertyOptional() @IsOptional() @IsString() imageUrl?: string;
    @ApiPropertyOptional() @IsOptional() certificationBank?: any;
    @ApiPropertyOptional() @IsOptional() placementBank?: any;
    @ApiPropertyOptional() @IsOptional() finalProject?: any;
    @ApiPropertyOptional() @IsOptional() isPublished?: boolean;
}

export class CreateModuleDto {
    @ApiProperty() @IsNotEmpty() @IsString() title!: string;
    @ApiProperty() @IsNotEmpty() @IsNumber() order!: number;
    @ApiPropertyOptional() @IsOptional() @IsString() content?: string;
    @ApiProperty() @IsUUID() courseId!: string;
}

export class UpdateModuleDto {
    @ApiPropertyOptional() @IsOptional() @IsString() title?: string;
    @ApiPropertyOptional() @IsOptional() @IsNumber() order?: number;
    @ApiPropertyOptional() @IsOptional() @IsString() content?: string;
}

export class CreateExerciseDto {
    @ApiProperty() @IsNotEmpty() @IsString() title!: string;
    @ApiProperty() @IsIn(['QUIZ', 'CIRCUIT_BUILD', 'CODE_CHALLENGE']) exerciseType!: 'QUIZ' | 'CIRCUIT_BUILD' | 'CODE_CHALLENGE';
    @ApiPropertyOptional() @IsOptional() @IsString() content?: string;
    @ApiPropertyOptional() @IsOptional() data?: any;
    @ApiProperty() @IsUUID() moduleId!: string;
}

export class UpdateExerciseDto {
    @ApiPropertyOptional() @IsOptional() @IsString() title?: string;
    @ApiPropertyOptional() @IsOptional() @IsIn(['QUIZ', 'CIRCUIT_BUILD', 'CODE_CHALLENGE']) exerciseType?: 'QUIZ' | 'CIRCUIT_BUILD' | 'CODE_CHALLENGE';
    @ApiPropertyOptional() @IsOptional() @IsString() content?: string;
    @ApiPropertyOptional() @IsOptional() data?: any;
}
