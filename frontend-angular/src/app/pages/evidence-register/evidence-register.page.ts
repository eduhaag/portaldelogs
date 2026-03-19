// ===============================
// Componente de Registro de Evidências
// Permite ao usuário registrar informações de tickets e anexar evidências.
// Demonstra uso de formulários, widgets e integração com PO UI.
// Comentários didáticos para facilitar o entendimento!
// ===============================
import { Component, inject, ViewChild, TemplateRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
    PoPageModule, PoFieldModule, PoButtonModule,
    PoLoadingModule, PoNotificationService, PoInfoModule,
    PoDividerModule, PoWidgetModule, PoSwitchModule,
    PoModalModule, PoModalComponent, PoModalAction
} from '@po-ui/ng-components';
import { BackendApiService } from '../../core/services/backend-api.service';

interface UploadedFile {
    filename: string;
    size: number;
}

// O componente principal do registro de evidências
@Component({
    selector: 'app-evidence-register',
    standalone: true,
    imports: [
        CommonModule, FormsModule,
        PoPageModule, PoFieldModule, PoButtonModule,
        PoLoadingModule, PoInfoModule, PoDividerModule,
        PoWidgetModule, PoSwitchModule, PoModalModule
    ],
    template: `
        <po-page-default p-title="Registro de Evidencia">
            <div class="po-row">
                <po-widget class="po-md-12" p-title="Informacoes do Ticket">
                    <div class="po-row">
                        <div class="po-md-6">
                            <po-input
                                name="ticket_number"
                                p-label="Nr do Ticket"
                                p-required
                                p-placeholder="Ex: T-00001"
                                [(ngModel)]="ticketNumber">
                            </po-input>
                        </div>
                        <div class="po-md-6">
                            <po-input
                                name="client_name"
                                p-label="Cliente"
                                p-required
                                p-placeholder="Nome do cliente"
                                [(ngModel)]="clientName">
                            </po-input>
                        </div>
                    </div>
                    <div class="po-row">
                        <div class="po-md-6">
                            <po-input
                                name="situation"
                                p-label="Titulo do Chamado"
                                p-required
                                p-placeholder="Descricao breve do chamado"
                                [(ngModel)]="situation">
                            </po-input>
                        </div>
                        <div class="po-md-6">
                            <po-input
                                name="issue"
                                p-label="Issue"
                                p-placeholder="Numero da issue (opcional)"
                                [(ngModel)]="issue">
                            </po-input>
                        </div>
                    </div>
                    <div class="po-row">
                        <div class="po-md-12">
                            <po-input
                                name="notification_emails"
                                p-label="Emails para Notificacao"
                                p-placeholder="email1&#64;exemplo.com, email2&#64;exemplo.com"
                                [(ngModel)]="notificationEmails">
                            </po-input>
                        </div>
                    </div>
                </po-widget>
            </div>
            <!--
                O formulário acima permite ao usuário inserir dados do ticket, cliente e emails para notificação.
                O uso de widgets PO UI facilita a criação de layouts responsivos e bonitos.
            -->

            <div class="po-row po-mt-3">
                <po-widget class="po-md-12" p-title="Configuracao Tecnica">
                    <div class="po-row">
                        <div class="po-md-6">
                            <po-input
                                name="routine_program"
                                p-label="Rotina/Programa"
                                p-required
                                p-placeholder="Ex: men/men001.p"
                                [(ngModel)]="routineProgram">
                            </po-input>
                        </div>
                        <div class="po-md-6">
                            <po-select
                                name="occurrence_type"
                                p-label="Tipo de Ocorrencia"
                                p-required
                                [p-options]="occurrenceTypeOptions"
                                [ngModel]="occurrenceType"
                                (p-change)="occurrenceType = $event">
                            </po-select>
                        </div>
                    </div>
                    <div class="po-row">
                        <div class="po-md-6">
                            <po-input
                                name="client_version"
                                p-label="Versao"
                                p-required
                                p-placeholder="Ex: 12.1.2403"
                                [(ngModel)]="clientVersion">
                            </po-input>
                        </div>
                        <div class="po-md-6">
                            <po-select
                                name="database_type"
                                p-label="Banco de Dados"
                                p-required
                                [p-options]="databaseTypeOptions"
                                [ngModel]="databaseType"
                                (p-change)="databaseType = $event">
                            </po-select>
                        </div>
                    </div>
                </po-widget>
            </div>

            <div class="po-row po-mt-3">
                <po-widget class="po-md-12" p-title="Analise Tecnica">
                    <div class="po-row">
                        <div class="po-md-6">
                            <po-switch
                                name="simulated_internally"
                                p-label="Situacao simulada internamente?"
                                p-label-on="Sim"
                                p-label-off="Nao"
                                [(ngModel)]="simulatedInternally">
                            </po-switch>
                        </div>
                        <div class="po-md-6">
                            <po-switch
                                name="program_needed"
                                p-label="Necessario programa de acerto?"
                                p-label-on="Sim"
                                p-label-off="Nao"
                                [(ngModel)]="programNeeded">
                            </po-switch>
                        </div>
                    </div>
                    @if (simulatedInternally) {
                    <div class="po-row">
                        <div class="po-md-12">
                            <po-input
                                name="simulation_base"
                                p-label="Base de Simulacao"
                                p-placeholder="Informe a base utilizada"
                                [(ngModel)]="simulationBase">
                            </po-input>
                        </div>
                    </div>
                    }
                </po-widget>
            </div>

            <div class="po-row po-mt-3">
                <po-widget class="po-md-12" p-title="Descricao Detalhada">
                    <div class="po-row">
                        <div class="po-md-12">
                            <po-textarea
                                name="occurrence_description"
                                p-label="Descricao da Ocorrencia"
                                [p-required]="true"
                                [p-rows]="6"
                                p-placeholder="Descreva detalhadamente a ocorrencia..."
                                [(ngModel)]="occurrenceDescription">
                            </po-textarea>
                        </div>
                    </div>
                    <div class="po-row">
                        <div class="po-md-12">
                            <po-textarea
                                name="expected_result"
                                p-label="Resultado Esperado"
                                [p-required]="true"
                                [p-rows]="4"
                                p-placeholder="Descreva o resultado esperado..."
                                [(ngModel)]="expectedResult">
                            </po-textarea>
                        </div>
                    </div>
                </po-widget>
            </div>

            <div class="po-row po-mt-3">
                <po-widget class="po-md-12" p-title="Arquivos de Evidencia">
                    <div class="po-row">
                        <div class="po-md-12">
                            <input
                                type="file"
                                multiple
                                (change)="onFilesSelected($event)"
                                data-testid="evidence-file-input"
                                style="margin-bottom: 12px"
                            />
                            <p class="po-font-text-small po-text-color-neutral-mid-40">
                                Maximo de 20MB por arquivo. Selecione multiplos arquivos se necessario.
                            </p>
                        </div>
                    </div>
                    @if (uploadedFiles.length > 0) {
                    <div class="po-row">
                        <div class="po-md-12">
                            <strong>Arquivos selecionados:</strong>
                            <ul style="list-style: none; padding: 0">
                                @for (file of uploadedFiles; track file.filename) {
                                <li style="padding: 4px 0; display: flex; align-items: center; gap: 8px">
                                    <span class="an an-file"></span>
                                    {{ file.filename }} ({{ (file.size / 1024).toFixed(1) }} KB)
                                    <po-button
                                        p-icon="an-trash"
                                        p-kind="tertiary"
                                        p-size="sm"
                                        (p-click)="removeFile(file.filename)"
                                        data-testid="remove-file-btn">
                                    </po-button>
                                </li>
                                }
                            </ul>
                        </div>
                    </div>
                    }
                </po-widget>
            </div>

            <div class="po-row po-mt-4 po-mb-4">
                <div class="po-md-12" style="display: flex; gap: 12px; justify-content: flex-end">
                    <po-button
                        p-label="Limpar Formulario"
                        p-kind="secondary"
                        (p-click)="resetForm()"
                        data-testid="clear-form-btn">
                    </po-button>
                    <po-button
                        p-label="Gerar Evidencia (PDF + DOCX)"
                        p-kind="primary"
                        [p-loading]="isGenerating"
                        [p-disabled]="!isFormValid()"
                        (p-click)="generateEvidence()"
                        data-testid="generate-evidence-btn">
                    </po-button>
                </div>
            </div>
        </po-page-default>
    `
})
export class EvidenceRegisterPageComponent {
    private readonly api = inject(BackendApiService);
    private readonly notification = inject(PoNotificationService);

    ticketNumber = '';
    situation = '';
    issue = '';
    clientName = '';
    clientVersion = '';
    databaseType = '';
    routineProgram = '';
    occurrenceType = '';
    simulatedInternally = false;
    simulationBase = '';
    occurrenceDescription = '';
    expectedResult = '';
    programNeeded = false;
    notificationEmails = '';
    isGenerating = false;
    sessionId = '';
    uploadedFiles: UploadedFile[] = [];
    selectedFiles: File[] = [];

    readonly occurrenceTypeOptions = [
        { label: 'Manutenção', value: 'Manutenção' },
        { label: 'Apoio', value: 'Apoio' },
        { label: 'Apoio Cliente', value: 'Apoio Cliente' },
        
    ];

    readonly databaseTypeOptions = [
        { label: 'Oracle', value: 'Oracle' },
        { label: 'SQL Server', value: 'SQL Server' },
        { label: 'PostgreSQL', value: 'PostgreSQL' },
        { label: 'Progress', value: 'Progress' },
        { label: 'Informix', value: 'Informix' },
    ];

    isFormValid(): boolean {
        return !!(
            this.ticketNumber.trim() &&
            this.clientName.trim() &&
            this.situation.trim() &&
            this.routineProgram.trim() &&
            this.occurrenceType &&
            this.clientVersion.trim() &&
            this.databaseType &&
            this.occurrenceDescription.trim() &&
            this.expectedResult.trim()
        );
    }

    onFilesSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (!input.files?.length) return;

        for (let i = 0; i < input.files.length; i++) {
            const file = input.files[i];
            if (file.size > 20 * 1024 * 1024) {
                this.notification.warning(`Arquivo ${file.name} excede 20MB e foi ignorado.`);
                continue;
            }
            this.selectedFiles.push(file);
            this.uploadedFiles.push({ filename: file.name, size: file.size });
        }
    }

    removeFile(filename: string): void {
        this.uploadedFiles = this.uploadedFiles.filter(f => f.filename !== filename);
        this.selectedFiles = this.selectedFiles.filter(f => f.name !== filename);
        if (this.sessionId) {
            this.api.deleteUploadedFile(this.sessionId, filename).subscribe();
        }
    }

    generateEvidence(): void {
        if (!this.isFormValid()) {
            this.notification.warning('Preencha todos os campos obrigatorios.');
            return;
        }

        this.isGenerating = true;

        const uploadAndGenerate = () => {
            const formData = new FormData();
            formData.append('ticket_number', this.ticketNumber);
            formData.append('situation', this.situation);
            formData.append('issue', this.issue);
            formData.append('client_name', this.clientName);
            formData.append('client_version', this.clientVersion);
            formData.append('database_type', this.databaseType);
            formData.append('routine_program', this.routineProgram);
            formData.append('occurrence_type', this.occurrenceType);
            formData.append('simulated_internally', String(this.simulatedInternally));
            formData.append('simulation_base', this.simulationBase);
            formData.append('occurrence_description', this.occurrenceDescription);
            formData.append('expected_result', this.expectedResult);
            formData.append('program_needed', String(this.programNeeded));
            formData.append('notification_emails', this.notificationEmails);
            if (this.sessionId) {
                formData.append('session_id', this.sessionId);
            }

            this.api.generatePdf(formData).subscribe({
                next: (response) => {
                    this.isGenerating = false;
                    const blob = response.body;
                    if (blob) {
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        const cd = response.headers.get('Content-Disposition');
                        const fn = cd?.match(/filename="?([^"]+)"?/)?.[1] || `${this.ticketNumber}_evidencias.zip`;
                        a.download = fn;
                        a.click();
                        window.URL.revokeObjectURL(url);
                        this.notification.success('Evidencia gerada com sucesso! O download ira iniciar automaticamente.');
                    }
                },
                error: (err) => {
                    this.isGenerating = false;
                    this.notification.error('Falha ao gerar evidencia: ' + (err.error?.detail || err.message));
                }
            });
        };

        if (this.selectedFiles.length > 0) {
            this.api.uploadFiles(this.selectedFiles, this.sessionId || undefined).subscribe({
                next: (res) => {
                    this.sessionId = res.session_id;
                    uploadAndGenerate();
                },
                error: (err) => {
                    this.isGenerating = false;
                    this.notification.error('Falha no upload de arquivos: ' + (err.error?.detail || err.message));
                }
            });
        } else {
            uploadAndGenerate();
        }
    }

    resetForm(): void {
        this.ticketNumber = '';
        this.situation = '';
        this.issue = '';
        this.clientName = '';
        this.clientVersion = '';
        this.databaseType = '';
        this.routineProgram = '';
        this.occurrenceType = '';
        this.simulatedInternally = false;
        this.simulationBase = '';
        this.occurrenceDescription = '';
        this.expectedResult = '';
        this.programNeeded = false;
        this.notificationEmails = '';
        this.uploadedFiles = [];
        this.selectedFiles = [];
        if (this.sessionId) {
            this.api.cleanupSession(this.sessionId).subscribe();
            this.sessionId = '';
        }
    }
}
