import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { TimeoutError, catchError, throwError, timeout } from 'rxjs';

const API_REQUEST_TIMEOUT_MS = 15000;

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

function isLongRunningApiRequest(url: string): boolean {
    return url.includes('/api/analyze-log')
        || url.includes('/api/analyze-info')
        || url.includes('/api/download-csv')
        || url.includes('/api/version-compare');
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

    const requestStream = isApiRequest(req.url) && !isLongRunningApiRequest(req.url)
        ? next(request).pipe(timeout(API_REQUEST_TIMEOUT_MS))
        : next(request);

    return requestStream.pipe(
        catchError((error: unknown) => {
            if (error instanceof TimeoutError) {
                return throwError(() => new HttpErrorResponse({
                    status: 408,
                    statusText: 'Request Timeout',
                    url: req.url,
                    error: {
                        detail: 'A requisicao demorou mais do que o esperado. Tente novamente em alguns segundos.'
                    }
                }));
            }

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
