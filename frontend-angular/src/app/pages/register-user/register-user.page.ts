// ===============================
// Componente de Cadastro de Usuário
// Permite ao usuário criar uma nova conta no sistema.
// Demonstra uso de formulários, validação e integração com PO UI.
// Comentários didáticos para facilitar o entendimento!
// ===============================
import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
    PoButtonModule,
    PoFieldModule,
    PoWidgetModule
} from '@po-ui/ng-components';

import { AuthSessionService } from '../../core/services/auth-session.service';

@Component({
    selector: 'app-register-user-page',
    standalone: true,
    imports: [CommonModule, FormsModule, PoWidgetModule, PoButtonModule, PoFieldModule],
    templateUrl: './register-user.page.html',
    styleUrl: './register-user.page.scss'
})
export class RegisterUserPageComponent {
    // Serviço de autenticação para cadastro
    private readonly auth = inject(AuthSessionService);
    // Serviço de navegação entre páginas
    private readonly router = inject(Router);
    // Mensagem de política de senha exibida ao usuário
    private readonly passwordPolicyMessage = 'A senha deve ter no mínimo 8 caracteres, incluindo letra maiúscula, número e caractere especial.';

    // Variáveis de estado protegidas para uso no template
    protected username = '';
    protected email = '';
    protected confirmEmail = '';
    protected password = '';
    protected confirmPassword = '';
    protected errorMessage = '';
    protected successMessage = '';
    protected loading = false;

    // Validação do nome de usuário
    protected get hasValidUsername(): boolean {
        return /^[A-Za-z0-9._-]{3,}$/.test(this.username.trim());
    }

    // Validação do email
    protected get hasValidEmail(): boolean {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.email.trim());
    }

    protected get canRegister(): boolean {
        return !!this.username.trim()
            && !!this.email.trim()
            && !!this.confirmEmail.trim()
            && !!this.password
            && !!this.confirmPassword
            && this.hasValidUsername
            && this.hasValidEmail;
    }

    protected get hasMinLength(): boolean {
        return this.password.length >= 8;
    }

    protected get hasUppercase(): boolean {
        return /[A-ZÀ-Ý]/.test(this.password);
    }

    protected get hasNumber(): boolean {
        return /\d/.test(this.password);
    }

    protected get hasSpecialCharacter(): boolean {
        return /[^A-Za-z0-9]/.test(this.password);
    }

    protected register(): void {
        this.errorMessage = '';
        this.successMessage = '';

        if (!this.username.trim() || !this.email.trim() || !this.confirmEmail.trim() || !this.password || !this.confirmPassword) {
            this.errorMessage = 'Preencha todos os campos para concluir o cadastro.';
            return;
        }

        if (!this.hasValidUsername) {
            this.errorMessage = 'O usuário deve ter ao menos 3 caracteres e usar apenas letras, números, ponto, traço ou sublinhado.';
            return;
        }

        if (!this.hasValidEmail) {
            this.errorMessage = 'Informe um e-mail válido para concluir o cadastro.';
            return;
        }

        if (this.email.trim().toLowerCase() !== this.confirmEmail.trim().toLowerCase()) {
            this.errorMessage = 'A confirmação de e-mail não confere.';
            return;
        }

        if (this.password !== this.confirmPassword) {
            this.errorMessage = 'A confirmação de senha não confere.';
            return;
        }

        if (!this.hasMinLength || !this.hasUppercase || !this.hasNumber || !this.hasSpecialCharacter) {
            this.errorMessage = this.passwordPolicyMessage;
            return;
        }

        this.loading = true;
        this.auth.registerUser({
            displayName: this.username.trim(),
            username: this.username.trim(),
            email: this.email.trim(),
            password: this.password
        }).subscribe((created) => {
            this.loading = false;

            if (!created.success) {
                this.errorMessage = created.message;
                return;
            }

            this.successMessage = 'Usuário cadastrado com sucesso. Faça login para acessar o analisador.';
            this.username = '';
            this.email = '';
            this.confirmEmail = '';
            this.password = '';
            this.confirmPassword = '';
        });
    }

    protected goToLogin(): void {
        void this.router.navigateByUrl('/login');
    }
}
