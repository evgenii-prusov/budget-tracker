import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import { AuthLayout } from "@/components/layout/AuthLayout";

const LoginPage = lazy(() => import("@/pages/LoginPage"));
const AccountsPage = lazy(() => import("@/pages/AccountsPage"));
const CategoriesPage = lazy(() => import("@/pages/CategoriesPage"));
const PostingsPage = lazy(() => import("@/pages/PostingsPage"));
const TransfersPage = lazy(() => import("@/pages/TransfersPage"));
const ReportsPage = lazy(() => import("@/pages/ReportsPage"));

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
      { index: true, element: <Navigate to="/accounts" replace /> },
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
    ],
  },
]);
