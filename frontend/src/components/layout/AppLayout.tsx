import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { MobileSidebar } from "./MobileSidebar";

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-svh">
      {/* Desktop sidebar */}
      <div className="hidden md:block">
        <Sidebar />
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Mobile header */}
        <header className="flex items-center border-b p-2 md:hidden">
          <MobileSidebar />
          <span className="ml-2 text-sm font-semibold">Budget Tracker</span>
        </header>

        <main className="flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
