import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
import {
    PoButtonModule,
    PoInfoModule,
    PoLoadingModule,
    PoPageModule,
    PoTableColumn,
    PoTableModule,
    PoWidgetModule
} from '@po-ui/ng-components';
import { finalize } from 'rxjs';

import { AnalysisHistoryItem } from '../../core/models/api.models';
import { BackendApiService } from '../../core/services/backend-api.service';

interface AnalysisHistoryTableItem {
    timestamp: string;
    filename: string;
    totalResults: number;
    mostCommonError: string;
}

@Component({
    selector: 'app-analysis-history-page',
    standalone: true,
    imports: [CommonModule, PoPageModule, PoWidgetModule, PoButtonModule, PoTableModule, PoLoadingModule, PoInfoModule],
    templateUrl: './analysis-history.page.html',
    styleUrl: './analysis-history.page.scss'
})
export class AnalysisHistoryPageComponent implements OnInit {
    private readonly api = inject(BackendApiService);

    protected historyRows: AnalysisHistoryTableItem[] = [];
    protected historyLoading = false;

    protected readonly historyColumns: PoTableColumn[] = [
        { property: 'timestamp', label: 'Quando', width: '200px' },
        { property: 'filename', label: 'Arquivo', width: '250px' },
        { property: 'totalResults', label: 'Resultados', width: '120px' },
        { property: 'mostCommonError', label: 'Erro mais comum' }
    ];

    protected readonly pageActions = [
        {
            label: 'Atualizar',
            icon: 'po-icon-refresh',
            action: () => this.loadHistory()
        }
    ];

    ngOnInit(): void {
        this.loadHistory();
    }

    protected loadHistory(): void {
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
}
