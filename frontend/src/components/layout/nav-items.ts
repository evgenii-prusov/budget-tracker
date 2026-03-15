import {
  Wallet,
  FolderTree,
  Receipt,
  ArrowLeftRight,
  BarChart3,
} from "lucide-react";

export const navItems = [
  { to: "/accounts", label: "Accounts", icon: Wallet },
  { to: "/categories", label: "Categories", icon: FolderTree },
  { to: "/postings", label: "Postings", icon: Receipt },
  { to: "/transfers", label: "Transfers", icon: ArrowLeftRight },
  { to: "/reports", label: "Reports", icon: BarChart3 },
] as const;
