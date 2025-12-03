import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Github, Mail } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/utils";

export default function SignIn() {
  const { toast } = useToast();
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
      navigate('/');
    } catch (e: any) {
      toast({ title: 'GitHub sign-in failed', description: e?.message || 'Try again', variant: 'destructive' });
    }
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast({ title: "Missing fields", description: "Enter email and password", variant: "destructive" });
      return;
    }
    setLoading(true);
    try {
      const res = await api.postJson('/api/auth/login', { email, password });
      localStorage.setItem('token', res.access_token);
      toast({ title: 'Signed in', description: res?.user?.email || 'Success' });
      navigate('/');
    } catch (err: any) {
      toast({ title: 'Sign in failed', description: err?.message || 'Please try again', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center px-4 py-8 relative bg-[hsl(258_90%_70%)]"
    >
      <div className="relative w-full max-w-6xl p-0 lg:p-8 overflow-visible">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-0">
          {/* Left hero */}
          <div className="relative lg:col-span-7 text-white py-12 px-8 lg:px-12">
            <div className="relative max-w-xl">
              <div className="mb-6">
                <img
                  src=""
                  alt=""
                  className="w-16 h-16 rounded-xl shadow-lg object-cover"
                  onError={(e) => {
                    const t = e.currentTarget as HTMLImageElement;
                    t.onerror = null;
                    t.src = "data:image/svg+xml,<svg xmlns=%27http://www.w3.org/2000/svg%27 width=%27256%27 height=%27256%27 viewBox=%270 0 100 100%27><rect width=%27100%27 height=%27100%27 rx=%2720%27 fill=%27%237d6ee7%27></rect><text x=%2750%25%27 y=%2758%25%27 dominant-baseline=%27middle%27 text-anchor=%27middle%27 font-family=%27Inter, Arial%27 font-size=%2746%27 fill=%27%23fff%27>RM</text></svg>";
                  }}
                />
              </div>
              <h2 className="text-4xl lg:text-5xl font-extrabold leading-tight mb-4">Hello, welcome!</h2>
              <p className="text-white/90 text-base lg:text-lg max-w-prose">
                Learn smarter, apply faster, and land interviews with AI-powered tools.
                Automate repetitive tasks and focus on what matters.
              </p>
              <p className="text-white/60 text-xs mt-10">© {new Date().getFullYear()} JobAlign. All rights reserved.</p>
            </div>
          </div>

          {/* Right floating auth panel */}
          <div className="lg:col-span-5 p-6 lg:p-10 relative">
            <div className="hidden lg:block absolute -left-8 top-6 right-6 bottom-6 rounded-xl bg-[hsl(258_90%_58%)] opacity-90 shadow-[0_24px_48px_rgba(62,46,189,0.35)]" />
            <Card className="relative w-full max-w-sm ml-0 lg:-ml-8 bg-white/85 backdrop-blur rounded-xl border border-[hsl(258_90%_58%)/18] shadow-xl">
              <CardHeader>
                <CardTitle className="text-2xl">Sign in</CardTitle>
                <CardDescription>
                  Use your account credentials or continue with a provider.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={onSubmit}>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email address</Label>
                    <Input id="email" type="email" placeholder="name@mail.com" value={email} onChange={(e)=>setEmail(e.target.value)} required className="focus-visible:ring-2 focus-visible:ring-[hsl(258_90%_60%)] focus-visible:border-[hsl(258_90%_60%)]" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input id="password" type="password" placeholder="••••••••" value={password} onChange={(e)=>setPassword(e.target.value)} required className="focus-visible:ring-2 focus-visible:ring-[hsl(258_90%_60%)] focus-visible:border-[hsl(258_90%_60%)]" />
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <label className="flex items-center gap-2 select-none">
                      <input type="checkbox" className="accent-primary" />
                      <span className="text-muted-foreground">Remember me</span>
                    </label>
                    <a href="#" className="text-[hsl(258_90%_45%)] hover:underline">Forgot password?</a>
                  </div>
                  <div className="flex gap-2">
                    <Button type="submit" className="flex-1 bg-[hsl(258_90%_60%)] hover:bg-[hsl(258_90%_55%)] text-white shadow" disabled={loading}>
                      {loading ? 'Logging in...' : 'Login'}
                    </Button>
                    <Button type="button" className="flex-1 border-2 border-[hsl(258_90%_60%)] text-[hsl(258_90%_45%)] hover:bg-[hsl(258_90%_60%)/6]" variant="outline" onClick={() => navigate('/sign-up')}>
                      Sign up
                    </Button>
                  </div>
                </form>
                <div className="mt-4 grid gap-2">
                  <Button className="w-full" variant="outline" onClick={signInGoogle}>
                    <Mail className="h-4 w-4 mr-2" /> Login with Google
                  </Button>
                  <Button className="w-full" variant="outline" onClick={signInGithub}>
                    <Github className="h-4 w-4 mr-2" /> Login with GitHub
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
