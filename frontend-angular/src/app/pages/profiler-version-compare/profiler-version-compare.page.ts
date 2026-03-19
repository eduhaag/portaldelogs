import { CommonModule } from '@angular/common';
import { Component, HostListener, inject } from '@angular/core';
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
    VersionCompareResponse,
    VersionCompareStatusResponse
} from '../../core/models/api.models';
import { BackendApiService } from '../../core/services/backend-api.service';

interface GenericTableItem {
    [key: string]: string | number;
}

interface RecommendationRow {
    recommendation: string;
}

@Component({
    selector: 'app-profiler-version-compare-page',
    standalone: true,
    imports: [CommonModule, PoPageModule, PoWidgetModule, PoButtonModule, PoTableModule, PoLoadingModule],
    templateUrl: './profiler-version-compare.page.html',
    styleUrl: './profiler-version-compare.page.scss'
})
export class ProfilerVersionComparePageComponent {
    private readonly api = inject(BackendApiService);

    protected profilerFile: File | null = null;
    protected versionCompareFile: File | null = null;
    protected profilerResult: ProfilerResponse | null = null;
    protected versionCompareResult: VersionCompareResponse | null = null;
    protected versionCompareStatus: VersionCompareStatusResponse | null = null;
    protected profilerLoading = false;
    protected versionCompareLoading = false;
    protected errorMessage = '';
    protected profilerLoadingMessage = 'Processando arquivo do profiler...';
    protected versionCompareLoadingMessage = 'Processando extrato de versao...';
    protected compactViewport = this.isCompactViewport();

    private readonly desktopProfilerColumns: PoTableColumn[] = [
        { property: 'program', label: 'Programa' },
        { property: 'duration', label: 'Duração' },
        { property: 'calls', label: 'Chamadas' }
    ];

    private readonly compactProfilerColumns: PoTableColumn[] = [
        { property: 'program', label: 'Programa' },
        { property: 'duration', label: 'Duração' }
    ];

    private readonly desktopProfilerModuleColumns: PoTableColumn[] = [
        { property: 'module', label: 'Módulo / fonte' },
        { property: 'calls', label: 'Chamadas', width: '120px' },
        { property: 'time_total_ms', label: 'Tempo total (ms)', width: '150px' },
        { property: 'time_avg_ms', label: 'Tempo médio (ms)', width: '150px' }
    ];

    private readonly compactProfilerModuleColumns: PoTableColumn[] = [
        { property: 'module', label: 'Módulo / fonte' },
        { property: 'time_total_ms', label: 'Tempo total (ms)', width: '150px' }
    ];

    private readonly desktopProfilerIssueColumns: PoTableColumn[] = [
        { property: 'module', label: 'Módulo' },
        { property: 'issues', label: 'Indícios / gargalos' },
        { property: 'calls', label: 'Chamadas', width: '120px' },
        { property: 'time_total_ms', label: 'Tempo total (ms)', width: '150px' }
    ];

    private readonly compactProfilerIssueColumns: PoTableColumn[] = [
        { property: 'module', label: 'Módulo' },
        { property: 'issues', label: 'Indícios / gargalos' }
    ];

    private readonly desktopRecommendationColumns: PoTableColumn[] = [
        { property: 'recommendation', label: 'Recomendação' }
    ];

    private readonly compactRecommendationColumns: PoTableColumn[] = [
        { property: 'recommendation', label: 'Recomendação' }
    ];

    private readonly desktopVersionCompareColumns: PoTableColumn[] = [
        { property: 'programa', label: 'Programa' },
        { property: 'cliente', label: 'Cliente' },
        { property: 'deveria_estar', label: 'Referência' },
        { property: 'fix_encontrada', label: 'Fix' },
        { property: 'diferenca_builds', label: 'Diferença' }
    ];

    private readonly compactVersionCompareColumns: PoTableColumn[] = [
        { property: 'programa', label: 'Programa' },
        { property: 'cliente', label: 'Cliente' },
        { property: 'deveria_estar', label: 'Referência' }
    ];

    constructor() {
        this.profilerLoading = false;
        this.versionCompareLoading = false;
        this.loadVersionCompareStatus();
    }

    @HostListener('window:resize')
    protected onWindowResize(): void {
        this.compactViewport = this.isCompactViewport();
    }

    protected get profilerColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactProfilerColumns : this.desktopProfilerColumns;
    }

    protected get profilerModuleColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactProfilerModuleColumns : this.desktopProfilerModuleColumns;
    }

    protected get profilerIssueColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactProfilerIssueColumns : this.desktopProfilerIssueColumns;
    }

    protected get recommendationColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactRecommendationColumns : this.desktopRecommendationColumns;
    }

    protected get versionCompareColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactVersionCompareColumns : this.desktopVersionCompareColumns;
    }

    protected get profilerRows(): GenericTableItem[] {
        const bottlenecks = this.profilerResult?.top_bottlenecks ?? [];
        return bottlenecks.slice(0, 20).map((item) => ({
            program: this.readValue(item, ['procedure_name', 'program', 'object_name']),
            duration: this.readValue(item, ['total_time', 'duration', 'elapsed_ms']),
            calls: this.readValue(item, ['calls', 'call_count', 'executions'])
        }));
    }

    protected get profilerAnalysis(): ProfilerAnalysisPayload | null {
        return this.profilerResult?.analysis ?? null;
    }

    protected get profilerTopByTimeRows(): GenericTableItem[] {
        return (this.profilerAnalysis?.top_modules_by_time ?? []).slice(0, 15).map((item) => ({
            module: this.readValue(item, ['module']),
            calls: this.readValue(item, ['calls']),
            time_total_ms: this.readValue(item, ['time_total_ms']),
            time_avg_ms: this.readValue(item, ['time_avg_ms'])
        }));
    }

    protected get profilerTopByCallsRows(): GenericTableItem[] {
        return (this.profilerAnalysis?.top_modules_by_calls ?? []).slice(0, 15).map((item) => ({
            module: this.readValue(item, ['module']),
            calls: this.readValue(item, ['calls']),
            time_total_ms: this.readValue(item, ['time_total_ms']),
            time_avg_ms: this.readValue(item, ['time_avg_ms'])
        }));
    }

    protected get profilerProblemRows(): GenericTableItem[] {
        return (this.profilerAnalysis?.problematic_modules ?? []).slice(0, 15).map((item) => ({
            module: this.readValue(item, ['module']),
            issues: Array.isArray(item.issues) ? item.issues.join(' • ') : '-',
            calls: this.readValue(item, ['calls']),
            time_total_ms: this.readValue(item, ['time_total_ms'])
        }));
    }

    protected get recommendationRows(): RecommendationRow[] {
        return (this.profilerAnalysis?.recommendations ?? []).map((recommendation) => ({ recommendation }));
    }

    protected onProfilerSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.profilerFile = input?.files?.item(0) ?? null;
        this.errorMessage = '';
    }

    protected onVersionCompareSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.versionCompareFile = input?.files?.item(0) ?? null;
        this.errorMessage = '';
    }

    protected analyzeProfiler(): void {
        if (!this.profilerFile) {
            this.errorMessage = 'Selecione um arquivo de profiler.';
            return;
        }

        this.profilerLoading = true;
        this.profilerLoadingMessage = 'Processando arquivo do profiler...';
        this.errorMessage = '';

        this.api.analyzeProfiler(this.profilerFile)
            .pipe(finalize(() => (this.profilerLoading = false)))
            .subscribe({
                next: (response) => {
                    this.profilerLoading = false;
                    this.profilerResult = response;
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.profilerLoading = false;
                    this.errorMessage = error.error?.detail ?? 'Falha ao analisar profiler.';
                }
            });
    }

    protected runVersionCompare(): void {
        if (!this.versionCompareFile) {
            this.errorMessage = 'Selecione um extrato para leitura de versão.';
            return;
        }

        this.versionCompareLoading = true;
        this.versionCompareLoadingMessage = 'Processando extrato de versao...';
        this.errorMessage = '';

        this.api.compareVersions(this.versionCompareFile)
            .pipe(finalize(() => (this.versionCompareLoading = false)))
            .subscribe({
                next: (response) => {
                    this.versionCompareLoading = false;
                    this.versionCompareResult = response;
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.versionCompareLoading = false;
                    this.errorMessage = error.error?.detail ?? 'Falha ao executar leitura do extrato de versão.';
                }
            });
    }

    protected reloadVersionIndex(): void {
        this.versionCompareLoading = true;
        this.versionCompareLoadingMessage = 'Atualizando o indice de versoes...';
        this.api.reloadVersionCompare()
            .pipe(finalize(() => (this.versionCompareLoading = false)))
            .subscribe({
                next: (response) => {
                    this.versionCompareLoading = false;
                    this.versionCompareStatus = response;
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.versionCompareLoading = false;
                    this.errorMessage = error.error?.detail ?? 'Falha ao recarregar índice de versões.';
                }
            });
    }

    private loadVersionCompareStatus(): void {
        this.api.getVersionCompareStatus().subscribe({
            next: (response) => {
                this.versionCompareStatus = response;
            },
            error: () => {
                this.versionCompareStatus = null;
            }
        });
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

    private isCompactViewport(): boolean {
        return typeof window !== 'undefined' && window.innerWidth <= 960;
    }
}
