import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import {
    PoButtonModule,
    PoDividerModule,
    PoInfoModule,
    PoLoadingModule,
    PoPageModule,
    PoTagModule,
    PoTagType,
    PoTableColumn,
    PoTableModule,
    PoWidgetModule
} from '@po-ui/ng-components';
import { finalize } from 'rxjs';

import {
    ProfilerAnalysisPayload,
    ProfilerIssueItem,
    ProfilerResponse,
    ProfilerSummaryItem
} from '../../core/models/api.models';
import { BackendApiService } from '../../core/services/backend-api.service';
import { ProfilerSessionService } from '../../core/services/profiler-session.service';

interface DashboardMetric {
    label: string;
    value: string;
    helper: string;
    accent: 'neutral' | 'alert' | 'success';
}

interface QuickInfoItem {
    label: string;
    value: string;
}

interface BottleneckCard {
    name: string;
    calls: string;
    totalTime: string;
    avgTime: string;
    percent: string;
    impactScore: string;
    severityLabel: string;
    severityType: PoTagType;
}

interface ModuleSpotlight {
    module: string;
    metricLabel: string;
    metricValue: string;
    secondaryLabel: string;
    secondaryValue: string;
    percent: string;
    callerSummary: string;
}

interface CallTreeEdge {
    caller?: string;
    callee?: string;
    calls?: number;
}

interface CallTreeHighlight {
    name: string;
    calls: string;
    totalTime: string;
    childrenCount: string;
    percent: string;
}

interface HotLineRow {
    module: string;
    line: number | string;
    calls: string;
    totalTimeMs: string;
    avgTimeMs: string;
}

@Component({
    selector: 'app-profiler-analysis-page',
    standalone: true,
    imports: [
        CommonModule,
        PoPageModule,
        PoWidgetModule,
        PoButtonModule,
        PoTableModule,
        PoLoadingModule,
        PoInfoModule,
        PoTagModule,
        PoDividerModule
    ],
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
    protected readonly TAG_INFO = PoTagType.Info;
    protected readonly TAG_WARNING = PoTagType.Warning;
    protected readonly TAG_DANGER = PoTagType.Danger;
    protected readonly TAG_SUCCESS = PoTagType.Success;

    protected readonly hotLineColumns: PoTableColumn[] = [
        { property: 'module', label: 'Módulo / fonte' },
        { property: 'line', label: 'Linha', width: '90px' },
        { property: 'calls', label: 'Chamadas', width: '120px' },
        { property: 'totalTimeMs', label: 'Tempo total', width: '150px' },
        { property: 'avgTimeMs', label: 'Tempo médio', width: '150px' }
    ];

    ngOnInit(): void {
        this.profilerLoading = false;
        this.restoreSession();
    }

    protected get hasResult(): boolean {
        return !!this.profilerResult;
    }

    protected get profilerAnalysis(): ProfilerAnalysisPayload | null {
        return this.profilerResult?.analysis ?? null;
    }

    protected get sessionData(): Record<string, unknown> {
        return (this.profilerResult?.session ?? this.profilerAnalysis?.session ?? {}) as Record<string, unknown>;
    }

    protected get summaryData(): Record<string, unknown> {
        return (this.profilerResult?.summary ?? this.profilerAnalysis?.summary ?? {}) as Record<string, unknown>;
    }

    protected get healthScore(): number {
        return this.readNumericValue(this.summaryData, ['health_score']);
    }

    protected get healthLabel(): string {
        if (this.healthScore >= 80) {
            return 'Sessão estável';
        }

        if (this.healthScore >= 55) {
            return 'Atenção moderada';
        }

        return 'Investigação prioritária';
    }

    protected get healthTagType(): PoTagType {
        if (this.healthScore >= 80) {
            return PoTagType.Success;
        }

        if (this.healthScore >= 55) {
            return PoTagType.Warning;
        }

        return PoTagType.Danger;
    }

    protected get headlineMetrics(): DashboardMetric[] {
        const totalCalls = this.readNumericValue(this.summaryData, ['total_calls']);
        const totalTime = this.readNumericValue(this.summaryData, ['total_time_ms']);
        const totalModules = this.readNumericValue(this.summaryData, ['total_modules']);
        const totalLines = this.readNumericValue(this.summaryData, ['total_lines']);
        const traceInfo = this.readNumericValue(this.summaryData, ['trace_info_count']);
        const nPlusOneCount = this.profilerResult?.n_plus_one_suspects?.length ?? 0;

        return [
            {
                label: 'Tempo total',
                value: this.formatMs(totalTime),
                helper: `${this.formatNumber(totalCalls)} chamadas acumuladas`,
                accent: totalTime > 5000 ? 'alert' : 'neutral'
            },
            {
                label: 'Procedures mapeadas',
                value: this.formatNumber(totalModules),
                helper: `${this.formatNumber(totalLines)} linhas com tempo consolidado`,
                accent: 'neutral'
            },
            {
                label: 'Saúde da sessão',
                value: `${this.healthScore.toFixed(0)} / 100`,
                helper: this.healthLabel,
                accent: this.healthScore >= 80 ? 'success' : 'alert'
            },
            {
                label: 'Sinais N+1',
                value: this.formatNumber(nPlusOneCount),
                helper: `${this.formatNumber(traceInfo)} registros auxiliares de trace`,
                accent: nPlusOneCount > 0 ? 'alert' : 'success'
            }
        ];
    }

    protected get sessionFacts(): QuickInfoItem[] {
        const session = this.sessionData;
        return [
            { label: 'Arquivo', value: this.profilerResult?.filename || this.uploadedFilename || '-' },
            { label: 'Analisado em', value: this.analyzedAt ? this.formatDate(this.analyzedAt) : '-' },
            { label: 'Data da sessão', value: this.readStringValue(session, ['date']) || '-' },
            { label: 'Hora da sessão', value: this.readStringValue(session, ['time']) || '-' },
            { label: 'Usuário', value: this.readStringValue(session, ['user']) || '-' },
            { label: 'Descrição', value: this.readStringValue(session, ['description']) || '-' }
        ];
    }

    protected get topBottleneckCards(): BottleneckCard[] {
        const bottlenecks = this.profilerResult?.top_bottlenecks ?? this.profilerAnalysis?.top_bottlenecks ?? [];
        return bottlenecks.slice(0, 5).map((item) => {
            const percent = this.readNumericValue(item, ['percent']);
            const severityLabel = this.readStringValue(item, ['severity']) || this.severityLabelFromPercent(percent);
            return {
                name: this.readStringValue(item, ['procedure', 'procedure_name', 'program', 'module', 'object_name']) || '-',
                calls: this.formatNumber(this.readNumericValue(item, ['calls', 'call_count', 'executions'])),
                totalTime: this.formatMs(this.readNumericValue(item, ['total_time', 'duration', 'elapsed_ms', 'time_total_ms'])),
                avgTime: this.formatMs(this.readNumericValue(item, ['avg_time', 'time_avg_ms'])),
                percent: `${percent.toFixed(2)}%`,
                impactScore: this.formatNumber(this.readNumericValue(item, ['impact_score']), 2),
                severityLabel: this.humanizeSeverity(severityLabel),
                severityType: this.severityTagType(severityLabel)
            };
        });
    }

    protected get topModulesByTime(): ModuleSpotlight[] {
        return this.mapModuleSpotlights(this.profilerAnalysis?.top_modules_by_time ?? [], 'Tempo total', 'Chamadas');
    }

    protected get topModulesByCalls(): ModuleSpotlight[] {
        return this.mapModuleSpotlights(this.profilerAnalysis?.top_modules_by_calls ?? [], 'Chamadas', 'Tempo médio');
    }

    protected get topAvgModules(): ModuleSpotlight[] {
        return this.mapModuleSpotlights(this.profilerAnalysis?.top_modules_by_avg_time ?? [], 'Tempo médio', 'Tempo total');
    }

    protected get callTreeSummary(): QuickInfoItem[] {
        const stats = this.profilerAnalysis?.call_tree_stats;
        return [
            {
                label: 'Relacionamentos',
                value: this.formatNumber(stats?.total_relationships ?? 0)
            },
            {
                label: 'Callers únicos',
                value: this.formatNumber(stats?.unique_callers ?? 0)
            },
            {
                label: 'Callees únicos',
                value: this.formatNumber(stats?.unique_callees ?? 0)
            }
        ];
    }

    protected get callTreeHighlights(): CallTreeHighlight[] {
        const callTree = this.profilerResult?.call_tree ?? this.profilerAnalysis?.call_tree ?? [];
        return callTree.slice(0, 5).map((item) => ({
            name: this.readStringValue(item, ['name', 'module']) || '-',
            calls: this.formatNumber(this.readNumericValue(item, ['calls'])),
            totalTime: this.formatMs(this.readNumericValue(item, ['total_time', 'time_total_ms'])),
            percent: `${Number(this.readNumericValue(item, ['percent'])).toFixed(2)}%`,
            childrenCount: Array.isArray((item as Record<string, unknown>)['children'])
                ? this.formatNumber(((item as Record<string, unknown>)['children'] as unknown[]).length)
                : '0'
        }));
    }

    protected get hotLineRows(): HotLineRow[] {
        return (this.profilerAnalysis?.top_lines ?? []).slice(0, 10).map((item) => ({
            module: this.readStringValue(item, ['module']) || '-',
            line: this.readValue(item, ['line']),
            calls: this.formatNumber(this.readNumericValue(item, ['calls'])),
            totalTimeMs: this.formatMs(this.readNumericValue(item, ['time_total_ms'])),
            avgTimeMs: this.formatMs(this.readNumericValue(item, ['time_avg_ms']))
        }));
    }

    protected get recommendations(): string[] {
        return this.profilerAnalysis?.recommendations ?? [];
    }

    protected get problematicModules(): ProfilerIssueItem[] {
        return (this.profilerAnalysis?.problematic_modules ?? []).slice(0, 6);
    }

    protected get nPlusOneSuspects(): ProfilerSummaryItem[] {
        return (this.profilerResult?.n_plus_one_suspects ?? this.profilerAnalysis?.n_plus_one_suspects ?? []).slice(0, 6);
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
                    this.profilerLoading = false;
                    this.profilerResult = response;
                    this.uploadedFilename = this.profilerFile?.name ?? response.filename;
                    this.analyzedAt = new Date().toISOString();
                    this.profilerSession.save(response, this.uploadedFilename);
                    this.successMessage = 'Profiler analisado e carregado na tela dedicada.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.profilerLoading = false;
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
        this.profilerLoading = false;
        const session = this.profilerSession.load();
        if (!session) {
            return;
        }

        this.profilerResult = session.result;
        this.analyzedAt = session.analyzedAt;
        this.uploadedFilename = session.filename;
    }

    protected issueTagType(issue: string): PoTagType {
        const normalized = issue.toLowerCase();
        if (normalized.includes('alto tempo') || normalized.includes('muitas chamadas')) {
            return PoTagType.Danger;
        }

        return PoTagType.Warning;
    }

    private mapModuleSpotlights(
        items: ProfilerSummaryItem[],
        primaryLabel: string,
        secondaryLabel: string
    ): ModuleSpotlight[] {
        return items.slice(0, 5).map((item) => ({
            module: this.readStringValue(item, ['module', 'procedure']) || '-',
            metricLabel: primaryLabel,
            metricValue: primaryLabel === 'Chamadas'
                ? this.formatNumber(this.readNumericValue(item, ['calls']))
                : this.formatMs(this.readNumericValue(item, primaryLabel === 'Tempo médio' ? ['time_avg_ms'] : ['time_total_ms'])),
            secondaryLabel,
            secondaryValue: secondaryLabel === 'Chamadas'
                ? this.formatNumber(this.readNumericValue(item, ['calls']))
                : secondaryLabel === 'Tempo médio'
                    ? this.formatMs(this.readNumericValue(item, ['time_avg_ms']))
                    : this.formatMs(this.readNumericValue(item, ['time_total_ms'])),
            percent: `${this.readNumericValue(item, ['percent']).toFixed(2)}% da sessão`,
            callerSummary: this.getCallerSummary(this.readStringValue(item, ['module', 'procedure']) || '-')
        }));
    }

    private getCallerSummary(moduleName: string): string {
        const callTreeEdges = this.readCallTreeEdges();
        const callers = callTreeEdges
            .filter((edge) => (edge.callee ?? '') === moduleName)
            .map((edge) => ({
                caller: edge.caller || 'Entrada da sessão',
                calls: edge.calls ?? 0
            }))
            .sort((left, right) => right.calls - left.calls);

        if (callers.length === 0) {
            return 'Procedure de entrada ou sem caller mapeado';
        }

        const primaryCaller = callers[0];
        const otherCallers = callers.length - 1;
        if (otherCallers <= 0) {
            return `Executada por ${primaryCaller.caller}`;
        }

        return `Executada por ${primaryCaller.caller} + ${otherCallers} programa(s)`;
    }

    private readCallTreeEdges(): CallTreeEdge[] {
        const rawData = this.profilerResult?.raw_data as Record<string, unknown> | undefined;
        const edges = rawData?.['call_tree_edges'];
        return Array.isArray(edges) ? edges as CallTreeEdge[] : [];
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

    private readStringValue(item: object, candidates: string[]): string {
        const value = this.readValue(item, candidates);
        return typeof value === 'string' ? value : String(value);
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

    private formatMs(value: number): string {
        if (!Number.isFinite(value) || value <= 0) {
            return '0 ms';
        }

        if (value >= 1000) {
            return `${(value / 1000).toFixed(2)} s`;
        }

        return `${value.toFixed(2)} ms`;
    }

    private formatNumber(value: number, fractionDigits = 0): string {
        return new Intl.NumberFormat('pt-BR', {
            minimumFractionDigits: fractionDigits,
            maximumFractionDigits: fractionDigits
        }).format(value);
    }

    private severityLabelFromPercent(percent: number): string {
        if (percent >= 40) {
            return 'critical';
        }

        if (percent >= 20) {
            return 'high';
        }

        if (percent >= 10) {
            return 'medium';
        }

        return 'low';
    }

    private humanizeSeverity(value: string): string {
        switch (value.toLowerCase()) {
            case 'critical':
                return 'Crítico';
            case 'high':
                return 'Alto';
            case 'medium':
                return 'Médio';
            case 'low':
                return 'Baixo';
            default:
                return 'Informativo';
        }
    }

    private severityTagType(value: string): PoTagType {
        switch (value.toLowerCase()) {
            case 'critical':
            case 'high':
                return PoTagType.Danger;
            case 'medium':
                return PoTagType.Warning;
            case 'low':
                return PoTagType.Success;
            default:
                return PoTagType.Info;
        }
    }
}
