import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Linkedin, CheckCircle, XCircle, RefreshCw } from "lucide-react";
import { api } from "@/lib/utils";

interface LinkedInStatus {
  connected: boolean;
  linkedin_id?: string;
}

interface LinkedInConnectionProps {
  onConnectionChange?: (connected: boolean) => void;
}

export default function LinkedInConnection({ onConnectionChange }: LinkedInConnectionProps) {
  const [status, setStatus] = useState<LinkedInStatus>({ connected: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [justConnected, setJustConnected] = useState(false);

  const checkStatus = async () => {
    try {
      const response = await api.get('/api/linkedin/status');
      setStatus(response);
      setError(null);
      // Notify parent component of connection status change
      if (onConnectionChange) {
        onConnectionChange(response.connected);
      }
    } catch (err) {
      console.error('Failed to check LinkedIn status:', err);
      setError('Failed to check LinkedIn connection status');
    }
  };

  const connectLinkedIn = async () => {
    setLoading(true);
    setError(null);

    try {
      // 1) Get LinkedIn auth URL from backend
      const response = await api.get('/api/linkedin/login');
      const authUrl = response.auth_url as string;

      // 2) Open popup
      const popup = window.open(
        authUrl,
        'linkedin-oauth',
        'width=600,height=700,scrollbars=yes,resizable=yes'
      );
      if (!popup) throw new Error('Popup blocked. Please allow popups for this site.');

      // 3) Listener to receive messages (from /auth/linkedin/callback or backend HTML)
      const messageListener = async (event: MessageEvent) => {
        const data: any = event.data || {};
        if (!data) return;

        if (data.type === 'LINKEDIN_CONNECTED') {
          cleanup();
          setError(null);
          if (data.message) {
            setSuccessMessage(data.message);
            setTimeout(() => setSuccessMessage(null), 5000);
          }
          setJustConnected(true);
          if (onConnectionChange) onConnectionChange(true);
          checkStatus();
        } else if (data.type === 'LINKEDIN_ERROR') {
          cleanup();
          setError(data.error || 'LinkedIn connection failed');
        } else if (data.code) {
          // Frontend callback posted { code, state } — exchange with backend
          try {
            await api.postJson('/api/auth/linkedin', { code: data.code, state: data.state });
            cleanup();
            setError(null);
            setSuccessMessage('LinkedIn connected successfully!');
            setTimeout(() => setSuccessMessage(null), 5000);
            setJustConnected(true);
            if (onConnectionChange) onConnectionChange(true);
            checkStatus();
          } catch (_) {
            cleanup();
            setError('LinkedIn connection failed');
          }
        }
      };

      window.addEventListener('message', messageListener as any);

      // 4) Detect popup close
      const closedInterval = window.setInterval(() => {
        if (popup.closed) {
          cleanup();
        }
      }, 500);

      // 5) Cleanup helper
      const cleanup = () => {
        try { window.removeEventListener('message', messageListener as any); } catch {}
        try { window.clearInterval(closedInterval); } catch {}
        try { if (!popup.closed) popup.close(); } catch {}
        setLoading(false);
      };

      // 6) Safety timeout cleanup (5 min)
      window.setTimeout(() => cleanup(), 300000);
    } catch (err) {
      console.error('Failed to initiate LinkedIn connection:', err);
      setError('Failed to connect to LinkedIn. Please try again.');
      setLoading(false);
    }
  };

  const disconnectLinkedIn = async () => {
    setLoading(true);
    setError(null);
    
    try {
      await api.postJson('/api/linkedin/disconnect', {});
      setStatus({ connected: false });
      setJustConnected(false);
      setError(null);
      // Notify parent component of disconnection
      if (onConnectionChange) {
        onConnectionChange(false);
      }
    } catch (err) {
      console.error('Failed to disconnect LinkedIn:', err);
      setError('Failed to disconnect LinkedIn. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
    
    // Check if we just returned from LinkedIn OAuth
    const urlParams = new URLSearchParams(window.location.search);
    const linkedinStatus = urlParams.get('linkedin');
    
    if (linkedinStatus === 'connected') {
      // Refresh status after successful connection
      setJustConnected(true);
      if (onConnectionChange) onConnectionChange(true);
      setTimeout(checkStatus, 1000);
    }
  }, []);

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Linkedin className="h-6 w-6 text-blue-600" />
          LinkedIn Integration
        </CardTitle>
        <CardDescription>
          Connect your LinkedIn account to get personalized job recommendations and access to LinkedIn job search
        </CardDescription>
      </CardHeader>
      
             <CardContent className="space-y-4">
               {error && (
                 <Alert variant="destructive">
                   <XCircle className="h-4 w-4" />
                   <AlertDescription>{error}</AlertDescription>
                 </Alert>
               )}
               
               {successMessage && (
                 <Alert variant="default" className="border-green-200 bg-green-50">
                   <CheckCircle className="h-4 w-4 text-green-600" />
                   <AlertDescription className="text-green-800">{successMessage}</AlertDescription>
                 </Alert>
               )}
        
        <div className="flex items-center justify-between p-4 border rounded-lg">
          <div className="flex items-center gap-3">
            { (status.connected || justConnected) ? (
              <CheckCircle className="h-5 w-5 text-green-600" />
            ) : (
              <XCircle className="h-5 w-5 text-red-600" />
            )}
            <div>
              <p className={`font-medium ${(status.connected || justConnected) ? 'text-green-700' : ''}`}>
                {(status.connected || justConnected) ? 'LinkedIn connected successfully' : 'LinkedIn Not Connected'}
              </p>
              <p className={`text-sm ${(status.connected || justConnected) ? 'text-green-600' : 'text-muted-foreground'}`}>
                {(status.connected || justConnected) 
                  ? `Connected as LinkedIn user ${status.linkedin_id || ''}` 
                  : 'Connect to access LinkedIn job search and recommendations'
                }
              </p>
            </div>
          </div>

          <Badge className={(status.connected || justConnected) ? 'bg-green-600 text-white' : ''} variant={(status.connected || justConnected) ? 'default' : 'secondary'}>
            {(status.connected || justConnected) ? 'Connected' : 'Not Connected'}
          </Badge>
        </div>
        
        <div className="flex gap-2">
          {(status.connected || justConnected) ? (
            <>
              <Button 
                variant="outline" 
                onClick={disconnectLinkedIn}
                disabled={loading}
                className="flex-1"
              >
                {loading ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <XCircle className="h-4 w-4 mr-2" />
                )}
                Disconnect LinkedIn
              </Button>
              <Button 
                variant="outline" 
                onClick={checkStatus}
                disabled={loading}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <Button 
              id="btn-connect-linkedin"
              onClick={connectLinkedIn}
              disabled={loading}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
            >
              {loading ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Linkedin className="h-4 w-4 mr-2" />
              )}
              Connect LinkedIn
            </Button>
          )}
        </div>
      
      {(status.connected || justConnected) && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <h4 className="font-medium text-green-800 mb-2">What you can do now:</h4>
          <ul className="text-sm text-green-700 space-y-1">
            <li>• Search for jobs on LinkedIn</li>
            <li>• Get personalized job recommendations</li>
            <li>• Track application status</li>
            <li>• Access LinkedIn job details</li>
          </ul>
        </div>
      )}

      {!(status.connected || justConnected) && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="font-medium text-blue-800 mb-2">Benefits of connecting:</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Access to LinkedIn's job database</li>
            <li>• Personalized job recommendations</li>
            <li>• Direct application links</li>
            <li>• Job search with AI-powered matching</li>
          </ul>
        </div>
      )}
      </CardContent>
    </Card>
  );
}
