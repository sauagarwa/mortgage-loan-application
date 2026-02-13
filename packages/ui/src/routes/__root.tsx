// mortgage-ai - Root Route
// React import required for JSX (ESLint requirement)
// @ts-expect-error - React is used implicitly by JSX transform
import React from 'react';
import { createRootRoute, Outlet } from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/router-devtools';
import { Header } from '../components/header/header';
import { Footer } from '../components/footer/footer';
import { Sidebar } from '../components/sidebar/sidebar';

export const Route = createRootRoute({
  component: () => (
    <div className="flex min-h-screen flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
      <Footer />
      <TanStackRouterDevtools />
    </div>
  ),
});