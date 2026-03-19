import { Injectable } from '@angular/core';

import { LogAnalysisResponse } from '../models/api.models';

interface StoredAnalysisSession {
    filename: string;
    analyzedAt: string;
    result: LogAnalysisResponse;
}

@Injectable({ providedIn: 'root' })
export class AnalysisSessionService {
    private readonly storageKey = 'log-analyzer:last-analysis';
    private memorySession: StoredAnalysisSession | null = null;

    save(result: LogAnalysisResponse, filename: string): void {
        const session: StoredAnalysisSession = {
            filename,
            analyzedAt: new Date().toISOString(),
            result
        };

        this.memorySession = session;

        if (typeof sessionStorage !== 'undefined') {
            sessionStorage.setItem(this.storageKey, JSON.stringify(session));
        }
    }

    load(): StoredAnalysisSession | null {
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
            const parsed = JSON.parse(raw) as StoredAnalysisSession;
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
