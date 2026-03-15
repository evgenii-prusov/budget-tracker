import { NavLink, useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { cn } from "@/lib/utils";
import { navItems } from "./nav-items";

export function Sidebar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("api_key");
    navigate("/login");
  };

  return (
    <aside className="flex h-full w-60 flex-col border-r bg-sidebar text-sidebar-foreground">
      <div className="p-4">
        <h2 className="text-lg font-semibold">Budget Tracker</h2>
      </div>
      <Separator />
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground",
              )
            }
          >
            <Icon className="size-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <Separator />
      <div className="flex items-center justify-between p-2">
        <ThemeToggle />
        <Button variant="ghost" size="icon" onClick={handleLogout}>
          <LogOut className="size-4" />
          <span className="sr-only">Logout</span>
        </Button>
      </div>
    </aside>
  );
}
