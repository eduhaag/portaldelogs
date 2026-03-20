import { Routes } from '@angular/router';
import { AdvancedSearchPageComponent } from './pages/advanced-search/advanced-search.page';
import { AnalysisHistoryPageComponent } from './pages/analysis-history/analysis-history.page';
import { AnalyzeLogPageComponent } from './pages/analyze-log/analyze-log.page';
import { AnalysisPageComponent } from './pages/analysis/analysis.page';
import { AnalysisResultsPageComponent } from './pages/analysis-results/analysis-results.page';
import { KnowledgeBasePageComponent } from './pages/knowledge-base/knowledge-base.page';
import { LoginPageComponent } from './pages/login/login.page';
import { ProfilerAnalysisPageComponent } from './pages/profiler-analysis/profiler-analysis.page';
import { RegisterUserPageComponent } from './pages/register-user/register-user.page';
import { VersionComparePageComponent } from './pages/version-compare/version-compare.page';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
    {
        path: 'login',
        title: 'Central do Suporte - Login',
        component: LoginPageComponent
    },
    {
        path: 'novo-usuario',
        title: 'Central do Suporte - Cadastro',
        component: RegisterUserPageComponent
    },
    {
        path: '',
        canActivate: [authGuard],
        children: [
            {
                path: '',
                pathMatch: 'full',
                redirectTo: 'analise'
            },
            {
                path: 'analise',
                title: 'Upload e análise de log',
                component: AnalysisPageComponent
            },
            {
                path: 'analise/historico',
                title: 'Histórico de análises',
                component: AnalysisHistoryPageComponent
            },
            {
                path: 'analise/upload',
                title: 'Analisar logs',
                component: AnalyzeLogPageComponent
            },
            {
                path: 'analise/resultados',
                title: 'Resultado da análise de log',
                component: AnalysisResultsPageComponent
            },
            {
                path: 'busca-avancada',
                title: 'Busca avançada',
                component: AdvancedSearchPageComponent
            },
            {
                path: 'base-conhecimento',
                title: 'Base de conhecimento',
                component: KnowledgeBasePageComponent
            },
            {
                path: 'profiler',
                title: 'Análise do profiler',
                component: ProfilerAnalysisPageComponent
            },
            {
                path: 'comparacao-versao',
                title: 'Comparação de extrato de versão',
                component: VersionComparePageComponent
            },
            {
                path: 'profiler-version-compare',
                redirectTo: 'profiler',
                pathMatch: 'full'
            },
            {
                path: '**',
                redirectTo: 'analise'
            }
        ]
    }
];
