import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Github, Mail } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/utils";

export default function Login() {
  const { toast } = useToast();

  const openPopup = (url: string): Promise<string | null> => {
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

  const signInGoogle = async () => {
    try {
      const redirect = (import.meta as any).env?.VITE_GOOGLE_REDIRECT_URI || `${window.location.origin}/auth/google/callback`;
      const url = `https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=${encodeURIComponent((import.meta as any).env?.VITE_GOOGLE_CLIENT_ID || '')}&redirect_uri=${encodeURIComponent(redirect)}&scope=${encodeURIComponent('openid email profile')}`;
      const code = await openPopup(url);
      if (!code) return;
      const res = await api.postJson('/api/auth/google', { code });
      localStorage.setItem('token', res.access_token);
      toast({ title: 'Signed in with Google', description: res?.user?.email });
      window.location.href = '/';
    } catch (e: any) {
      toast({ title: 'Google sign-in failed', description: e?.message || 'Try again', variant: 'destructive' });
    }
  };

  const signInGithub = async () => {
    try {
      const clientId = (import.meta as any).env?.VITE_GITHUB_CLIENT_ID || '';
      if (!clientId) {
        toast({ title: 'Missing GitHub Client ID', description: 'Set VITE_GITHUB_CLIENT_ID in your .env and restart Vite.', variant: 'destructive' });
        return;
      }
      const redirect = (import.meta as any).env?.VITE_GITHUB_REDIRECT_URI || `${window.location.origin}/auth/github/callback`;
      const url = `https://github.com/login/oauth/authorize?client_id=${encodeURIComponent(clientId)}&redirect_uri=${encodeURIComponent(redirect)}&scope=read:user user:email`;
      const code = await openPopup(url);
      if (!code) return;
      const res = await api.postJson('/api/auth/github', { code });
      localStorage.setItem('token', res.access_token);
      toast({ title: 'Signed in with GitHub', description: res?.user?.email });
      window.location.href = '/';
    } catch (e: any) {
      toast({ title: 'GitHub sign-in failed', description: e?.message || 'Try again', variant: 'destructive' });
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-8">
      <Card className="w-full max-w-md border-border shadow-lg">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>Use your Google or GitHub account</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button className="w-full" variant="outline" onClick={signInGoogle}>
            <Mail className="h-4 w-4 mr-2" /> Sign in with Google
          </Button>
          <Button className="w-full" variant="outline" onClick={signInGithub}>
            <Github className="h-4 w-4 mr-2" /> Sign in with GitHub
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}


