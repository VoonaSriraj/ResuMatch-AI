import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { useLocation } from "react-router-dom";

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const hideSidebar = (
    location.pathname === "/sign-in" ||
    location.pathname === "/sign-up" ||
    location.pathname === "/login" ||
    location.pathname.startsWith("/auth/")
  );
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        {!hideSidebar && <AppSidebar />}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </SidebarProvider>
  );
}
