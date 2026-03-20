// =============================
// Resultados da análise: aqui os logs ganham vida!
// Este componente mostra tabelas, gráficos e insights para o usuário.
// Comentários didáticos para quem está aprendendo Angular ou PO UI.
// =============================
// Importando tudo que é necessário para mostrar resultados incríveis!
import { CommonModule } from '@angular/common';
import { Component, HostListener, OnInit, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ChartConfiguration } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import {
    PoButtonModule,
    PoFieldModule,
    PoIconModule,
    PoLoadingModule,
    PoModalComponent,
    PoModalModule,
    PoPageModule,
    PoTableColumn,
    PoTableModule,
    PoTagModule,
    PoTagType,
    PoWidgetModule,
    PoInfoModule,
    PoDividerModule
} from '@po-ui/ng-components';
import { finalize } from 'rxjs';

import {
    AnalyzeInfoResponse,
    AnalysisResultItem,
    AttentionPointItem,
    InformationalLineItem,
    LogAnalysisResponse,
    PerformanceAnalysisResponse,
    PatternSuggestionItem,
    PotentialNewErrorItem,
    TopProgramMethodItem
} from '../../core/models/api.models';
import { BackendApiService } from '../../core/services/backend-api.service';
import { AnalysisSessionService } from '../../core/services/analysis-session.service';

interface AnalysisDetailRow {
    lineNumber: number | string;
    severity: string;
    category: string;
    type: string;
    matchedPattern: string;
    preview: string;
    description: string;
    solution: string;
    source: string;
    timestamp: string;
    subtype: string;
    recommendationHint: string;
    insightTags: string[];
    domainFields: DomainFieldEntry[];
}

interface BreakdownItem {
    label: string;
    value: number;
}

interface MethodCallRow {
    label: string;
    value: number;
    share: string | number;
}

interface PerformanceTableItem {
    label: string;
    value: string | number;
    detail?: string;
}

interface PerformanceHealthSummary {
    score: number | null;
    label: string;
    helper: string;
    reasons: string[];
    tagType: PoTagType;
}

interface DomainFieldEntry {
    label: string;
    value: string;
}

interface StructuredMetricRow {
    label: string;
    value: string | number;
    detail?: string;
}

interface PotentialErrorTableItem {
    line: number;
    confidence: string;
    suggestedPattern: string;
    suspiciousWords: string;
    message: string;
}

type NonErrorSelectionMode = 'auto' | 'full' | 'custom';

interface NonErrorDialogItem {
    kind: 'result' | 'potential';
    lineNumber: number | string;
    message: string;
    suggestedPattern: string;
    title: string;
    helperText: string;
}

interface PatternSuggestionTableItem {
    pattern: string;
    frequency: number;
    suggestedRegex: string;
}

type AnalysisInsightView = 'linhas' | 'geral' | 'performance' | 'novos-erros' | 'estruturado' | 'atencao' | 'informativas';

interface AnalysisViewOption {
    key: AnalysisInsightView;
    label: string;
    count?: number;
}

// Componente de resultados: aqui os logs ganham vida!
//
// DICA: Use @Component para criar componentes reutilizáveis.
//       O PO UI facilita a criação de tabelas, gráficos e modais sem dor de cabeça.
//       O ciclo de vida do Angular começa com ngOnInit.
@Component({
    selector: 'app-analysis-results-page',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        PoPageModule,
        PoWidgetModule,
        PoButtonModule,
        PoTableModule,
        PoTagModule,
        PoModalModule,
        PoFieldModule,
        PoLoadingModule,
        PoIconModule,
        PoInfoModule,
        PoDividerModule,
        BaseChartDirective
    ],
    templateUrl: './analysis-results.page.html',
    styleUrl: './analysis-results.page.scss'
})
// Aqui é onde os resultados aparecem e surpreendem!
//
// DICA: Use getters para calcular dados em tempo real para o template.
//       Separe variáveis de estado (loading, error, etc) para facilitar manutenção.
//       Use protected para expor só o necessário ao HTML.
export class AnalysisResultsPageComponent implements OnInit {
    @ViewChild('nonErrorModal', { static: true }) nonErrorModal!: PoModalComponent;

    protected readonly TAG_INFO = PoTagType.Info;
    protected readonly TAG_WARNING = PoTagType.Warning;
    protected readonly TAG_DANGER = PoTagType.Danger;
    protected readonly TAG_SUCCESS = PoTagType.Success;

    private readonly router = inject(Router);
    private readonly api = inject(BackendApiService);
    private readonly session = inject(AnalysisSessionService);

    protected logFile: File | null = null;
    protected patternsFile: File | null = null;
    protected previewInfo: AnalyzeInfoResponse | null = null;
    protected analysisResult: LogAnalysisResponse | null = null;
    protected analyzedFilename = '';
    protected analyzedAt = '';
    protected errorMessage = '';
    protected successMessage = '';
    protected loading = false;
    protected savingNonError = false;
    protected savingInformationalLine: number | null = null;
    protected compactViewport = this.isCompactViewport();

    protected resultRows: AnalysisDetailRow[] = [];
    protected summaryCards: Array<{ label: string; value: string | number }> = [];
    protected highlightedStats: Array<{ label: string; value: string | number }> = [];
    protected attentionPoints: AttentionPointItem[] = [];
    protected informationalLines: InformationalLineItem[] = [];
    protected structuredSummaryCards: Array<{ label: string; value: string | number }> = [];
    protected structuredSubtypeRows: StructuredMetricRow[] = [];
    protected structuredCategoryRows: StructuredMetricRow[] = [];
    protected statisticsRows: StructuredMetricRow[] = [];
    protected errorCountRows: StructuredMetricRow[] = [];
    protected severityCountRows: StructuredMetricRow[] = [];
    protected specializedInsightRows: StructuredMetricRow[] = [];
    protected specializedRecommendationRows: StructuredMetricRow[] = [];
    protected specializedAccessRows: StructuredMetricRow[] = [];
    protected specializedProgressRows: StructuredMetricRow[] = [];
    protected specializedTabanalysRows: StructuredMetricRow[] = [];
    protected specializedXrefRows: StructuredMetricRow[] = [];
    protected specializedLogixCommandRows: StructuredMetricRow[] = [];
    protected specializedLogixProgramRows: StructuredMetricRow[] = [];
    protected performanceSummaryCards: Array<{ label: string; value: string | number }> = [];
    protected slowProgramRows: PerformanceTableItem[] = [];
    protected slowOperationRows: PerformanceTableItem[] = [];
    protected topMethodRows: MethodCallRow[] = [];
    protected topProgramRows: TopProgramMethodItem[] = [];
    protected specificAlertRows: PerformanceTableItem[] = [];
    protected performanceHealthScore: number | null = null;
    protected performanceHealthLabel = 'Sem dados suficientes';
    protected performanceHealthHelper = 'O log precisa trazer tempos, chamadas ou falhas para compor este indicador.';
    protected performanceHealthReasons: string[] = [];
    protected performanceHealthTagType: PoTagType = PoTagType.Info;
    protected newErrorSummaryCards: Array<{ label: string; value: string | number }> = [];
    protected newErrorCoverageRows: StructuredMetricRow[] = [];
    protected potentialErrorRows: PotentialErrorTableItem[] = [];
    protected patternSuggestionRows: PatternSuggestionTableItem[] = [];
    protected suspiciousWordRows: StructuredMetricRow[] = [];
    protected activeInsightView: AnalysisInsightView = 'linhas';
    protected selectedResultRow: AnalysisDetailRow | null = null;
    protected expandedResultRows = new Set<string>();
    protected resultSearchTerm = '';
    protected severityFilter = 'all';

    protected selectedError: NonErrorDialogItem | null = null;
    protected nonErrorFullLine = '';
    protected nonErrorPartialPattern = '';
    protected nonErrorReason = '';
    protected nonErrorSelectionMode: NonErrorSelectionMode = 'auto';

    // Colunas da tabela de resultados: cada linha é uma história do log!
    //
    // DICA: Customize as colunas conforme o tipo de análise ou perfil do usuário.
    //       O PO UI permite tabelas responsivas e fáceis de usar.
    protected readonly resultColumns: PoTableColumn[] = [
        { property: 'lineNumber', label: 'Linha', width: '90px' },
        { property: 'severity', label: 'Severidade', width: '120px' },
        { property: 'category', label: 'Categoria', width: '160px' },
        { property: 'type', label: 'Tipo', width: '160px' },
        { property: 'matchedPattern', label: 'Padrão' },
        { property: 'preview', label: 'Linha / Mensagem' }
    ];

    private readonly desktopPerformanceColumns: PoTableColumn[] = [
        { property: 'label', label: 'Indicador' },
        { property: 'value', label: 'Valor', width: '140px' },
        { property: 'detail', label: 'Detalhe' }
    ];

    private readonly compactPerformanceColumns: PoTableColumn[] = [
        { property: 'label', label: 'Indicador' },
        { property: 'value', label: 'Valor', width: '120px' }
    ];

    private readonly desktopTopProgramColumns: PoTableColumn[] = [
        { property: 'program', label: 'Programa' },
        { property: 'method', label: 'Método' },
        { property: 'calls', label: 'Chamadas', width: '110px' },
        { property: 'total_time_ms', label: 'Tempo total (ms)', width: '150px' },
        { property: 'avg_time_ms', label: 'Tempo médio (ms)', width: '150px' },
        { property: 'percent_of_total_time', label: '% do tempo', width: '120px' },
        { property: 'callers_summary', label: 'Callers' }
    ];

    private readonly compactTopProgramColumns: PoTableColumn[] = [
        { property: 'program', label: 'Programa' },
        { property: 'method', label: 'Método' },
        { property: 'total_time_ms', label: 'Tempo total (ms)', width: '150px' }
    ];

    private readonly desktopBreakdownColumns: PoTableColumn[] = [
        { property: 'label', label: 'Método / indicador' },
        { property: 'value', label: 'Valor', width: '120px' }
    ];

    private readonly compactBreakdownColumns: PoTableColumn[] = [
        { property: 'label', label: 'Indicador' },
        { property: 'value', label: 'Valor', width: '120px' }
    ];

    private readonly desktopTopMethodColumns: PoTableColumn[] = [
        { property: 'label', label: 'Método / indicador' },
        { property: 'value', label: 'Chamadas', width: '120px' },
        { property: 'share', label: '% do total', width: '120px' }
    ];

    private readonly compactTopMethodColumns: PoTableColumn[] = [
        { property: 'label', label: 'Método / indicador' },
        { property: 'value', label: 'Chamadas', width: '120px' }
    ];

    private readonly desktopPotentialErrorColumns: PoTableColumn[] = [
        { property: 'line', label: 'Linha', width: '90px' },
        { property: 'confidence', label: 'Confiança', width: '110px' },
        { property: 'suggestedPattern', label: 'Padrão sugerido', width: '220px' },
        { property: 'suspiciousWords', label: 'Palavras suspeitas', width: '220px' },
        { property: 'message', label: 'Mensagem' }
    ];

    private readonly compactPotentialErrorColumns: PoTableColumn[] = [
        { property: 'line', label: 'Linha', width: '90px' },
        { property: 'confidence', label: 'Confiança', width: '110px' },
        { property: 'message', label: 'Mensagem' }
    ];

    private readonly desktopPatternSuggestionColumns: PoTableColumn[] = [
        { property: 'pattern', label: 'Padrão' },
        { property: 'frequency', label: 'Frequência', width: '120px' },
        { property: 'suggestedRegex', label: 'Regex sugerida' }
    ];

    private readonly compactPatternSuggestionColumns: PoTableColumn[] = [
        { property: 'pattern', label: 'Padrão' },
        { property: 'frequency', label: 'Freq.', width: '100px' }
    ];

    protected readonly barChartOptions: ChartConfiguration<'bar'>['options'] = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
    };

    protected readonly doughnutChartOptions: ChartConfiguration<'doughnut'>['options'] = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
    };

    protected readonly lineChartOptions: ChartConfiguration<'line'>['options'] = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
    };

    ngOnInit(): void {
        this.loading = false;
        const sessionData = this.session.load();
        if (sessionData) {
            this.applyAnalysisResult(sessionData.result, sessionData.filename, sessionData.analyzedAt);
        }
    }

    @HostListener('window:resize')
    protected onWindowResize(): void {
        this.compactViewport = this.isCompactViewport();
    }

    protected get hasAnalysisResult(): boolean {
        return !!this.analysisResult;
    }

    protected get performanceColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactPerformanceColumns : this.desktopPerformanceColumns;
    }

    protected get topProgramColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactTopProgramColumns : this.desktopTopProgramColumns;
    }

    protected get breakdownColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactBreakdownColumns : this.desktopBreakdownColumns;
    }

    protected get topMethodColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactTopMethodColumns : this.desktopTopMethodColumns;
    }

    protected get potentialErrorColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactPotentialErrorColumns : this.desktopPotentialErrorColumns;
    }

    protected get patternSuggestionColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactPatternSuggestionColumns : this.desktopPatternSuggestionColumns;
    }

    protected get viewOptions(): AnalysisViewOption[] {
        const views: AnalysisViewOption[] = [
            { key: 'linhas', label: 'Linhas', count: this.resultRows.length },
            { key: 'geral', label: 'Visão geral' },
            { key: 'performance', label: 'Performance', count: this.hasPerformanceData ? this.performanceSummaryCards.length : 0 },
            { key: 'novos-erros', label: 'Novos erros', count: this.hasNewErrorsData ? this.potentialErrorRows.length : 0 },
            { key: 'estruturado', label: 'Estruturado', count: this.hasStructuredDetails ? this.structuredSummaryCards.length : 0 },
            { key: 'atencao', label: 'Atenção', count: this.attentionPoints.length },
            { key: 'informativas', label: 'Informativas', count: this.informationalLines.length }
        ];

        return views.filter((item) => this.isViewAvailable(item.key));
    }

    protected get severityFilterOptions(): string[] {
        return ['all', ...new Set(this.resultRows.map((item) => item.severity).filter((value) => value && value !== '-'))];
    }

    protected get filteredResultRows(): AnalysisDetailRow[] {
        const search = this.resultSearchTerm.trim().toLowerCase();
        return this.resultRows.filter((item) => {
            const severityMatches = this.severityFilter === 'all' || item.severity === this.severityFilter;
            if (!severityMatches) {
                return false;
            }

            if (!search) {
                return true;
            }

            const haystack = [item.preview, item.type, item.category, item.description, item.solution, String(item.lineNumber)]
                .join(' ')
                .toLowerCase();
            return haystack.includes(search);
        });
    }

    protected get currentResultDetail(): AnalysisDetailRow | null {
        if (!this.selectedResultRow) {
            return this.filteredResultRows[0] ?? null;
        }

        const match = this.filteredResultRows.find((item) => item.lineNumber === this.selectedResultRow?.lineNumber && item.preview === this.selectedResultRow?.preview);
        return match ?? this.filteredResultRows[0] ?? null;
    }

    protected get hasStructuredDetails(): boolean {
        return this.structuredSummaryCards.length > 0
            || this.structuredSubtypeRows.length > 0
            || this.structuredCategoryRows.length > 0
            || this.specializedInsightRows.length > 0
            || this.specializedRecommendationRows.length > 0
            || this.specializedAccessRows.length > 0
            || this.specializedProgressRows.length > 0
            || this.specializedTabanalysRows.length > 0
            || this.specializedXrefRows.length > 0
            || this.specializedLogixCommandRows.length > 0
            || this.specializedLogixProgramRows.length > 0;
    }

    protected get hasNewErrorsData(): boolean {
        return this.newErrorSummaryCards.length > 0
            || this.newErrorCoverageRows.length > 0
            || this.potentialErrorRows.length > 0
            || this.patternSuggestionRows.length > 0
            || this.suspiciousWordRows.length > 0;
    }

    protected get hasPerformanceData(): boolean {
        return this.performanceSummaryCards.length > 0
            || this.slowProgramRows.length > 0
            || this.slowOperationRows.length > 0
            || this.topMethodRows.length > 0
            || this.topProgramRows.length > 0
            || this.specificAlertRows.length > 0;
    }

    protected setInsightView(view: AnalysisInsightView): void {
        this.activeInsightView = view;
    }

    protected isActiveView(view: AnalysisInsightView): boolean {
        return this.activeInsightView === view;
    }

    protected selectResultRow(row: AnalysisDetailRow): void {
        this.selectedResultRow = row;
    }

    protected setSeverityFilter(value: string): void {
        this.severityFilter = value;
        this.ensureSelectedResultRow();
    }

    protected isResultRowExpanded(row: AnalysisDetailRow): boolean {
        return this.expandedResultRows.has(this.getResultRowKey(row));
    }

    protected toggleResultRow(row: AnalysisDetailRow): void {
        const key = this.getResultRowKey(row);
        if (this.expandedResultRows.has(key)) {
            this.expandedResultRows.delete(key);
            return;
        }

        this.expandedResultRows.add(key);
    }

    protected onLogFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.logFile = input?.files?.item(0) ?? null;
        this.previewInfo = null;
        this.errorMessage = '';
        this.successMessage = '';
    }

    protected onPatternsFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.patternsFile = input?.files?.item(0) ?? null;
    }

    protected previewLog(): void {
        if (!this.logFile) {
            this.errorMessage = 'Selecione um arquivo de log para pré-análise.';
            return;
        }

        this.loading = true;
        this.errorMessage = '';
        this.successMessage = '';

        this.api.analyzeInfo(this.logFile)
            .pipe(finalize(() => (this.loading = false)))
            .subscribe({
                next: (response) => {
                    this.loading = false;
                    this.previewInfo = response;
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao obter prévia do log.';
                }
            });
    }

    protected analyzeLog(): void {
        if (!this.logFile) {
            this.errorMessage = 'Selecione um arquivo de log antes de iniciar a análise.';
            return;
        }

        this.loading = true;
        this.errorMessage = '';
        this.successMessage = '';

        this.api.analyzeLog(this.logFile, this.patternsFile)
            .pipe(finalize(() => (this.loading = false)))
            .subscribe({
                next: (response) => {
                    this.loading = false;
                    const filename = this.logFile?.name ?? this.previewInfo?.file_info.filename ?? 'log';
                    const analyzedAt = new Date().toISOString();
                    this.applyAnalysisResult(response, filename, analyzedAt);
                    this.successMessage = response.informational_lines?.length
                        ? 'Análise concluída. As linhas informativas ficaram separadas na seção Informativas.'
                        : 'Análise concluída com sucesso.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.loading = false;
                    this.errorMessage = error.error?.detail ?? 'Falha ao analisar o log.';
                }
            });
    }

    protected get errorTypeChartData(): ChartConfiguration<'bar'>['data'] {
        const errorTypes = this.analysisResult?.chart_data?.error_types;
        return {
            labels: errorTypes?.labels ?? [],
            datasets: [{ data: errorTypes?.values ?? [], label: 'Tipos de erro', backgroundColor: '#0c5abe' }]
        };
    }

    protected get severityChartData(): ChartConfiguration<'doughnut'>['data'] {
        const severity = this.analysisResult?.chart_data?.severity;
        const labels = severity?.labels?.length ? severity.labels : Object.keys(this.analysisResult?.severity_counts ?? {});
        const values = severity?.values?.length
            ? severity.values
            : Object.values(this.analysisResult?.severity_counts ?? {}).map((value) => Number(value) || 0);

        return {
            labels,
            datasets: [{ data: values, backgroundColor: ['#ef4444', '#f59e0b', '#2dd4bf', '#0c5abe', '#8b5cf6'] }]
        };
    }

    protected get hourlyChartData(): ChartConfiguration<'line'>['data'] {
        const hourly = this.analysisResult?.chart_data?.hourly;
        return {
            labels: hourly?.labels ?? [],
            datasets: [{ data: hourly?.values ?? [], label: 'Ocorrências por hora', borderColor: '#2d7ff9', backgroundColor: '#2d7ff9', tension: 0.25 }]
        };
    }

    protected get temporalChartData(): ChartConfiguration<'line'>['data'] {
        const temporal = this.analysisResult?.chart_data?.temporal;
        return {
            labels: temporal?.labels ?? [],
            datasets: [{ data: temporal?.values ?? [], label: 'Ocorrências no tempo', borderColor: '#0ea5e9', backgroundColor: '#0ea5e9', tension: 0.25 }]
        };
    }

    protected openNonErrorModal(item: AnalysisDetailRow): void {
        this.selectedError = {
            kind: 'result',
            lineNumber: item.lineNumber,
            message: item.preview,
            suggestedPattern: item.matchedPattern !== '-' ? item.matchedPattern : this.extractAutomaticPattern(item.preview),
            title: `Ocorrência encontrada na linha ${item.lineNumber}`,
            helperText: item.description !== '-' ? item.description : 'Selecione a parte da mensagem que deve ser tratada como não-erro.'
        };
        this.nonErrorFullLine = item.preview;
        this.nonErrorReason = item.description !== '-' ? item.description : 'Linha classificada como não-erro após análise manual.';
        this.setNonErrorSelectionMode('auto');
        this.nonErrorModal.open();
    }

    protected openPotentialNonErrorModal(item: PotentialErrorTableItem): void {
        this.selectedError = {
            kind: 'potential',
            lineNumber: item.line,
            message: item.message,
            suggestedPattern: item.suggestedPattern || this.extractAutomaticPattern(item.message),
            title: `Possível novo erro na linha ${item.line}`,
            helperText: `Confiança ${item.confidence}. Revise a mensagem e informe qual trecho não deve ser tratado como erro.`
        };
        this.nonErrorFullLine = item.message;
        this.nonErrorReason = 'Possível erro marcado manualmente como não-erro após revisão do usuário.';
        this.setNonErrorSelectionMode('auto');
        this.nonErrorModal.open();
    }

    protected setNonErrorSelectionMode(mode: NonErrorSelectionMode): void {
        this.nonErrorSelectionMode = mode;

        if (mode === 'full') {
            this.nonErrorPartialPattern = this.nonErrorFullLine;
            return;
        }

        if (mode === 'auto') {
            this.nonErrorPartialPattern = this.selectedError?.suggestedPattern || this.extractAutomaticPattern(this.nonErrorFullLine);
            return;
        }

        if (!this.nonErrorPartialPattern || this.nonErrorPartialPattern === this.selectedError?.suggestedPattern || this.nonErrorPartialPattern === this.nonErrorFullLine) {
            this.nonErrorPartialPattern = '';
        }
    }

    protected saveAsNonError(): void {
        const fullMessage = this.nonErrorFullLine.trim() || this.selectedError?.message || '';
        const partialPattern = this.resolveNonErrorPattern();
        const reason = this.nonErrorReason.trim();

        if (!fullMessage) {
            this.errorMessage = 'Informe a linha completa para salvar como não-erro.';
            return;
        }

        if (!partialPattern) {
            this.errorMessage = this.nonErrorSelectionMode === 'custom'
                ? 'Informe o trecho que não deve ser tratado como erro.'
                : 'Não foi possível definir automaticamente o trecho do não-erro.';
            return;
        }

        if (!reason) {
            this.errorMessage = 'Informe a explicação do não-erro.';
            return;
        }

        this.savingNonError = true;
        this.errorMessage = '';
        this.successMessage = '';

        this.api.markAsNonError({
            pattern: partialPattern,
            partial_pattern: partialPattern,
            full_message: fullMessage,
            selection_type: this.nonErrorSelectionMode,
            reason,
            source_line: this.selectedError?.lineNumber ?? null
        })
            .pipe(finalize(() => (this.savingNonError = false)))
            .subscribe({
                next: () => {
                    this.removeCurrentNonErrorItem();
                    this.successMessage = 'Não-erro salvo no banco. Nas próximas análises essa ocorrência deixará de ser retornada enquanto permanecer ativa.';
                    this.closeNonErrorModal();
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao salvar o não-erro.';
                }
            });
    }

    protected closeNonErrorModal(): void {
        this.nonErrorModal.close();
        this.selectedError = null;
        this.nonErrorFullLine = '';
        this.nonErrorPartialPattern = '';
        this.nonErrorReason = '';
        this.nonErrorSelectionMode = 'auto';
    }

    protected approveInformationalLine(item: InformationalLineItem): void {
        const fullMessage = item.message?.trim();
        if (!fullMessage) {
            this.errorMessage = 'A linha informativa não possui conteúdo para ser salva como não-erro.';
            return;
        }

        const partialPattern = this.extractInformationalPattern(item);
        this.savingInformationalLine = item.line;
        this.errorMessage = '';
        this.successMessage = '';

        this.api.markAsNonError({
            pattern: partialPattern,
            partial_pattern: partialPattern,
            full_message: fullMessage,
            reason: item.suggestion?.trim() || 'Linha informativa aprovada como não-erro pelo usuário.',
            source_line: item.line
        })
            .pipe(finalize(() => (this.savingInformationalLine = null)))
            .subscribe({
                next: () => {
                    this.informationalLines = this.informationalLines.filter((line) => line !== item);
                    this.successMessage = 'Linha informativa aprovada. Ela será desconsiderada nas próximas análises enquanto a restrição estiver ativa.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao salvar a linha informativa como não-erro.';
                }
            });
    }

    protected rejectInformationalLine(item: InformationalLineItem): void {
        this.informationalLines = this.informationalLines.filter((line) => line !== item);
        this.successMessage = 'Sugestão descartada apenas nesta visualização.';
    }

    protected backToAnalysis(): void {
        void this.router.navigateByUrl('/analise');
    }

    protected newAnalysis(): void {
        this.session.clear();
        void this.router.navigateByUrl('/analise');
    }

    protected severityClass(severity: string): string {
        const value = (severity || '').toLowerCase();
        if (value.includes('cr') || value.includes('alta')) {
            return 'result-card__severity--high';
        }
        if (value.includes('m')) {
            return 'result-card__severity--medium';
        }
        return 'result-card__severity--low';
    }

    protected severityTagType(severity: string): PoTagType {
        const value = (severity || '').toLowerCase();
        if (value.includes('cr') || value.includes('alto') || value.includes('alta')) {
            return PoTagType.Danger;
        }
        if (value.includes('méd') || value.includes('med')) {
            return PoTagType.Warning;
        }
        if (value.includes('baix') || value.includes('low')) {
            return PoTagType.Success;
        }
        return PoTagType.Info;
    }

    protected logTypeColor(logType: string): string {
        const map: Record<string, string> = {
            'Datasul': 'color-01',
            'LOGIX': 'color-08',
            'AppServer': 'color-07',
            'JBoss': 'color-10',
            'Tomcat': 'color-04',
            'Fluig': 'color-11',
            'SmartClient': 'color-03',
        };
        return map[logType] || 'color-12';
    }

    private mapResultRow(item: AnalysisResultItem): AnalysisDetailRow {
        const lineValue = item.line_number ?? item.line ?? '-';
        const preview = this.resolveResultPreview(item);
        const type = String(item.type ?? item.error_type ?? '-');
        const description = String(item.description ?? this.buildFallbackDescription(type, preview));
        const solution = String(item.solution ?? this.buildFallbackSolution(type, item.severity ?? '-', preview));

        return {
            lineNumber: typeof lineValue === 'number' || typeof lineValue === 'string' ? lineValue : '-',
            severity: String(item.severity ?? '-'),
            category: String(item.category ?? '-'),
            type,
            matchedPattern: String(item.matched_pattern ?? item.error_signature ?? '-'),
            preview,
            description,
            solution,
            source: String(item.source ?? item.tag ?? 'Análise automática'),
            timestamp: String(item.timestamp ?? '-'),
            subtype: String(item.log_subtype ?? '-'),
            recommendationHint: this.formatRecommendationHint(item.recommendation_hint),
            insightTags: item.insight_tags ?? [],
            domainFields: this.mapDomainFields(item.domain_fields)
        };
    }

    private buildSummaryCards(response: LogAnalysisResponse): Array<{ label: string; value: string | number }> {
        const stats = response.statistics ?? {};
        return [
            { label: 'Resultados encontrados', value: response.total_results },
            { label: 'Categorias mapeadas', value: Object.keys(response.error_counts ?? {}).length },
            { label: 'Severidades', value: Object.keys(response.severity_counts ?? {}).length },
            { label: 'Linhas analisadas', value: this.pickStatistic(stats, ['total_lines_processed', 'total_lines', 'lines_analyzed']) }
        ];
    }

    private buildHighlightedStats(response: LogAnalysisResponse): Array<{ label: string; value: string | number }> {
        const stats = response.statistics ?? {};
        return [
            { label: 'Linhas informativas', value: response.informational_lines?.length ?? 0 },
            { label: 'Pontos de atenção', value: response.total_attention_points ?? response.attention_points?.length ?? 0 },
            { label: 'Erro mais comum', value: this.formatMostCommonError(stats['most_common_error']) },
            { label: 'Faixa do log', value: this.pickStatistic(stats, ['date_range', 'processing_mode', 'processing_type']) }
        ];
    }

    private buildBackendSummaryBlocks(response: LogAnalysisResponse): void {
        this.statisticsRows = this.mapGenericObject(response.statistics);
        this.errorCountRows = this.mapBreakdown(response.error_counts);
        this.severityCountRows = this.mapBreakdown(response.severity_counts);
    }

    private buildNewErrorsBlocks(response: LogAnalysisResponse): void {
        const newErrors = response.new_errors;
        if (!newErrors) {
            this.newErrorSummaryCards = [];
            this.newErrorCoverageRows = [];
            this.potentialErrorRows = [];
            this.patternSuggestionRows = [];
            this.suspiciousWordRows = [];
            return;
        }

        this.newErrorSummaryCards = [
            { label: 'Possíveis novos erros', value: newErrors.total_potential_errors ?? 0 },
            { label: 'Sugestões de padrão', value: newErrors.pattern_suggestions?.length ?? 0 },
            { label: 'Palavras suspeitas', value: newErrors.frequent_suspicious_words?.length ?? 0 }
        ];

        this.newErrorCoverageRows = this.mapGenericObject(newErrors.analysis_coverage);
        this.potentialErrorRows = (newErrors.potential_errors ?? []).map((item) => this.mapPotentialErrorRow(item));
        this.patternSuggestionRows = (newErrors.pattern_suggestions ?? []).map((item) => this.mapPatternSuggestionRow(item));
        this.suspiciousWordRows = (newErrors.frequent_suspicious_words ?? []).map((item) => ({
            label: item.word,
            value: item.count
        }));
    }

    private buildStructuredBlocks(response: LogAnalysisResponse): void {
        const structured = response.structured_analysis;
        if (!structured?.enabled) {
            this.structuredSummaryCards = [];
            this.structuredSubtypeRows = [];
            this.structuredCategoryRows = [];
            this.specializedInsightRows = [];
            this.specializedRecommendationRows = [];
            this.specializedAccessRows = [];
            this.specializedProgressRows = [];
            this.specializedTabanalysRows = [];
            this.specializedXrefRows = [];
            this.specializedLogixCommandRows = [];
            this.specializedLogixProgramRows = [];
            return;
        }

        this.structuredSummaryCards = [
            { label: 'Eventos estruturados', value: structured.total_events ?? 0 },
            { label: 'Tipos estruturados', value: Object.keys(structured.type_breakdown ?? {}).length },
            { label: 'Subtipos detectados', value: Object.keys(structured.subtype_breakdown ?? {}).length },
            { label: 'Categorias estruturadas', value: Object.keys(structured.category_breakdown ?? {}).length }
        ];

        this.structuredSubtypeRows = this.mapBreakdown(structured.subtype_breakdown);
        this.structuredCategoryRows = this.mapBreakdown(structured.category_breakdown);

        const specialized = structured.specialized_metrics;
        this.specializedInsightRows = this.mapBreakdown(specialized?.insight_tags);
        this.specializedRecommendationRows = this.mapBreakdown(specialized?.recommendation_hints)
            .map((item) => ({ ...item, label: this.formatRecommendationHint(String(item.label)) }));
        this.specializedAccessRows = (specialized?.access_kpis?.top_5xx_routes ?? []).map((item) => ({
            label: item.route,
            value: item.count,
            detail: 'Rotas com maior incidência de HTTP 5xx'
        }));
        this.specializedProgressRows = [
            ...(specialized?.progress_kpis?.top_programs ?? []).map((item) => ({
                label: item.program_name,
                value: item.count,
                detail: 'Programa Progress/PASOE/AppServer recorrente'
            })),
            ...(specialized?.progress_kpis?.broker_incidents ?? []).map((item) => ({
                label: item.broker_name,
                value: item.count,
                detail: 'Incidentes associados ao broker'
            }))
        ];
        this.specializedTabanalysRows = (specialized?.tabanalys_kpis?.top_objects ?? []).map((item) => ({
            label: item.object_name,
            value: item.count,
            detail: 'Tabela ou índice mais recorrente no TabAnalys'
        }));
        this.specializedXrefRows = this.mapBreakdown(specialized?.xref_kpis?.type_breakdown);
        this.specializedLogixCommandRows = (specialized?.logix_kpis?.top_command_types ?? []).map((item) => ({
            label: item.command_type,
            value: item.count,
            detail: 'Tipo de comando SQL/LOGIX encontrado'
        }));
        this.specializedLogixProgramRows = (specialized?.logix_kpis?.top_programs ?? []).map((item) => ({
            label: item.program_name,
            value: item.count,
            detail: 'Programa LOGIX mapeado no parser estruturado'
        }));
    }

    private buildPerformanceBlocks(response: LogAnalysisResponse): void {
        const performance = response.performance_analysis;
        if (!performance) {
            this.performanceSummaryCards = [];
            this.slowProgramRows = [];
            this.slowOperationRows = [];
            this.topMethodRows = [];
            this.specificAlertRows = [];
            this.performanceHealthScore = null;
            this.performanceHealthLabel = 'Sem dados suficientes';
            this.performanceHealthHelper = 'O log precisa trazer tempos, chamadas ou falhas para compor este indicador.';
            this.performanceHealthReasons = [];
            this.performanceHealthTagType = PoTagType.Info;
            return;
        }

        const health = this.calculatePerformanceHealth(performance);
        this.performanceHealthScore = health.score;
        this.performanceHealthLabel = health.label;
        this.performanceHealthHelper = health.helper;
        this.performanceHealthReasons = health.reasons;
        this.performanceHealthTagType = health.tagType;

        this.performanceSummaryCards = [
            { label: 'Saúde da performance', value: health.score === null ? 'N/D' : `${health.score} / 100` },
            { label: 'Tipo de log', value: performance.log_type ?? response.log_type ?? '-' },
            { label: 'Amostras resposta', value: performance.response_time_stats?.['total_samples'] ?? 0 },
            { label: 'Programas lentos', value: performance.slow_programs_stats?.['total_slow_programs'] ?? performance.slow_programs?.length ?? 0 },
            { label: 'Chamadas totais', value: performance.call_analysis?.total_calls ?? 0 },
            { label: 'Queries mapeadas', value: performance.database_queries?.length ?? 0 },
            { label: 'Tempo rastreado (ms)', value: performance.program_analysis?.total_tracked_program_time_ms ?? 0 }
        ];

        this.slowProgramRows = (performance.slow_programs ?? []).slice(0, 15).map((item) => ({
            label: String(item['program'] ?? '-'),
            value: `${Number(item['duration_ms'] ?? 0)} ms`,
            detail: `Linha ${item['line'] ?? '-'} • ${item['severity'] ?? '-'} • ${item['timestamp'] ?? '-'} • ${Number(item['percent_of_total_tracked_time'] ?? 0).toFixed(2)}%`
        }));

        this.slowOperationRows = (performance.slow_operations ?? []).slice(0, 15).map((item) => ({
            label: String(item['keyword'] ?? '-'),
            value: `Linha ${item['line'] ?? '-'}`,
            detail: String(item['message'] ?? '-')
        }));

        this.topMethodRows = (performance.call_analysis?.top_methods ?? []).slice(0, 15).map((item) => ({
            label: item.method,
            value: item.count,
            share: `${Number(item.percent_of_total_calls ?? 0).toFixed(2)}%`
        }));

        const alerts = performance.specific_alerts;
        this.specificAlertRows = [
            {
                label: 'UPC detectado',
                value: alerts?.upc_count ?? 0,
                detail: alerts?.upc_detected ? 'Ocorrências UPC encontradas no log.' : 'Sem UPC detectado.'
            },
            {
                label: 'ESPEC detectado',
                value: alerts?.espec_count ?? 0,
                detail: alerts?.espec_detected ? 'Ocorrências ESPEC encontradas no log.' : 'Sem ESPEC detectado.'
            },
            {
                label: 'Procedures em erro',
                value: alerts?.procedure_error_count ?? 0,
                detail: alerts?.procedure_in_errors ? 'Erros com procedure foram encontrados.' : 'Sem procedures associadas a erros.'
            }
        ];
    }

    private calculatePerformanceHealth(performance: PerformanceAnalysisResponse): PerformanceHealthSummary {
        let score = 100;
        let hasSignals = false;
        const reasons: string[] = [];

        const responseSamples = this.readMetric(performance.response_time_stats, 'total_samples');
        const responseAverageMs = this.readMetric(performance.response_time_stats, 'average');
        if (responseSamples > 0) {
            hasSignals = true;
            if (responseAverageMs >= 5000) {
                score -= 35;
                reasons.push(`Latência média alta: ${responseAverageMs.toFixed(0)} ms em ${responseSamples} amostras.`);
            } else if (responseAverageMs >= 2500) {
                score -= 25;
                reasons.push(`Latência média relevante: ${responseAverageMs.toFixed(0)} ms em ${responseSamples} amostras.`);
            } else if (responseAverageMs >= 1000) {
                score -= 15;
                reasons.push(`Latência média de atenção: ${responseAverageMs.toFixed(0)} ms.`);
            } else if (responseAverageMs >= 500) {
                score -= 8;
                reasons.push(`Latência média moderada: ${responseAverageMs.toFixed(0)} ms.`);
            }
        }

        const criticalSlowPrograms = this.readMetric(performance.slow_programs_stats, 'critical_count');
        const highSlowPrograms = this.readMetric(performance.slow_programs_stats, 'high_count');
        const mediumSlowPrograms = this.readMetric(performance.slow_programs_stats, 'medium_count');
        if ((criticalSlowPrograms + highSlowPrograms + mediumSlowPrograms) > 0) {
            hasSignals = true;
            if (criticalSlowPrograms > 0) {
                score -= Math.min(criticalSlowPrograms * 18, 36);
                reasons.push(`${criticalSlowPrograms} programa(s) crítico(s) acima de 5 s.`);
            }
            if (highSlowPrograms > 0) {
                score -= Math.min(highSlowPrograms * 10, 25);
                reasons.push(`${highSlowPrograms} programa(s) lentos acima de 3 s.`);
            }
            if (mediumSlowPrograms > 0) {
                score -= Math.min(mediumSlowPrograms * 4, 12);
                reasons.push(`${mediumSlowPrograms} programa(s) em faixa de atenção acima de 2 s.`);
            }
        }

        const slowOperationsCount = performance.slow_operations?.length ?? 0;
        if (slowOperationsCount > 0) {
            hasSignals = true;
            if (slowOperationsCount >= 20) {
                score -= 12;
            } else if (slowOperationsCount >= 10) {
                score -= 8;
            } else if (slowOperationsCount >= 3) {
                score -= 4;
            }
            reasons.push(`${slowOperationsCount} operação(ões) com palavra-chave de lentidão ou espera.`);
        }

        const totalConnections = this.readMetric(performance.connection_stats, 'total_connections');
        const failedConnections = this.readMetric(performance.connection_stats, 'failed_connections');
        const timeoutConnections = this.readMetric(performance.connection_stats, 'timeout_connections');
        if (totalConnections > 0) {
            hasSignals = true;
            const unstableConnections = failedConnections + timeoutConnections;
            const unstableRate = unstableConnections > 0 ? (unstableConnections / totalConnections) * 100 : 0;
            if (unstableRate >= 40) {
                score -= 20;
                reasons.push(`Taxa alta de falha/timeout em conexões: ${unstableRate.toFixed(0)}%.`);
            } else if (unstableRate >= 20) {
                score -= 12;
                reasons.push(`Taxa de falha/timeout em conexões exige atenção: ${unstableRate.toFixed(0)}%.`);
            } else if (unstableRate >= 10) {
                score -= 6;
                reasons.push(`Falhas pontuais de conexão: ${unstableRate.toFixed(0)}% do total.`);
            }
        }

        const peakPeriods = performance.throughput?.peak_periods?.length ?? 0;
        if (peakPeriods > 0) {
            hasSignals = true;
            if (peakPeriods >= 5) {
                score -= 10;
            } else if (peakPeriods >= 2) {
                score -= 5;
            }
            reasons.push(`${peakPeriods} janela(s) com pico de throughput acima da média.`);
        }

        const totalCalls = Number(performance.call_analysis?.total_calls ?? 0);
        if (totalCalls > 0) {
            hasSignals = true;
        }

        if (!hasSignals) {
            return {
                score: null,
                label: 'Sem amostras suficientes',
                helper: 'O backend retornou o bloco de performance, mas sem tempos, falhas ou chamadas suficientes para consolidar a saúde.',
                reasons: ['Use um log com tempos de execução, erros de conexão ou trechos de performance para preencher o indicador.'],
                tagType: PoTagType.Info
            };
        }

        score = Math.max(0, Math.min(100, Math.round(score)));

        if (score >= 80) {
            return {
                score,
                label: 'Saudável',
                helper: 'Os indicadores não apontam degradação relevante no log analisado.',
                reasons: reasons.length > 0 ? reasons : ['Sem sinais relevantes de lentidão, saturação ou falhas recorrentes.'],
                tagType: PoTagType.Success
            };
        }

        if (score >= 55) {
            return {
                score,
                label: 'Atenção moderada',
                helper: 'Há sinais de impacto, mas ainda sem caracterizar degradação crítica.',
                reasons,
                tagType: PoTagType.Warning
            };
        }

        return {
            score,
            label: 'Investigação prioritária',
            helper: 'Os indicadores sugerem degradação importante de performance neste log.',
            reasons,
            tagType: PoTagType.Danger
        };
    }

    private readMetric(source: Record<string, unknown> | undefined, key: string): number {
        const value = source?.[key];
        const numericValue = Number(value);
        return Number.isFinite(numericValue) ? numericValue : 0;
    }

    private buildFallbackDescription(type: string, preview: string): string {
        if (type && type !== '-') {
            return `Ocorrência classificada como ${type}.`;
        }
        return `Linha sinalizada pela análise automática: ${preview.slice(0, 120)}`;
    }

    private buildFallbackSolution(type: string, severity: string, preview: string): string {
        if ((type || '').toLowerCase().includes('timeout')) {
            return 'Validar tempo de resposta, concorrência, banco de dados e integrações envolvidas.';
        }
        if ((severity || '').toLowerCase().includes('alta') || (severity || '').toLowerCase().includes('cr')) {
            return 'Revisar imediatamente a causa raiz, dependências do processo e impacto operacional antes de nova execução.';
        }
        return `Revisar o contexto da linha, validar parâmetros do processo e confirmar se a ocorrência em "${preview.slice(0, 60)}" realmente exige tratamento.`;
    }

    private extractInformationalPattern(item: InformationalLineItem): string {
        const detectedPattern = item.detected_pattern?.trim();
        if (detectedPattern) {
            return detectedPattern;
        }

        const normalized = item.message.replace(/\s+/g, ' ').trim();
        return normalized.length > 160 ? `${normalized.slice(0, 160)}...` : normalized;
    }

    private formatMostCommonError(value: unknown): string {
        if (Array.isArray(value) && value.length >= 2) {
            return `${value[0]} (${value[1]})`;
        }
        return String(value ?? '-');
    }

        private mapBreakdown(source?: Record<string, unknown>): StructuredMetricRow[] {
        return Object.entries(source ?? {})
            .sort(([, valueA], [, valueB]) => (Number(valueB) || 0) - (Number(valueA) || 0))
            .map(([label, value]) => ({ label, value: Number(value) || 0 }));
    }

    private mapGenericObject(source?: Record<string, unknown>): StructuredMetricRow[] {
        return Object.entries(source ?? {}).map(([label, value]) => ({
            label: this.formatDomainLabel(label),
            value: this.formatDomainValue(value)
        }));
    }

    private mapPotentialErrorRow(item: PotentialNewErrorItem): PotentialErrorTableItem {
        return {
            line: item.line,
            confidence: item.confidence,
            suggestedPattern: item.suggested_pattern,
            suspiciousWords: (item.suspicious_words ?? []).join(', '),
            message: item.message
        };
    }

    private mapPatternSuggestionRow(item: PatternSuggestionItem): PatternSuggestionTableItem {
        return {
            pattern: item.pattern,
            frequency: item.frequency,
            suggestedRegex: item.suggested_regex
        };
    }

    private mapDomainFields(fields?: Record<string, unknown>): DomainFieldEntry[] {
        return Object.entries(fields ?? {})
            .filter(([, value]) => this.hasRenderableDomainValue(value))
            .map(([key, value]) => ({
                label: this.formatDomainLabel(key),
                value: this.formatDomainValue(value)
            }));
    }

    private hasRenderableDomainValue(value: unknown): boolean {
        if (value === null || value === undefined || value === '') {
            return false;
        }

        if (Array.isArray(value)) {
            return value.length > 0;
        }

        return true;
    }

    private formatDomainLabel(key: string): string {
        const dictionary: Record<string, string> = {
            client_ip: 'IP do cliente',
            http_method: 'Método HTTP',
            path: 'Path',
            route: 'Rota',
            query_string: 'Query string',
            status_code: 'Status',
            status_family: 'Família HTTP',
            response_size_bytes: 'Tamanho resposta',
            route_depth: 'Profundidade da rota',
            logger_name: 'Logger',
            thread_name: 'Thread',
            web_component: 'Componente web',
            servlet_name: 'Servlet',
            deployment_name: 'Deployment',
            lifecycle_event: 'Evento lifecycle',
            process_id: 'Processo',
            thread_id: 'Thread ID',
            component: 'Componente',
            program_path: 'Programa',
            program_name: 'Nome do programa',
            procedure_name: 'Procedure',
            database_name: 'Banco',
            error_code: 'Código',
            duration_ms: 'Duração (ms)',
            broker_name: 'Broker',
            agent_name: 'Agente',
            analysis_type: 'Tipo de análise',
            missing_variable: 'Variável ausente',
            class_name: 'Classe',
            method_name: 'Método',
            table_name: 'Tabela',
            index_name: 'Índice',
            record_count: 'Registros',
            field_count: 'Campos',
            factor: 'Factor',
            observation: 'Observação',
            full_scan: 'Full scan',
            xref_type: 'Tipo XREF',
            source_program: 'Programa origem',
            target_program: 'Programa destino',
            key_name: 'Chave',
            parameters: 'Parâmetros',
            return_type: 'Retorno',
            source_routine: 'Rotina origem',
            source_file: 'Arquivo fonte',
            missing_file: 'Arquivo ausente',
            sequence_flag: 'Sequência',
            global_flag: 'Global',
            shared_flag: 'Shared',
            persistent_flag: 'Persistente',
            translatable_flag: 'Traduzível',
            line_number_ref: 'Linha XREF',
            source_line: 'Linha fonte',
            rows_affected: 'Rows affected',
            sql_command: 'Comando SQL',
            command_type: 'Tipo comando',
            running_time_ms: 'Tempo execução (ms)',
            module: 'Módulo'
        };

        return dictionary[key] ?? key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
    }

    private formatDomainValue(value: unknown): string {
        if (typeof value === 'boolean') {
            return value ? 'Sim' : 'Não';
        }

        if (Array.isArray(value)) {
            return value.map((item) => String(item)).join(', ');
        }

        if (typeof value === 'object' && value !== null) {
            return JSON.stringify(value);
        }

        return String(value);
    }

    private formatRecommendationHint(value: string | undefined): string {
        if (!value || value === '-') {
            return '-';
        }

        const dictionary: Record<string, string> = {
            investigate_server_error: 'Investigar erro de servidor',
            review_client_request: 'Revisar requisição do cliente',
            review_redirect_chain: 'Revisar cadeia de redirecionamento',
            monitor_http_traffic: 'Monitorar tráfego HTTP',
            inspect_pasoe_web_stack: 'Inspecionar stack web do PASOE',
            review_pasoe_lifecycle: 'Revisar ciclo de vida do PASOE',
            verify_pasoe_availability: 'Verificar disponibilidade do PASOE',
            inspect_java_application: 'Inspecionar aplicação Java',
            inspect_java_stacktrace: 'Inspecionar stacktrace Java',
            review_java_performance: 'Revisar performance Java',
            inspect_progress_flow: 'Inspecionar fluxo Progress',
            inspect_progress_program: 'Inspecionar programa Progress',
            review_slow_program: 'Revisar programa lento',
            review_database_dependency: 'Revisar dependência de banco',
            investigate_agent_pool: 'Investigar pool de agentes',
            verify_broker_availability: 'Verificar disponibilidade do broker',
            review_dispatch_queue: 'Revisar fila de dispatch',
            investigate_appserver_crash: 'Investigar queda do AppServer',
            verify_appserver_availability: 'Verificar disponibilidade do AppServer',
            urgent_dump_load: 'Executar DUMP/LOAD urgente',
            review_table_fragmentation: 'Revisar fragmentação da tabela',
            urgent_reindex: 'Executar reindexação urgente',
            review_index_fragmentation: 'Revisar fragmentação do índice',
            review_full_scan_reference: 'Revisar referência com full scan',
            review_global_shared_usage: 'Revisar uso de globais/shared',
            review_persistent_run: 'Revisar RUN persistente',
            review_xref_dependencies: 'Revisar dependências XREF',
            review_logix_sql: 'Revisar SQL do LOGIX',
            review_logix_xml_validation: 'Revisar validação XML do LOGIX',
            verify_logix_integration: 'Verificar integração do LOGIX',
            inspect_logix_framework: 'Inspecionar framework do LOGIX',
            inspect_logix_application: 'Inspecionar aplicação LOGIX'
        };

        return dictionary[value] ?? value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
    }

    private pickStatistic(source: Record<string, unknown>, candidates: string[]): string | number {
        for (const candidate of candidates) {
            const value = source[candidate];
            if (typeof value === 'string' || typeof value === 'number') {
                return value;
            }
        }

        return '-';
    }

    private resolveNonErrorPattern(): string {
        if (this.nonErrorSelectionMode === 'full') {
            return this.nonErrorFullLine.trim();
        }

        if (this.nonErrorSelectionMode === 'custom') {
            return this.nonErrorPartialPattern.trim();
        }

        return (this.selectedError?.suggestedPattern || this.nonErrorPartialPattern || this.extractAutomaticPattern(this.nonErrorFullLine)).trim();
    }

    private isCompactViewport(): boolean {
        return typeof window !== 'undefined' && window.innerWidth <= 960;
    }

    private removeCurrentNonErrorItem(): void {
        if (!this.selectedError) {
            return;
        }

        if (this.selectedError.kind === 'result') {
            this.resultRows = this.resultRows.filter((item) => !(item.lineNumber === this.selectedError?.lineNumber && item.preview === this.selectedError?.message));
            this.expandedResultRows.delete(`${this.selectedError.lineNumber}::${this.selectedError.message}`);
        } else {
            this.potentialErrorRows = this.potentialErrorRows.filter((item) => !(item.line === this.selectedError?.lineNumber && item.message === this.selectedError?.message));
        }

        this.ensureSelectedResultRow();
        this.syncCurrentSession();
    }

    private syncCurrentSession(): void {
        if (!this.analysisResult) {
            return;
        }

        const updatedResult: LogAnalysisResponse = {
            ...this.analysisResult,
            total_results: this.resultRows.length,
            results: this.analysisResult.results.filter((item) => this.resultRows.some((row) => this.matchesResultRow(item, row))),
            informational_lines: [...this.informationalLines],
            new_errors: this.analysisResult.new_errors ? {
                ...this.analysisResult.new_errors,
                potential_errors: (this.analysisResult.new_errors.potential_errors ?? [])
                    .filter((item) => this.potentialErrorRows.some((row) => this.matchesPotentialErrorRow(item, row))),
                total_potential_errors: this.potentialErrorRows.length
            } : this.analysisResult.new_errors
        };

        this.analysisResult = updatedResult;
        this.summaryCards = this.buildSummaryCards(updatedResult);
        this.highlightedStats = this.buildHighlightedStats(updatedResult);
        this.buildNewErrorsBlocks(updatedResult);
        this.session.save(updatedResult, this.analyzedFilename || 'log');
    }

    private applyAnalysisResult(result: LogAnalysisResponse, filename: string, analyzedAt: string): void {
        this.loading = false;
        this.analysisResult = result;
        this.analyzedFilename = filename;
        this.analyzedAt = analyzedAt;
        this.resultRows = (result.results ?? []).map((item) => this.mapResultRow(item));
        this.expandedResultRows = new Set();
        this.selectedResultRow = this.resultRows[0] ?? null;
        this.summaryCards = this.buildSummaryCards(result);
        this.highlightedStats = this.buildHighlightedStats(result);
        this.attentionPoints = result.attention_points ?? [];
        this.informationalLines = result.informational_lines ?? [];
        this.topProgramRows = result.top_programs_methods?.top_programs ?? [];
        this.buildBackendSummaryBlocks(result);
        this.buildNewErrorsBlocks(result);
        this.buildStructuredBlocks(result);
        this.buildPerformanceBlocks(result);
        this.session.save(result, filename);
    }

    private ensureSelectedResultRow(): void {
        const current = this.currentResultDetail;
        this.selectedResultRow = current;
    }

    private getResultRowKey(row: AnalysisDetailRow): string {
        return `${row.lineNumber}::${row.preview}`;
    }

    private isViewAvailable(view: AnalysisInsightView): boolean {
        switch (view) {
            case 'linhas':
            case 'geral':
                return true;
            case 'performance':
                return this.hasPerformanceData;
            case 'novos-erros':
                return this.hasNewErrorsData;
            case 'estruturado':
                return this.hasStructuredDetails;
            case 'atencao':
                return this.attentionPoints.length > 0;
            case 'informativas':
                return this.informationalLines.length > 0;
        }
    }

    private matchesResultRow(item: AnalysisResultItem, row: AnalysisDetailRow): boolean {
        const lineValue = item.line_number ?? item.line ?? '-';
        const preview = this.resolveResultPreview(item);

        return String(lineValue) === String(row.lineNumber) && preview === row.preview;
    }

    private resolveResultPreview(item: AnalysisResultItem): string {
        return String(item.line_text ?? item.content ?? item.message ?? item.clean_message ?? '-');
    }

    private matchesPotentialErrorRow(item: PotentialNewErrorItem, row: PotentialErrorTableItem): boolean {
        return item.line === row.line && item.message === row.message;
    }

    private extractAutomaticPattern(message: string): string {
        const words = message.split(' ').map((word) => word.trim()).filter((word) => word.length > 2);
        if (words.length > 0) {
            return words.slice(0, Math.min(3, words.length)).join(' ');
        }

        return message.substring(0, 50);
    }
}
