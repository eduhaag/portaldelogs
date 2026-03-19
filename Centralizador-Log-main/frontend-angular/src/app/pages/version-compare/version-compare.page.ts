import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import {
    PoButtonModule,
    PoLoadingModule,
    PoPageModule,
    PoTableColumn,
    PoTableModule,
    PoTabsModule,
    PoWidgetModule
} from '@po-ui/ng-components';
import { finalize } from 'rxjs';

import {
    VersionCompareEntry,
    VersionCompareResponse,
    VersionCompareStatusResponse
} from '../../core/models/api.models';
import { BackendApiService } from '../../core/services/backend-api.service';
import { VersionCompareSessionService } from '../../core/services/version-compare-session.service';

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

@Component({
    selector: 'app-version-compare-page',
    standalone: true,
    imports: [CommonModule, PoPageModule, PoWidgetModule, PoButtonModule, PoTableModule, PoTabsModule, PoLoadingModule],
    templateUrl: './version-compare.page.html',
    styleUrl: './version-compare.page.scss'
})
export class VersionComparePageComponent implements OnInit {
    private readonly api = inject(BackendApiService);
    private readonly versionCompareSession = inject(VersionCompareSessionService);

    protected versionCompareFile: File | null = null;
    protected versionCompareResult: VersionCompareResponse | null = null;
    protected versionCompareStatus: VersionCompareStatusResponse | null = null;
    protected versionCompareLoading = false;
    protected errorMessage = '';
    protected successMessage = '';
    protected analyzedAt = '';
    protected uploadedFilename = '';

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

    ngOnInit(): void {
        this.restoreSession();
        this.loadVersionCompareStatus();
    }

    protected get hasResult(): boolean {
        return !!this.versionCompareResult;
    }

    protected get effectiveIndexStatus(): VersionCompareStatusResponse | null {
        return this.versionCompareStatus ?? this.versionCompareResult?.index_info ?? null;
    }

    protected get backendReturnCards(): Array<{ label: string; value: string | number }> {
        const result = this.versionCompareResult;
        if (!result) {
            return [];
        }

        const summary = result.summary ?? {};

        return [
            { label: 'Versão do produto', value: result.product_version || '-' },
            { label: 'Desatualizados', value: summary['desatualizados'] ?? result.desatualizados?.length ?? 0 },
            { label: 'OK', value: summary['ok'] ?? result.ok?.length ?? 0 },
            { label: 'Não encontrados', value: summary['nao_encontrado'] ?? result.nao_encontrado?.length ?? 0 },
            { label: 'Com UPC', value: summary['programas_com_upc'] ?? result.programas_com_upc?.length ?? 0 }
        ];
    }

    protected get summaryCards(): Array<{ label: string; value: string | number }> {
        const result = this.versionCompareResult;
        if (!result) {
            return [];
        }

        return [
            { label: 'Arquivo lido', value: this.uploadedFilename || '-' },
            { label: 'Última análise', value: this.analyzedAt ? this.analyzedAt : '-' },
            { label: 'Versão do produto', value: result.product_version || '-' },
            { label: 'Desatualizados', value: result.desatualizados?.length ?? 0 },
            { label: 'OK', value: result.ok?.length ?? 0 },
            { label: 'Com UPC', value: result.programas_com_upc?.length ?? 0 }
        ];
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

    protected onVersionCompareSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.versionCompareFile = input?.files?.item(0) ?? null;
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
        this.successMessage = '';

        this.api.compareVersions(this.versionCompareFile)
            .pipe(finalize(() => (this.versionCompareLoading = false)))
            .subscribe({
                next: (response) => {
                    this.versionCompareResult = response;
                    this.versionCompareStatus = response.index_info ?? this.versionCompareStatus;
                    this.uploadedFilename = this.versionCompareFile?.name ?? 'extrato';
                    this.analyzedAt = new Date().toISOString();
                    this.versionCompareSession.save(response, this.uploadedFilename);
                    this.successMessage = 'Extrato processado e exibido nesta tela dedicada.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao executar leitura do extrato de versão.';
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
                    this.successMessage = 'Índice interno atualizado com sucesso.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao recarregar índice de versões.';
                }
            });
    }

    protected clearVersionCompareSession(): void {
        this.versionCompareSession.clear();
        this.versionCompareFile = null;
        this.versionCompareResult = null;
        this.uploadedFilename = '';
        this.analyzedAt = '';
        this.errorMessage = '';
        this.successMessage = '';
    }

    private restoreSession(): void {
        const session = this.versionCompareSession.load();
        if (!session) {
            return;
        }

        this.versionCompareResult = session.result;
        this.uploadedFilename = session.filename;
        this.analyzedAt = session.analyzedAt;
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

    private mapVersionCompareRow(item: VersionCompareEntry): VersionCompareTableItem {
        return {
            programa: item.programa,
            versao_extrato: item.cliente || '-',
            versao_correta: item.deveria_estar || item.referencia_oficial || '-',
            fix_encontrada: item.fix_encontrada || '-',
            diferenca_builds: item.diferenca_builds ?? '-'
        };
    }
}
