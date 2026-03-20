// =============================
// Bem-vindo ao coração do frontend!
// Aqui começa a jornada da análise de logs, com Angular + PO UI.
// Cada bloco de código tem um propósito e uma dica para quem está aprendendo!
// =============================
// Importando módulos essenciais para a mágica do Angular acontecer!
import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, ElementRef, HostListener, OnInit, ViewChild, inject } from '@angular/core';
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
    SaveAnalysisChangesPayload,
    VersionCompareEntry,
    VersionCompareResponse,
    VersionCompareStatusResponse
} from '../../core/models/api.models';
import { AnalysisSessionService } from '../../core/services/analysis-session.service';
import { BackendApiService } from '../../core/services/backend-api.service';
import { VersionCompareSessionService } from '../../core/services/version-compare-session.service';

interface ActionCard {
    // Cartão de ação: cada um é um superpoder do dashboard!
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

// Componente principal da página de análise: aqui começa a diversão!
//
// DICA: O Angular usa decorators (@Component) para transformar classes em componentes de tela.
//       O PO UI traz componentes prontos para dashboards, tabelas e formulários bonitos.
//       Use o 'inject' para acessar serviços e APIs sem precisar de construtor!
@Component({
    selector: 'app-analysis-page',
    standalone: true,
    imports: [CommonModule, FormsModule, PoPageModule, PoWidgetModule, PoButtonModule, PoCheckboxModule, PoDropdownModule, PoTableModule, PoLoadingModule, PoModalModule, PoInfoModule, PoTagModule, PoFieldModule, PoIconModule, PoTabsModule],
    templateUrl: './analysis.page.html',
    styleUrl: './analysis.page.scss'
})
// Aqui é onde a mágica da análise de logs acontece!
//
// O ciclo de vida do Angular começa com ngOnInit (inicialização) e AfterViewInit (após renderizar a tela).
// Use @ViewChild para acessar elementos do template (HTML) diretamente.
//
// DICA: Os protected são visíveis no template, os private só no TypeScript.
export class AnalysisPageComponent implements OnInit, AfterViewInit {
    @ViewChild('dashboardStart') dashboardStart?: ElementRef<HTMLDivElement>;
    @ViewChild('patternModal') patternModal?: PoModalComponent;
    @ViewChild('cleanerModal') cleanerModal?: PoModalComponent;
    @ViewChild('splitterModal') splitterModal?: PoModalComponent;
    @ViewChild('datasulModal') datasulModal?: PoModalComponent;

    private readonly api = inject(BackendApiService);
    private readonly analysisSession = inject(AnalysisSessionService);
    private readonly router = inject(Router);
    private readonly versionCompareSession = inject(VersionCompareSessionService);

    // Cartões de ação do dashboard: escolha seu superpoder!
    //
    // Cada card representa uma funcionalidade principal do sistema.
    // Você pode adicionar, remover ou customizar cards para guiar o usuário!
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

    // Variáveis protegidas: acessíveis no HTML, mas não fora do componente.
    // Use elas para controlar o estado da tela, arquivos enviados, resultados, etc.
    protected logFile: File | null = null;
    protected patternsFile: File | null = null;
    protected cleanerFile: File | null = null;
    protected splitterFile: File | null = null;
    protected versionCompareFile: File | null = null;
    protected previewInfo: AnalyzeInfoResponse | null = null;
    protected cleanerCategoryAnalysis: LogCategoryInfoResponse | null = null;
    protected analysisResult: LogAnalysisResponse | null = null;
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
    protected cleanerLogType = 'auto';
    protected cleanerCategoryItems: CleanerCategoryItem[] = [];
    protected selectedCleanerCategories: string[] = [];
    protected cleanerStep = 1;
    protected cleanerResultStats: Record<string, unknown> | null = null;
    protected splitLinesPerChunk = 50000;
    protected splitLoading = false;
    protected splitResultStats: SplitLogResultStats | null = null;
    protected compactViewport = this.isCompactViewport();
    protected loading = false;
    protected cleanerLoading = false;
    protected exporting = false;
    protected historyLoading = false;
    protected managementLoading = false;
    protected versionCompareLoading = false;
    protected successMessage = '';
    protected categorizationDescription = '';
    protected nonErrorReason = '';
    protected manualChangeNotes = '';
    protected errorMessage = '';
    // Dicas rápidas para quem quer ir além!
    //
    // DICA: Adicione suas próprias dicas para ajudar colegas ou você mesmo no futuro!
    protected readonly quickInsights = [
        'Use a pré-análise para estimar custo antes do processamento completo.',
        'O arquivo opcional de padrões complementa o matcher do backend.',
        'Os gráficos usam `chart_data`, `error_counts` e `severity_counts` do FastAPI.'
    ];

    // Getter: calcula estatísticas do dashboard em tempo real para exibir no HTML.
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

    // Definição das colunas da tabela de resultados.
    // DICA: Você pode customizar as colunas para mostrar só o que faz sentido para o usuário!
    protected readonly resultColumns: PoTableColumn[] = [
        { property: 'lineNumber', label: 'Linha', width: '90px' },
        { property: 'severity', label: 'Severidade', width: '120px' },
        { property: 'category', label: 'Categoria', width: '180px' },
        { property: 'type', label: 'Tipo', width: '160px' },
        { property: 'matchedPattern', label: 'Padrão' },
        { property: 'preview', label: 'Trecho' }
    ];

    protected readonly desktopHistoryColumns: PoTableColumn[] = [
        { property: 'timestamp', label: 'Quando', width: '190px' },
        { property: 'filename', label: 'Arquivo' },
        { property: 'totalResults', label: 'Resultados', width: '120px' },
        { property: 'mostCommonError', label: 'Erro mais comum' }
    ];

    protected readonly compactHistoryColumns: PoTableColumn[] = [
        { property: 'timestamp', label: 'Quando', width: '170px' },
        { property: 'filename', label: 'Arquivo' },
        { property: 'totalResults', label: 'Resultados', width: '110px' }
    ];

    protected readonly knowledgeColumns: PoTableColumn[] = [
        { property: 'type', label: 'Tipo', width: '140px' },
        { property: 'code', label: 'Código', width: '140px' },
        { property: 'category', label: 'Categoria', width: '180px' },
        { property: 'severity', label: 'Severidade', width: '130px' },
        { property: 'source', label: 'Origem' },
        { property: 'description', label: 'Descrição' }
    ];

    protected readonly desktopDatasulPatternColumns: PoTableColumn[] = [
        { property: 'pattern', label: 'Padrão' },
        { property: 'category', label: 'Categoria', width: '180px' },
        { property: 'severity', label: 'Severidade', width: '130px' },
        { property: 'tag', label: 'Tag', width: '160px' },
        { property: 'priority', label: 'Prioridade', width: '110px' },
        { property: 'usageCount', label: 'Uso', width: '90px' }
    ];

    protected readonly compactDatasulPatternColumns: PoTableColumn[] = [
        { property: 'pattern', label: 'Padrão' },
        { property: 'category', label: 'Categoria', width: '160px' },
        { property: 'usageCount', label: 'Uso', width: '90px' }
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

    protected readonly desktopBreakdownColumns: PoTableColumn[] = [
        { property: 'label', label: 'Indicador' },
        { property: 'value', label: 'Valor', width: '120px' }
    ];

    protected readonly compactBreakdownColumns: PoTableColumn[] = [
        { property: 'label', label: 'Indicador' },
        { property: 'value', label: 'Valor', width: '100px' }
    ];

    protected readonly desktopPerformanceColumns: PoTableColumn[] = [
        { property: 'label', label: 'Indicador' },
        { property: 'value', label: 'Valor', width: '140px' },
        { property: 'detail', label: 'Detalhe' }
    ];

    protected readonly compactPerformanceColumns: PoTableColumn[] = [
        { property: 'label', label: 'Indicador' },
        { property: 'value', label: 'Valor', width: '120px' }
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

    protected readonly cleanerLogTypeOptions: PoSelectOption[] = [
        { label: 'Detectar automaticamente', value: 'auto' },
        { label: 'Progress / OpenEdge', value: 'progress' },
        { label: 'Datasul / Progress', value: 'datasul' },
        { label: 'Fluig / Progress', value: 'fluig' },
        { label: 'PASOE / Tomcat', value: 'pasoe' },
        { label: 'AppServer Progress', value: 'appserver' },
        { label: 'LOGIX', value: 'logix' },
        { label: 'Protheus / ADVPL', value: 'protheus' },
        { label: 'JBoss / WildFly', value: 'jboss' },
        { label: 'Acesso HTTP / Web', value: 'access' },
        { label: 'Genérico', value: 'generic' }
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
        this.resetTransientLoadingStates();
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

    @HostListener('window:resize')
    protected onWindowResize(): void {
        this.compactViewport = this.isCompactViewport();
    }

    protected get historyColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactHistoryColumns : this.desktopHistoryColumns;
    }

    protected get datasulPatternColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactDatasulPatternColumns : this.desktopDatasulPatternColumns;
    }

    protected get breakdownColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactBreakdownColumns : this.desktopBreakdownColumns;
    }

    protected get performanceColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactPerformanceColumns : this.desktopPerformanceColumns;
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
                    this.knowledgeLoading = false;
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

        this.api.analyzeLog(this.logFile, this.patternsFile)
            .pipe(finalize(() => (this.loading = false)))
            .subscribe({
                next: (response) => {
                    this.loading = false;
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
                    this.reviewCandidates = this.buildReviewCandidates();
                    if (this.reviewCandidates.length > 0) {
                        this.useReviewCandidate(this.reviewCandidates[0]);
                    }
                    queueMicrotask(() => {
                        this.loading = false;
                        void this.router.navigateByUrl('/analise/resultados');
                    });
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.loading = false;
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

        this.api.analyzeLogCategories(this.cleanerFile, this.cleanerLogType)
            .pipe(finalize(() => (this.cleanerLoading = false)))
            .subscribe({
                next: (response) => {
                    this.cleanerLoading = false;
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
                    this.cleanerLoading = false;
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
                    this.splitLoading = false;
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
                    this.versionCompareLoading = false;
                    this.versionCompareResult = response;
                    this.versionCompareStatus = response.index_info ?? this.versionCompareStatus;
                    this.versionCompareSession.save(response, this.versionCompareFile?.name ?? 'extrato.txt');
                    this.successMessage = 'Extrato de versão analisado com sucesso.';
                    queueMicrotask(() => {
                        this.versionCompareLoading = false;
                        void this.router.navigateByUrl('/comparacao-versao');
                    });
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.versionCompareLoading = false;
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
                    this.versionCompareLoading = false;
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

    protected get versionCompareRows(): VersionCompareTableItem[] {
        return (this.versionCompareResult?.desatualizados ?? []).map((item) => this.mapVersionCompareRow(item));
    }

    protected get versionCompareOkRows(): VersionCompareTableItem[] {
        return (this.versionCompareResult?.ok ?? []).map((item) => this.mapVersionCompareRow(item));
    }

    protected get versionCompareAdvancedRows(): VersionCompareTableItem[] {
        return (this.versionCompareResult?.adiantado_customizado ?? []).map((item) => this.mapVersionCompareRow(item));
    }

    protected get versionCompareUpcRows(): UpcTableItem[] {
        return (this.versionCompareResult?.programas_com_upc ?? []).map((item) => ({ programa: item.programa || String(item) }));
    }

    protected get versionCompareSummaryCards(): Array<{ label: string; value: string | number }> {
        const result = this.versionCompareResult;
        if (!result) {
            return [];
        }

        return [
            { label: 'Versão do produto', value: result.product_version || '-' },
            { label: 'Programas comparados', value: this.versionCompareRows.length + this.versionCompareOkRows.length + this.versionCompareAdvancedRows.length },
            { label: 'Desatualizados', value: result.desatualizados?.length ?? 0 },
            { label: 'OK', value: result.ok?.length ?? 0 },
            { label: 'Adiantado/Custom.', value: result.adiantado_customizado?.length ?? 0 },
            { label: 'Com UPC', value: result.programas_com_upc?.length ?? 0 }
        ];
    }

    protected get outdatedTabLabel(): string {
        return `Desatualizados (${this.versionCompareRows.length})`;
    }

    protected get okTabLabel(): string {
        return `OK (${this.versionCompareOkRows.length})`;
    }

    protected get advancedTabLabel(): string {
        return `Adiantado/Custom. (${this.versionCompareAdvancedRows.length})`;
    }

    protected get upcTabLabel(): string {
        return `UPC (${this.versionCompareUpcRows.length})`;
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

    protected trackKnowledgeTerm(term: string): string {
        return term;
    }

    protected openKnowledgeBase(): void {
        void this.router.navigateByUrl('/base-conhecimento');
    }

    protected openVersionCompare(): void {
        void this.router.navigateByUrl('/comparacao-versao');
    }

    protected openProfilerPage(): void {
        void this.router.navigateByUrl('/profiler');
    }

    protected openAnalyzeLogPage(): void {
        void this.router.navigateByUrl('/analise/resultados');
    }

    private resetTransientLoadingStates(): void {
        this.loading = false;
        this.versionCompareLoading = false;
    }

    protected openEvidenceRegister(): void {
        this.errorMessage = '';
        this.successMessage = '';
        void this.router.navigateByUrl('/registro-evidencia');
    }

    protected openIssueControl(): void {
        this.errorMessage = '';
        this.successMessage = '';
        void this.router.navigateByUrl('/controle-issues');
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
                    this.historyLoading = false;
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
                    this.managementLoading = false;
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
                    this.datasulLoading = false;
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

    private isCompactViewport(): boolean {
        return typeof window !== 'undefined' ? window.innerWidth <= 960 : false;
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
