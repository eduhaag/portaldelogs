import { Page, Route } from '@playwright/test';

interface AuthSessionOptions {
    username?: string;
    displayName?: string;
    email?: string;
    token?: string;
    expiresAt?: string;
}

export interface AnalyzeLogMockResponse {
    success: boolean;
    log_type?: string;
    total_results: number;
    results: Array<Record<string, unknown>>;
    statistics: Record<string, unknown>;
    error_counts: Record<string, unknown>;
    severity_counts: Record<string, unknown>;
    chart_data?: Record<string, unknown>;
    attention_points?: Array<Record<string, unknown>>;
    total_attention_points?: number;
    informational_lines?: Array<Record<string, unknown>>;
    new_errors?: Record<string, unknown>;
    performance_analysis?: Record<string, unknown> | null;
    structured_analysis?: Record<string, unknown> | null;
    top_programs_methods?: Record<string, unknown>;
}

function jsonHeaders(extra?: Record<string, string>): Record<string, string> {
    return {
        'content-type': 'application/json',
        'access-control-allow-origin': '*',
        'access-control-allow-methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
        'access-control-allow-headers': '*',
        ...extra
    };
}

export async function fulfillJson(route: Route, body: unknown, status = 200): Promise<void> {
    if (route.request().method() === 'OPTIONS') {
        await route.fulfill({
            status: 204,
            headers: jsonHeaders()
        });
        return;
    }

    await route.fulfill({
        status,
        headers: jsonHeaders(),
        json: body
    });
}

export async function seedAuthenticatedSession(page: Page, options: AuthSessionOptions = {}): Promise<void> {
    const session = {
        username: options.username ?? 'qa-user',
        displayName: options.displayName ?? 'QA User',
        email: options.email ?? 'qa@example.com',
        token: options.token ?? 'fake-jwt-token',
        tokenType: 'Bearer',
        expiresAt: options.expiresAt ?? '2099-01-01T00:00:00.000Z',
        authenticatedAt: '2026-03-16T10:00:00.000Z'
    };

    await page.addInitScript((storageSession) => {
        window.sessionStorage.setItem('log-analyzer:auth-session', JSON.stringify(storageSession));
    }, session);
}

export async function mockDashboardBootstrap(page: Page): Promise<void> {
    await page.route('**/api/analysis-history*', (route) => fulfillJson(route, []));
    await page.route('**/api/custom-patterns*', (route) => fulfillJson(route, { success: true, patterns: [] }));
    await page.route('**/api/error-categorizations*', (route) => fulfillJson(route, {
        success: true,
        permanent_patterns: [],
        session_patterns: []
    }));
    await page.route('**/api/non-error-patterns*', (route) => fulfillJson(route, { success: true, patterns: [] }));
    await page.route('**/api/analysis-changes*', (route) => fulfillJson(route, { success: true, changes: [] }));
    await page.route('**/api/datasul-patterns*', (route) => fulfillJson(route, { success: true, patterns: [], total: 0 }));
    await page.route('**/api/datasul-statistics*', (route) => fulfillJson(route, {
        success: true,
        statistics: {
            total_patterns: 0,
            patterns_by_priority: {},
            patterns_by_category: {},
            cache_age_seconds: 0,
            most_used_patterns: []
        }
    }));
    await page.route('**/api/version-compare/status*', (route) => fulfillJson(route, {
        success: true,
        base_lib_directory: 'C:/bases',
        directory_exists: true,
        indexed_bases: 2,
        indexed_fixes: 3,
        indexed_program_versions: 20,
        message: 'ok'
    }));
}

export async function mockLoginSuccess(page: Page): Promise<void> {
    await page.route('**/api/auth/login*', (route) => fulfillJson(route, {
        success: true,
        message: 'Login realizado com sucesso.',
        user: {
            username: 'qa-user',
            display_name: 'QA User',
            email: 'qa@example.com'
        },
        access_token: 'fake-jwt-token',
        token_type: 'Bearer',
        expires_in: 3600,
        expires_at: '2099-01-01T00:00:00.000Z'
    }));
}

export async function mockKnowledgeBaseSearch(page: Page): Promise<void> {
    await page.route('**/api/search-knowledge-base*', (route) => fulfillJson(route, {
        success: true,
        search_term: 'DataServer',
        total_found: 12,
        returned_count: 5,
        truncated: true,
        max_results: 5,
        matches: [
            {
                type: 'Padrão Datasul',
                code: '18215',
                category: 'Banco',
                severity: 'Alto',
                description: 'Falha no DataServer ao sincronizar metadados.',
                solution: 'Validar conectividade e reiniciar o serviço.',
                example: 'DataServer metadata sync failed',
                pattern: 'DataServer',
                source: 'Datasul Knowledge Base'
            },
            {
                type: 'Padrão LOGIX',
                code: 'LOG-77',
                category: 'Integração',
                severity: 'Médio',
                description: 'Timeout durante envio de lote.',
                solution: 'Reprocessar após revisar fila.',
                example: 'Timeout on batch send',
                pattern: 'Timeout',
                source: 'LOGIX Knowledge Base'
            },
            {
                type: 'Padrão TOTVS',
                code: 'TVS-91',
                category: 'Middleware',
                severity: 'Alto',
                description: 'Falha de comunicação entre serviço e broker.',
                solution: 'Verificar broker e certificados.',
                example: 'Broker communication failed',
                pattern: 'broker',
                source: 'TOTVS Knowledge Base'
            },
            {
                type: 'Padrão Sistema',
                code: 'PASOE',
                category: 'AppServer/PASOE',
                severity: 'Crítico',
                description: 'Instância PASOE indisponível.',
                solution: 'Reiniciar instância e validar healthcheck.',
                example: 'PASOE instance failed',
                pattern: 'PASOE',
                source: 'Sistema - Padrões Progress/PASOE'
            },
            {
                type: 'Padrão Personalizado',
                code: 'Custom',
                category: 'Personalizado',
                severity: 'Médio',
                description: 'Mensagem catalogada pelo usuário.',
                solution: 'Seguir playbook interno.',
                example: 'Erro interno de negócio',
                pattern: 'erro interno',
                source: 'MongoDB - Padrões Personalizados'
            }
        ],
        sources: {
            datasul_patterns: 4,
            logix_patterns: 3,
            totvs_patterns: 2,
            custom_patterns: 2,
            system_patterns: 1
        }
    }));
}

export async function mockAnalyzeInfo(page: Page): Promise<void> {
    await page.route('**/api/analyze-info*', (route) => fulfillJson(route, {
        success: true,
        file_info: {
            filename: 'app.log',
            size_bytes: 2048,
            size_mb: 0.01,
            line_count: 120,
            processing_type: 'standard'
        },
        processing_estimate: {
            estimated_time_seconds: 5,
            estimated_time_human: '5s',
            will_use_optimization: false,
            chunk_processing: false
        },
        sample_preview: {
            first_lines: ['ERROR broker unavailable'],
            total_preview_lines: 1
        },
        recommendations: ['Processamento padrão será usado']
    }));
}

export async function mockAnalyzeLog(page: Page, response?: Partial<AnalyzeLogMockResponse>): Promise<void> {
    const payload: AnalyzeLogMockResponse = {
        success: true,
        log_type: 'progress',
        total_results: 1,
        results: [
            {
                line_number: 10,
                severity: 'Alto',
                category: 'AppServer',
                type: 'Timeout',
                message: 'Broker unavailable',
                matched_pattern: 'broker unavailable',
                description: 'Falha no broker',
                solution: 'Reiniciar broker',
                timestamp: '2026-03-16 10:00:00'
            }
        ],
        statistics: {
            total_lines_processed: 120,
            most_common_error: ['Timeout', 1]
        },
        error_counts: { Timeout: 1 },
        severity_counts: { Alto: 1 },
        chart_data: {
            error_types: { labels: ['Timeout'], values: [1] },
            temporal: { labels: ['10:00'], values: [1] },
            severity: { labels: ['Alto'], values: [1] },
            hourly: { labels: ['10'], values: [1] }
        },
        attention_points: [],
        total_attention_points: 0,
        informational_lines: [],
        new_errors: {
            potential_errors: [],
            pattern_suggestions: [],
            frequent_suspicious_words: [],
            total_potential_errors: 0
        },
        performance_analysis: null,
        structured_analysis: null,
        top_programs_methods: {
            top_programs: []
        },
        ...response
    };

    await page.route('**/api/analyze-log*', (route) => fulfillJson(route, payload));
}

export async function mockAdvancedSearch(page: Page): Promise<void> {
    await page.route('**/api/search-log*', (route) => fulfillJson(route, {
        success: true,
        total_matches: 2,
        matches: [
            {
                line_number: 14,
                content: 'Procedure test.p failed',
                highlighted_content: '**Procedure** test.p failed',
                timestamp: '2026-03-16 10:15:00',
                match_position: 0
            },
            {
                line_number: 88,
                content: 'Procedure worker.p timeout',
                highlighted_content: '**Procedure** worker.p timeout',
                timestamp: '2026-03-16 10:16:00',
                match_position: 0
            }
        ],
        search_info: {
            pattern: 'Procedure',
            search_type: 'procedure',
            case_sensitive: false,
            total_lines_searched: 240,
            filename: 'app.log'
        }
    }));
}
