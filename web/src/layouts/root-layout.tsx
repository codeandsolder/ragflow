import { useAuth } from '@/hooks/auth-hooks';
import { redirectToLogin } from '@/utils/authorization-util';
import { Outlet } from 'react-router';
import { Header } from './components/header';
import { useTranslation } from 'react-i18next';

export function RootLayoutContainer({ children }: React.PropsWithChildren) {
  const { t } = useTranslation();

  return (
    <div className="size-full grid grid-rows-[auto_1fr] grid-cols-1 grid-flow-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:outline-none"
      >
        {t('common.skipToContent') || 'Skip to main content'}
      </a>
      <Header className="px-5 py-4" />

      <main id="main-content" className="size-full overflow-hidden" tabIndex={-1}>
        {children}
      </main>
    </div>
  );
}

export default function RootLayout() {
  const { isLogin } = useAuth();

  if (isLogin === false) {
    redirectToLogin();
    return null;
  }
  if (isLogin === null) return null;

  return (
    <RootLayoutContainer>
      <Outlet />
    </RootLayoutContainer>
  );
}
