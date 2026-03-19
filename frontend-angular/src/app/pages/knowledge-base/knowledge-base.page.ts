// ===============================
// Componente de Base de Conhecimento
// Permite pesquisar e visualizar padrões conhecidos de erros e mensagens.
// Demonstra uso de tabelas, filtros e integração com PO UI.
// Comentários didáticos para facilitar o entendimento!
// ===============================
import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
    PoButtonModule,
    PoDropdownAction,
    PoDropdownModule,
    PoFieldModule,
    PoInfoModule,
    PoLoadingModule,
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

import { KnowledgeBaseMatch } from '../../core/models/api.models';
import { BackendApiService } from '../../core/services/backend-api.service';

interface KnowledgeTableItem {
    type: string;
    code: string;
    category: string;
    severity: string;
    source: string;
    description: string;
}

@Component({
    selector: 'app-knowledge-base-page',
    standalone: true,
    imports: [CommonModule, FormsModule, PoPageModule, PoWidgetModule, PoFieldModule, PoButtonModule, PoDropdownModule, PoTableModule, PoModalModule, PoTagModule, PoInfoModule, PoLoadingModule],
    templateUrl: './knowledge-base.page.html',
    styleUrl: './knowledge-base.page.scss'
})
export class KnowledgeBasePageComponent {
    // Serviço de API para comunicação com o backend
    private readonly api = inject(BackendApiService);

    protected searchTerm = '';
    protected loading = false;
    protected errorMessage = '';
    protected totalFound = 0;
    protected returnedCount = 0;
    protected resultLimit = 0;
    protected truncatedResults = false;
    protected sourceStats: Array<{ key: string; value: number }> = [];
    protected matches: KnowledgeBaseMatch[] = [];
    protected tableItems: KnowledgeTableItem[] = [];
    protected filteredItems: KnowledgeTableItem[] = [];
    protected selectedMatch: KnowledgeBaseMatch | null = null;
    protected sourceFilter = 'all';
    protected severityFilter = 'all';
    protected recentTerms: string[] = [];
    // Termos rápidos para facilitar a busca do usuário
    protected readonly quickTerms = ['DataServer', 'Rejeição 999', '18215', 'AppServer', 'PASOE'];

    protected readonly columns: PoTableColumn[] = [
        { property: 'type', label: 'Tipo', width: '140px' },
        { property: 'code', label: 'Código', width: '140px' },
        { property: 'category', label: 'Categoria', width: '180px' },
        { property: 'severity', label: 'Severidade', width: '130px' },
        { property: 'source', label: 'Origem' },
        { property: 'description', label: 'Descrição' }
    ];

    protected readonly closeDetailAction: PoModalAction = {
        label: 'Fechar',
        action: () => this.closeDetails()
    };

    protected get sourceFilterOptions(): PoSelectOption[] {
        return [
            { label: 'Todas', value: 'all' },
            ...this.availableSources.map((source) => ({ label: source, value: source }))
        ];
        // O filtro acima permite ao usuário selecionar a origem dos padrões exibidos na tabela.
    }

    protected get severityFilterOptions(): PoSelectOption[] {
        return [
            { label: 'Todas', value: 'all' },
            ...this.availableSeverities.map((severity) => ({ label: severity, value: severity }))
        ];
    }

    protected get knowledgeActions(): PoDropdownAction[] {
        return [
            {
                label: 'Aplicar DataServer',
                action: () => this.applyQuickTerm('DataServer')
            },
            {
                label: 'Aplicar PASOE',
                action: () => this.applyQuickTerm('PASOE')
            },
            {
                label: 'Limpar filtros',
                action: () => {
                    this.sourceFilter = 'all';
                    this.severityFilter = 'all';
                    this.applyFilters();
                }
            }
        ];
    }

    protected search(detailModal: PoModalComponent): void {
        if (!this.searchTerm.trim()) {
            this.errorMessage = 'Informe um termo para pesquisar na base de conhecimento.';
            return;
        }

        this.loading = true;
        this.errorMessage = '';

        this.api.searchKnowledgeBase(this.searchTerm.trim())
            .pipe(finalize(() => (this.loading = false)))
            .subscribe({
                next: (response) => {
                    this.loading = false;
                    this.totalFound = response.total_found;
                    this.returnedCount = response.returned_count;
                    this.resultLimit = response.max_results;
                    this.truncatedResults = response.truncated;
                    this.matches = response.matches;
                    this.sourceStats = Object.entries(response.sources).map(([key, value]) => ({ key, value }));
                    this.tableItems = response.matches.map((match) => ({
                        type: match.type,
                        code: match.code,
                        category: match.category,
                        severity: match.severity,
                        source: match.source,
                        description: match.description
                    }));
                    this.applyFilters();
                    this.pushRecentTerm(this.searchTerm.trim());

                    if (response.matches.length > 0) {
                        this.openDetails(response.matches[0], detailModal);
                    }
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao consultar a base de conhecimento.';
                }
            });
    }

    protected openDetails(match: KnowledgeBaseMatch, detailModal: PoModalComponent): void {
        this.selectedMatch = match;
        detailModal.open();
    }

    protected closeDetails(): void {
        this.selectedMatch = null;
    }

    protected applyQuickTerm(term: string): void {
        this.searchTerm = term;
    }

    protected applyFilters(): void {
        this.filteredItems = this.tableItems.filter((item) => {
            const sourceMatches = this.sourceFilter === 'all' || item.source === this.sourceFilter;
            const severityMatches = this.severityFilter === 'all' || item.severity === this.severityFilter;
            return sourceMatches && severityMatches;
        });
    }

    protected get availableSources(): string[] {
        return [...new Set(this.tableItems.map((item) => item.source).filter(Boolean))];
    }

    protected get availableSeverities(): string[] {
        return [...new Set(this.tableItems.map((item) => item.severity).filter(Boolean))];
    }

    protected selectRecentTerm(term: string): void {
        this.searchTerm = term;
    }

    protected trackTerm(term: string): string {
        return term;
    }

    private pushRecentTerm(term: string): void {
        if (!term) {
            return;
        }

        this.recentTerms = [term, ...this.recentTerms.filter((item) => item !== term)].slice(0, 5);
    }
}
