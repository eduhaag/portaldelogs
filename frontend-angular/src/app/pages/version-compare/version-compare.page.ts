// ===============================
// Componente de Comparação de Versões
// Permite comparar extratos de versões de sistemas para identificar diferenças.
// Demonstra uso de tabelas, tabs e integração com PO UI.
// Comentários didáticos para facilitar o entendimento!
// ===============================
import { CommonModule, DOCUMENT } from '@angular/common';
import { Component, HostListener, OnInit, inject } from '@angular/core';
import {
    PoButtonModule,
    PoLoadingModule,
    PoPageModule,
    PoTableColumn,
    PoTableModule,
    PoTabsModule,
    PoTagModule,
    PoTagType,
    PoWidgetModule,
    PoDividerModule
} from '@po-ui/ng-components';
import { finalize } from 'rxjs';

import {
    VersionCompareEntry,
    VersionCompareResponse,
    VersionCompareStatusResponse
} from '../../core/models/api.models';
import { BackendApiService } from '../../core/services/backend-api.service';
import { VersionCompareSessionService } from '../../core/services/version-compare-session.service';

interface TableRow {
    [key: string]: string | number;
}

type DetailSectionKey =
    | 'product'
    | 'programasExtrato'
    | 'comparados'
    | 'desatualizados'
    | 'ok'
    | 'adiantado'
    | 'upc'
    | 'dpc'
    | 'especificos'
    | 'funcoes';

interface SummaryCard {
    label: string;
    value: string | number;
    section: DetailSectionKey;
}

interface DetailSection {
    key: DetailSectionKey;
    domId: string;
    label: string;
    description: string;
    columns?: PoTableColumn[];
    rows?: TableRow[];
    emptyMessage?: string;
    kind: 'info' | 'table';
}

@Component({
    selector: 'app-version-compare-page',
    standalone: true,
    imports: [
        CommonModule, PoPageModule, PoWidgetModule, PoButtonModule,
        PoTableModule, PoTabsModule, PoLoadingModule, PoTagModule,
        PoDividerModule
    ],
    templateUrl: './version-compare.page.html',
    styleUrl: './version-compare.page.scss'
})
export class VersionComparePageComponent implements OnInit {
    // Serviço de API para comunicação com o backend
    private readonly api = inject(BackendApiService);
    // Serviço de sessão para armazenar dados temporários da comparação
    private readonly session = inject(VersionCompareSessionService);
    // Referência ao objeto document para manipulação do DOM
    private readonly document = inject(DOCUMENT);

    // Quantidade de linhas exibidas no preview e nos detalhes
    private readonly previewRowCount = 8;
    private readonly detailBatchSize = 10;
    // Identificadores de seções de detalhes para navegação
    private readonly detailSectionIds: Record<DetailSectionKey, string> = {
        product: 'version-compare-product-details',
        programasExtrato: 'version-compare-programas-extrato',
        comparados: 'version-compare-programas-comparados',
        desatualizados: 'version-compare-desatualizados',
        ok: 'version-compare-ok',
        adiantado: 'version-compare-adiantado',
        upc: 'version-compare-upc',
        dpc: 'version-compare-dpc',
        especificos: 'version-compare-especificos',
        funcoes: 'version-compare-funcoes'
    };

    protected readonly TAG_DANGER = PoTagType.Danger;
    protected readonly TAG_WARNING = PoTagType.Warning;
    protected readonly TAG_SUCCESS = PoTagType.Success;
    protected readonly TAG_INFO = PoTagType.Info;

    protected file: File | null = null;
    protected result: VersionCompareResponse | null = null;
    protected status: VersionCompareStatusResponse | null = null;
    protected loading = false;
    protected errorMessage = '';
    protected successMessage = '';
    protected analyzedAt = '';
    protected uploadedFilename = '';
    protected activeDetailSection: DetailSectionKey = 'product';
    protected detailVisibleCounts = this.createDetailVisibleCounts();
    protected loadingMessage = 'Processando extrato do cliente...';
    protected compactViewport = this.isCompactViewport();

    // --- Columns ---
    private readonly desktopCompColumns: PoTableColumn[] = [
        {
            property: 'programa',
            label: 'Programa',
            type: 'link',
            action: (value: string, row: TableRow) => this.openProgramDetails(String(row['programa'] ?? value ?? ''))
        },
        { property: 'cliente', label: 'Versao cliente' },
        { property: 'oficial', label: 'Versao oficial' },
        { property: 'diferenca', label: 'Diferenca', width: '120px' }
    ];

    private readonly compactCompColumns: PoTableColumn[] = [
        {
            property: 'programa',
            label: 'Programa',
            type: 'link',
            action: (value: string, row: TableRow) => this.openProgramDetails(String(row['programa'] ?? value ?? ''))
        },
        { property: 'cliente', label: 'Cliente' },
        { property: 'oficial', label: 'Oficial' }
    ];

    private readonly desktopOkColumns: PoTableColumn[] = [
        {
            property: 'programa',
            label: 'Programa',
            type: 'link',
            action: (value: string, row: TableRow) => this.openProgramDetails(String(row['programa'] ?? value ?? ''))
        },
        { property: 'cliente', label: 'Versao cliente' },
        { property: 'oficial', label: 'Versao oficial' }
    ];

    private readonly compactOkColumns: PoTableColumn[] = [
        {
            property: 'programa',
            label: 'Programa',
            type: 'link',
            action: (value: string, row: TableRow) => this.openProgramDetails(String(row['programa'] ?? value ?? ''))
        },
        { property: 'oficial', label: 'Oficial' }
    ];

    private readonly desktopUpcColumns: PoTableColumn[] = [
        {
            property: 'programa',
            label: 'Programa',
            type: 'link',
            action: (value: string, row: TableRow) => this.openProgramDetails(String(row['programa'] ?? value ?? ''))
        },
        { property: 'caminho', label: 'Caminho' }
    ];

    private readonly compactUpcColumns: PoTableColumn[] = [
        {
            property: 'programa',
            label: 'Programa',
            type: 'link',
            action: (value: string, row: TableRow) => this.openProgramDetails(String(row['programa'] ?? value ?? ''))
        },
        { property: 'caminho', label: 'Caminho' }
    ];

    private readonly desktopFuncColumns: PoTableColumn[] = [
        { property: 'funcao', label: 'Funcao' },
        { property: 'ativa_status', label: 'Ativa', width: '110px' },
        { property: 'valor', label: 'Valor bruto', width: '130px' },
        { property: 'origem', label: 'Origem', width: '150px' },
        { property: 'programa', label: 'Programa' }
    ];

    private readonly compactFuncColumns: PoTableColumn[] = [
        { property: 'funcao', label: 'Funcao' },
        { property: 'ativa_status', label: 'Ativa', width: '90px' },
        { property: 'valor', label: 'Valor' }
    ];

    private readonly desktopDetalheColumns: PoTableColumn[] = [
        { property: 'programa', label: 'Programa' },
        { property: 'programa_original', label: 'Programa original' },
        { property: 'versao', label: 'Versao' },
        { property: 'programa_pai', label: 'Programa Pai' },
        { property: 'caminho', label: 'Caminho' },
        { property: 'data', label: 'Data' },
        { property: 'hora', label: 'Hora' }
    ];

    private readonly compactDetalheColumns: PoTableColumn[] = [
        { property: 'programa', label: 'Programa' },
        { property: 'versao', label: 'Versao' },
        { property: 'caminho', label: 'Caminho' }
    ];

    private readonly desktopComparedColumns: PoTableColumn[] = [
        {
            property: 'programa',
            label: 'Programa',
            type: 'link',
            action: (value: string, row: TableRow) => this.openProgramDetails(String(row['programa'] ?? value ?? ''))
        },
        { property: 'status', label: 'Status', width: '170px' },
        { property: 'cliente', label: 'Versao cliente' },
        { property: 'oficial', label: 'Versao oficial' },
        { property: 'fix_encontrada', label: 'Fix encontrada' },
        { property: 'diferenca', label: 'Diferenca', width: '120px' },
        { property: 'caminho_encontrado', label: 'Caminho oficial' }
    ];

    private readonly compactComparedColumns: PoTableColumn[] = [
        {
            property: 'programa',
            label: 'Programa',
            type: 'link',
            action: (value: string, row: TableRow) => this.openProgramDetails(String(row['programa'] ?? value ?? ''))
        },
        { property: 'status', label: 'Status', width: '120px' },
        { property: 'oficial', label: 'Oficial' },
        { property: 'diferenca', label: 'Dif.' }
    ];

    ngOnInit(): void {
        this.loading = false;
        this.restoreSession();
        this.loadStatus();
    }

    @HostListener('window:resize')
    protected onWindowResize(): void {
        this.compactViewport = this.isCompactViewport();
    }

    // --- Computed ---
    protected get hasResult(): boolean {
        return !!this.result;
    }

    protected get summaryCards(): SummaryCard[] {
        const r = this.result;
        if (!r) return [];
        const s = r.summary ?? {};
        return [
            {
                label: 'Versao do produto',
                value: this.productVersionDisplay,
                section: 'product'
            },
            {
                label: 'Programas no extrato',
                value: s['total_programas_cliente'] ?? 0,
                section: 'programasExtrato'
            },
            {
                label: 'Programas comparados',
                value: this.comparedProgramsCount,
                section: 'comparados'
            },
            {
                label: 'Desatualizados',
                value: s['desatualizados'] ?? 0,
                section: 'desatualizados'
            },
            {
                label: 'OK',
                value: s['ok'] ?? 0,
                section: 'ok'
            },
            {
                label: 'Adiantado/Custom.',
                value: s['adiantado_customizado'] ?? 0,
                section: 'adiantado'
            },
            {
                label: 'UPC',
                value: s['com_upc'] ?? 0,
                section: 'upc'
            },
            {
                label: 'DPC',
                value: s['com_dpc'] ?? 0,
                section: 'dpc'
            },
            {
                label: 'Especificos',
                value: s['especificos'] ?? 0,
                section: 'especificos'
            },
            {
                label: 'Funcoes',
                value: s['funcoes_ativas'] ?? 0,
                section: 'funcoes'
            }
        ];
    }

    protected get compColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactCompColumns : this.desktopCompColumns;
    }

    protected get okColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactOkColumns : this.desktopOkColumns;
    }

    protected get upcColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactUpcColumns : this.desktopUpcColumns;
    }

    protected get funcColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactFuncColumns : this.desktopFuncColumns;
    }

    protected get detalheColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactDetalheColumns : this.desktopDetalheColumns;
    }

    protected get comparedColumns(): PoTableColumn[] {
        return this.compactViewport ? this.compactComparedColumns : this.desktopComparedColumns;
    }

    protected get desatualizadosRows(): TableRow[] {
        return (this.result?.desatualizados ?? []).map(i => ({
            programa: i.programa,
            cliente: i.cliente,
            oficial: i.deveria_estar || '-',
            diferenca: i.diferenca_builds ?? '-'
        }));
    }

    protected get okRows(): TableRow[] {
        return (this.result?.ok ?? []).map(i => ({
            programa: i.programa,
            cliente: i.cliente,
            oficial: i.referencia_oficial || '-'
        }));
    }

    protected get adiantadoRows(): TableRow[] {
        return (this.result?.adiantado_customizado ?? []).map(i => ({
            programa: i.programa,
            cliente: i.cliente,
            oficial: i.referencia_oficial || '-',
            diferenca: i.diferenca_builds ?? '-'
        }));
    }

    protected get comparedProgramsCount(): number {
        return this.desatualizadosRows.length + this.okRows.length + this.adiantadoRows.length;
    }

    protected get productVersionDisplay(): string {
        if (!this.result) {
            return '-';
        }

        return this.result.header?.versao_produto_completa
            || this.result.header?.versao_produto
            || this.result.product_version
            || (this.result.product_version_missing ? 'Nao informada no extrato' : '-');
    }

    protected get productVersionWarning(): string {
        return this.result?.product_version_warning || '';
    }

    protected get genericIndexWarning(): string {
        const indexWarning = this.result?.index_warning || '';
        if (!indexWarning || indexWarning === this.productVersionWarning) {
            return '';
        }

        return indexWarning;
    }

    protected get comparedRows(): TableRow[] {
        return [
            ...(this.result?.desatualizados ?? []).map((item) => this.mapComparedRow(item, 'Desatualizado')),
            ...(this.result?.ok ?? []).map((item) => this.mapComparedRow(item, 'OK')),
            ...(this.result?.adiantado_customizado ?? []).map((item) => this.mapComparedRow(item, 'Adiantado/Custom.'))
        ];
    }

    protected get upcRows(): TableRow[] {
        return (this.result?.programas_com_upc ?? []).map(i => ({
            programa: i.programa,
            caminho: i.caminho
        }));
    }

    protected get dpcRows(): TableRow[] {
        return (this.result?.programas_com_dpc ?? []).map(i => ({
            programa: i.programa,
            caminho: i.caminho
        }));
    }

    protected get especificosRows(): TableRow[] {
        return (this.result?.especificos ?? []).map(i => ({
            programa: i.programa,
            caminho: i.caminho
        }));
    }

    protected get funcaoRows(): TableRow[] {
        return (this.result?.funcoes_ativas ?? []).map(i => ({
            funcao: i.funcao,
            valor: i.valor,
            ativa_status: this.mapAtivaStatus(i.ativa, i.valor),
            origem: i.origem || '-',
            programa: i.programa || '-'
        }));
    }

    protected get detalheRows(): TableRow[] {
        return (this.result?.programas_detalhe ?? []).map(i => ({
            programa: i.programa,
            programa_original: i.programa_original || '-',
            versao: i.versao,
            programa_pai: i.programa_pai || '-',
            caminho: i.caminho || '-',
            data: i.data || '-',
            hora: i.hora || '-'
        }));
    }

    protected tabLabel(base: string, count: number): string {
        return `${base} (${count})`;
    }

    protected get previewDesatualizadosRows(): TableRow[] {
        return this.desatualizadosRows.slice(0, this.previewRowCount);
    }

    protected get previewOkRows(): TableRow[] {
        return this.okRows.slice(0, this.previewRowCount);
    }

    protected get previewAdiantadoRows(): TableRow[] {
        return this.adiantadoRows.slice(0, this.previewRowCount);
    }

    protected get detailSections(): DetailSection[] {
        return [
            {
                key: 'product',
                domId: this.detailSectionIds.product,
                label: 'Versao do produto',
                description: 'Dados de identificacao do extrato e da analise executada.',
                kind: 'info'
            },
            {
                key: 'programasExtrato',
                domId: this.detailSectionIds.programasExtrato,
                label: 'Programas no extrato',
                description: 'Lista completa dos programas extraidos do arquivo do cliente.',
                kind: 'table',
                columns: this.detalheColumns,
                rows: this.detalheRows,
                emptyMessage: 'Nenhum programa extraido.'
            },
            {
                key: 'comparados',
                domId: this.detailSectionIds.comparados,
                label: 'Programas comparados',
                description: 'Consolidado com todos os programas comparados e o status final da comparacao.',
                kind: 'table',
                columns: this.comparedColumns,
                rows: this.comparedRows,
                emptyMessage: this.result?.product_version_missing
                    ? 'A comparacao de versoes nao foi executada porque o extrato nao informa a versao do cliente.'
                    : 'Nenhum programa comparado para exibir.'
            },
            {
                key: 'desatualizados',
                domId: this.detailSectionIds.desatualizados,
                label: 'Desatualizados',
                description: 'Programas do cliente que estao atras da versao oficial encontrada.',
                kind: 'table',
                columns: this.comparedColumns,
                rows: (this.result?.desatualizados ?? []).map((item) => this.mapComparedRow(item, 'Desatualizado')),
                emptyMessage: this.result?.product_version_missing
                    ? 'Sem comparacao de versao: o extrato nao informa a versao do cliente.'
                    : 'Nenhum programa desatualizado encontrado.'
            },
            {
                key: 'ok',
                domId: this.detailSectionIds.ok,
                label: 'OK',
                description: 'Programas que ja estao alinhados com a referencia oficial.',
                kind: 'table',
                columns: this.comparedColumns,
                rows: (this.result?.ok ?? []).map((item) => this.mapComparedRow(item, 'OK')),
                emptyMessage: this.result?.product_version_missing
                    ? 'Sem comparacao de versao: o extrato nao informa a versao do cliente.'
                    : 'Nenhum programa com versao OK para exibir.'
            },
            {
                key: 'adiantado',
                domId: this.detailSectionIds.adiantado,
                label: 'Adiantado/Custom.',
                description: 'Programas acima da referencia oficial ou com indicio de customizacao.',
                kind: 'table',
                columns: this.comparedColumns,
                rows: (this.result?.adiantado_customizado ?? []).map((item) => this.mapComparedRow(item, 'Adiantado/Custom.')),
                emptyMessage: this.result?.product_version_missing
                    ? 'Sem comparacao de versao: o extrato nao informa a versao do cliente.'
                    : 'Nenhum programa adiantado ou customizado.'
            },
            {
                key: 'upc',
                domId: this.detailSectionIds.upc,
                label: 'UPC',
                description: 'Programas com artefatos de UPC detectados no extrato.',
                kind: 'table',
                columns: this.upcColumns,
                rows: this.upcRows,
                emptyMessage: 'Nenhum programa com UPC identificado.'
            },
            {
                key: 'dpc',
                domId: this.detailSectionIds.dpc,
                label: 'DPC',
                description: 'Programas com DPC ou artefatos equivalentes detectados.',
                kind: 'table',
                columns: this.upcColumns,
                rows: this.dpcRows,
                emptyMessage: 'Nenhum programa com DPC identificado.'
            },
            {
                key: 'especificos',
                domId: this.detailSectionIds.especificos,
                label: 'Especificos',
                description: 'Itens classificados como especificos pelo processamento do backend.',
                kind: 'table',
                columns: this.upcColumns,
                rows: this.especificosRows,
                emptyMessage: 'Nenhum especifico identificado.'
            },
            {
                key: 'funcoes',
                domId: this.detailSectionIds.funcoes,
                label: 'Funcoes identificadas',
                description: 'Funcoes e parametrizacoes encontradas no extrato, com indicacao se estao ativas ou nao.',
                kind: 'table',
                columns: this.funcColumns,
                rows: this.funcaoRows,
                emptyMessage: 'Nenhuma funcao identificada.'
            }
        ];
    }

    // --- Actions ---
    protected onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.file = input?.files?.item(0) ?? null;
        this.errorMessage = '';
        this.successMessage = '';
    }

    protected runCompare(): void {
        if (!this.file) {
            this.errorMessage = 'Selecione o extrato do cliente.';
            return;
        }

        this.loading = true;
        this.loadingMessage = 'Processando extrato do cliente...';
        this.errorMessage = '';
        this.successMessage = '';

        this.api.compareVersions(this.file)
            .pipe(finalize(() => (this.loading = false)))
            .subscribe({
                next: (response) => {
                    this.loading = false;
                    this.result = response;
                    this.status = response.index_info ?? this.status;
                    this.uploadedFilename = this.file?.name ?? 'extrato';
                    this.analyzedAt = new Date().toLocaleString('pt-BR');
                    this.resetDetailPagination();
                    this.session.save(response, this.uploadedFilename);
                    this.successMessage = response.product_version_missing
                        ? 'Extrato processado com sucesso. A versao do cliente nao foi informada no cabecalho; os demais dados foram carregados.'
                        : 'Extrato processado com sucesso.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.loading = false;
                    this.errorMessage = error.error?.detail ?? 'Falha ao processar o extrato.';
                }
            });
    }

    protected reloadIndex(): void {
        this.loading = true;
        this.loadingMessage = 'Atualizando o indice de versoes...';
        this.errorMessage = '';

        this.api.reloadVersionCompare()
            .pipe(finalize(() => (this.loading = false)))
            .subscribe({
                next: (response) => {
                    this.loading = false;
                    this.status = response;
                    this.successMessage = 'Indice recarregado.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.loading = false;
                    this.errorMessage = error.error?.detail ?? 'Falha ao recarregar indice.';
                }
            });
    }

    protected clearSession(): void {
        this.session.clear();
        this.file = null;
        this.result = null;
        this.uploadedFilename = '';
        this.analyzedAt = '';
        this.errorMessage = '';
        this.successMessage = '';
        this.resetDetailPagination();
    }

    protected onSummaryCardClick(section: DetailSectionKey): void {
        this.scrollToSection(section);
    }

    protected getVisibleRows(section: DetailSectionKey, rows: TableRow[] = []): TableRow[] {
        if (section === 'product') {
            return rows;
        }

        return rows.slice(0, this.detailVisibleCounts[section]);
    }

    protected hasMoreRows(section: DetailSectionKey, rows: TableRow[] = []): boolean {
        return rows.length > this.detailVisibleCounts[section];
    }

    protected canCollapseRows(section: DetailSectionKey, rows: TableRow[] = []): boolean {
        return rows.length > this.detailBatchSize && this.detailVisibleCounts[section] > this.detailBatchSize;
    }

    protected loadMoreRows(section: DetailSectionKey, rows: TableRow[] = []): void {
        this.detailVisibleCounts[section] = Math.min(rows.length, this.detailVisibleCounts[section] + this.detailBatchSize);
    }

    protected resetVisibleRows(section: DetailSectionKey): void {
        this.detailVisibleCounts[section] = this.detailBatchSize;
    }

    protected visibleRowsLabel(section: DetailSectionKey, rows: TableRow[] = []): string {
        if (!rows.length) {
            return 'Nenhum registro encontrado.';
        }

        const visible = Math.min(rows.length, this.detailVisibleCounts[section]);
        return `Mostrando ${visible} de ${rows.length} registros.`;
    }

    protected openProgramDetails(programa: string): void {
        if (!programa) {
            return;
        }

        this.scrollToSection('programasExtrato');
    }

    private restoreSession(): void {
        const saved = this.session.load();
        this.loading = false;
        if (!saved) return;
        this.result = saved.result;
        this.uploadedFilename = saved.filename;
        this.analyzedAt = saved.analyzedAt;
    }

    private loadStatus(): void {
        this.api.getVersionCompareStatus().subscribe({
            next: (response) => { this.status = response; },
            error: () => { this.status = null; }
        });
    }

    private mapComparedRow(item: VersionCompareEntry, status: string): TableRow {
        return {
            programa: item.programa,
            status,
            cliente: item.cliente,
            oficial: item.deveria_estar || item.referencia_oficial || item.versao_encontrada || '-',
            fix_encontrada: item.fix_encontrada || '-',
            diferenca: item.diferenca_builds ?? '-',
            caminho_encontrado: item.caminho_encontrado || '-'
        };
    }

    private mapAtivaStatus(ativa?: boolean, valor?: string): string {
        if (typeof ativa === 'boolean') {
            return ativa ? 'Sim' : 'Nao';
        }

        const normalizedValue = String(valor ?? '').trim().toLowerCase();
        if (['sim', 'yes', 'true', '1', 'ativo', 'on'].includes(normalizedValue)) {
            return 'Sim';
        }
        if (['nao', 'não', 'no', 'false', '0', 'inativo', 'off'].includes(normalizedValue)) {
            return 'Nao';
        }

        return '-';
    }

    private scrollToSection(section: DetailSectionKey): void {
        this.activeDetailSection = section;

        const sectionId = this.detailSectionIds[section];
        setTimeout(() => {
            this.document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 0);
    }

    private createDetailVisibleCounts(): Record<DetailSectionKey, number> {
        return {
            product: 1,
            programasExtrato: this.detailBatchSize,
            comparados: this.detailBatchSize,
            desatualizados: this.detailBatchSize,
            ok: this.detailBatchSize,
            adiantado: this.detailBatchSize,
            upc: this.detailBatchSize,
            dpc: this.detailBatchSize,
            especificos: this.detailBatchSize,
            funcoes: this.detailBatchSize
        };
    }

    private resetDetailPagination(): void {
        this.detailVisibleCounts = this.createDetailVisibleCounts();
        this.activeDetailSection = 'product';
    }

    private isCompactViewport(): boolean {
        return typeof window !== 'undefined' && window.innerWidth <= 960;
    }
}
