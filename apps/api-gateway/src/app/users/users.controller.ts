import {
  Controller,
  Get,
  Patch,
  Body,
  Req,
  UseGuards,
  HttpException,
  HttpStatus,
  Post,
  UseInterceptors,
  UploadedFile,
  Delete,
} from '@nestjs/common';
import { ApiBearerAuth, ApiOperation, ApiTags } from '@nestjs/swagger';
import { JwtAuthGuard } from '@org/auth';
import { PrismaService } from '@org/database';
import { UpdateProfileDto } from './dto/update-profile.dto';
import { ChangePasswordDto } from './dto/change-password.dto';
import * as bcrypt from 'bcrypt';
import { FileInterceptor } from '@nestjs/platform-express';
import { diskStorage } from 'multer';
import * as path from 'path';
import * as fs from 'fs';

@ApiTags('Users')
@Controller('users')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class UsersController {
  private readonly UPLOADS_DIR = path.resolve('./uploads');

  constructor(private readonly prisma: PrismaService) {}

  @Get('profile')
  @ApiOperation({ summary: "Récupérer le profil de l'utilisateur connecté" })
  async getProfile(@Req() req: any) {
    const userId = req.user?.userId ?? req.user?.sub;
    if (!userId) throw new HttpException('Utilisateur non authentifié', HttpStatus.UNAUTHORIZED);

    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      include: { profile: true },
    });

    if (!user) throw new HttpException('Utilisateur introuvable', HttpStatus.NOT_FOUND);

    return {
      id: user.id,
      email: user.email,
      role: user.role,
      firstName: user.profile?.firstName,
      lastName: user.profile?.lastName,
      phoneNumber: user.profile?.phoneNumber,
      address: user.profile?.address,
      avatar: user.profile?.avatar ? `/uploads/${user.profile.avatar.replace(/.*[\/\\]/, '')}` : null,
    };
  }

  @Patch('profile')
  @ApiOperation({ summary: "Mettre à jour les informations du profil" })
  async updateProfile(@Req() req: any, @Body() dto: UpdateProfileDto) {
    const userId = req.user?.userId ?? req.user?.sub;
    if (!userId) throw new HttpException('Utilisateur non authentifié', HttpStatus.UNAUTHORIZED);

    const data: any = {};
    if (dto.firstName !== undefined) data.firstName = dto.firstName;
    if (dto.lastName !== undefined) data.lastName = dto.lastName;
    if (dto.phoneNumber !== undefined) data.phoneNumber = dto.phoneNumber;
    if (dto.address !== undefined) data.address = dto.address;

    const profile = await this.prisma.profile.upsert({
      where: { userId },
      update: data,
      create: { userId, ...data },
    });

    return { message: 'Profil mis à jour', profile };
  }

  @Patch('password')
  @ApiOperation({ summary: "Changer le mot de passe (vérifie le mot de passe actuel)" })
  async changePassword(@Req() req: any, @Body() dto: ChangePasswordDto) {
    const userId = req.user?.userId ?? req.user?.sub;
    if (!userId) throw new HttpException('Utilisateur non authentifié', HttpStatus.UNAUTHORIZED);

    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) throw new HttpException('Utilisateur introuvable', HttpStatus.NOT_FOUND);

    const valid = await bcrypt.compare(dto.currentPassword, user.passwordHash);
    if (!valid) throw new HttpException('Mot de passe actuel incorrect', HttpStatus.BAD_REQUEST);

    const newHash = await bcrypt.hash(dto.newPassword, 10);
    await this.prisma.user.update({ where: { id: userId }, data: { passwordHash: newHash } });

    return { message: 'Mot de passe mis à jour avec succès' };
  }

  @Post('avatar')
  @UseInterceptors(
    FileInterceptor('file', {
      storage: diskStorage({
        destination: './uploads',
        filename: (req, file, cb) => {
          const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
          cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
        },
      }),
      limits: { fileSize: 5 * 1024 * 1024 },
    }),
  )
  @ApiOperation({ summary: "Uploader / Mettre à jour l'avatar de l'utilisateur" })
  async uploadAvatar(@Req() req: any, @UploadedFile() file?: Express.Multer.File) {
    const userId = req.user?.userId ?? req.user?.sub;
    if (!userId) throw new HttpException('Utilisateur non authentifié', HttpStatus.UNAUTHORIZED);
    if (!file) throw new HttpException('Fichier manquant', HttpStatus.BAD_REQUEST);

    const filename = path.basename(file.path);

    const profile = await this.prisma.profile.upsert({
      where: { userId },
      update: { avatar: filename },
      create: { userId, firstName: '', lastName: '', avatar: filename },
    });

    return { message: 'Avatar enregistré', avatarUrl: `/uploads/${filename}`, profile };
  }

  @Delete('avatar')
  @ApiOperation({ summary: "Supprimer l'avatar de l'utilisateur" })
  async deleteAvatar(@Req() req: any) {
    const userId = req.user?.userId ?? req.user?.sub;
    if (!userId) throw new HttpException('Utilisateur non authentifié', HttpStatus.UNAUTHORIZED);

    const profile = await this.prisma.profile.findUnique({ where: { userId } });
    if (!profile || !profile.avatar) return { message: 'Aucun avatar à supprimer' };

    const filePath = path.resolve(this.UPLOADS_DIR, profile.avatar);
    if (filePath.startsWith(this.UPLOADS_DIR + path.sep) && fs.existsSync(filePath)) {
      try { fs.unlinkSync(filePath); } catch (e) { /* ignore */ }
    }

    await this.prisma.profile.update({ where: { userId }, data: { avatar: null } });
    return { message: 'Avatar supprimé' };
  }

  @Delete()
  @ApiOperation({ summary: "Supprimer définitivement mon compte" })
  async deleteAccount(@Req() req: any) {
    const userId = req.user?.userId ?? req.user?.sub;
    if (!userId) throw new HttpException('Utilisateur non authentifié', HttpStatus.UNAUTHORIZED);

    const profile = await this.prisma.profile.findUnique({ where: { userId } });
    if (profile?.avatar) {
      const filePath = path.resolve(this.UPLOADS_DIR, profile.avatar);
      if (filePath.startsWith(this.UPLOADS_DIR + path.sep) && fs.existsSync(filePath)) {
        try { fs.unlinkSync(filePath); } catch (e) { /* ignore */ }
      }
    }

    await this.prisma.user.delete({ where: { id: userId } });
    return { message: 'Compte supprimé définitivement' };
  }
}
