import { Navigate, Outlet } from "react-router-dom";
import { AppLayout } from "./AppLayout";

export function AuthLayout() {
  const apiKey = localStorage.getItem("api_key");

  if (!apiKey) {
    return <Navigate to="/login" replace />;
  }

  return (
    <AppLayout>
      <Outlet />
    </AppLayout>
  );
}
