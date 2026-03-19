export interface AnalysisResultItem {
    line_number?: number;
    line?: number | string;
    line_text?: string;
    severity?: string;
    category?: string;
    type?: string;
    error_type?: string;
    content?: string;
    message?: string;
    clean_message?: string;
    timestamp?: string;
    matched_pattern?: string;
    error_signature?: string;
    description?: string;
    solution?: string;
    tag?: string;
    source?: string;
    example?: string;
    log_subtype?: string;
    structured_type?: string;
    log_family?: string;
    domain_fields?: Record<string, unknown>;
    insight_tags?: string[];
    recommendation_hint?: string;
}

export interface AuthUserProfile {
    username: string;
    display_name: string;
    email: string;
}

export interface AuthResponse {
    success: boolean;
    message: string;
    user?: AuthUserProfile;
    access_token?: string;
    token_type?: string;
    expires_in?: number;
    expires_at?: string;
}

export interface ApiMessageResponse {
    success: boolean;
    message?: string;
    error?: string;
}

export interface PatternTestRequest {
    pattern: string;
    partial_pattern?: string;
    description?: string;
    example?: string;
    test_logs?: string[];
}

export interface AddCustomPatternPayload {
    pattern: string;
    partial_pattern?: string;
    description: string;
    category: string;
    severity: string;
    example?: string;
    solution: string;
}

export interface CategorizeErrorPayload {
    pattern_id: string;
    pattern: string;
    category_type: 'permanent' | 'session';
    description?: string;
}

export interface MarkAsNonErrorPayload {
    pattern: string;
    full_message: string;
    partial_pattern?: string;
    reason?: string;
    source_line?: number | string | null;
    selection_type?: string;
}

export interface SaveAnalysisChangesPayload {
    type: string;
    [key: string]: unknown;
}

export interface AttentionPointItem {
    line: number;
    message: string;
    clean_message?: string;
    timestamp: string;
    type: string;
    matched_keywords?: string[];
    description?: string;
    solution?: string;
    tag?: string;
    matched_pattern?: string;
    priority?: number;
}

export interface InformationalLineItem {
    line: number;
    message: string;
    timestamp: string;
    detected_pattern: string;
    suggestion: string;
}

export interface StructuredAnalysisResponse {
    enabled: boolean;
    total_events: number;
    type_breakdown?: Record<string, number>;
    subtype_breakdown?: Record<string, number>;
    category_breakdown?: Record<string, number>;
    http_metrics?: {
        status_distribution?: Record<string, number>;
        total_requests?: number;
    };
    java_metrics?: {
        level_distribution?: Record<string, number>;
        top_exceptions?: Record<string, number>;
    };
    progress_metrics?: {
        level_distribution?: Record<string, number>;
    };
    specialized_metrics?: {
        insight_tags?: Record<string, number>;
        recommendation_hints?: Record<string, number>;
        access_kpis?: {
            top_5xx_routes?: Array<{ route: string; count: number }>;
        };
        progress_kpis?: {
            top_programs?: Array<{ program_name: string; count: number }>;
            broker_incidents?: Array<{ broker_name: string; count: number }>;
        };
        tabanalys_kpis?: {
            top_objects?: Array<{ object_name: string; count: number }>;
        };
        xref_kpis?: {
            type_breakdown?: Record<string, number>;
        };
        logix_kpis?: {
            top_command_types?: Array<{ command_type: string; count: number }>;
            top_programs?: Array<{ program_name: string; count: number }>;
        };
    };
}

export interface PerformanceAnalysisResponse {
    log_type?: string;
    analysis_scope?: string;
    response_time_stats?: Record<string, number>;
    memory_stats?: Record<string, number>;
    cpu_stats?: Record<string, number>;
    slow_programs_stats?: Record<string, number>;
    program_analysis?: {
        total_tracked_program_time_ms?: number;
        total_timed_entries?: number;
        top_programs_by_time?: Array<Record<string, unknown>>;
    };
    slow_operations?: Array<Record<string, unknown>>;
    slow_programs?: Array<Record<string, unknown>>;
    database_queries?: Array<Record<string, unknown>>;
    response_times?: Array<Record<string, unknown>>;
    connection_stats?: Record<string, number>;
    throughput?: {
        requests_per_minute?: Record<string, number>;
        peak_periods?: Array<Record<string, unknown>>;
    };
    call_analysis?: {
        calls_by_hour?: Record<string, number>;
        calls_by_minute?: Record<string, number>;
        method_call_count?: Record<string, number>;
        top_methods?: Array<{ method: string; count: number; percent_of_total_calls?: number }>;
        total_calls?: number;
    };
    specific_alerts?: {
        upc_detected?: boolean;
        upc_count?: number;
        upc_lines?: Array<Record<string, unknown>>;
        espec_detected?: boolean;
        espec_count?: number;
        espec_lines?: Array<Record<string, unknown>>;
        procedure_in_errors?: boolean;
        procedure_error_count?: number;
        procedure_error_lines?: Array<Record<string, unknown>>;
    };
}

export interface TopProgramMethodItem {
    program: string;
    method: string;
    calls: number;
    total_time_ms: number;
    avg_time_ms?: number;
    percent_of_total_time?: number;
    callers_summary?: string;
    log_type?: string;
    callers?: Array<{ program: string; method: string; count: number }>;
}

export interface TopProgramsMethodsResponse {
    top_programs: TopProgramMethodItem[];
    total_tracked_time_ms?: number;
    total_ranked_programs?: number;
    log_type?: string;
}

export interface AnalysisHistoryItem {
    id: string;
    filename: string;
    timestamp: string;
    total_results: number;
    statistics: Record<string, unknown>;
    error_counts: Record<string, unknown>;
}

export interface PatternTestResponse {
    success: boolean;
    validation_result: Record<string, unknown>;
    test_summary: {
        pattern_valid: boolean;
        match_rate: number;
        matches_found: number;
        total_tests: number;
        pattern_works: boolean;
    };
    recommendations: string[];
    suggestions: string[];
}

export interface AddCustomPatternValidationResponse {
    match_rate: number;
    pattern_works: boolean;
    complexity: string;
    recommendations: string[];
    warnings: string[];
    suggestions: string[];
}

export interface CustomPatternRecord {
    id: string;
    pattern: string;
    partial_pattern?: string;
    description: string;
    category: string;
    severity: string;
    example?: string;
    solution?: string;
    created_at?: string;
    active?: boolean;
    user_created?: boolean;
    categorization_type?: string;
    validation_info?: Record<string, unknown>;
}

export interface CustomPatternsResponse {
    success: boolean;
    patterns: CustomPatternRecord[];
}

export interface AddCustomPatternResponse extends ApiMessageResponse {
    pattern?: CustomPatternRecord;
    validation_result?: AddCustomPatternValidationResponse;
}

export interface DeleteCustomPatternResponse extends ApiMessageResponse { }

export interface CategorizeErrorResponse extends ApiMessageResponse {
    type?: 'permanent' | 'session';
    pattern_id?: string;
}

export interface ErrorCategorizationsResponse {
    success: boolean;
    permanent_patterns: CustomPatternRecord[];
    session_patterns: CustomPatternRecord[];
}

export interface NonErrorPatternRecord {
    id: string;
    pattern: string;
    full_message: string;
    partial_pattern?: string;
    reason?: string;
    source_line?: number | string;
    created_at?: string;
    active?: boolean;
}

export interface NonErrorPatternsResponse {
    success: boolean;
    patterns: NonErrorPatternRecord[];
}

export interface MarkAsNonErrorResponse extends ApiMessageResponse {
    pattern_id?: string;
}

export interface AnalysisChangeRecord {
    id: string;
    changes: Record<string, unknown>;
    timestamp: string;
    user_id: string;
    change_type: string;
}

export interface AnalysisChangesResponse {
    success: boolean;
    changes: AnalysisChangeRecord[];
}

export interface SaveAnalysisChangesResponse extends ApiMessageResponse {
    change_id?: string;
}

export interface PotentialNewErrorItem {
    line: number;
    message: string;
    suspicious_words: string[];
    suggested_pattern: string;
    confidence: string;
}

export interface PatternSuggestionItem {
    pattern: string;
    frequency: number;
    suggested_regex: string;
}

export interface FrequentSuspiciousWordItem {
    word: string;
    count: number;
}

export interface NewErrorsAnalysisResponse {
    potential_errors: PotentialNewErrorItem[];
    pattern_suggestions: PatternSuggestionItem[];
    frequent_suspicious_words: FrequentSuspiciousWordItem[];
    total_potential_errors: number;
    analysis_coverage?: {
        lines_analyzed?: number;
        lines_with_known_patterns?: number;
        lines_with_potential_new_errors?: number;
    };
}

export interface LogAnalysisResponse {
    success: boolean;
    log_type?: string;
    total_results: number;
    results: AnalysisResultItem[];
    statistics: Record<string, unknown>;
    error_counts: Record<string, unknown>;
    severity_counts: Record<string, unknown>;
    chart_data?: {
        error_types?: { labels: string[]; values: number[] };
        temporal?: { labels: string[]; values: number[] };
        severity?: { labels: string[]; values: number[] };
        hourly?: { labels: string[]; values: number[] };
    };
    attention_points?: AttentionPointItem[];
    total_attention_points?: number;
    informational_lines?: InformationalLineItem[];
    new_errors?: NewErrorsAnalysisResponse;
    performance_analysis?: PerformanceAnalysisResponse;
    structured_analysis?: StructuredAnalysisResponse | null;
    top_programs_methods?: TopProgramsMethodsResponse;
    error?: string;
}

export interface AnalyzeInfoResponse {
    success: boolean;
    file_info: {
        filename: string;
        size_bytes: number;
        size_mb: number;
        line_count: number;
        processing_type: string;
    };
    processing_estimate: {
        estimated_time_seconds: number;
        estimated_time_human: string;
        will_use_optimization: boolean;
        chunk_processing: boolean;
    };
    sample_preview: {
        first_lines: string[];
        total_preview_lines: number;
    };
    recommendations: string[];
}

export interface LogCategoryMatch {
    count: number;
    display_name: string;
    samples: string[];
}

export interface LogCategoryGroupMatch {
    name: string;
    count: number;
    items: Record<string, LogCategoryMatch>;
}

export interface LogCategoryInfoResponse {
    success: boolean;
    filename: string;
    file_size: number;
    total_lines: number;
    analysis: Record<string, number>;
    selected_log_type?: string;
    selected_log_type_label?: string;
    detected_log_type?: string;
    detected_log_type_label?: string;
    effective_log_type?: string;
    effective_log_type_label?: string;
    found_categories: Record<string, LogCategoryMatch>;
    found_groups?: Record<string, LogCategoryGroupMatch>;
    category_info: {
        display_names?: Record<string, string>;
        descriptions?: Record<string, string>;
        log_types?: Record<string, {
            name: string;
        }>;
        groups?: Record<string, {
            name: string;
            categories: string[];
        }>;
    };
    samples?: Record<string, string[]>;
}

export interface SearchLogMatch {
    line_number: number;
    content: string;
    highlighted_content: string;
    timestamp: string | null;
    match_position: number;
}

export interface SearchLogResponse {
    success: boolean;
    total_matches: number;
    matches: SearchLogMatch[];
    search_info: {
        pattern: string;
        search_type: string;
        case_sensitive: boolean;
        total_lines_searched: number;
        filename: string;
    };
    error?: string;
}

export interface KnowledgeBaseMatch {
    type: string;
    code: string;
    category: string;
    severity: string;
    description: string;
    solution: string;
    example: string;
    pattern: string;
    source: string;
}

export interface KnowledgeBaseResponse {
    success: boolean;
    search_term: string;
    total_found: number;
    returned_count: number;
    truncated: boolean;
    max_results: number;
    matches: KnowledgeBaseMatch[];
    sources: Record<string, number>;
}

export interface DatasulPatternRecord {
    id: string;
    pattern: string;
    description: string;
    category: string;
    severity: string;
    solution?: string;
    tag?: string;
    priority?: number;
    active?: boolean;
    usage_count?: number;
    created_at?: string;
    last_detected?: string | null;
}

export interface DatasulPatternsResponse {
    success: boolean;
    patterns: DatasulPatternRecord[];
    total: number;
    error?: string;
}

export interface DatasulStatistics {
    total_patterns?: number;
    source?: string;
    patterns_by_priority?: Record<string, number>;
    patterns_by_category?: Record<string, number>;
    cache_age_seconds?: number;
    most_used_patterns?: Array<{
        pattern: string;
        usage_count: number;
        tag?: string;
    }>;
}

export interface DatasulStatisticsResponse {
    success: boolean;
    statistics?: DatasulStatistics;
    error?: string;
}

export interface DatasulRefreshResponse extends ApiMessageResponse { }

export interface ProfilerSummaryItem {
    [key: string]: unknown;
}

export interface ProfilerIssueItem {
    module: string;
    issues: string[];
    calls?: number;
    time_total_ms?: number;
    time_avg_ms?: number;
}

export interface ProfilerCallTreeStats {
    total_relationships?: number;
    unique_callers?: number;
    unique_callees?: number;
}

export interface ProfilerAnalysisPayload {
    session?: Record<string, unknown>;
    summary?: Record<string, unknown>;
    top_modules_by_time?: ProfilerSummaryItem[];
    top_modules_by_calls?: ProfilerSummaryItem[];
    top_modules_by_avg_time?: ProfilerSummaryItem[];
    top_lines?: ProfilerSummaryItem[];
    problematic_modules?: ProfilerIssueItem[];
    call_tree_stats?: ProfilerCallTreeStats;
    recommendations?: string[];
    top_bottlenecks?: ProfilerSummaryItem[];
    n_plus_one_suspects?: ProfilerSummaryItem[];
    call_tree?: ProfilerSummaryItem[];
}

export interface ProfilerResponse {
    success: boolean;
    filename: string;
    file_size: number;
    session?: Record<string, unknown>;
    summary?: Record<string, unknown>;
    top_bottlenecks?: ProfilerSummaryItem[];
    n_plus_one_suspects?: ProfilerSummaryItem[];
    call_tree?: ProfilerSummaryItem[];
    raw_data?: Record<string, unknown>;
    analysis?: ProfilerAnalysisPayload;
}

export interface VersionCompareStatusResponse {
    success?: boolean;
    base_lib_directory: string;
    directory_exists: boolean;
    versoes_indexadas: string[];
    total_versoes: number;
    total_programas_indexados: number;
    message?: string;
}

export interface VersionCompareEntry {
    programa: string;
    cliente: string;
    deveria_estar?: string;
    referencia_oficial?: string;
    fix_encontrada?: string;
    diferenca_builds?: number;
    caminho_encontrado?: string;
    versao_encontrada?: string;
}

export interface VersionCompareUpcEntry {
    programa: string;
    caminho: string;
    tipo?: string;
}

export interface VersionCompareFuncaoAtiva {
    origem?: string;
    funcao: string;
    valor: string;
    programa?: string;
    ativa?: boolean;
}

export interface VersionCompareExecucao {
    nome: string;
}

export interface VersionCompareAlias {
    alias: string;
    base: string;
}

export interface VersionCompareProgramaDetalhe {
    programa: string;
    programa_original?: string;
    versao: string;
    programa_pai?: string;
    caminho?: string;
    data?: string;
    hora?: string;
}

export interface VersionCompareHeader {
    criado_por?: string;
    criado_em?: string;
    versao_produto?: string;
    versao_produto_completa?: string;
    empresa?: string;
    progress?: string;
}

export interface VersionCompareResponse {
    success: boolean;
    product_version: string;
    header: VersionCompareHeader;
    summary: Record<string, number>;
    desatualizados: VersionCompareEntry[];
    ok: VersionCompareEntry[];
    adiantado_customizado: VersionCompareEntry[];
    nao_encontrado: VersionCompareEntry[];
    programas_com_appc?: VersionCompareUpcEntry[];
    programas_com_upc: VersionCompareUpcEntry[];
    programas_com_dpc: VersionCompareUpcEntry[];
    especificos: VersionCompareUpcEntry[];
    funcoes_ativas: VersionCompareFuncaoAtiva[];
    execucoes: VersionCompareExecucao[];
    databases: string[];
    aliases: VersionCompareAlias[];
    programas_detalhe: VersionCompareProgramaDetalhe[];
    index_info: VersionCompareStatusResponse;
    index_warning?: string;
    timings?: Record<string, string | number>;
    compare_metrics?: Record<string, string | number>;
}



// ===================== Issue Control & Evidence Register =====================

export interface IssueItem {
    id: string;
    data_criacao: string;
    ticket: string;
    issue: string;
    cliente: string;
    rotina: string;
    situacao: string;
    status: string;
    liberado_versoes: string;
}

export interface IssueCreatePayload {
    ticket: string;
    issue: string;
    cliente: string;
    rotina: string;
    situacao: string;
    status: string;
    liberado_versoes?: string;
}

export interface IssueUpdatePayload {
    ticket?: string;
    issue?: string;
    cliente?: string;
    rotina?: string;
    situacao?: string;
    status?: string;
    liberado_versoes?: string;
}

export interface UploadFilesResponse {
    session_id: string;
    files: Array<{ filename: string; path: string; size: number }>;
    message: string;
}

export interface ImportCsvResponse {
    imported_count: number;
    errors?: string[];
    total_errors?: number;
}
