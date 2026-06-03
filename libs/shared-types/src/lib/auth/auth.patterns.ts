// Patterns TCP pour l'auth-service
export const AUTH_PATTERNS = {
    REGISTER: { cmd: 'auth.register' },
    LOGIN: { cmd: 'auth.login' },
    VERIFY_EMAIL: { cmd: 'auth.verify-email' },
    RESEND_VERIFICATION: { cmd: 'auth.resend-verification' },
    FORGOT_PASSWORD: { cmd: 'auth.forgot-password' },
    RESET_PASSWORD: { cmd: 'auth.reset-password' },
} as const;
