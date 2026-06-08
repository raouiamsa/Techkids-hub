import * as nodemailer from 'nodemailer';
import { Injectable, Logger } from '@nestjs/common';

@Injectable()
export class AdminEmailService {
    private readonly logger = new Logger(AdminEmailService.name);
    private transporter?: nodemailer.Transporter;

    constructor() {
        const host = process.env.SMTP_HOST;

        if (host) {
            this.transporter = nodemailer.createTransport({
                host,
                port: parseInt(process.env.SMTP_PORT || '587'),
                auth: {
                    user: process.env.SMTP_USER,
                    pass: process.env.SMTP_PASS,
                },
            });
            this.logger.log(`📧  SMTP configuré (Admin) : ${host}`);
        } else {
            this.logger.warn('⚠️  SMTP non configuré (Admin) — Emails affichés dans le terminal');
        }
    }

    async sendTeacherCredentials(email: string, firstName: string, plainPassword: string): Promise<void> {
        if (!this.transporter) {
            this.logger.log(`[DEV] Email prof pour ${email} | Mdp: ${plainPassword}`);
            return;
        }

        await this.transporter.sendMail({
            from: `"TechKids Hub" <${process.env.SMTP_FROM || process.env.SMTP_USER}>`,
            to: email,
            subject: '[TechKids] Bienvenue dans l\'équipe pédagogique !',
            html: `
        <div style="font-family: 'Segoe UI', sans-serif; max-width: 480px; margin: 0 auto;
                    padding: 32px; background: #f8f8ff; border-radius: 16px;">
          <div style="text-align: center; margin-bottom: 24px;">
            <h2 style="color: #0d9488; margin: 0;">&lt;/&gt; TechKids Hub</h2>
            <p style="color: #555; margin-top: 8px;">Espace Enseignant</p>
          </div>

          <p style="color: #333;">Bonjour <strong>${firstName}</strong>,</p>
          <p style="color: #333;">L'administrateur vous a créé un compte professeur sur la plateforme TechKids Hub.</p>
          <p style="color: #333;">Voici vos identifiants de connexion temporaires :</p>

          <div style="text-align: center; padding: 20px;
                      background: #fff; border-radius: 12px;
                      border: 2px solid #0d9488; color: #333;
                      margin: 20px 0; box-shadow: 0 4px 12px rgba(13,148,136,0.15);">
            <p style="margin: 0; font-size: 16px;">Email : <strong>${email}</strong></p>
            <p style="margin: 10px 0 0 0; font-size: 16px;">Mot de passe : <strong style="color: #0d9488;">${plainPassword}</strong></p>
          </div>

          <p style="color: #666; font-size: 14px; text-align: center;">
            Nous vous conseillons de changer ce mot de passe dès votre première connexion via l'onglet Profil.
          </p>

          <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">

          <p style="color: #aaa; font-size: 12px; text-align: center;">
            Ce message est généré automatiquement par TechKids Hub.
          </p>
        </div>
      `,
        });

        this.logger.log(`Email d'invitation prof envoyé à ${email}`);
    }
}
