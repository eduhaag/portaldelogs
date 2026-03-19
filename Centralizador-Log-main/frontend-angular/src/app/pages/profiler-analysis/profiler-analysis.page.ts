import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import {
    PoButtonModule,
    PoLoadingModule,
    PoPageModule,
    PoTableColumn,
    PoTableModule,
    PoWidgetModule
} from '@po-ui/ng-components';
import { finalize } from 'rxjs';

import {
    ProfilerAnalysisPayload,
    ProfilerResponse,
    ProfilerSummaryItem
} from '../../core/models/api.models';
import { BackendApiService } from '../../core/services/backend-api.service';
import { ProfilerSessionService } from '../../core/services/profiler-session.service';

interface GenericTableItem {
    [key: string]: string | number;
}

interface RecommendationRow {
    recommendation: string;
}

@Component({
    selector: 'app-profiler-analysis-page',
    standalone: true,
    imports: [CommonModule, PoPageModule, PoWidgetModule, PoButtonModule, PoTableModule, PoLoadingModule],
    templateUrl: './profiler-analysis.page.html',
    styleUrl: './profiler-analysis.page.scss'
})
export class ProfilerAnalysisPageComponent implements OnInit {
    private readonly api = inject(BackendApiService);
    private readonly profilerSession = inject(ProfilerSessionService);

    protected profilerFile: File | null = null;
    protected profilerResult: ProfilerResponse | null = null;
    protected profilerLoading = false;
    protected errorMessage = '';
    protected successMessage = '';
    protected analyzedAt = '';
    protected uploadedFilename = '';

    protected readonly profilerColumns: PoTableColumn[] = [
        { property: 'program', label: 'Programa' },
        { property: 'duration', label: 'Duração', width: '160px' },
        { property: 'calls', label: 'Chamadas', width: '120px' }
    ];

    protected readonly profilerModuleColumns: PoTableColumn[] = [
        { property: 'module', label: 'Módulo / fonte' },
        { property: 'calls', label: 'Chamadas', width: '120px' },
        { property: 'totalTimeMs', label: 'Tempo total (ms)', width: '150px' },
        { property: 'avgTimeMs', label: 'Tempo médio (ms)', width: '150px' }
    ];

    protected readonly profilerIssueColumns: PoTableColumn[] = [
        { property: 'module', label: 'Módulo' },
        { property: 'issues', label: 'Indícios / gargalos' },
        { property: 'calls', label: 'Chamadas', width: '120px' },
        { property: 'totalTimeMs', label: 'Tempo total (ms)', width: '150px' }
    ];

    protected readonly profilerCallTreeColumns: PoTableColumn[] = [
        { property: 'name', label: 'Nó / módulo' },
        { property: 'calls', label: 'Chamadas', width: '110px' },
        { property: 'totalTimeMs', label: 'Tempo total (ms)', width: '150px' },
        { property: 'percent', label: '% sessão', width: '110px' },
        { property: 'childrenCount', label: 'Dependências', width: '120px' }
    ];

    protected readonly recommendationColumns: PoTableColumn[] = [
        { property: 'recommendation', label: 'Recomendação / insight' }
    ];

    protected readonly breakdownColumns: PoTableColumn[] = [
        { property: 'label', label: 'Indicador' },
        { property: 'value', label: 'Valor', width: '140px' }
    ];

    ngOnInit(): void {
        this.restoreSession();
    }

    protected get hasResult(): boolean {
        return !!this.profilerResult;
    }

    protected get profilerAnalysis(): ProfilerAnalysisPayload | null {
        return this.profilerResult?.analysis ?? null;
    }

    protected get summaryCards(): Array<{ label: string; value: string | number }> {
        const summary = this.profilerResult?.summary ?? this.profilerAnalysis?.summary ?? {};
        return [
            { label: 'Arquivo', value: this.profilerResult?.filename || this.uploadedFilename || '-' },
            { label: 'Analisado em', value: this.analyzedAt ? this.formatDate(this.analyzedAt) : '-' },
            { label: 'Duração total (ms)', value: Number(summary['total_time_ms'] ?? 0) },
            { label: 'Chamadas', value: Number(summary['total_calls'] ?? 0) },
            { label: 'Bottlenecks', value: this.profilerResult?.top_bottlenecks?.length ?? 0 },
            { label: 'N+1 suspects', value: this.profilerResult?.n_plus_one_suspects?.length ?? 0 }
        ];
    }

    protected get profilerRows(): GenericTableItem[] {
        const bottlenecks = this.profilerResult?.top_bottlenecks ?? [];
        return bottlenecks.slice(0, 20).map((item) => ({
            program: this.readValue(item, ['procedure_name', 'program', 'object_name', 'module']),
            duration: this.readValue(item, ['total_time', 'duration', 'elapsed_ms', 'time_total_ms']),
            calls: this.readValue(item, ['calls', 'call_count', 'executions'])
        }));
    }

    protected get profilerTopByTimeRows(): GenericTableItem[] {
        return this.mapModuleRows(this.profilerAnalysis?.top_modules_by_time ?? []);
    }

    protected get profilerTopByCallsRows(): GenericTableItem[] {
        return this.mapModuleRows(this.profilerAnalysis?.top_modules_by_calls ?? []);
    }

    protected get profilerTopByAvgRows(): GenericTableItem[] {
        return this.mapModuleRows(this.profilerAnalysis?.top_modules_by_avg_time ?? []);
    }

    protected get profilerProblemRows(): GenericTableItem[] {
        return (this.profilerAnalysis?.problematic_modules ?? []).slice(0, 15).map((item) => ({
            module: this.readValue(item, ['module']),
            issues: Array.isArray(item.issues) ? item.issues.join(' • ') : '-',
            calls: this.readValue(item, ['calls']),
            totalTimeMs: this.readValue(item, ['time_total_ms'])
        }));
    }

    protected get profilerCallTreeRows(): GenericTableItem[] {
        const callTree = this.profilerResult?.call_tree ?? this.profilerAnalysis?.call_tree ?? [];
        return callTree.slice(0, 20).map((item) => ({
            name: this.readValue(item, ['name', 'module']),
            calls: this.readValue(item, ['calls']),
            totalTimeMs: this.readValue(item, ['total_time', 'time_total_ms']),
            percent: `${Number(this.readNumericValue(item, ['percent'])).toFixed(2)}%`,
            childrenCount: Array.isArray((item as Record<string, unknown>)['children'])
                ? ((item as Record<string, unknown>)['children'] as unknown[]).length
                : 0
        }));
    }

    protected get profilerCallTreeStatRows(): GenericTableItem[] {
        const stats = this.profilerAnalysis?.call_tree_stats ?? {};
        return [
            { label: 'Relacionamentos', value: Number(stats.total_relationships ?? 0) },
            { label: 'Callers únicos', value: Number(stats.unique_callers ?? 0) },
            { label: 'Callees únicos', value: Number(stats.unique_callees ?? 0) }
        ];
    }

    protected get recommendationRows(): RecommendationRow[] {
        return (this.profilerAnalysis?.recommendations ?? []).map((recommendation) => ({ recommendation }));
    }

    protected onProfilerSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.profilerFile = input?.files?.item(0) ?? null;
        this.errorMessage = '';
        this.successMessage = '';
    }

    protected analyzeProfiler(): void {
        if (!this.profilerFile) {
            this.errorMessage = 'Selecione um arquivo .out para analisar o profiler.';
            return;
        }

        this.profilerLoading = true;
        this.errorMessage = '';
        this.successMessage = '';

        this.api.analyzeProfiler(this.profilerFile)
            .pipe(finalize(() => (this.profilerLoading = false)))
            .subscribe({
                next: (response) => {
                    this.profilerResult = response;
                    this.uploadedFilename = this.profilerFile?.name ?? response.filename;
                    this.analyzedAt = new Date().toISOString();
                    this.profilerSession.save(response, this.uploadedFilename);
                    this.successMessage = 'Profiler analisado e carregado na tela dedicada.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao analisar profiler.';
                }
            });
    }

    protected clearProfilerSession(): void {
        this.profilerSession.clear();
        this.profilerFile = null;
        this.profilerResult = null;
        this.analyzedAt = '';
        this.uploadedFilename = '';
        this.errorMessage = '';
        this.successMessage = '';
    }

    private restoreSession(): void {
        const session = this.profilerSession.load();
        if (!session) {
            return;
        }

        this.profilerResult = session.result;
        this.analyzedAt = session.analyzedAt;
        this.uploadedFilename = session.filename;
    }

    private mapModuleRows(items: ProfilerSummaryItem[]): GenericTableItem[] {
        return items.slice(0, 15).map((item) => ({
            module: this.readValue(item, ['module']),
            calls: this.readValue(item, ['calls']),
            totalTimeMs: this.readValue(item, ['time_total_ms']),
            avgTimeMs: this.readValue(item, ['time_avg_ms'])
        }));
    }

    private readValue(item: object, candidates: string[]): string | number {
        const record = item as Record<string, unknown>;
        for (const key of candidates) {
            const value = record[key];
            if (typeof value === 'number' || typeof value === 'string') {
                return value;
            }
        }

        return '-';
    }

    private readNumericValue(item: object, candidates: string[]): number {
        const record = item as Record<string, unknown>;
        for (const key of candidates) {
            const value = record[key];
            if (typeof value === 'number') {
                return value;
            }

            if (typeof value === 'string') {
                const parsed = Number(value);
                if (!Number.isNaN(parsed)) {
                    return parsed;
                }
            }
        }

        return 0;
    }

    private formatDate(value: string): string {
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? value : date.toLocaleString('pt-BR');
    }
}
