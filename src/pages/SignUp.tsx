import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Github, Mail } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/utils";

export default function SignUp() {
  const { toast } = useToast();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

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
      window.alert('Signed in successfully');
      navigate('/');
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
      window.alert('Signed in successfully');
      navigate('/');
    } catch (e: any) {
      toast({ title: 'GitHub sign-in failed', description: e?.message || 'Try again', variant: 'destructive' });
    }
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !password) {
      toast({ title: "Missing fields", description: "Enter name, email and password", variant: "destructive" });
      return;
    }
    setLoading(true);
    try {
      const res = await api.postJson('/api/auth/register', { name, email, password });
      localStorage.setItem('token', res.access_token);
      toast({ title: 'Account created', description: res?.user?.email || 'Success' });
      window.alert('Account created successfully');
      navigate('/');
    } catch (err: any) {
      toast({ title: 'Sign up failed', description: err?.message || 'Please try again', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-8">
      <Card className="w-full max-w-md border-border shadow-lg">
        <CardHeader>
          <CardTitle>Create your account</CardTitle>
          <CardDescription>Use your email and password or continue with a provider</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" type="text" placeholder="Your name" value={name} onChange={(e)=>setName(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="you@example.com" value={email} onChange={(e)=>setEmail(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" placeholder="••••••••" value={password} onChange={(e)=>setPassword(e.target.value)} required />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Creating...' : 'Create account'}
            </Button>
          </form>
          <div className="mt-4 grid gap-2">
            <Button className="w-full" variant="outline" onClick={signInGoogle}>
              <Mail className="h-4 w-4 mr-2" /> Continue with Google
            </Button>
            <Button className="w-full" variant="outline" onClick={signInGithub}>
              <Github className="h-4 w-4 mr-2" /> Continue with GitHub
            </Button>
            <p className="text-sm text-muted-foreground text-center mt-2">
              Already have an account? <Link className="text-primary hover:underline" to="/sign-in">Sign in</Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
