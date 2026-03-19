import { HttpClient, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
    AddCustomPatternPayload,
    AddCustomPatternResponse,
    AuthResponse,
    CategorizeErrorPayload,
    CategorizeErrorResponse,
    AnalysisChangesResponse,
    AnalyzeInfoResponse,
    AnalysisHistoryItem,
    CustomPatternsResponse,
    DatasulRefreshResponse,
    DatasulPatternsResponse,
    DatasulStatisticsResponse,
    DeleteCustomPatternResponse,
    ErrorCategorizationsResponse,
    KnowledgeBaseResponse,
    LogCategoryInfoResponse,
    LogAnalysisResponse,
    MarkAsNonErrorPayload,
    MarkAsNonErrorResponse,
    NonErrorPatternsResponse,
    PatternTestRequest,
    PatternTestResponse,
    ProfilerResponse,
    SaveAnalysisChangesPayload,
    SaveAnalysisChangesResponse,
    SearchLogResponse,
    VersionCompareResponse,
    VersionCompareStatusResponse,
    IssueItem,
    IssueCreatePayload,
    IssueUpdatePayload,
    UploadFilesResponse,
    ImportCsvResponse,
    ApiMessageResponse
} from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class BackendApiService {
    private readonly http = inject(HttpClient);
    private readonly apiBaseUrl = this.resolveApiBaseUrl();

    login(payload: { username: string; password: string }): Observable<AuthResponse> {
        return this.http.post<AuthResponse>(`${this.apiBaseUrl}/auth/login`, payload);
    }

    registerUser(payload: {
        display_name: string;
        username: string;
        email: string;
        password: string;
    }): Observable<AuthResponse> {
        return this.http.post<AuthResponse>(`${this.apiBaseUrl}/auth/register`, payload);
    }

    analyzeInfo(logFile: File): Observable<AnalyzeInfoResponse> {
        const formData = new FormData();
        formData.append('log_file', logFile);
        return this.http.post<AnalyzeInfoResponse>(`${this.apiBaseUrl}/analyze-info`, formData);
    }

    analyzeLog(logFile: File, patternsFile?: File | null): Observable<LogAnalysisResponse> {
        const formData = new FormData();
        formData.append('log_file', logFile);

        if (patternsFile) {
            formData.append('patterns_file', patternsFile);
        }

        return this.http.post<LogAnalysisResponse>(`${this.apiBaseUrl}/analyze-log`, formData);
    }

    analyzeLogCategories(logFile: File, selectedLogType: string): Observable<LogCategoryInfoResponse> {
        const formData = new FormData();
        formData.append('log_file', logFile);
        formData.append('selected_log_type', selectedLogType);
        return this.http.post<LogCategoryInfoResponse>(`${this.apiBaseUrl}/analyze-log-categories`, formData);
    }

    cleanLog(logFile: File, categoriesToRemove: string[]): Observable<HttpResponse<Blob>> {
        const formData = new FormData();
        formData.append('log_file', logFile);
        formData.append('categories_to_remove', categoriesToRemove.join(','));

        return this.http.post(`${this.apiBaseUrl}/clean-log`, formData, {
            observe: 'response',
            responseType: 'blob'
        });
    }

    splitLogFile(logFile: File, linesPerChunk: number): Observable<HttpResponse<Blob>> {
        const formData = new FormData();
        formData.append('log_file', logFile);
        formData.append('lines_per_chunk', String(linesPerChunk));

        return this.http.post(`${this.apiBaseUrl}/split-log`, formData, {
            observe: 'response',
            responseType: 'blob'
        });
    }

    downloadAnalysisCsv(logFile: File, patternsFile?: File | null): Observable<HttpResponse<Blob>> {
        const formData = new FormData();
        formData.append('log_file', logFile);

        if (patternsFile) {
            formData.append('patterns_file', patternsFile);
        }

        return this.http.post(`${this.apiBaseUrl}/download-csv`, formData, {
            observe: 'response',
            responseType: 'blob'
        });
    }

    getAnalysisHistory(): Observable<AnalysisHistoryItem[]> {
        return this.http.get<AnalysisHistoryItem[]>(`${this.apiBaseUrl}/analysis-history`);
    }

    testPattern(payload: PatternTestRequest): Observable<PatternTestResponse> {
        return this.http.post<PatternTestResponse>(`${this.apiBaseUrl}/test-pattern`, payload);
    }

    addCustomPattern(payload: AddCustomPatternPayload): Observable<AddCustomPatternResponse> {
        return this.http.post<AddCustomPatternResponse>(`${this.apiBaseUrl}/add-pattern`, payload);
    }

    getCustomPatterns(): Observable<CustomPatternsResponse> {
        return this.http.get<CustomPatternsResponse>(`${this.apiBaseUrl}/custom-patterns`);
    }

    deleteCustomPattern(patternId: string): Observable<DeleteCustomPatternResponse> {
        return this.http.delete<DeleteCustomPatternResponse>(`${this.apiBaseUrl}/custom-patterns/${patternId}`);
    }

    categorizeError(payload: CategorizeErrorPayload): Observable<CategorizeErrorResponse> {
        return this.http.post<CategorizeErrorResponse>(`${this.apiBaseUrl}/categorize-error`, payload);
    }

    getErrorCategorizations(): Observable<ErrorCategorizationsResponse> {
        return this.http.get<ErrorCategorizationsResponse>(`${this.apiBaseUrl}/error-categorizations`);
    }

    markAsNonError(payload: MarkAsNonErrorPayload): Observable<MarkAsNonErrorResponse> {
        return this.http.post<MarkAsNonErrorResponse>(`${this.apiBaseUrl}/mark-as-non-error`, payload);
    }

    getNonErrorPatterns(): Observable<NonErrorPatternsResponse> {
        return this.http.get<NonErrorPatternsResponse>(`${this.apiBaseUrl}/non-error-patterns`);
    }

    saveAnalysisChanges(payload: SaveAnalysisChangesPayload): Observable<SaveAnalysisChangesResponse> {
        return this.http.post<SaveAnalysisChangesResponse>(`${this.apiBaseUrl}/save-analysis-changes`, payload);
    }

    getAnalysisChanges(): Observable<AnalysisChangesResponse> {
        return this.http.get<AnalysisChangesResponse>(`${this.apiBaseUrl}/analysis-changes`);
    }

    searchLog(
        logFile: File,
        searchPattern: string,
        caseSensitive: boolean,
        searchType: string
    ): Observable<SearchLogResponse> {
        const formData = new FormData();
        formData.append('log_file', logFile);
        formData.append('search_pattern', searchPattern);
        formData.append('case_sensitive', String(caseSensitive));
        formData.append('search_type', searchType);

        return this.http.post<SearchLogResponse>(`${this.apiBaseUrl}/search-log`, formData);
    }

    searchKnowledgeBase(searchTerm: string, maxResults = 50): Observable<KnowledgeBaseResponse> {
        return this.http.post<KnowledgeBaseResponse>(`${this.apiBaseUrl}/search-knowledge-base`, {
            search_term: searchTerm,
            max_results: maxResults
        });
    }

    analyzeProfiler(logFile: File): Observable<ProfilerResponse> {
        const formData = new FormData();
        formData.append('log_file', logFile);
        return this.http.post<ProfilerResponse>(`${this.apiBaseUrl}/analyze-profiler`, formData);
    }

    getDatasulPatterns(): Observable<DatasulPatternsResponse> {
        return this.http.get<DatasulPatternsResponse>(`${this.apiBaseUrl}/datasul-patterns`);
    }

    getDatasulStatistics(): Observable<DatasulStatisticsResponse> {
        return this.http.get<DatasulStatisticsResponse>(`${this.apiBaseUrl}/datasul-statistics`);
    }

    refreshDatasulPatterns(): Observable<DatasulRefreshResponse> {
        return this.http.post<DatasulRefreshResponse>(`${this.apiBaseUrl}/refresh-datasul-patterns`, {});
    }

    getVersionCompareStatus(): Observable<VersionCompareStatusResponse> {
        return this.http.get<VersionCompareStatusResponse>(`${this.apiBaseUrl}/version-compare/status`);
    }

    reloadVersionCompare(): Observable<VersionCompareStatusResponse> {
        return this.http.post<VersionCompareStatusResponse>(`${this.apiBaseUrl}/version-compare/reload`, {});
    }

    compareVersions(logFile: File): Observable<VersionCompareResponse> {
        const formData = new FormData();
        formData.append('log_file', logFile);
        return this.http.post<VersionCompareResponse>(`${this.apiBaseUrl}/version-compare`, formData);
    }

    // Issue Control & Evidence Register
    getIssues(): Observable<IssueItem[]> {
        return this.http.get<IssueItem[]>(`${this.apiBaseUrl}/issues`);
    }

    createIssue(payload: IssueCreatePayload): Observable<IssueItem> {
        return this.http.post<IssueItem>(`${this.apiBaseUrl}/issues`, payload);
    }

    updateIssue(issueId: string, payload: IssueUpdatePayload): Observable<ApiMessageResponse> {
        return this.http.put<ApiMessageResponse>(`${this.apiBaseUrl}/issues/${issueId}`, payload);
    }

    deleteIssue(issueId: string): Observable<ApiMessageResponse> {
        return this.http.delete<ApiMessageResponse>(`${this.apiBaseUrl}/issues/${issueId}`);
    }

    uploadFiles(files: File[], sessionId?: string): Observable<UploadFilesResponse> {
        const formData = new FormData();
        files.forEach(f => formData.append('files', f));
        if (sessionId) {
            formData.append('session_id', sessionId);
        }
        return this.http.post<UploadFilesResponse>(`${this.apiBaseUrl}/upload-files`, formData);
    }

    deleteUploadedFile(sessionId: string, filename: string): Observable<ApiMessageResponse> {
        return this.http.delete<ApiMessageResponse>(`${this.apiBaseUrl}/uploaded-files/${sessionId}?filename=${encodeURIComponent(filename)}`);
    }

    generatePdf(formData: FormData): Observable<HttpResponse<Blob>> {
        return this.http.post(`${this.apiBaseUrl}/generate-pdf`, formData, {
            observe: 'response',
            responseType: 'blob'
        });
    }

    cleanupSession(sessionId: string): Observable<ApiMessageResponse> {
        return this.http.delete<ApiMessageResponse>(`${this.apiBaseUrl}/cleanup-session/${sessionId}`);
    }

    importCsv(file: File): Observable<ImportCsvResponse> {
        const formData = new FormData();
        formData.append('file', file);
        return this.http.post<ImportCsvResponse>(`${this.apiBaseUrl}/import-csv`, formData);
    }

    exportCsv(): Observable<HttpResponse<Blob>> {
        return this.http.get(`${this.apiBaseUrl}/export-csv`, {
            observe: 'response',
            responseType: 'blob'
        });
    }

    private resolveApiBaseUrl(): string {
        if (typeof window === 'undefined') {
            return 'http://127.0.0.1:8001/api';
        }

        const { hostname, port, protocol } = window.location;
        if ((hostname === '127.0.0.1' || hostname === 'localhost') && /^42\d{2}$/.test(port)) {
            return `${protocol}//127.0.0.1:8001/api`;
        }

        return '/api';
    }
}
