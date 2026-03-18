import {
  LayoutDashboard,
  Wallet,
  FolderTree,
  Receipt,
  ArrowLeftRight,
  BarChart3,
  Settings,
} from "lucide-react";

export const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/accounts", label: "Accounts", icon: Wallet },
  { to: "/categories", label: "Categories", icon: FolderTree },
  { to: "/postings", label: "Postings", icon: Receipt },
  { to: "/transfers", label: "Transfers", icon: ArrowLeftRight },
  { to: "/reports", label: "Reports", icon: BarChart3 },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;
