import { Component, HostListener, inject } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { PoAvatarModule, PoButtonModule, PoIconModule } from '@po-ui/ng-components';
import { AuthSessionService } from './core/services/auth-session.service';

type SidebarChild = {
  label: string;
  route: string;
};

type SidebarItem = {
  id: string;
  label: string;
  icon: string;
  route?: string;
  children?: SidebarChild[];
};

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, PoAvatarModule, PoButtonModule, PoIconModule],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  private readonly auth = inject(AuthSessionService);
  private readonly router = inject(Router);
  private readonly rememberedCredentialsKey = 'central-suporte:remembered-credentials';

  protected sidebarCollapsed = false;
  protected mobileSidebarOpen = false;
  protected userMenuOpen = false;

  protected readonly sidebarItems: SidebarItem[] = [
    {
      id: 'home',
      label: 'Início',
      icon: 'an-house-line',
      route: '/analise'
    },
    {
      id: 'analysis',
      label: 'Análise',
      icon: 'an-upload-simple',
      children: [
        { label: 'Upload e análise', route: '/analise' },
        { label: 'Histórico operacional', route: '/analise/historico' }
      ]
    },
    {
      id: 'search',
      label: 'Busca avançada',
      icon: 'an-magnifying-glass',
      route: '/busca-avancada'
    },
    {
      id: 'knowledge',
      label: 'Conhecimento',
      icon: 'an-book-open',
      children: [
        { label: 'Base de conhecimento', route: '/base-conhecimento' },
        { label: 'Categorias', route: '/analise' },
        { label: 'Não-erros', route: '/analise' },
        { label: 'Mudanças salvas', route: '/analise' }
      ]
    },
    {
      id: 'performance',
      label: 'Profiler / Extrato',
      icon: 'an-chart-bar',
      children: [
        { label: 'Profiler', route: '/profiler' },
        { label: 'Extrato de Versão', route: '/comparacao-versao' }
      ]
    }
  ];

  protected readonly expandedSections: Record<string, boolean> = {
    analysis: true,
    knowledge: true,
    performance: true
  };

  protected get visibleSidebarItems(): SidebarItem[] {
    return this.sidebarItems;
  }

  protected get isAuthRoute(): boolean {
    return this.router.url.startsWith('/login') || this.router.url.startsWith('/novo-usuario');
  }

  protected get currentUserLabel(): string {
    return this.auth.getDisplayName();
  }

  protected get currentUsername(): string {
    return this.auth.getUsername();
  }

  protected get currentUserEmail(): string {
    return this.auth.getEmail();
  }

  protected get currentUserInitials(): string {
    const value = this.currentUserLabel || this.currentUsername;
    return value
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() ?? '')
      .join('') || 'US';
  }

  protected get userAvatarSrc(): string {
    const initials = this.currentUserInitials;
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
        <rect width="64" height="64" rx="32" fill="#0f3550"></rect>
        <text x="50%" y="53%" dominant-baseline="middle" text-anchor="middle"
          font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#ffffff">${initials}</text>
      </svg>`;

    return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
  }

  protected get rememberedPassword(): string {
    if (typeof localStorage === 'undefined') {
      return 'Não salva';
    }

    try {
      const raw = localStorage.getItem(this.rememberedCredentialsKey);
      if (!raw) {
        return 'Não salva';
      }

      const saved = JSON.parse(raw) as { password?: string };
      return saved.password?.trim() ? saved.password : 'Não salva';
    } catch {
      return 'Não salva';
    }
  }

  protected get isMobileViewport(): boolean {
    return typeof window !== 'undefined' && window.innerWidth <= 960;
  }

  protected get shouldCollapseSidebar(): boolean {
    return !this.isMobileViewport && this.sidebarCollapsed;
  }

  protected get shouldShowMobileSidebar(): boolean {
    return this.isMobileViewport && this.mobileSidebarOpen;
  }

  protected get sidebarToggleTitle(): string {
    if (this.isMobileViewport) {
      return this.shouldShowMobileSidebar ? 'Fechar menu lateral' : 'Abrir menu lateral';
    }

    return this.shouldCollapseSidebar ? 'Abrir menu lateral' : 'Fechar menu lateral';
  }

  protected get sidebarToggleIcon(): string {
    if (this.isMobileViewport) {
      return this.shouldShowMobileSidebar ? 'an-menu-close' : 'an-menu-open';
    }

    return this.shouldCollapseSidebar ? 'an-menu-open' : 'an-menu-close';
  }

  @HostListener('window:resize')
  protected onWindowResize(): void {
    if (!this.isMobileViewport) {
      this.mobileSidebarOpen = false;
    }
  }

  @HostListener('document:click', ['$event'])
  protected onDocumentClick(event: MouseEvent): void {
    const target = event.target as HTMLElement | null;
    if (!target?.closest('.workspace-header__user-tools')) {
      this.userMenuOpen = false;
    }
  }

  protected toggleSidebar(): void {
    this.userMenuOpen = false;

    if (this.isMobileViewport) {
      this.mobileSidebarOpen = !this.mobileSidebarOpen;
      return;
    }

    this.sidebarCollapsed = !this.sidebarCollapsed;
  }

  protected closeMobileSidebar(): void {
    this.mobileSidebarOpen = false;
  }

  protected toggleUserMenu(event: MouseEvent): void {
    event.stopPropagation();
    this.userMenuOpen = !this.userMenuOpen;
  }

  protected toggleSection(item: SidebarItem): void {
    if (!item.children?.length) {
      if (item.route) {
        this.navigateTo(item.route);
      }

      return;
    }

    if (this.shouldCollapseSidebar) {
      this.sidebarCollapsed = false;
    }

    this.expandedSections[item.id] = !this.isSectionOpen(item);
  }

  protected isSectionOpen(item: SidebarItem): boolean {
    return !!this.expandedSections[item.id];
  }

  protected isItemActive(item: SidebarItem): boolean {
    if (item.route) {
      return this.isRouteActive(item.route);
    }

    return item.children?.some((child) => this.isRouteActive(child.route)) ?? false;
  }

  protected isRouteActive(route: string): boolean {
    return this.router.url.startsWith(route);
  }

  protected navigateTo(route: string): void {
    if (this.isMobileViewport) {
      this.mobileSidebarOpen = false;
    }

    this.userMenuOpen = false;

    void this.router.navigateByUrl(route);
  }

  protected logout(): void {
    this.auth.logout();
    this.mobileSidebarOpen = false;
    this.userMenuOpen = false;
    void this.router.navigateByUrl('/login');
  }
}
