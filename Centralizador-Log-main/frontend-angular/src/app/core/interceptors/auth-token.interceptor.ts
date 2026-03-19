import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

const sessionStorageKey = 'log-analyzer:auth-session';

interface StoredAuthSession {
    token?: string;
    expiresAt?: string;
}

function readToken(): string {
    if (typeof sessionStorage === 'undefined') {
        return '';
    }

    const raw = sessionStorage.getItem(sessionStorageKey);
    if (!raw) {
        return '';
    }

    try {
        const session = JSON.parse(raw) as StoredAuthSession;
        const expiresAt = Date.parse(session.expiresAt ?? '');
        if (!session.token) {
            sessionStorage.removeItem(sessionStorageKey);
            return '';
        }

        if (!Number.isNaN(expiresAt) && expiresAt <= Date.now()) {
            sessionStorage.removeItem(sessionStorageKey);
            return '';
        }

        return session.token;
    } catch {
        sessionStorage.removeItem(sessionStorageKey);
        return '';
    }
}

function clearSession(): void {
    if (typeof sessionStorage !== 'undefined') {
        sessionStorage.removeItem(sessionStorageKey);
    }
}

function isApiRequest(url: string): boolean {
    return url.includes('/api/');
}

function isPublicAuthRequest(url: string): boolean {
    return url.endsWith('/api/auth/login') || url.endsWith('/api/auth/register');
}

export const authTokenInterceptor: HttpInterceptorFn = (req, next) => {
    const router = inject(Router);
    const token = readToken();
    const shouldAttachToken = !!token && isApiRequest(req.url) && !isPublicAuthRequest(req.url);

    const request = shouldAttachToken
        ? req.clone({
            setHeaders: {
                Authorization: `Bearer ${token}`
            }
        })
        : req;

    return next(request).pipe(
        catchError((error: unknown) => {
            if (
                error instanceof HttpErrorResponse
                && error.status === 401
                && isApiRequest(req.url)
                && !isPublicAuthRequest(req.url)
            ) {
                clearSession();
                const redirectTo = router.url && router.url !== '/login' ? router.url : '/analise';
                void router.navigate(['/login'], {
                    queryParams: redirectTo ? { redirectTo } : undefined
                });
            }

            return throwError(() => error);
        })
    );
};
