import { expect, test } from '@playwright/test';

import {
    mockAdvancedSearch,
    mockAnalyzeInfo,
    mockAnalyzeLog,
    mockDashboardBootstrap,
    mockKnowledgeBaseSearch,
    mockLoginSuccess,
    seedAuthenticatedSession
} from './support/backend-mocks';

async function applyAngularChanges(page: import('@playwright/test').Page, selector: string): Promise<void> {
    await page.evaluate((componentSelector) => {
        const element = document.querySelector(componentSelector);
        if (!(element instanceof Element)) {
            return;
        }

        const ng = (window as Window & {
            ng?: {
                getComponent?: (node: Element | null) => any;
                applyChanges?: (component: any) => void;
            };
        }).ng;
        const component = ng?.getComponent?.(element);
        if (component && ng?.applyChanges) {
            ng.applyChanges(component);
        }
    }, selector);
}

test('login redireciona para o painel após autenticação bem-sucedida', async ({ page }) => {
    await mockLoginSuccess(page);
    await mockDashboardBootstrap(page);

    await page.goto('/login');
    await page.getByLabel('Usuário ou Email').fill('qa-user');
    await page.locator('#password').fill('123456');
    await page.getByRole('button', { name: 'Entrar' }).click();

    await page.waitForURL('**/analise');
    await expect(page.getByRole('heading', { name: 'Analisador de Logs' })).toBeVisible();
});

test('análise de log percorre upload, chamada backend e tela de resultados', async ({ page }) => {
    await seedAuthenticatedSession(page);
    await mockAnalyzeInfo(page);
    await mockAnalyzeLog(page);

    await page.goto('/analise/upload');
    await page.locator('#logFilePage').setInputFiles({
        name: 'app.log',
        mimeType: 'text/plain',
        buffer: Buffer.from('ERROR broker unavailable')
    });

    await Promise.all([
        page.waitForResponse((response) => response.url().includes('/api/analyze-info') && response.request().method() === 'POST'),
        page.getByRole('button', { name: 'Pré-analisar' }).click()
    ]);
    await applyAngularChanges(page, 'app-analyze-log-page');
    await expect(page.getByText('Arquivo:')).toBeVisible();
    await expect(page.locator('.modal-preview-box')).toContainText('app.log');

    await Promise.all([
        page.waitForResponse((response) => response.url().includes('/api/analyze-log') && response.request().method() === 'POST'),
        page.getByRole('button', { name: 'Analisar log' }).click()
    ]);
    await applyAngularChanges(page, 'app-analyze-log-page');
    await page.waitForURL('**/analise/resultados');
    await expect(page.getByText('Resultados encontrados')).toBeVisible();
    await expect(page.locator('.result-card__message').filter({ hasText: 'Broker unavailable' }).first()).toBeVisible();
});

test('base de conhecimento sinaliza retorno truncado do backend', async ({ page }) => {
    await seedAuthenticatedSession(page);
    await mockKnowledgeBaseSearch(page);

    await page.goto('/base-conhecimento');
    await page.getByLabel('Termo de busca').fill('DataServer');
    const [knowledgeResponse] = await Promise.all([
        page.waitForResponse((response) => response.url().includes('/api/search-knowledge-base') && response.request().method() === 'POST'),
        page.getByRole('button', { name: 'Pesquisar' }).click()
    ]);
    await expect(knowledgeResponse.status()).toBe(200);
    await applyAngularChanges(page, 'app-knowledge-base-page');

    await expect(page.getByText(/Exibindo 5 de 12 resultado\(s\), limitado a 5 itens por consulta\./)).toBeVisible();
    await expect(page.getByRole('table').getByText('Falha no DataServer ao sincronizar metadados.')).toBeVisible();
});

test('busca avançada renderiza matches retornados pelo backend', async ({ page }) => {
    await seedAuthenticatedSession(page);
    await mockAdvancedSearch(page);

    await page.goto('/busca-avancada');
    await page.getByRole('button', { name: 'Arquivo de log' }).setInputFiles({
        name: 'app.log',
        mimeType: 'text/plain',
        buffer: Buffer.from('Procedure test.p failed')
    });
    await page.getByLabel('Padrão').fill('Procedure');
    await Promise.all([
        page.waitForResponse((response) => response.url().includes('/api/search-log') && response.request().method() === 'POST'),
        page.getByRole('button', { name: 'Buscar' }).click()
    ]);
    await applyAngularChanges(page, 'app-advanced-search-page');

    await expect(page.getByText(/2 match\(es\) encontrados\./)).toBeVisible();
    await expect(page.getByRole('table').getByText('Procedure test.p failed')).toBeVisible();
});
