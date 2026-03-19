// ===============================
// Componente de Controle de Issues
// Permite gerenciar, editar e filtrar issues relacionadas a tickets e clientes.
// Demonstra uso de tabelas, modais e integração com PO UI.
// Comentários didáticos para facilitar o entendimento!
// ===============================
import { Component, ElementRef, inject, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
    PoPageModule, PoFieldModule, PoButtonModule,
    PoLoadingModule, PoNotificationService,
    PoWidgetModule, PoTableModule,
    PoTableColumn, PoModalModule, PoModalComponent,
    PoModalAction
} from '@po-ui/ng-components';
import { BackendApiService } from '../../core/services/backend-api.service';
import { IssueItem, IssueCreatePayload } from '../../core/models/api.models';

@Component({
    selector: 'app-issue-control',
    standalone: true,
    imports: [
        CommonModule, FormsModule,
        PoPageModule, PoFieldModule, PoButtonModule,
        PoLoadingModule, PoWidgetModule, PoTableModule, PoModalModule
    ],
    templateUrl: './issue-control.page.html',
    styleUrl: './issue-control.page.scss'
})
export class IssueControlPageComponent implements OnInit {
    // Serviço de API para comunicação com o backend
    private readonly api = inject(BackendApiService);
    // Serviço de notificação para exibir mensagens ao usuário
    private readonly notification = inject(PoNotificationService);

    @ViewChild('editModal') editModal!: PoModalComponent;
    @ViewChild('newModal') newModal!: PoModalComponent;
    @ViewChild('csvInput') csvInput?: ElementRef<HTMLInputElement>;

    // Lista de issues carregadas do backend
    issues: IssueItem[] = [];
    // Lista filtrada de issues para exibição
    filteredIssues: IssueItem[] = [];
    isLoading = false;
    filterText = '';
    filterStatus = '';

    // Objetos para edição e criação de issues
    editingIssue: Partial<IssueItem> = {};
    newIssue: IssueCreatePayload = {
        ticket: '', issue: '', cliente: '', rotina: '',
        situacao: '', status: 'Aberto', liberado_versoes: ''
    };

    // Definição das colunas da tabela de issues
    readonly columns: PoTableColumn[] = [
        { property: 'data_criacao', label: 'Data', width: '120px' },
        { property: 'ticket', label: 'Ticket', width: '150px' },
        { property: 'issue', label: 'Issue', width: '140px' },
        { property: 'cliente', label: 'Cliente', width: '200px' },
        { property: 'rotina', label: 'Rotina', width: '190px' },
        { property: 'situacao', label: 'Situacao', width: '360px' },
        {
            property: 'status', label: 'Status', width: '140px',
            type: 'label', labels: [
                { value: 'Aberto', color: 'color-08', label: 'Aberto' },
                { value: 'Em Andamento', color: 'color-01', label: 'Em Andamento' },
                { value: 'Resolvido', color: 'color-11', label: 'Resolvido' },
                { value: 'Fechado', color: 'color-07', label: 'Fechado' },
                { value: 'Pendente', color: 'color-12', label: 'Pendente' },
            ]
        },
        { property: 'liberado_versoes', label: 'Versoes', width: '190px' },
    ];

    // Ações disponíveis na tabela de issues
    readonly tableActions = [
        { action: (row: IssueItem) => this.openEditModal(row), icon: 'po-icon-edit', label: 'Editar' },
        { action: (row: IssueItem) => this.deleteIssue(row), icon: 'po-icon-delete', label: 'Excluir' },
    ];

    // Opções de status para seleção e filtro
    readonly statusOptions = [
        { label: 'Aberto', value: 'Aberto' },
        { label: 'Em Andamento', value: 'Em Andamento' },
        { label: 'Resolvido', value: 'Resolvido' },
        { label: 'Fechado', value: 'Fechado' },
        { label: 'Pendente', value: 'Pendente' },
    ];

    readonly statusFilterOptions = [
        { label: 'Todos', value: '' },
        ...this.statusOptions,
    ];

    readonly editConfirm: PoModalAction = {
        label: 'Salvar', action: () => this.saveEdit()
    };
    readonly editCancel: PoModalAction = {
        label: 'Cancelar', action: () => this.editModal.close()
    };
    readonly newConfirm: PoModalAction = {
        label: 'Criar', action: () => this.createIssue()
    };
    readonly newCancel: PoModalAction = {
        label: 'Cancelar', action: () => this.newModal.close()
    };

    ngOnInit(): void {
        this.loadIssues();
    }

    loadIssues(): void {
        this.isLoading = true;
        this.api.getIssues().subscribe({
            next: (data) => {
                this.isLoading = false;
                this.issues = data;
                this.applyFilter();
            },
            error: (err) => {
                this.isLoading = false;
                this.notification.error('Falha ao carregar issues: ' + (err.error?.detail || err.message));
            }
        });
    }

    applyFilter(): void {
        let result = [...this.issues];
        if (this.filterStatus) {
            result = result.filter(i => i.status === this.filterStatus);
        }
        if (this.filterText.trim()) {
            const term = this.filterText.toLowerCase();
            result = result.filter(i =>
                i.ticket?.toLowerCase().includes(term) ||
                i.issue?.toLowerCase().includes(term) ||
                i.cliente?.toLowerCase().includes(term) ||
                i.rotina?.toLowerCase().includes(term) ||
                i.situacao?.toLowerCase().includes(term)
            );
        }
        this.filteredIssues = result;
    }

    openNewIssueModal(): void {
        this.newIssue = {
            ticket: '', issue: '', cliente: '', rotina: '',
            situacao: '', status: 'Aberto', liberado_versoes: ''
        };
        this.newModal.open();
    }

    createIssue(): void {
        if (!this.newIssue.ticket || !this.newIssue.issue) {
            this.notification.warning('Ticket e Issue sao obrigatorios.');
            return;
        }
        this.api.createIssue(this.newIssue).subscribe({
            next: () => {
                this.notification.success('Issue criada com sucesso.');
                this.newModal.close();
                this.loadIssues();
            },
            error: (err) => {
                this.notification.error('Falha ao criar issue: ' + (err.error?.detail || err.message));
            }
        });
    }

    openEditModal(issue: IssueItem): void {
        this.editingIssue = { ...issue };
        this.editModal.open();
    }

    saveEdit(): void {
        if (!this.editingIssue.id) return;
        const { id, data_criacao, ...updateData } = this.editingIssue;
        this.api.updateIssue(id!, updateData).subscribe({
            next: () => {
                this.notification.success('Issue atualizada com sucesso.');
                this.editModal.close();
                this.loadIssues();
            },
            error: (err) => {
                this.notification.error('Falha ao atualizar: ' + (err.error?.detail || err.message));
            }
        });
    }

    deleteIssue(issue: IssueItem): void {
        if (!confirm(`Deseja realmente excluir a issue ${issue.ticket}?`)) return;
        this.api.deleteIssue(issue.id).subscribe({
            next: () => {
                this.notification.success('Issue removida com sucesso.');
                this.loadIssues();
            },
            error: (err) => {
                this.notification.error('Falha ao excluir: ' + (err.error?.detail || err.message));
            }
        });
    }

    triggerCsvImport(): void {
        this.csvInput?.nativeElement.click();
    }

    onCsvSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (!input.files?.length) return;
        const file = input.files[0];
        this.isLoading = true;
        this.api.importCsv(file).subscribe({
            next: (res) => {
                this.isLoading = false;
                this.notification.success(`${res.imported_count} issue(s) importada(s) com sucesso.`);
                if (res.errors?.length) {
                    this.notification.warning(`${res.total_errors} aviso(s) durante importacao.`);
                }
                this.loadIssues();
            },
            error: (err) => {
                this.isLoading = false;
                this.notification.error('Falha na importacao: ' + (err.error?.detail || err.message));
            }
        });
    }

    exportCsv(): void {
        this.api.exportCsv().subscribe({
            next: (response) => {
                const blob = response.body;
                if (blob) {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'issues.csv';
                    a.click();
                    window.URL.revokeObjectURL(url);
                    this.notification.success('CSV exportado com sucesso.');
                }
            },
            error: (err) => {
                this.notification.error('Falha ao exportar: ' + (err.error?.detail || err.message));
            }
        });
    }

}
