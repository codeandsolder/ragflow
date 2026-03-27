import { useAuth } from '@/hooks/auth-hooks';
import { redirectToLogin } from '@/utils/authorization-util';
import { Outlet } from 'react-router';
import { Header } from './components/header';

export function RootLayoutContainer({ children }: React.PropsWithChildren) {
  return (
    <div className="size-full grid grid-rows-[auto_1fr] grid-cols-1 grid-flow-col">
      <Header className="px-5 py-4" />

      <main className="size-full overflow-hidden">{children}</main>
    </div>
  );
}

<<<<<<< HEAD:web/src/layouts/root-layout.tsx
export default function RootLayout() {
=======
export default function NextLayout() {
  const { isLogin } = useAuth();

  if (isLogin === false) {
    redirectToLogin();
    return null;
  }
  if (isLogin === null) return null;

>>>>>>> refs/pull/13446/head:web/src/layouts/next.tsx
  return (
    <RootLayoutContainer>
      <Outlet />
    </RootLayoutContainer>
  );
}
