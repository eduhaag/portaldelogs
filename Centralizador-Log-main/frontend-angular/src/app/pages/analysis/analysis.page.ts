import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, ElementRef, OnInit, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
    PoButtonModule,
    PoCheckboxModule,
    PoDropdownAction,
    PoDropdownModule,
    PoFieldModule,
    PoIconModule,
    PoInfoModule,
    PoLoadingModule,
    PoModalComponent,
    PoModalModule,
    PoPageModule,
    PoSelectOption,
    PoTableColumn,
    PoTableModule,
    PoTabsModule,
    PoTagModule,
    PoWidgetModule
} from '@po-ui/ng-components';
import { finalize, forkJoin } from 'rxjs';

import {
    AnalysisChangeRecord,
    AnalysisChangesResponse,
    AnalysisHistoryItem,
    AnalyzeInfoResponse,
    AttentionPointItem,
    CustomPatternRecord,
    CustomPatternsResponse,
    DatasulPatternRecord,
    DatasulPatternsResponse,
    DatasulStatistics,
    DatasulStatisticsResponse,
    ErrorCategorizationsResponse,
    InformationalLineItem,
    KnowledgeBaseMatch,
    LogCategoryInfoResponse,
    LogAnalysisResponse,
    NonErrorPatternRecord,
    NonErrorPatternsResponse,
    PatternTestResponse,
    ProfilerAnalysisPayload,
    ProfilerResponse,
    SaveAnalysisChangesPayload,
    TopProgramMethodItem
    , VersionCompareEntry
    , VersionCompareResponse
    , VersionCompareStatusResponse
} from '../../core/models/api.models';
import { AnalysisSessionService } from '../../core/services/analysis-session.service';
import { BackendApiService } from '../../core/services/backend-api.service';
import { ProfilerSessionService } from '../../core/services/profiler-session.service';
import { VersionCompareSessionService } from '../../core/services/version-compare-session.service';

interface ActionCard {
    title: string;
    description: string;
    icon: string;
    actionLabel: string;
    theme: 'primary' | 'default';
}

interface CleanerCategoryItem {
    key: string;
    displayName: string;
    count: number;
    samples: string[];
}

interface SplitLogResultStats {
    original_filename: string;
    total_lines: number;
    lines_per_chunk: number;
    generated_files: number;
}

interface ProfilerTableItem {
    program: string;
    duration: string | number;
    calls: string | number;
}

interface ProfilerModuleRow {
    module: string;
    calls: string | number;
    totalTimeMs: string | number;
    avgTimeMs: string | number;
}

interface ProfilerIssueRow {
    module: string;
    issues: string;
    calls: string | number;
    totalTimeMs: string | number;
}

interface ProfilerCallTreeRow {
    name: string;
    calls: string | number;
    totalTimeMs: string | number;
    percent: string | number;
    childrenCount: string | number;
}

interface RecommendationRow {
    recommendation: string;
}

interface VersionCompareTableItem {
    programa: string;
    versao_extrato: string;
    versao_correta: string;
    fix_encontrada: string;
    diferenca_builds: string | number;
}

interface UpcTableItem {
    programa: string;
}

interface AnalysisTableItem {
    lineNumber: number | string;
    severity: string;
    category: string;
    type: string;
    matchedPattern: string;
    preview: string;
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

interface AnalysisHistoryTableItem {
    timestamp: string;
    filename: string;
    totalResults: number;
    mostCommonError: string;
}

interface KnowledgeTableItem {
    type: string;
    code: string;
    category: string;
    severity: string;
    source: string;
    description: string;
}

interface DatasulPatternTableItem {
    pattern: string;
    category: string;
    severity: string;
    tag: string;
    priority: number | string;
    usageCount: number | string;
}

interface ReviewCandidate {
    lineNumber: number | string;
    severity: string;
    category: string;
    type: string;
    matchedPattern: string;
    preview: string;
}

interface CustomPatternFormValue {
    pattern: string;
    partial_pattern: string;
    description: string;
    category: string;
    severity: string;
    example: string;
    solution: string;
}

@Component({
    selector: 'app-analysis-page',
    standalone: true,
    imports: [CommonModule, FormsModule, PoPageModule, PoWidgetModule, PoButtonModule, PoCheckboxModule, PoDropdownModule, PoTableModule, PoLoadingModule, PoModalModule, PoInfoModule, PoTagModule, PoFieldModule, PoIconModule, PoTabsModule],
    templateUrl: './analysis.page.html',
    styleUrl: './analysis.page.scss'
})
export class AnalysisPageComponent implements OnInit, AfterViewInit {
    @ViewChild('dashboardStart') dashboardStart?: ElementRef<HTMLDivElement>;
    @ViewChild('patternModal') patternModal?: PoModalComponent;
    @ViewChild('cleanerModal') cleanerModal?: PoModalComponent;
    @ViewChild('splitterModal') splitterModal?: PoModalComponent;
    @ViewChild('profilerModal') profilerModal?: PoModalComponent;
    @ViewChild('versionCompareModal') versionCompareModal?: PoModalComponent;
    @ViewChild('performanceModal') performanceModal?: PoModalComponent;
    @ViewChild('knowledgeModal') knowledgeModal?: PoModalComponent;
    @ViewChild('datasulModal') datasulModal?: PoModalComponent;

    private readonly api = inject(BackendApiService);
    private readonly analysisSession = inject(AnalysisSessionService);
    private readonly profilerSession = inject(ProfilerSessionService);
    private readonly router = inject(Router);
    private readonly versionCompareSession = inject(VersionCompareSessionService);

    protected readonly actionCards: ActionCard[] = [
        {
            title: 'Analisar log',
            description: 'Envie um arquivo .log, .txt ou .out e execute a leitura com base nas regras do backend.',
            icon: 'po-icon-upload',
            actionLabel: 'Abrir página',
            theme: 'primary'
        },
        {
            title: 'Novo padrão',
            description: 'Cadastre um novo padrão com validação, descrição, severidade e exemplo funcional.',
            icon: 'po-icon-plus',
            actionLabel: 'Cadastrar',
            theme: 'default'
        },
        {
            title: 'Limpar log',
            description: 'Analise categorias do log e remova somente os blocos que não deseja manter.',
            icon: 'po-icon-filter',
            actionLabel: 'Selecionar categorias',
            theme: 'default'
        },
        {
            title: 'Profiler',
            description: 'Carregue o arquivo .out do Progress Profiler e visualize o retorno em grid PO UI.',
            icon: 'po-icon-chart-bar',
            actionLabel: 'Analisar .out',
            theme: 'default'
        }
    ];

    protected logFile: File | null = null;
    protected patternsFile: File | null = null;
    protected cleanerFile: File | null = null;
    protected splitterFile: File | null = null;
    protected profilerFile: File | null = null;
    protected versionCompareFile: File | null = null;
    protected previewInfo: AnalyzeInfoResponse | null = null;
    protected cleanerCategoryAnalysis: LogCategoryInfoResponse | null = null;
    protected analysisResult: LogAnalysisResponse | null = null;
    protected profilerResult: ProfilerResponse | null = null;
    protected versionCompareResult: VersionCompareResponse | null = null;
    protected versionCompareStatus: VersionCompareStatusResponse | null = null;
    protected tableItems: AnalysisTableItem[] = [];
    protected summaryCards: Array<{ label: string; value: string | number }> = [];
    protected highlightedStats: Array<{ label: string; value: string | number }> = [];
    protected attentionPoints: AttentionPointItem[] = [];
    protected informationalLines: InformationalLineItem[] = [];
    protected structuredSummaryCards: Array<{ label: string; value: string | number }> = [];
    protected structuredTypeRows: BreakdownItem[] = [];
    protected structuredSubtypeRows: BreakdownItem[] = [];
    protected structuredCategoryRows: BreakdownItem[] = [];
    protected httpStatusRows: BreakdownItem[] = [];
    protected javaExceptionRows: BreakdownItem[] = [];
    protected performanceSummaryCards: Array<{ label: string; value: string | number }> = [];
    protected slowProgramRows: PerformanceTableItem[] = [];
    protected slowOperationRows: PerformanceTableItem[] = [];
    protected topMethodRows: MethodCallRow[] = [];
    protected topProgramRows: TopProgramMethodItem[] = [];
    protected specificAlertRows: PerformanceTableItem[] = [];
    protected historyRows: AnalysisHistoryTableItem[] = [];
    protected reviewCandidates: ReviewCandidate[] = [];
    protected selectedReviewCandidate: ReviewCandidate | null = null;
    protected customPatternForm: CustomPatternFormValue = this.createEmptyCustomPatternForm();
    protected patternTestResult: PatternTestResponse | null = null;
    protected customPatterns: CustomPatternRecord[] = [];
    protected permanentPatterns: CustomPatternRecord[] = [];
    protected sessionPatterns: CustomPatternRecord[] = [];
    protected nonErrorPatterns: NonErrorPatternRecord[] = [];
    protected analysisChanges: AnalysisChangeRecord[] = [];
    protected knowledgeSearchTerm = '';
    protected knowledgeLoading = false;
    protected knowledgeTotalFound = 0;
    protected knowledgeReturnedCount = 0;
    protected knowledgeResultLimit = 0;
    protected knowledgeTruncated = false;
    protected knowledgeSourceStats: Array<{ key: string; value: number }> = [];
    protected knowledgeMatches: KnowledgeBaseMatch[] = [];
    protected knowledgeTableItems: KnowledgeTableItem[] = [];
    protected knowledgeFilteredItems: KnowledgeTableItem[] = [];
    protected selectedKnowledgeMatch: KnowledgeBaseMatch | null = null;
    protected knowledgeSourceFilter = 'all';
    protected knowledgeSeverityFilter = 'all';
    protected knowledgeRecentTerms: string[] = [];
    protected datasulPatterns: DatasulPatternRecord[] = [];
    protected datasulStatistics: DatasulStatistics | null = null;
    protected datasulLoading = false;
    protected cleanerCategoryItems: CleanerCategoryItem[] = [];
    protected selectedCleanerCategories: string[] = [];
    protected cleanerStep = 1;
    protected cleanerResultStats: Record<string, unknown> | null = null;
    protected splitLinesPerChunk = 50000;
    protected splitLoading = false;
    protected splitResultStats: SplitLogResultStats | null = null;
    protected profilerSummaryCards: Array<{ label: string; value: string | number }> = [];
    protected loading = false;
    protected cleanerLoading = false;
    protected exporting = false;
    protected historyLoading = false;
    protected managementLoading = false;
    protected profilerLoading = false;
    protected versionCompareLoading = false;
    protected successMessage = '';
    protected categorizationDescription = '';
    protected nonErrorReason = '';
    protected manualChangeNotes = '';
    protected errorMessage = '';
    protected readonly quickInsights = [
        'Use a pré-análise para estimar custo antes do processamento completo.',
        'O arquivo opcional de padrões complementa o matcher do backend.',
        'Os gráficos usam `chart_data`, `error_counts` e `severity_counts` do FastAPI.'
    ];

    protected get dashboardStats(): Array<{ label: string; value: string | number; detail: string }> {
        return [
            {
                label: 'Histórico',
                value: this.historyRows.length,
                detail: 'análises registradas'
            },
            {
                label: 'Padrões ativos',
                value: this.customPatterns.length,
                detail: 'customizações carregadas'
            },
            {
                label: 'Base local',
                value: this.nonErrorPatterns.length,
                detail: 'não-erros catalogados'
            }
        ];
    }

    protected readonly resultColumns: PoTableColumn[] = [
        { property: 'lineNumber', label: 'Linha', width: '90px' },
        { property: 'severity', label: 'Severidade', width: '120px' },
        { property: 'category', label: 'Categoria', width: '180px' },
        { property: 'type', label: 'Tipo', width: '160px' },
        { property: 'matchedPattern', label: 'Padrão' },
        { property: 'preview', label: 'Trecho' }
    ];

    protected readonly historyColumns: PoTableColumn[] = [
        { property: 'timestamp', label: 'Quando', width: '190px' },
        { property: 'filename', label: 'Arquivo' },
        { property: 'totalResults', label: 'Resultados', width: '120px' },
        { property: 'mostCommonError', label: 'Erro mais comum' }
    ];

    protected readonly knowledgeColumns: PoTableColumn[] = [
        { property: 'type', label: 'Tipo', width: '140px' },
        { property: 'code', label: 'Código', width: '140px' },
        { property: 'category', label: 'Categoria', width: '180px' },
        { property: 'severity', label: 'Severidade', width: '130px' },
        { property: 'source', label: 'Origem' },
        { property: 'description', label: 'Descrição' }
    ];

    protected readonly datasulPatternColumns: PoTableColumn[] = [
        { property: 'pattern', label: 'Padrão' },
        { property: 'category', label: 'Categoria', width: '180px' },
        { property: 'severity', label: 'Severidade', width: '130px' },
        { property: 'tag', label: 'Tag', width: '160px' },
        { property: 'priority', label: 'Prioridade', width: '110px' },
        { property: 'usageCount', label: 'Uso', width: '90px' }
    ];

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

    protected readonly versionCompareColumns: PoTableColumn[] = [
        { property: 'programa', label: 'Programa' },
        { property: 'versao_extrato', label: 'Versão no extrato' },
        { property: 'versao_correta', label: 'Versão correta' },
        { property: 'fix_encontrada', label: 'Fix' },
        { property: 'diferenca_builds', label: 'Diferença', width: '120px' }
    ];

    protected readonly upcColumns: PoTableColumn[] = [
        { property: 'programa', label: 'Programa com UPC' }
    ];

    protected readonly breakdownColumns: PoTableColumn[] = [
        { property: 'label', label: 'Indicador' },
        { property: 'value', label: 'Valor', width: '120px' }
    ];

    protected readonly topMethodColumns: PoTableColumn[] = [
        { property: 'label', label: 'Método / indicador' },
        { property: 'value', label: 'Chamadas', width: '120px' },
        { property: 'share', label: '% do total', width: '120px' }
    ];

    protected readonly performanceColumns: PoTableColumn[] = [
        { property: 'label', label: 'Indicador' },
        { property: 'value', label: 'Valor', width: '140px' },
        { property: 'detail', label: 'Detalhe' }
    ];

    protected readonly topProgramColumns: PoTableColumn[] = [
        { property: 'program', label: 'Programa' },
        { property: 'method', label: 'Método' },
        { property: 'calls', label: 'Chamadas', width: '110px' },
        { property: 'total_time_ms', label: 'Tempo total (ms)', width: '150px' },
        { property: 'avg_time_ms', label: 'Tempo médio (ms)', width: '150px' },
        { property: 'percent_of_total_time', label: '% do tempo', width: '120px' },
        { property: 'callers_summary', label: 'Callers' }
    ];

    protected readonly customCategoryOptions: PoSelectOption[] = [
        { label: 'User-Categorized', value: 'User-Categorized' },
        { label: 'Infra/PASOE', value: 'Infra/PASOE' },
        { label: 'Infra/Tomcat', value: 'Infra/Tomcat' },
        { label: 'Performance/PASOE', value: 'Performance/PASOE' },
        { label: 'Datasul/NFe', value: 'Datasul/NFe' },
        { label: 'OpenEdge/DB', value: 'OpenEdge/DB' }
    ];

    protected readonly customSeverityOptions: PoSelectOption[] = [
        { label: 'Baixo', value: 'Baixo' },
        { label: 'Médio', value: 'Médio' },
        { label: 'Alta', value: 'Alta' },
        { label: 'Crítico', value: 'Crítico' }
    ];

    protected readonly splitChunkOptions: PoSelectOption[] = [
        { label: '50 mil linhas', value: 50000 },
        { label: '100 mil linhas', value: 100000 },
        { label: '150 mil linhas', value: 150000 },
        { label: '200 mil linhas', value: 200000 },
        { label: '250 mil linhas', value: 250000 }
    ];

    protected readonly knowledgeQuickTerms = ['DataServer', 'Rejeição 999', '18215', 'AppServer', 'PASOE'];

    protected get knowledgeSourceFilterOptions(): PoSelectOption[] {
        return [
            { label: 'Todas', value: 'all' },
            ...this.availableKnowledgeSources.map((source) => ({ label: source, value: source }))
        ];
    }

    protected get knowledgeSeverityFilterOptions(): PoSelectOption[] {
        return [
            { label: 'Todas', value: 'all' },
            ...this.availableKnowledgeSeverities.map((severity) => ({ label: severity, value: severity }))
        ];
    }

    protected get knowledgeActions(): PoDropdownAction[] {
        return [
            {
                label: 'Aplicar DataServer',
                action: () => this.applyKnowledgeQuickTerm('DataServer')
            },
            {
                label: 'Aplicar PASOE',
                action: () => this.applyKnowledgeQuickTerm('PASOE')
            },
            {
                label: 'Limpar filtros',
                action: () => {
                    this.knowledgeSourceFilter = 'all';
                    this.knowledgeSeverityFilter = 'all';
                    this.applyKnowledgeFilters();
                }
            }
        ];
    }

    protected get topActions(): PoDropdownAction[] {
        return [
            {
                label: 'Exportar CSV',
                action: () => this.exportCsv(),
                disabled: this.exporting || !this.logFile
            },
            {
                label: 'Atualizar histórico',
                action: () => this.refreshHistory(),
                disabled: this.historyLoading
            },
            {
                label: 'Limpar formulários de aprendizado',
                action: () => this.clearLearningForms(),
                disabled: this.managementLoading
            },
            {
                label: 'Atualizar catálogo Datasul',
                action: () => this.refreshDatasulCatalog(),
                disabled: this.datasulLoading
            }
        ];
    }

    ngOnInit(): void {
        this.loadHistory();
        this.loadManagementData();
        this.loadDatasulCatalog();
        this.loadVersionCompareStatus();
    }

    ngAfterViewInit(): void {
        queueMicrotask(() => {
            this.closeAllModals();
            this.scrollToDashboard();
        });
    }

    protected onLogFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.logFile = input?.files?.item(0) ?? null;
        this.previewInfo = null;
        this.analysisResult = null;
        this.tableItems = [];
        this.attentionPoints = [];
        this.informationalLines = [];
        this.structuredSummaryCards = [];
        this.structuredTypeRows = [];
        this.structuredSubtypeRows = [];
        this.structuredCategoryRows = [];
        this.httpStatusRows = [];
        this.javaExceptionRows = [];
        this.performanceSummaryCards = [];
        this.slowProgramRows = [];
        this.slowOperationRows = [];
        this.topMethodRows = [];
        this.topProgramRows = [];
        this.specificAlertRows = [];
        this.reviewCandidates = [];
        this.selectedReviewCandidate = null;
        this.patternTestResult = null;
        this.successMessage = '';
        this.errorMessage = '';
    }

    protected onPatternsFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.patternsFile = input?.files?.item(0) ?? null;
    }

    protected onCleanerFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.cleanerFile = input?.files?.item(0) ?? null;
        this.cleanerCategoryAnalysis = null;
        this.cleanerCategoryItems = [];
        this.selectedCleanerCategories = [];
        this.cleanerResultStats = null;
        this.cleanerStep = 1;
        this.errorMessage = '';
        this.successMessage = '';
    }

    protected onSplitterFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.splitterFile = input?.files?.item(0) ?? null;
        this.splitResultStats = null;
        this.errorMessage = '';
        this.successMessage = '';
    }

    protected onProfilerFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.profilerFile = input?.files?.item(0) ?? null;
        this.errorMessage = '';
        this.successMessage = '';
    }

    protected onVersionCompareFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.versionCompareFile = input?.files?.item(0) ?? null;
        this.errorMessage = '';
        this.successMessage = '';
    }

    protected searchKnowledgeBase(): void {
        if (!this.knowledgeSearchTerm.trim()) {
            this.errorMessage = 'Informe um termo para pesquisar na base de conhecimento.';
            return;
        }

        this.knowledgeLoading = true;
        this.errorMessage = '';

        this.api.searchKnowledgeBase(this.knowledgeSearchTerm.trim())
            .pipe(finalize(() => (this.knowledgeLoading = false)))
            .subscribe({
                next: (response) => {
                    this.knowledgeTotalFound = response.total_found;
                    this.knowledgeReturnedCount = response.returned_count;
                    this.knowledgeResultLimit = response.max_results;
                    this.knowledgeTruncated = response.truncated;
                    this.knowledgeMatches = response.matches;
                    this.knowledgeSourceStats = Object.entries(response.sources).map(([key, value]) => ({ key, value }));
                    this.knowledgeTableItems = response.matches.map((match) => ({
                        type: match.type,
                        code: match.code,
                        category: match.category,
                        severity: match.severity,
                        source: match.source,
                        description: match.description
                    }));
                    this.applyKnowledgeFilters();
                    this.pushKnowledgeRecentTerm(this.knowledgeSearchTerm.trim());
                    this.selectedKnowledgeMatch = response.matches[0] ?? null;
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao consultar a base de conhecimento.';
                }
            });
    }

    protected applyKnowledgeQuickTerm(term: string): void {
        this.knowledgeSearchTerm = term;
    }

    protected selectKnowledgeRecentTerm(term: string): void {
        this.knowledgeSearchTerm = term;
    }

    protected applyKnowledgeFilters(): void {
        this.knowledgeFilteredItems = this.knowledgeTableItems.filter((item) => {
            const sourceMatches = this.knowledgeSourceFilter === 'all' || item.source === this.knowledgeSourceFilter;
            const severityMatches = this.knowledgeSeverityFilter === 'all' || item.severity === this.knowledgeSeverityFilter;
            return sourceMatches && severityMatches;
        });
    }

    protected selectKnowledgeMatch(match: KnowledgeBaseMatch): void {
        this.selectedKnowledgeMatch = match;
    }

    protected previewLog(): void {
        if (!this.logFile) {
            this.errorMessage = 'Selecione um arquivo de log para pré-análise.';
            return;
        }

        this.loading = true;
        this.errorMessage = '';

        this.api.analyzeInfo(this.logFile)
            .pipe(finalize(() => (this.loading = false)))
            .subscribe({
                next: (response) => {
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

        this.api.analyzeLog(this.logFile, this.patternsFile)
            .pipe(finalize(() => (this.loading = false)))
            .subscribe({
                next: (response) => {
                    this.analysisSession.save(response, this.logFile?.name ?? this.previewInfo?.file_info.filename ?? 'log');
                    this.analysisResult = response;
                    this.tableItems = (response.results ?? []).slice(0, 300).map((item) => ({
                        lineNumber: item.line_number ?? item.line ?? '-',
                        severity: item.severity ?? '-',
                        category: item.category ?? '-',
                        type: item.type ?? item.error_type ?? '-',
                        matchedPattern: item.matched_pattern ?? item.error_signature ?? '-',
                        preview: item.message ?? item.clean_message ?? item.content ?? item.line_text ?? '-'
                    }));
                    this.summaryCards = this.buildSummaryCards(response);
                    this.highlightedStats = this.buildHighlightedStats(response);
                    this.attentionPoints = (response.attention_points ?? []).slice(0, 15);
                    this.informationalLines = (response.informational_lines ?? []).slice(0, 15);
                    this.buildStructuredBlocks(response);
                    this.buildPerformanceBlocks(response);
                    this.topProgramRows = response.top_programs_methods?.top_programs ?? [];
                    this.reviewCandidates = this.buildReviewCandidates();
                    if (this.reviewCandidates.length > 0) {
                        this.useReviewCandidate(this.reviewCandidates[0]);
                    }
                    this.loadHistory();
                    void this.router.navigateByUrl('/analise/resultados');
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao analisar o log.';
                }
            });
    }

    protected analyzeCleanerCategories(): void {
        if (!this.cleanerFile) {
            this.errorMessage = 'Selecione um arquivo de log antes de analisar as categorias.';
            return;
        }

        this.cleanerLoading = true;
        this.errorMessage = '';

        this.api.analyzeLogCategories(this.cleanerFile)
            .pipe(finalize(() => (this.cleanerLoading = false)))
            .subscribe({
                next: (response) => {
                    this.cleanerCategoryAnalysis = response;
                    this.cleanerCategoryItems = Object.entries(response.found_categories ?? {})
                        .map(([key, value]) => ({
                            key,
                            displayName: value.display_name,
                            count: value.count,
                            samples: value.samples ?? []
                        }))
                        .sort((left, right) => right.count - left.count);
                    this.selectedCleanerCategories = this.cleanerCategoryItems.map((item) => item.key);
                    this.cleanerStep = 2;
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao analisar categorias do log.';
                }
            });
    }

    protected toggleCleanerCategory(category: string, checked: boolean): void {
        this.selectedCleanerCategories = checked
            ? [...new Set([...this.selectedCleanerCategories, category])]
            : this.selectedCleanerCategories.filter((item) => item !== category);
    }

    protected isCleanerCategorySelected(category: string): boolean {
        return this.selectedCleanerCategories.includes(category);
    }

    protected cleanSelectedCategories(): void {
        if (!this.cleanerFile) {
            this.errorMessage = 'Selecione um arquivo antes de limpar o log.';
            return;
        }

        if (this.selectedCleanerCategories.length === 0) {
            this.errorMessage = 'Selecione pelo menos uma categoria para remover.';
            return;
        }

        this.cleanerLoading = true;
        this.errorMessage = '';

        this.api.cleanLog(this.cleanerFile, this.selectedCleanerCategories)
            .pipe(finalize(() => (this.cleanerLoading = false)))
            .subscribe({
                next: (response) => {
                    const blob = response.body;
                    if (!blob) {
                        this.errorMessage = 'O backend não retornou o arquivo limpo.';
                        return;
                    }

                    const header = response.headers.get('Content-Disposition') ?? '';
                    const filenameMatch = /filename="?([^\"]+)"?/i.exec(header);
                    const filename = filenameMatch?.[1] ?? 'log_limpo.log';
                    const statsHeader = response.headers.get('X-Cleaning-Stats');
                    this.cleanerResultStats = statsHeader ? JSON.parse(statsHeader) as Record<string, unknown> : null;
                    this.saveBlob(blob, filename);
                    this.cleanerStep = 3;
                    this.successMessage = 'Log limpo com sucesso. O download foi iniciado.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao limpar o log.';
                }
            });
    }

    protected resetCleanerWorkflow(): void {
        this.cleanerFile = null;
        this.cleanerCategoryAnalysis = null;
        this.cleanerCategoryItems = [];
        this.selectedCleanerCategories = [];
        this.cleanerResultStats = null;
        this.cleanerStep = 1;
    }

    protected splitLargeLogFile(): void {
        if (!this.splitterFile) {
            this.errorMessage = 'Selecione um arquivo de log antes de dividir.';
            return;
        }

        this.splitLoading = true;
        this.errorMessage = '';
        this.successMessage = '';

        this.api.splitLogFile(this.splitterFile, this.splitLinesPerChunk)
            .pipe(finalize(() => (this.splitLoading = false)))
            .subscribe({
                next: (response) => {
                    const blob = response.body;
                    if (!blob) {
                        this.errorMessage = 'O backend não retornou os arquivos divididos.';
                        return;
                    }

                    const header = response.headers.get('Content-Disposition') ?? '';
                    const filenameMatch = /filename="?([^\"]+)"?/i.exec(header);
                    const filename = filenameMatch?.[1] ?? `log_dividido_${Date.now()}.zip`;
                    const statsHeader = response.headers.get('X-Split-Stats');
                    this.splitResultStats = statsHeader ? JSON.parse(statsHeader) as SplitLogResultStats : null;
                    this.saveBlob(blob, filename);
                    this.successMessage = 'Arquivo dividido com sucesso. O download do pacote foi iniciado.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao dividir o arquivo de log.';
                }
            });
    }

    protected resetSplitWorkflow(): void {
        this.splitterFile = null;
        this.splitLinesPerChunk = 50000;
        this.splitResultStats = null;
        this.errorMessage = '';
        this.successMessage = '';
    }

    protected analyzeProfilerFile(): void {
        if (!this.profilerFile) {
            this.errorMessage = 'Selecione um arquivo .out para analisar o profiler.';
            return;
        }

        this.profilerLoading = true;
        this.errorMessage = '';

        this.api.analyzeProfiler(this.profilerFile)
            .pipe(finalize(() => (this.profilerLoading = false)))
            .subscribe({
                next: (response) => {
                    this.profilerResult = response;
                    this.profilerSummaryCards = this.buildProfilerSummaryCards(response);
                    this.profilerSession.save(response, this.profilerFile?.name ?? response.filename ?? 'profiler.out');
                    this.successMessage = 'Análise do profiler concluída com sucesso.';
                    void this.router.navigateByUrl('/profiler');
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao analisar profiler.';
                }
            });
    }

    protected resetProfilerWorkflow(): void {
        this.profilerFile = null;
    }

    protected runVersionCompare(): void {
        if (!this.versionCompareFile) {
            this.errorMessage = 'Selecione um extrato para leitura de versão.';
            return;
        }

        this.versionCompareLoading = true;
        this.errorMessage = '';

        this.api.compareVersions(this.versionCompareFile)
            .pipe(finalize(() => (this.versionCompareLoading = false)))
            .subscribe({
                next: (response) => {
                    this.versionCompareResult = response;
                    this.versionCompareStatus = response.index_info ?? this.versionCompareStatus;
                    this.versionCompareSession.save(response, this.versionCompareFile?.name ?? 'extrato.txt');
                    this.successMessage = 'Extrato de versão analisado com sucesso.';
                    void this.router.navigateByUrl('/comparacao-versao');
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao processar extrato de versão.';
                }
            });
    }

    protected reloadVersionIndex(): void {
        this.versionCompareLoading = true;
        this.errorMessage = '';

        this.api.reloadVersionCompare()
            .pipe(finalize(() => (this.versionCompareLoading = false)))
            .subscribe({
                next: (response) => {
                    this.versionCompareStatus = response;
                    this.successMessage = 'Índice do extrato de versão recarregado.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao recarregar índice do extrato de versão.';
                }
            });
    }

    protected useReviewCandidate(candidate: ReviewCandidate): void {
        this.selectedReviewCandidate = candidate;
        this.customPatternForm = {
            ...this.customPatternForm,
            pattern: candidate.matchedPattern !== '-' ? candidate.matchedPattern : this.extractPatternFromCandidate(candidate),
            description: candidate.type !== '-' ? `Ocorrência categorizada como ${candidate.type}` : this.customPatternForm.description,
            category: candidate.category !== '-' ? candidate.category : this.customPatternForm.category,
            severity: candidate.severity !== '-' ? candidate.severity : this.customPatternForm.severity,
            example: candidate.preview,
            solution: this.customPatternForm.solution || 'Validar causa raiz e aplicar correção conforme contexto do log.'
        };
    }

    protected testCustomPattern(): void {
        if (!this.customPatternForm.pattern.trim()) {
            this.errorMessage = 'Informe um padrão antes de testar.';
            return;
        }

        this.managementLoading = true;
        this.errorMessage = '';
        this.successMessage = '';

        this.api.testPattern({
            pattern: this.customPatternForm.pattern.trim(),
            partial_pattern: this.customPatternForm.partial_pattern.trim(),
            description: this.customPatternForm.description.trim(),
            example: this.customPatternForm.example.trim(),
            test_logs: this.buildPatternTestLogs()
        })
            .pipe(finalize(() => (this.managementLoading = false)))
            .subscribe({
                next: (response) => {
                    this.patternTestResult = response;
                    this.successMessage = 'Teste do padrão executado com sucesso.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao testar o padrão.';
                }
            });
    }

    protected saveCustomPattern(): void {
        if (!this.customPatternForm.pattern.trim() || !this.customPatternForm.description.trim() || !this.customPatternForm.solution.trim()) {
            this.errorMessage = 'Preencha padrão, descrição e solução antes de salvar.';
            return;
        }

        this.managementLoading = true;
        this.errorMessage = '';
        this.successMessage = '';

        this.api.addCustomPattern({
            pattern: this.customPatternForm.pattern.trim(),
            partial_pattern: this.customPatternForm.partial_pattern.trim(),
            description: this.customPatternForm.description.trim(),
            category: this.customPatternForm.category.trim(),
            severity: this.customPatternForm.severity.trim(),
            example: this.customPatternForm.example.trim(),
            solution: this.customPatternForm.solution.trim()
        })
            .pipe(finalize(() => (this.managementLoading = false)))
            .subscribe({
                next: () => {
                    this.successMessage = 'Padrão customizado salvo com sucesso.';
                    this.recordAnalysisChange({
                        type: 'custom-pattern-added',
                        pattern: this.customPatternForm.pattern,
                        example: this.customPatternForm.example,
                        source_line: this.selectedReviewCandidate?.lineNumber ?? null
                    });
                    this.patternTestResult = null;
                    this.customPatternForm = this.createEmptyCustomPatternForm();
                    this.loadManagementData();
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao salvar padrão customizado.';
                }
            });
    }

    protected categorizeCandidate(categoryType: 'permanent' | 'session'): void {
        const pattern = this.resolveCandidatePattern();
        if (!pattern) {
            this.errorMessage = 'Selecione uma ocorrência ou informe um padrão para categorizar.';
            return;
        }

        this.managementLoading = true;
        this.errorMessage = '';
        this.successMessage = '';

        this.api.categorizeError({
            pattern_id: String(this.selectedReviewCandidate?.lineNumber ?? 'manual'),
            pattern,
            category_type: categoryType,
            description: this.categorizationDescription.trim() || this.selectedReviewCandidate?.preview || 'Categorização manual via interface Angular'
        })
            .pipe(finalize(() => (this.managementLoading = false)))
            .subscribe({
                next: () => {
                    this.successMessage = categoryType === 'permanent'
                        ? 'Ocorrência categorizada como padrão permanente.'
                        : 'Ocorrência marcada apenas para esta sessão.';
                    this.recordAnalysisChange({
                        type: `categorize-${categoryType}`,
                        pattern,
                        description: this.categorizationDescription,
                        source_line: this.selectedReviewCandidate?.lineNumber ?? null
                    });
                    this.loadManagementData();
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao categorizar a ocorrência.';
                }
            });
    }

    protected markCandidateAsNonError(): void {
        const pattern = this.resolveCandidatePattern();
        const fullMessage = this.selectedReviewCandidate?.preview || this.customPatternForm.example || this.customPatternForm.pattern;
        if (!pattern || !fullMessage) {
            this.errorMessage = 'Selecione uma ocorrência válida para marcar como não-erro.';
            return;
        }

        this.managementLoading = true;
        this.errorMessage = '';
        this.successMessage = '';

        this.api.markAsNonError({
            pattern,
            full_message: fullMessage,
            reason: this.nonErrorReason.trim() || 'Marcado na tela de análise Angular'
        })
            .pipe(finalize(() => (this.managementLoading = false)))
            .subscribe({
                next: () => {
                    this.successMessage = 'Ocorrência marcada como não-erro.';
                    this.recordAnalysisChange({
                        type: 'mark-non-error',
                        pattern,
                        full_message: fullMessage,
                        reason: this.nonErrorReason,
                        source_line: this.selectedReviewCandidate?.lineNumber ?? null
                    });
                    this.loadManagementData();
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao marcar ocorrência como não-erro.';
                }
            });
    }

    protected saveManualAnalysisChange(): void {
        const payload = {
            type: 'manual-analysis-note',
            notes: this.manualChangeNotes.trim(),
            source_line: this.selectedReviewCandidate?.lineNumber ?? null,
            selected_preview: this.selectedReviewCandidate?.preview ?? null,
            selected_pattern: this.resolveCandidatePattern() || null
        };

        if (!payload.notes) {
            this.errorMessage = 'Informe uma observação antes de salvar a mudança da análise.';
            return;
        }

        this.managementLoading = true;
        this.errorMessage = '';
        this.successMessage = '';

        this.api.saveAnalysisChanges(payload)
            .pipe(finalize(() => (this.managementLoading = false)))
            .subscribe({
                next: () => {
                    this.successMessage = 'Mudança da análise salva com sucesso.';
                    this.manualChangeNotes = '';
                    this.loadManagementData();
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao salvar alteração da análise.';
                }
            });
    }

    protected removeCustomPattern(patternId: string): void {
        this.managementLoading = true;
        this.errorMessage = '';
        this.successMessage = '';

        this.api.deleteCustomPattern(patternId)
            .pipe(finalize(() => (this.managementLoading = false)))
            .subscribe({
                next: () => {
                    this.successMessage = 'Padrão customizado removido.';
                    this.recordAnalysisChange({
                        type: 'custom-pattern-removed',
                        pattern_id: patternId
                    });
                    this.loadManagementData();
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao remover padrão customizado.';
                }
            });
    }

    protected exportCsv(): void {
        if (!this.logFile) {
            this.errorMessage = 'Selecione um arquivo de log antes de exportar o CSV.';
            return;
        }

        this.exporting = true;
        this.errorMessage = '';

        this.api.downloadAnalysisCsv(this.logFile, this.patternsFile)
            .pipe(finalize(() => (this.exporting = false)))
            .subscribe({
                next: (response) => {
                    const blob = response.body;
                    if (!blob) {
                        this.errorMessage = 'O backend não retornou conteúdo para exportação.';
                        return;
                    }

                    const header = response.headers.get('Content-Disposition') ?? '';
                    const filenameMatch = /filename="?([^\"]+)"?/i.exec(header);
                    const filename = filenameMatch?.[1] ?? `analise_log_${Date.now()}.csv`;
                    this.saveBlob(blob, filename);
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao exportar CSV da análise.';
                }
            });
    }

    protected refreshHistory(): void {
        this.loadHistory();
    }

    protected clearLearningForms(): void {
        this.customPatternForm = this.createEmptyCustomPatternForm();
        this.patternTestResult = null;
        this.categorizationDescription = '';
        this.nonErrorReason = '';
        this.manualChangeNotes = '';
        this.selectedReviewCandidate = null;
        this.successMessage = '';
        this.errorMessage = '';
    }

    protected get profilerRows(): ProfilerTableItem[] {
        const bottlenecks = this.profilerResult?.top_bottlenecks ?? [];

        return bottlenecks.slice(0, 20).map((item) => ({
            program: String(this.readProfilerValue(item, ['procedure_name', 'program', 'object_name'])),
            duration: this.readProfilerValue(item, ['total_time', 'duration', 'elapsed_ms', 'time_total_ms']),
            calls: this.readProfilerValue(item, ['calls', 'call_count', 'executions'])
        }));
    }

    protected get versionCompareRows(): VersionCompareTableItem[] {
        return (this.versionCompareResult?.desatualizados ?? []).map((item) => this.mapVersionCompareRow(item));
    }

    protected get versionCompareOkRows(): VersionCompareTableItem[] {
        return (this.versionCompareResult?.ok ?? []).map((item) => this.mapVersionCompareRow(item));
    }

    protected get versionCompareNotFoundRows(): VersionCompareTableItem[] {
        return (this.versionCompareResult?.nao_encontrado ?? []).map((item) => this.mapVersionCompareRow(item));
    }

    protected get versionCompareUpcRows(): UpcTableItem[] {
        return (this.versionCompareResult?.programas_com_upc ?? []).map((programa) => ({ programa }));
    }

    protected get versionCompareSummaryCards(): Array<{ label: string; value: string | number }> {
        const result = this.versionCompareResult;
        if (!result) {
            return [];
        }

        return [
            { label: 'Versão do produto', value: result.product_version || '-' },
            { label: 'Desatualizados', value: result.desatualizados?.length ?? 0 },
            { label: 'Não encontrados', value: result.nao_encontrado?.length ?? 0 },
            { label: 'Com UPC', value: result.programas_com_upc?.length ?? 0 }
        ];
    }

    protected get outdatedTabLabel(): string {
        return `Desatualizados (${this.versionCompareRows.length})`;
    }

    protected get okTabLabel(): string {
        return `OK (${this.versionCompareOkRows.length})`;
    }

    protected get notFoundTabLabel(): string {
        return `Não encontrado (${this.versionCompareNotFoundRows.length})`;
    }

    protected get upcTabLabel(): string {
        return `UPC (${this.versionCompareUpcRows.length})`;
    }

    protected get hasPerformanceData(): boolean {
        return this.performanceSummaryCards.length > 0
            || this.slowProgramRows.length > 0
            || this.slowOperationRows.length > 0
            || this.topMethodRows.length > 0
            || this.topProgramRows.length > 0
            || this.specificAlertRows.length > 0;
    }

    protected get availableKnowledgeSources(): string[] {
        return [...new Set(this.knowledgeTableItems.map((item) => item.source).filter(Boolean))];
    }

    protected get availableKnowledgeSeverities(): string[] {
        return [...new Set(this.knowledgeTableItems.map((item) => item.severity).filter(Boolean))];
    }

    protected get datasulSummaryCards(): Array<{ label: string; value: string | number }> {
        return [
            { label: 'Padrões Datasul', value: this.datasulStatistics?.total_patterns ?? this.datasulPatterns.length },
            { label: 'Categorias', value: Object.keys(this.datasulStatistics?.patterns_by_category ?? {}).length },
            { label: 'Prioridades', value: Object.keys(this.datasulStatistics?.patterns_by_priority ?? {}).length },
            { label: 'Cache (s)', value: this.datasulStatistics?.cache_age_seconds ?? 0 }
        ];
    }

    protected get datasulPatternRows(): DatasulPatternTableItem[] {
        return this.datasulPatterns.slice(0, 150).map((item) => ({
            pattern: item.pattern,
            category: item.category || '-',
            severity: item.severity || '-',
            tag: item.tag || '-',
            priority: item.priority ?? '-',
            usageCount: item.usage_count ?? 0
        }));
    }

    protected get datasulCategoryRows(): BreakdownItem[] {
        return this.mapBreakdown(this.datasulStatistics?.patterns_by_category);
    }

    protected get datasulPriorityRows(): BreakdownItem[] {
        return this.mapBreakdown(this.datasulStatistics?.patterns_by_priority);
    }

    protected get datasulMostUsedRows(): PerformanceTableItem[] {
        return (this.datasulStatistics?.most_used_patterns ?? []).map((item) => ({
            label: item.pattern,
            value: item.usage_count,
            detail: item.tag || '-'
        }));
    }

    protected get profilerAnalysis(): ProfilerAnalysisPayload | null {
        return this.profilerResult?.analysis ?? null;
    }

    protected get profilerOverviewCards(): Array<{ label: string; value: string | number }> {
        const summary = this.profilerResult?.summary ?? this.profilerAnalysis?.summary ?? {};
        return [
            { label: 'Arquivo', value: this.profilerResult?.filename ?? '-' },
            { label: 'Módulos', value: Number(summary['total_modules'] ?? 0) },
            { label: 'Chamadas totais', value: Number(summary['total_calls'] ?? 0) },
            { label: 'Tempo total (ms)', value: Number(summary['total_time_ms'] ?? 0) },
            { label: 'Health score', value: Number(summary['health_score'] ?? 0) },
            { label: 'Trace info', value: Number(summary['trace_info_count'] ?? 0) }
        ];
    }

    protected get profilerTopByTimeRows(): ProfilerModuleRow[] {
        return (this.profilerAnalysis?.top_modules_by_time ?? []).slice(0, 15).map((item) => ({
            module: String(item['module'] ?? '-'),
            calls: String(item['calls'] ?? '-'),
            totalTimeMs: String(item['time_total_ms'] ?? '-'),
            avgTimeMs: String(item['time_avg_ms'] ?? '-')
        }));
    }

    protected get profilerTopByCallsRows(): ProfilerModuleRow[] {
        return (this.profilerAnalysis?.top_modules_by_calls ?? []).slice(0, 15).map((item) => ({
            module: String(item['module'] ?? '-'),
            calls: String(item['calls'] ?? '-'),
            totalTimeMs: String(item['time_total_ms'] ?? '-'),
            avgTimeMs: String(item['time_avg_ms'] ?? '-')
        }));
    }

    protected get profilerTopByAvgRows(): ProfilerModuleRow[] {
        return (this.profilerAnalysis?.top_modules_by_avg_time ?? []).slice(0, 15).map((item) => ({
            module: String(item['module'] ?? '-'),
            calls: String(item['calls'] ?? '-'),
            totalTimeMs: String(item['time_total_ms'] ?? '-'),
            avgTimeMs: String(item['time_avg_ms'] ?? '-')
        }));
    }

    protected get profilerProblemRows(): ProfilerIssueRow[] {
        return (this.profilerAnalysis?.problematic_modules ?? []).slice(0, 15).map((item) => ({
            module: String(item.module ?? '-'),
            issues: (item.issues ?? []).join(' • '),
            calls: String(item.calls ?? '-'),
            totalTimeMs: String(item.time_total_ms ?? '-')
        }));
    }

    protected get profilerRecommendationRows(): RecommendationRow[] {
        return (this.profilerAnalysis?.recommendations ?? []).map((recommendation) => ({ recommendation }));
    }

    protected get profilerCallTreeRows(): ProfilerCallTreeRow[] {
        const callTree = this.profilerResult?.call_tree ?? this.profilerAnalysis?.call_tree ?? [];
        return callTree.slice(0, 20).map((item) => ({
            name: String(item['name'] ?? item['module'] ?? '-'),
            calls: String(item['calls'] ?? '-'),
            totalTimeMs: String(item['total_time'] ?? item['time_total_ms'] ?? '-'),
            percent: `${Number(item['percent'] ?? 0).toFixed(2)}%`,
            childrenCount: Array.isArray(item['children']) ? item['children'].length : 0
        }));
    }

    protected get profilerCallTreeStatRows(): BreakdownItem[] {
        const stats = this.profilerAnalysis?.call_tree_stats ?? {};
        return [
            { label: 'Relacionamentos', value: Number(stats.total_relationships ?? 0) },
            { label: 'Callers únicos', value: Number(stats.unique_callers ?? 0) },
            { label: 'Callees únicos', value: Number(stats.unique_callees ?? 0) }
        ];
    }

    protected trackKnowledgeTerm(term: string): string {
        return term;
    }

    protected openKnowledgeBase(): void {
        void this.router.navigateByUrl('/base-conhecimento');
    }

    protected openVersionCompare(): void {
        void this.router.navigateByUrl('/comparacao-versao');
    }

    protected openPerformanceView(): void {
        void this.router.navigateByUrl('/profiler');
    }

    protected openAnalyzeLogPage(): void {
        void this.router.navigateByUrl('/analise/upload');
    }

    protected openEvidenceRegister(): void {
        this.errorMessage = '';
        this.successMessage = 'Card "Registro de Evidência" adicionado ao painel. O fluxo detalhado pode ser conectado na próxima etapa.';
        this.scrollToDashboard();
    }

    protected openIssueControl(): void {
        this.errorMessage = '';
        this.successMessage = 'Card "Controle de Issues" adicionado ao painel. O fluxo detalhado pode ser conectado na próxima etapa.';
        this.scrollToDashboard();
    }

    protected refreshDatasulCatalog(): void {
        this.datasulLoading = true;
        this.errorMessage = '';

        this.api.refreshDatasulPatterns()
            .pipe(finalize(() => (this.datasulLoading = false)))
            .subscribe({
                next: (response) => {
                    const success = Boolean(response['success']);
                    if (!success) {
                        this.errorMessage = String(response['error'] ?? 'Falha ao atualizar catálogo Datasul.');
                        return;
                    }

                    this.successMessage = String(response['message'] ?? 'Catálogo Datasul atualizado com sucesso.');
                    this.loadDatasulCatalog();
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao atualizar catálogo Datasul.';
                }
            });
    }

    private loadHistory(): void {
        this.historyLoading = true;
        this.api.getAnalysisHistory()
            .pipe(finalize(() => (this.historyLoading = false)))
            .subscribe({
                next: (items) => {
                    this.historyRows = items.map((item) => this.mapHistoryItem(item));
                },
                error: () => {
                    this.historyRows = [];
                }
            });
    }

    private loadManagementData(): void {
        this.managementLoading = true;
        forkJoin({
            customPatterns: this.api.getCustomPatterns(),
            categorizations: this.api.getErrorCategorizations(),
            nonErrors: this.api.getNonErrorPatterns(),
            changes: this.api.getAnalysisChanges()
        })
            .pipe(finalize(() => (this.managementLoading = false)))
            .subscribe({
                next: ({ customPatterns, categorizations, nonErrors, changes }) => {
                    this.customPatterns = (customPatterns as CustomPatternsResponse).patterns ?? [];
                    this.permanentPatterns = (categorizations as ErrorCategorizationsResponse).permanent_patterns ?? [];
                    this.sessionPatterns = (categorizations as ErrorCategorizationsResponse).session_patterns ?? [];
                    this.nonErrorPatterns = (nonErrors as NonErrorPatternsResponse).patterns ?? [];
                    this.analysisChanges = (changes as AnalysisChangesResponse).changes ?? [];
                },
                error: () => {
                    this.customPatterns = [];
                    this.permanentPatterns = [];
                    this.sessionPatterns = [];
                    this.nonErrorPatterns = [];
                    this.analysisChanges = [];
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

    private loadDatasulCatalog(): void {
        this.datasulLoading = true;

        forkJoin({
            patterns: this.api.getDatasulPatterns(),
            statistics: this.api.getDatasulStatistics()
        })
            .pipe(finalize(() => (this.datasulLoading = false)))
            .subscribe({
                next: ({ patterns, statistics }) => {
                    const patternsResponse = patterns as DatasulPatternsResponse;
                    const statisticsResponse = statistics as DatasulStatisticsResponse;

                    this.datasulPatterns = patternsResponse.success ? patternsResponse.patterns ?? [] : [];
                    this.datasulStatistics = statisticsResponse.success ? statisticsResponse.statistics ?? null : null;

                    if (!patternsResponse.success || !statisticsResponse.success) {
                        this.errorMessage = patternsResponse.error
                            ?? statisticsResponse.error
                            ?? 'Não foi possível carregar o catálogo Datasul.';
                    }
                },
                error: () => {
                    this.datasulPatterns = [];
                    this.datasulStatistics = null;
                }
            });
    }

    private closeAllModals(): void {
        [
            this.patternModal,
            this.cleanerModal,
            this.splitterModal,
            this.profilerModal,
            this.versionCompareModal,
            this.performanceModal,
            this.knowledgeModal,
            this.datasulModal
        ].forEach((modal) => modal?.close());
    }

    private scrollToDashboard(): void {
        const dashboardElement = this.dashboardStart?.nativeElement;
        if (dashboardElement) {
            dashboardElement.scrollIntoView({ block: 'start', behavior: 'auto' });
            return;
        }

        if (typeof window !== 'undefined') {
            window.scrollTo({ top: 0, behavior: 'auto' });
        }
    }

    private buildSummaryCards(response: LogAnalysisResponse): Array<{ label: string; value: string | number }> {
        const stats = response.statistics ?? {};

        return [
            { label: 'Resultados encontrados', value: response.total_results },
            { label: 'Categorias mapeadas', value: Object.keys(response.error_counts ?? {}).length },
            { label: 'Severidades', value: Object.keys(response.severity_counts ?? {}).length },
            { label: 'Linhas analisadas', value: this.pickStatistic(stats, ['total_lines', 'lines_analyzed', 'total_linhas']) }
        ];
    }

    private buildHighlightedStats(response: LogAnalysisResponse): Array<{ label: string; value: string | number }> {
        const stats = response.statistics ?? {};

        return [
            { label: 'Linhas informativas', value: response.informational_lines?.length ?? 0 },
            { label: 'Pontos de atenção', value: response.total_attention_points ?? response.attention_points?.length ?? 0 },
            { label: 'Processamento', value: this.pickStatistic(stats, ['processing_mode', 'processing_type', 'processor']) },
            { label: 'Estruturado', value: response.structured_analysis ? 'Sim' : 'Não' }
        ];
    }

    private buildProfilerSummaryCards(response: ProfilerResponse): Array<{ label: string; value: string | number }> {
        const summary = response.summary ?? response.analysis?.summary ?? {};
        return [
            { label: 'Arquivo', value: response.filename },
            { label: 'Módulos', value: Number(summary['total_modules'] ?? 0) },
            { label: 'Chamadas totais', value: Number(summary['total_calls'] ?? 0) },
            { label: 'Tempo total (ms)', value: Number(summary['total_time_ms'] ?? 0) },
            { label: 'Bottlenecks', value: response.top_bottlenecks?.length ?? 0 },
            { label: 'N+1 suspects', value: response.n_plus_one_suspects?.length ?? 0 },
            { label: 'Call tree', value: response.call_tree?.length ?? 0 }
        ];
    }

    private buildStructuredBlocks(response: LogAnalysisResponse): void {
        const structured = response.structured_analysis;
        if (!structured) {
            this.structuredSummaryCards = [];
            this.structuredTypeRows = [];
            this.structuredSubtypeRows = [];
            this.structuredCategoryRows = [];
            this.httpStatusRows = [];
            this.javaExceptionRows = [];
            return;
        }

        this.structuredSummaryCards = [
            { label: 'Eventos estruturados', value: structured.total_events ?? 0 },
            { label: 'Tipos distintos', value: Object.keys(structured.type_breakdown ?? {}).length },
            { label: 'Subtipos', value: Object.keys(structured.subtype_breakdown ?? {}).length },
            { label: 'HTTP requests', value: structured.http_metrics?.total_requests ?? 0 }
        ];

        this.structuredTypeRows = this.mapBreakdown(structured.type_breakdown);
        this.structuredSubtypeRows = this.mapBreakdown(structured.subtype_breakdown);
        this.structuredCategoryRows = this.mapBreakdown(structured.category_breakdown);
        this.httpStatusRows = this.mapBreakdown(structured.http_metrics?.status_distribution);
        this.javaExceptionRows = this.mapBreakdown(structured.java_metrics?.top_exceptions);
    }

    private buildPerformanceBlocks(response: LogAnalysisResponse): void {
        const performance = response.performance_analysis;
        if (!performance) {
            this.performanceSummaryCards = [];
            this.slowProgramRows = [];
            this.slowOperationRows = [];
            this.topMethodRows = [];
            this.specificAlertRows = [];
            return;
        }

        this.performanceSummaryCards = [
            { label: 'Tipo de log', value: performance.log_type ?? this.analysisResult?.log_type ?? '-' },
            { label: 'Amostras resposta', value: performance.response_time_stats?.['total_samples'] ?? 0 },
            { label: 'Programas lentos', value: performance.slow_programs_stats?.['total_slow_programs'] ?? performance.slow_programs?.length ?? 0 },
            { label: 'Queries mapeadas', value: performance.database_queries?.length ?? 0 },
            { label: 'Chamadas totais', value: performance.call_analysis?.total_calls ?? 0 },
            { label: 'Tempo rastreado (ms)', value: performance.program_analysis?.total_tracked_program_time_ms ?? 0 }
        ];

        this.slowProgramRows = (performance.slow_programs ?? []).slice(0, 10).map((item) => ({
            label: String(item['program'] ?? '-'),
            value: `${Number(item['duration_ms'] ?? 0)} ms`,
            detail: `Linha ${item['line'] ?? '-'} • ${item['severity'] ?? '-'} • ${item['timestamp'] ?? '-'} • ${Number(item['percent_of_total_tracked_time'] ?? 0).toFixed(2)}%`
        }));

        this.slowOperationRows = (performance.slow_operations ?? []).slice(0, 10).map((item) => ({
            label: String(item['keyword'] ?? '-'),
            value: `Linha ${item['line'] ?? '-'}`,
            detail: String(item['message'] ?? '-')
        }));

        this.topMethodRows = (performance.call_analysis?.top_methods ?? []).slice(0, 10).map((item) => ({
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
                label: 'Procedure em erros',
                value: alerts?.procedure_error_count ?? 0,
                detail: alerts?.procedure_in_errors ? 'Erros com marcação de procedure foram encontrados.' : 'Sem procedures dentro de erros.'
            }
        ];
    }

    private buildReviewCandidates(): ReviewCandidate[] {
        return this.tableItems.slice(0, 12).map((item) => ({
            lineNumber: item.lineNumber,
            severity: item.severity,
            category: item.category,
            type: item.type,
            matchedPattern: item.matchedPattern,
            preview: item.preview
        }));
    }

    private mapBreakdown(source?: Record<string, number>): BreakdownItem[] {
        return Object.entries(source ?? {})
            .map(([label, value]) => ({ label, value }))
            .sort((left, right) => right.value - left.value)
            .slice(0, 12);
    }

    private mapHistoryItem(item: AnalysisHistoryItem): AnalysisHistoryTableItem {
        const mostCommonError = this.extractMostCommonError(item.error_counts);
        return {
            timestamp: item.timestamp,
            filename: item.filename,
            totalResults: item.total_results,
            mostCommonError
        };
    }

    private extractMostCommonError(errorCounts: Record<string, unknown>): string {
        const entries = Object.entries(errorCounts ?? {}).map(([label, value]) => ({
            label,
            value: Number(value) || 0
        }));
        const top = entries.sort((left, right) => right.value - left.value)[0];
        return top ? `${top.label} (${top.value})` : '-';
    }

    private pushKnowledgeRecentTerm(term: string): void {
        if (!term) {
            return;
        }

        this.knowledgeRecentTerms = [term, ...this.knowledgeRecentTerms.filter((item) => item !== term)].slice(0, 5);
    }

    private mapVersionCompareRow(item: VersionCompareEntry): VersionCompareTableItem {
        return {
            programa: item.programa ?? '-',
            versao_extrato: item.cliente ?? '-',
            versao_correta: item.deveria_estar ?? item.referencia_oficial ?? '-',
            fix_encontrada: item.fix_encontrada ?? '-',
            diferenca_builds: item.diferenca_builds ?? '-'
        };
    }

    private saveBlob(blob: Blob, filename: string): void {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        window.URL.revokeObjectURL(url);
    }

    private createEmptyCustomPatternForm(): CustomPatternFormValue {
        return {
            pattern: '',
            partial_pattern: '',
            description: '',
            category: 'User-Categorized',
            severity: 'Médio',
            example: '',
            solution: ''
        };
    }

    private buildPatternTestLogs(): string[] {
        const logs = [
            this.customPatternForm.example,
            this.selectedReviewCandidate?.preview,
            this.selectedReviewCandidate?.matchedPattern,
            this.selectedReviewCandidate?.type
        ].filter((value): value is string => Boolean(value && value !== '-'));

        return [...new Set(logs)];
    }

    private resolveCandidatePattern(): string {
        if (this.customPatternForm.pattern.trim()) {
            return this.customPatternForm.pattern.trim();
        }

        if (this.selectedReviewCandidate?.matchedPattern && this.selectedReviewCandidate.matchedPattern !== '-') {
            return this.selectedReviewCandidate.matchedPattern;
        }

        return this.selectedReviewCandidate ? this.extractPatternFromCandidate(this.selectedReviewCandidate) : '';
    }

    private readProfilerValue(item: Record<string, unknown>, candidates: string[]): string | number {
        for (const key of candidates) {
            const value = item[key];
            if (typeof value === 'number' || typeof value === 'string') {
                return value;
            }
        }

        return '-';
    }

    private extractPatternFromCandidate(candidate: ReviewCandidate): string {
        return candidate.preview.length > 120 ? `${candidate.preview.slice(0, 120)}...` : candidate.preview;
    }

    private recordAnalysisChange(payload: SaveAnalysisChangesPayload): void {
        this.api.saveAnalysisChanges(payload).subscribe({
            next: () => {
                this.loadManagementData();
            },
            error: () => {
                // Registro auxiliar; falha não deve interromper o fluxo principal.
            }
        });
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
}
