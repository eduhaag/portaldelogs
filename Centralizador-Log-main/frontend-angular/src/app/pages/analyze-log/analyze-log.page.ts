import { CommonModule } from '@angular/common';
import { Component, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';
import {
    PoButtonModule,
    PoIconModule,
    PoLoadingModule,
    PoModalComponent,
    PoModalModule,
    PoTagModule,
    PoWidgetModule
} from '@po-ui/ng-components';

import { AnalyzeInfoResponse, InformationalLineItem, LogAnalysisResponse } from '../../core/models/api.models';
import { BackendApiService } from '../../core/services/backend-api.service';
import { AnalysisSessionService } from '../../core/services/analysis-session.service';

@Component({
    selector: 'app-analyze-log-page',
    standalone: true,
    imports: [CommonModule, FormsModule, PoButtonModule, PoIconModule, PoLoadingModule, PoModalModule, PoTagModule, PoWidgetModule],
    templateUrl: './analyze-log.page.html',
    styleUrl: './analyze-log.page.scss'
})
export class AnalyzeLogPageComponent {
    @ViewChild('informationalReviewModal', { static: true }) informationalReviewModal!: PoModalComponent;

    private readonly api = inject(BackendApiService);
    private readonly analysisSession = inject(AnalysisSessionService);
    private readonly router = inject(Router);

    protected logFile: File | null = null;
    protected patternsFile: File | null = null;
    protected previewInfo: AnalyzeInfoResponse | null = null;
    protected analysisResult: LogAnalysisResponse | null = null;
    protected informationalLines: InformationalLineItem[] = [];
    protected loading = false;
    protected errorMessage = '';
    protected successMessage = '';
    protected savingInformationalLine: number | null = null;

    protected onLogFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.logFile = input?.files?.item(0) ?? null;
        this.previewInfo = null;
        this.analysisResult = null;
        this.informationalLines = [];
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
                    this.analysisResult = response;
                    this.informationalLines = [...(response.informational_lines ?? [])];
                    this.syncAnalysisSession();

                    if (this.informationalLines.length > 0) {
                        this.successMessage = 'Análise concluída. Revise as linhas informativas antes de abrir o resultado completo.';
                        this.informationalReviewModal.open();
                        return;
                    }

                    this.successMessage = 'Análise concluída com sucesso.';
                    void this.router.navigateByUrl('/analise/resultados');
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao analisar o log.';
                }
            });
    }

    protected goBack(): void {
        void this.router.navigateByUrl('/analise');
    }

    protected get hasAnalysisResult(): boolean {
        return !!this.analysisResult;
    }

    protected get informationalSuggestionCount(): number {
        return this.informationalLines.length;
    }

    protected openInformationalReview(): void {
        if (this.informationalLines.length > 0) {
            this.informationalReviewModal.open();
        }
    }

    protected goToResults(): void {
        if (!this.analysisResult) {
            return;
        }

        this.syncAnalysisSession();
        void this.router.navigateByUrl('/analise/resultados');
    }

    protected markInformationalAsNonError(item: InformationalLineItem): void {
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
                    this.removeInformationalLine(item);
                    this.successMessage = 'Linha marcada como não-erro e salva para as próximas análises.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao salvar a linha informativa como não-erro.';
                }
            });
    }

    protected keepInformationalAsError(item: InformationalLineItem): void {
        this.removeInformationalLine(item);
        this.successMessage = 'Linha mantida como ocorrência válida. A sugestão informativa foi apenas descartada.';
    }

    private removeInformationalLine(item: InformationalLineItem): void {
        this.informationalLines = this.informationalLines.filter((line) => line !== item);
        this.syncAnalysisSession();

        if (this.informationalLines.length === 0) {
            this.informationalReviewModal.close();
        }
    }

    private syncAnalysisSession(): void {
        if (!this.analysisResult) {
            return;
        }

        const updatedResult: LogAnalysisResponse = {
            ...this.analysisResult,
            informational_lines: [...this.informationalLines]
        };

        this.analysisResult = updatedResult;
        this.analysisSession.save(updatedResult, this.logFile?.name ?? this.previewInfo?.file_info.filename ?? 'log');
    }

    private extractInformationalPattern(item: InformationalLineItem): string {
        const detectedPattern = item.detected_pattern?.trim();
        if (detectedPattern) {
            return detectedPattern;
        }

        const normalized = item.message.replace(/\s+/g, ' ').trim();
        return normalized.length > 160 ? `${normalized.slice(0, 160)}...` : normalized;
    }
}
