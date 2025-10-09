import { LayoutDashboard, Target, FileText, Briefcase, Settings, ChevronRight, MessageSquare, Github, Mail } from "lucide-react";
import { NavLink } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
  useSidebar,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/utils";

const navItems = [
  { title: "Dashboard", url: "/", icon: LayoutDashboard },
  { title: "Job Match", url: "/job-match", icon: Target },
  { title: "Resume Optimizer", url: "/resume-optimizer", icon: FileText },
  { title: "Interview Prep", url: "/interview-prep", icon: MessageSquare },
  { title: "Recommended Jobs", url: "/recommended-jobs", icon: Briefcase },
  { title: "Settings", url: "/settings", icon: Settings },
];

export function AppSidebar() {
  const { open } = useSidebar();
  const { toast } = useToast();

  const oauthPopup = async (url: string): Promise<string | null> => {
    return new Promise((resolve) => {
      const w = 500, h = 600;
      const y = window.top!.outerHeight / 2 + window.top!.screenY - ( h / 2);
      const x = window.top!.outerWidth / 2 + window.top!.screenX - ( w / 2);
      const popup = window.open(url, "oauth", `width=${w},height=${h},top=${y},left=${x}`);
      const handler = (event: MessageEvent) => {
        if (typeof event.data === 'object' && event.data && (event.data as any).code) {
          window.removeEventListener('message', handler);
          resolve((event.data as any).code as string);
          popup?.close();
        }
      };
      window.addEventListener('message', handler);
      const timer = setInterval(()=>{ if (popup && popup.closed) { clearInterval(timer); window.removeEventListener('message', handler); resolve(null); } }, 500);
    });
  };

  const startGoogle = async () => {
    try {
      const redirect = (import.meta as any).env?.VITE_GOOGLE_REDIRECT_URI || `${window.location.origin}/auth/google/callback`;
      const url = `https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=${encodeURIComponent((import.meta as any).env?.VITE_GOOGLE_CLIENT_ID || '')}&redirect_uri=${encodeURIComponent(redirect)}&scope=${encodeURIComponent('openid email profile')}`;
      const code = await oauthPopup(url);
      if (!code) return;
      const res = await api.postJson('/api/auth/google', { code });
      localStorage.setItem('token', res.access_token);
      toast({ title: 'Signed in with Google', description: res?.user?.email });
    } catch (e: any) {
      toast({ title: 'Google sign-in failed', description: e?.message || 'Try again', variant: 'destructive' });
    }
  };

  const startGithub = async () => {
    try {
      const redirect = (import.meta as any).env?.VITE_GITHUB_REDIRECT_URI || `${window.location.origin}/auth/github/callback`;
      const url = `https://github.com/login/oauth/authorize?client_id=${encodeURIComponent((import.meta as any).env?.VITE_GITHUB_CLIENT_ID || '')}&redirect_uri=${encodeURIComponent(redirect)}&scope=read:user user:email`;
      const code = await oauthPopup(url);
      if (!code) return;
      const res = await api.postJson('/api/auth/github', { code });
      localStorage.setItem('token', res.access_token);
      toast({ title: 'Signed in with GitHub', description: res?.user?.email });
    } catch (e: any) {
      toast({ title: 'GitHub sign-in failed', description: e?.message || 'Try again', variant: 'destructive' });
    }
  };

  return (
    <Sidebar className="border-r border-sidebar-border">
      <SidebarHeader className="border-b border-sidebar-border p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center shadow-glow">
            <Target className="h-6 w-6 text-primary-foreground" />
          </div>
          {open && (
            <div className="flex flex-col animate-fade-in">
              <h2 className="text-lg font-bold text-sidebar-foreground">JobAlign AI</h2>
              <p className="text-xs text-muted-foreground">Your Career Assistant</p>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs uppercase tracking-wider text-muted-foreground px-4">
            Main Menu
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild className="transition-all duration-200">
                    <NavLink
                      to={item.url}
                      end
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-4 py-3 rounded-lg ${
                          isActive
                            ? "bg-sidebar-accent text-sidebar-primary font-medium shadow-sm"
                            : "text-sidebar-foreground hover:bg-sidebar-accent/50"
                        }`
                      }
                    >
                      <item.icon className="h-5 w-5" />
                      {open && <span>{item.title}</span>}
                      {open && <ChevronRight className="h-4 w-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border p-4" />
    </Sidebar>
  );
}
