import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import { AuthLayout } from "@/components/layout/AuthLayout";

const LoginPage = lazy(() => import("@/pages/LoginPage"));
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const AccountsPage = lazy(() => import("@/pages/AccountsPage"));
const CategoriesPage = lazy(() => import("@/pages/CategoriesPage"));
const PostingsPage = lazy(() => import("@/pages/PostingsPage"));
const TransfersPage = lazy(() => import("@/pages/TransfersPage"));
const ReportsPage = lazy(() => import("@/pages/ReportsPage"));
const SettingsPage = lazy(() => import("@/pages/SettingsPage"));

function SuspenseWrapper({ children }: { children: ReactNode }) {
  return <Suspense fallback={null}>{children}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: (
      <SuspenseWrapper>
        <LoginPage />
      </SuspenseWrapper>
    ),
  },
  {
    element: <AuthLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      {
        path: "dashboard",
        element: (
          <SuspenseWrapper>
            <DashboardPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "accounts",
        element: (
          <SuspenseWrapper>
            <AccountsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "categories",
        element: (
          <SuspenseWrapper>
            <CategoriesPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "postings",
        element: (
          <SuspenseWrapper>
            <PostingsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "transfers",
        element: (
          <SuspenseWrapper>
            <TransfersPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "reports",
        element: (
          <SuspenseWrapper>
            <ReportsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "settings",
        element: (
          <SuspenseWrapper>
            <SettingsPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },
]);
