import { Injectable } from '@angular/core';

import { ProfilerResponse } from '../models/api.models';

interface StoredProfilerSession {
    filename: string;
    analyzedAt: string;
    result: ProfilerResponse;
}

@Injectable({ providedIn: 'root' })
export class ProfilerSessionService {
    private readonly storageKey = 'log-analyzer:last-profiler-analysis';
    private memorySession: StoredProfilerSession | null = null;

    save(result: ProfilerResponse, filename: string): void {
        const session: StoredProfilerSession = {
            filename,
            analyzedAt: new Date().toISOString(),
            result
        };

        this.memorySession = session;

        if (typeof sessionStorage !== 'undefined') {
            sessionStorage.setItem(this.storageKey, JSON.stringify(session));
        }
    }

    load(): StoredProfilerSession | null {
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
            const parsed = JSON.parse(raw) as StoredProfilerSession;
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
