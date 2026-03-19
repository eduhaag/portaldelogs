// ===============================
// Componente de Comparação de Versão
// Aqui é onde a mágica da comparação acontece!
// Este arquivo é responsável por ler o extrato do cliente, comparar com a base interna
// e mostrar tudo de forma visual, colorida e (esperamos) sem dor de cabeça.
// Comentários didáticos e bem humorados para quem for manter, aprender ou só curtir o código!
// ===============================
import { CommonModule } from '@angular/common';
// Importando o essencial do Angular para criar componentes, ciclo de vida e injeção de dependências
import { Component, OnInit, inject } from '@angular/core';
// PO UI: biblioteca de componentes visuais que deixa tudo bonito e funcional
import {
    PoButtonModule,
    PoLoadingModule,
    PoPageModule,
    PoTableColumn,
    PoTableModule,
    PoTabsModule,
    PoWidgetModule
} from '@po-ui/ng-components';
// finalize: operador RxJS para saber quando a requisição terminou (sucesso ou erro)
import { finalize } from 'rxjs';

// Tipos e serviços do backend e sessão
import {
    VersionCompareEntry,
    VersionCompareResponse,
    VersionCompareStatusResponse
} from '../../core/models/api.models';
import { BackendApiService } from '../../core/services/backend-api.service';
import { VersionCompareSessionService } from '../../core/services/version-compare-session.service';

// Interface para exibir cada linha da tabela principal de comparação
interface VersionCompareTableItem {
    programa: string; // Nome do programa analisado
    versao_extrato: string; // Versão encontrada no extrato do cliente
    versao_correta: string; // Versão correta segundo a base interna
    fix_encontrada: string; // Fix sugerida (se houver)
    diferenca_builds: string | number; // Diferença de builds (pode ser número ou texto)
}

// Interface para exibir programas com UPC (tratamento especial)
interface UpcTableItem {
    programa: string;
}

// Decorador Angular: define o componente, template, estilos e dependências
@Component({
    selector: 'app-version-compare-page',
    standalone: true,
    imports: [CommonModule, PoPageModule, PoWidgetModule, PoButtonModule, PoTableModule, PoTabsModule, PoLoadingModule],
    templateUrl: './version-compare.page.html',
    styleUrl: './version-compare.page.scss'
})
export class VersionComparePageComponent implements OnInit {
    // Serviços injetados: comunicação com backend e sessão local
    private readonly api = inject(BackendApiService);
    private readonly versionCompareSession = inject(VersionCompareSessionService);

    // Estado do componente: arquivos, resultados, status, mensagens e loading
    protected versionCompareFile: File | null = null; // Arquivo selecionado pelo usuário
    protected versionCompareResult: VersionCompareResponse | null = null; // Resultado da comparação
    protected versionCompareStatus: VersionCompareStatusResponse | null = null; // Status do índice interno
    protected versionCompareLoading = false; // Exibe loading na tela
    protected errorMessage = ''; // Mensagem de erro para feedback
    protected successMessage = ''; // Mensagem de sucesso para feedback
    protected analyzedAt = ''; // Data/hora da última análise
    protected uploadedFilename = ''; // Nome do arquivo analisado

    // Colunas da tabela principal de comparação
    protected readonly versionCompareColumns: PoTableColumn[] = [
        { property: 'programa', label: 'Programa' },
        { property: 'versao_extrato', label: 'Versão no extrato' },
        { property: 'versao_correta', label: 'Versão correta' },
        { property: 'fix_encontrada', label: 'Fix' },
        { property: 'diferenca_builds', label: 'Diferença', width: '120px' }
    ];

    // Colunas da tabela de programas com UPC
    protected readonly upcColumns: PoTableColumn[] = [
        { property: 'programa', label: 'Programa com UPC' }
    ];

    // Ao inicializar, restaura sessão anterior e carrega status do backend
    ngOnInit(): void {
        this.restoreSession();
        this.loadVersionCompareStatus();
    }

    // Indica se já existe resultado carregado para exibir na tela
    protected get hasResult(): boolean {
        return !!this.versionCompareResult;
    }

    // Retorna o status do índice interno (prioriza status carregado, senão pega do resultado)
    protected get effectiveIndexStatus(): VersionCompareStatusResponse | null {
        return this.versionCompareStatus ?? this.versionCompareResult?.index_info ?? null;
    }

    // Cartões-resumo para exibir no topo do dashboard (produto, desatualizados, OK, etc)
    protected get backendReturnCards(): Array<{ label: string; value: string | number }> {
        const result = this.versionCompareResult;
        if (!result) {
            return [];
        }

        // Pega resumo do backend, se não existir usa contagem dos arrays
        const summary = result.summary ?? {};

        return [
            { label: 'Versão do produto', value: result.product_version || '-' },
            { label: 'Desatualizados', value: summary['desatualizados'] ?? result.desatualizados?.length ?? 0 },
            { label: 'OK', value: summary['ok'] ?? result.ok?.length ?? 0 },
            { label: 'Não encontrados', value: summary['nao_encontrado'] ?? result.nao_encontrado?.length ?? 0 },
            { label: 'Com UPC', value: summary['programas_com_upc'] ?? result.programas_com_upc?.length ?? 0 }
        ];
    }

    // Cartões-resumo para exibir informações do arquivo analisado
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

    // Linhas da aba "Desatualizados" (programas que precisam de atualização)
    protected get versionCompareRows(): VersionCompareTableItem[] {
        return (this.versionCompareResult?.desatualizados ?? []).map((item) => this.mapVersionCompareRow(item));
    }

    // Linhas da aba "OK" (programas alinhados com a referência)
    protected get versionCompareOkRows(): VersionCompareTableItem[] {
        return (this.versionCompareResult?.ok ?? []).map((item) => this.mapVersionCompareRow(item));
    }

    // Linhas da aba "Não encontrado" (programas que não existem na base interna)
    protected get versionCompareNotFoundRows(): VersionCompareTableItem[] {
        return (this.versionCompareResult?.nao_encontrado ?? []).map((item) => this.mapVersionCompareRow(item));
    }

    // Linhas da aba "UPC" (programas com tratamento especial UPC)
    protected get versionCompareUpcRows(): UpcTableItem[] {
        return (this.versionCompareResult?.programas_com_upc ?? []).map((programa) => ({ programa }));
    }

    // Rótulo da aba "Desatualizados" com contagem dinâmica
    protected get outdatedTabLabel(): string {
        return `Desatualizados (${this.versionCompareRows.length})`;
    }

    // Rótulo da aba "OK" com contagem dinâmica
    protected get okTabLabel(): string {
        return `OK (${this.versionCompareOkRows.length})`;
    }

    // Rótulo da aba "Não encontrado" com contagem dinâmica
    protected get notFoundTabLabel(): string {
        return `Não encontrado (${this.versionCompareNotFoundRows.length})`;
    }

    // Rótulo da aba "UPC" com contagem dinâmica
    protected get upcTabLabel(): string {
        return `UPC (${this.versionCompareUpcRows.length})`;
    }

    // Quando o usuário seleciona um arquivo, salva referência e limpa mensagens
    protected onVersionCompareSelected(event: Event): void {
        const input = event.target as HTMLInputElement | null;
        this.versionCompareFile = input?.files?.item(0) ?? null;
        this.errorMessage = '';
        this.successMessage = '';
    }

    // Executa a comparação de versões chamando o backend
    // Exibe loading, trata sucesso e erro, salva sessão e feedback
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
                // O backend retorna o resultado da comparação
                next: (response: VersionCompareResponse) => {
                    this.versionCompareResult = response;
                    this.versionCompareStatus = response.index_info ?? this.versionCompareStatus;
                    this.uploadedFilename = this.versionCompareFile?.name ?? 'extrato';
                    this.analyzedAt = new Date().toISOString();
                    this.versionCompareSession.save(response, this.uploadedFilename);
                    this.successMessage = 'Extrato processado e exibido nesta tela dedicada.';
                },
                // Se der ruim, mostra mensagem de erro amigável
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao executar leitura do extrato de versão.';
                }
            });
    }

    // Recarrega o índice interno de versões do backend (útil após atualização de base)
    protected reloadVersionIndex(): void {
        this.versionCompareLoading = true;
        this.errorMessage = '';

        this.api.reloadVersionCompare()
            .pipe(finalize(() => (this.versionCompareLoading = false)))
            .subscribe({
                next: (response: VersionCompareStatusResponse) => {
                    this.versionCompareStatus = response;
                    this.successMessage = 'Índice interno atualizado com sucesso.';
                },
                error: (error: { error?: { detail?: string } }) => {
                    this.errorMessage = error.error?.detail ?? 'Falha ao recarregar índice de versões.';
                }
            });
    }

    // Limpa toda a sessão de comparação (útil para recomeçar do zero)
    protected clearVersionCompareSession(): void {
        this.versionCompareSession.clear();
        this.versionCompareFile = null;
        this.versionCompareResult = null;
        this.uploadedFilename = '';
        this.analyzedAt = '';
        this.errorMessage = '';
        this.successMessage = '';
    }

    // Restaura sessão salva no navegador (para não perder o trabalho ao recarregar a página)
    private restoreSession(): void {
        const session = this.versionCompareSession.load();
        if (!session) {
            return;
        }

        this.versionCompareResult = session.result;
        this.uploadedFilename = session.filename;
        this.analyzedAt = session.analyzedAt;
    }

    // Carrega status do backend sobre o índice de versões (útil para saber se está atualizado)
    private loadVersionCompareStatus(): void {
        this.api.getVersionCompareStatus().subscribe({
            next: (response: VersionCompareStatusResponse) => {
                this.versionCompareStatus = response;
            },
            error: () => {
                this.versionCompareStatus = null;
            }
        });
    }

    // Mapeia o retorno do backend para o formato da tabela (garante que não quebra se faltar campo)
    private mapVersionCompareRow(item: VersionCompareEntry): VersionCompareTableItem {
        return {
            programa: item.programa,
            versao_extrato: item.cliente || '-',
            versao_correta: item.deveria_estar || item.referencia_oficial || '-',
            fix_encontrada: item.fix_encontrada || '-',
            diferenca_builds: item.diferenca_builds ?? '-'
        };
    }
    // Fim do componente! Se chegou até aqui, parabéns: você já entende mais de comparação de versões do que 99% dos usuários!
}
