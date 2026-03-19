import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthSessionService } from '../services/auth-session.service';

export const authGuard: CanActivateFn = (_route, state) => {
    const auth = inject(AuthSessionService);
    const router = inject(Router);

    if (auth.isAuthenticated()) {
        return true;
    }

    return router.createUrlTree(['/login'], {
        queryParams: state.url && state.url !== '/' ? { redirectTo: state.url } : undefined
    });
};
