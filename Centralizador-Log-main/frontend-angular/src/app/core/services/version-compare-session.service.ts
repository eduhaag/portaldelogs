import { Injectable } from '@angular/core';

import { VersionCompareResponse } from '../models/api.models';

interface StoredVersionCompareSession {
    filename: string;
    analyzedAt: string;
    result: VersionCompareResponse;
}

@Injectable({ providedIn: 'root' })
export class VersionCompareSessionService {
    private readonly storageKey = 'log-analyzer:last-version-compare';
    private memorySession: StoredVersionCompareSession | null = null;

    save(result: VersionCompareResponse, filename: string): void {
        const session: StoredVersionCompareSession = {
            filename,
            analyzedAt: new Date().toISOString(),
            result
        };

        this.memorySession = session;

        if (typeof sessionStorage !== 'undefined') {
            sessionStorage.setItem(this.storageKey, JSON.stringify(session));
        }
    }

    load(): StoredVersionCompareSession | null {
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
            const parsed = JSON.parse(raw) as StoredVersionCompareSession;
            this.memorySession = parsed;
            return parsed;
        } catch {
            sessionStorage.removeItem(this.storageKey);
            return null;
        }
    }

    clear(): void {
        this.memorySession = null;
        if (typeof sessionStorage !== 'undefined') {
            sessionStorage.removeItem(this.storageKey);
        }
    }
}
