import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import { AuthSessionService } from '../../core/services/auth-session.service';

@Component({
    selector: 'app-login-page',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './login.page.html',
    styleUrl: './login.page.scss'
})
export class LoginPageComponent implements OnInit {
    private readonly auth = inject(AuthSessionService);
    private readonly route = inject(ActivatedRoute);
    private readonly router = inject(Router);
    private readonly rememberedCredentialsKey = 'central-suporte:remembered-credentials';

    protected username = '';
    protected password = '';
    protected rememberPassword = false;
    protected infoMessage = '';
    protected loading = false;
    protected loginErrors: string[] = [];
    protected passwordErrors: string[] = [];
    protected showPassword = false;

    ngOnInit(): void {
        if (this.auth.isAuthenticated()) {
            void this.router.navigateByUrl(this.getRedirectTarget());
            return;
        }

        this.loadRememberedCredentials();
    }

    protected onLoginChange(value: string): void {
        this.username = value;
        this.loginErrors = [];
        this.infoMessage = '';
    }

    protected onPasswordChange(value: string): void {
        this.password = value;
        this.passwordErrors = [];
        this.infoMessage = '';
    }

    protected togglePasswordVisibility(): void {
        this.showPassword = !this.showPassword;
    }

    protected requestNewUser(): void {
        void this.router.navigateByUrl('/novo-usuario');
    }

    protected onRememberPasswordChange(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.rememberPassword = !!input?.checked;

        if (!this.rememberPassword) {
            this.clearRememberedCredentials();
        }
    }

    protected login(): void {
        this.infoMessage = '';
        this.loginErrors = [];
        this.passwordErrors = [];

        const username = this.username.trim();
        const password = this.password;

        if (!username || !password) {
            if (!username) {
                this.loginErrors = ['Informe o usuário para entrar.'];
            }

            if (!password) {
                this.passwordErrors = ['Informe a senha para entrar.'];
            }

            return;
        }

        this.loading = true;
        this.auth.login(username, password).subscribe((result) => {
            this.loading = false;

            if (!result.success) {
                this.passwordErrors = [result.message];
                return;
            }

            this.loginErrors = [];
            this.passwordErrors = [];

            if (this.rememberPassword) {
                this.persistRememberedCredentials();
            } else {
                this.clearRememberedCredentials();
            }

            const redirectTo = this.getRedirectTarget();
            void this.router.navigateByUrl(redirectTo).then((navigated) => {
                if (navigated) {
                    return;
                }

                const fallbackTarget = redirectTo !== '/analise' ? '/analise' : redirectTo;
                void this.router.navigateByUrl(fallbackTarget).then((fallbackNavigated) => {
                    if (!fallbackNavigated && typeof window !== 'undefined') {
                        window.location.assign(fallbackTarget);
                    }
                });
            }).catch(() => {
                if (typeof window !== 'undefined') {
                    window.location.assign('/analise');
                }
            });
        });
    }

    private getRedirectTarget(): string {
        const redirectTo = this.route.snapshot.queryParamMap.get('redirectTo')?.trim();

        if (!redirectTo || !redirectTo.startsWith('/') || redirectTo.startsWith('/login') || redirectTo.startsWith('/novo-usuario')) {
            return '/analise';
        }

        return redirectTo;
    }

    private loadRememberedCredentials(): void {
        if (typeof localStorage === 'undefined') {
            return;
        }

        const raw = localStorage.getItem(this.rememberedCredentialsKey);
        if (!raw) {
            return;
        }

        try {
            const saved = JSON.parse(raw) as { username?: string; password?: string };
            this.username = saved.username ?? '';
            this.password = saved.password ?? '';
            this.rememberPassword = !!this.username || !!this.password;
        } catch {
            this.clearRememberedCredentials();
        }
    }

    private persistRememberedCredentials(): void {
        if (typeof localStorage === 'undefined') {
            return;
        }

        localStorage.setItem(this.rememberedCredentialsKey, JSON.stringify({
            username: this.username.trim(),
            password: this.password
        }));
    }

    private clearRememberedCredentials(): void {
        if (typeof localStorage === 'undefined') {
            return;
        }

        localStorage.removeItem(this.rememberedCredentialsKey);
    }
}
