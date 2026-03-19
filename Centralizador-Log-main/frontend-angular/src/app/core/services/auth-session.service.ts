import { Injectable, inject } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { AuthResponse, AuthUserProfile } from '../models/api.models';
import { BackendApiService } from './backend-api.service';

interface AuthUserSession {
    username: string;
    displayName: string;
    email?: string;
    token: string;
    tokenType: string;
    expiresAt: string;
    authenticatedAt: string;
}

interface AuthActionResult {
    success: boolean;
    message: string;
}

@Injectable({ providedIn: 'root' })
export class AuthSessionService {
    private readonly backendApi = inject(BackendApiService);
    private readonly storageKey = 'log-analyzer:auth-session';
    private memorySession: AuthUserSession | null = null;

    login(username: string, password: string): Observable<AuthActionResult> {
        return this.backendApi.login({ username: username.trim(), password }).pipe(
            map((response) => this.handleLoginResponse(response)),
            catchError((error) => of({ success: false, message: this.extractErrorMessage(error) }))
        );
    }

    registerUser(user: {
        displayName: string;
        username: string;
        email: string;
        password: string;
    }): Observable<AuthActionResult> {
        return this.backendApi.registerUser({
            display_name: user.displayName.trim(),
            username: user.username.trim(),
            email: user.email.trim(),
            password: user.password
        }).pipe(
            map((response) => ({ success: response.success, message: response.message })),
            catchError((error) => of({ success: false, message: this.extractErrorMessage(error) }))
        );
    }

    isAuthenticated(): boolean {
        return !!this.getSession();
    }

    getDisplayName(): string {
        return this.getSession()?.displayName ?? 'Usuário';
    }

    getUsername(): string {
        return this.getSession()?.username ?? '';
    }

    getEmail(): string {
        return this.getSession()?.email ?? '';
    }

    getToken(): string {
        return this.getSession()?.token ?? '';
    }

    logout(): void {
        this.memorySession = null;
        if (typeof sessionStorage !== 'undefined') {
            sessionStorage.removeItem(this.storageKey);
        }
    }

    private persistSession(session: AuthUserSession): void {
        this.memorySession = session;
        if (typeof sessionStorage !== 'undefined') {
            sessionStorage.setItem(this.storageKey, JSON.stringify(session));
        }
    }

    private getSession(): AuthUserSession | null {
        if (this.memorySession) {
            return this.memorySession;
        }

        if (typeof sessionStorage === 'undefined') {
            return null;
        }

        const raw = sessionStorage.getItem(this.storageKey);
        if (!raw) {
            return null;
        }

        try {
            const parsed = JSON.parse(raw) as AuthUserSession;
            if (this.isSessionExpired(parsed)) {
                this.logout();
                return null;
            }
            this.memorySession = parsed;
            return parsed;
        } catch {
            sessionStorage.removeItem(this.storageKey);
            return null;
        }
    }

    private handleLoginResponse(response: AuthResponse): AuthActionResult {
        if (!response.success || !response.user || !response.access_token || !response.expires_at) {
            return { success: false, message: response.message || 'Não foi possível entrar.' };
        }

        this.persistSession(this.createSessionFromResponse(response));
        return { success: true, message: response.message };
    }

    private createSessionFromResponse(response: AuthResponse): AuthUserSession {
        const user = response.user as AuthUserProfile;
        return {
            username: user.username,
            displayName: user.display_name,
            email: user.email,
            token: response.access_token ?? '',
            tokenType: response.token_type ?? 'Bearer',
            expiresAt: response.expires_at ?? new Date().toISOString(),
            authenticatedAt: new Date().toISOString()
        };
    }

    private isSessionExpired(session: AuthUserSession): boolean {
        const expiresAt = Date.parse(session.expiresAt);
        if (Number.isNaN(expiresAt)) {
            return !session.token;
        }

        return expiresAt <= Date.now();
    }

    private extractErrorMessage(error: unknown): string {
        if (error instanceof HttpErrorResponse) {
            const detail = error.error?.detail;
            if (typeof detail === 'string' && detail.trim()) {
                return detail;
            }
        }

        return 'Não foi possível concluir a solicitação.';
    }
}
