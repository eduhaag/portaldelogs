import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
    PoButtonModule,
    PoCheckboxModule,
    PoDropdownAction,
    PoDropdownModule,
    PoFieldModule,
    PoInfoModule,
    PoModalAction,
    PoModalComponent,
    PoModalModule,
    PoPageModule,
    PoSelectOption,
    PoTagModule,
    PoTableColumn,
    PoTableModule,
    PoWidgetModule
} from '@po-ui/ng-components';
import { finalize } from 'rxjs';

import { SearchLogMatch } from '../../core/models/api.models';
import { BackendApiService } from '../../core/services/backend-api.service';

interface SearchTableItem {
    lineNumber: number;
    timestamp: string;
    content: string;
    highlightedContent: string;
    matchPosition: number;
}

@Component({
    selector: 'app-advanced-search-page',
    standalone: true,
    imports: [CommonModule, FormsModule, PoPageModule, PoWidgetModule, PoFieldModule, PoButtonModule, PoDropdownModule, PoTableModule, PoModalModule, PoCheckboxModule, PoTagModule, PoInfoModule],
    templateUrl: './advanced-search.page.html',
    styleUrl: './advanced-search.page.scss'
})
export class AdvancedSearchPageComponent {
    private readonly api = inject(BackendApiService);
    private readonly searchTypeDescriptions: Record<string, string> = {
        procedure: 'Busca literal orientada a procedures e trechos conhecidos.',
        literal: 'Busca texto puro no arquivo.',
        custom: 'Usa expressão regular livre.'
    };

    protected logFile: File | null = null;
    protected searchPattern = '';
    protected caseSensitive = false;
    protected searchType = 'procedure';
    protected loading = false;
    protected errorMessage = '';
    protected matches: SearchLogMatch[] = [];
    protected tableItems: SearchTableItem[] = [];
    protected selectedMatch: SearchLogMatch | null = null;
    protected resultSummary: Array<{ label: string; value: string | number }> = [];
    protected recentPatterns: string[] = [];
    protected readonly quickPatterns = ['Procedure:', 'AppServer', 'PASOE', 'DataServer', 'ERROR'];

    protected readonly searchTypeOptions: PoSelectOption[] = [
        { label: 'Procedure', value: 'procedure' },
        { label: 'Literal', value: 'literal' },
        { label: 'Regex customizada', value: 'custom' }
    ];

    protected get searchActions(): PoDropdownAction[] {
        return [
            {
                label: 'Buscar agora',
                action: () => {
                    if (this.logFile && this.searchPattern.trim()) {
                        // action intentionally left for the main primary button to execute with modal context
                    }
                },
                disabled: !this.logFile || !this.searchPattern.trim() || this.loading
            },
            {
                label: 'Aplicar Procedure',
                action: () => this.applyQuickPattern('Procedure:')
            },
            {
                label: 'Aplicar AppServer',
                action: () => this.applyQuickPattern('AppServer')
            },
            {
                label: 'Limpar resultados',
                action: () => this.clearResults()
            }
        ];
    }

    protected readonly matchColumns: PoTableColumn[] = [
        { property: 'lineNumber', label: 'Linha', width: '100px' },
        { property: 'timestamp', label: 'Timestamp', width: '180px' },
        { property: 'content', label: 'Conteúdo' }
    ];

    protected readonly closeDetailAction: PoModalAction = {
        label: 'Fechar',
        action: () => this.closeDetail()
    };

    protected onLogFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.logFile = input?.files?.item(0) ?? null;
        this.matches = [];
        this.tableItems = [];
        this.resultSummary = [];
        this.errorMessage = '';
    }

    protected applyQuickPattern(pattern: string): void {
        this.searchPattern = pattern;
    }

    protected executeSearch(detailModal: PoModalComponent): void {
        if (!this.logFile || !this.searchPattern.trim()) {
            this.errorMessage = 'Selecione um log e informe o padrão de busca.';
            return;
        }

        this.loading = true;
        this.errorMessage = '';

        this.api.searchLog(this.logFile, this.searchPattern.trim(), this.caseSensitive, this.searchType)
            .pipe(finalize(() => (this.loading = false)))
            .subscribe({
                next: (response) => {
                    this.loading = false;
                    this.matches = response.matches;
                    this.tableItems = response.matches.map((match) => ({
                        lineNumber: match.line_number,
                        timestamp: match.timestamp ?? '-',
                        content: match.content,
                        highlightedContent: match.highlighted_content,
                        matchPosition: match.match_position
                    }));
                    this.resultSummary = [
                        { label: 'Matches encontrados', value: response.total_matches },
                        { label: 'Linhas varridas', value: response.search_info.total_lines_searched },
                        { label: 'Tipo de busca', value: this.resolveSearchTypeLabel(response.search_info.search_type) },
                        { label: 'Case sensitive', value: response.search_info.case_sensitive ? 'Sim' : 'Não' }
                    ];
                    this.pushRecentPattern(this.searchPattern.trim());

                    if (response.matches.length > 0) {
                        this.openMatchDetail(response.matches[0], detailModal);
                    }
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao executar busca avançada.';
                }
            });
    }

    protected openMatchDetail(match: SearchLogMatch, detailModal: PoModalComponent): void {
        this.selectedMatch = match;
        detailModal.open();
    }

    protected closeDetail(): void {
        this.selectedMatch = null;
    }

    protected trackRecentPattern(pattern: string): string {
        return pattern;
    }

    protected selectRecentPattern(pattern: string): void {
        this.searchPattern = pattern;
    }

    protected get selectedSearchTypeDescription(): string {
        return this.searchTypeDescriptions[this.searchType] ?? '';
    }

    protected clearResults(): void {
        this.matches = [];
        this.tableItems = [];
        this.resultSummary = [];
        this.selectedMatch = null;
        this.errorMessage = '';
    }

    private pushRecentPattern(pattern: string): void {
        if (!pattern) {
            return;
        }

        this.recentPatterns = [pattern, ...this.recentPatterns.filter((item) => item !== pattern)].slice(0, 5);
    }

    private resolveSearchTypeLabel(searchType: string): string {
        return this.searchTypeOptions.find((option) => option.value === searchType)?.label ?? searchType;
    }
}
