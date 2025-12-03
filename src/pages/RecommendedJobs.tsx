import { ExternalLink, MapPin, Briefcase, TrendingUp, Upload, Linkedin } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useEffect, useState } from "react";
import { api } from "@/lib/utils";
import LinkedInConnection from "@/components/LinkedInConnection";

type JobItem = {
  id: number;
  title: string;
  company: string;
  location?: string;
  description?: string;
  match_score?: number;
  linkedin_url?: string;
  source?: string;
  salary_range?: string;
  job_type?: string;
  seniority_level?: string;
  remote_friendly?: string;
  posted_at?: string;
  skills_required?: string[];
};

const getMatchColor = (score: number) => {
  if (score >= 85) return "default";
  if (score >= 70) return "secondary";
  return "outline";
};

export default function RecommendedJobs() {
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [linkedinConnected, setLinkedinConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [linkedinMessage, setLinkedinMessage] = useState<string | null>(null);

  const refresh = async () => {
    try {
      // Load stored recommendations
      const res = await api.get('/api/jobs/recommendations');
      setJobs(res.jobs || []);
      setError(null);
    } catch (err) {
      console.error('Failed to refresh:', err);
      setError('Failed to load job recommendations');
    }
  };

  const handleLinkedInConnectionChange = (connected: boolean) => {
    setLinkedinConnected(connected);
    if (connected) {
      setLinkedinMessage('LinkedIn connected successfully!');
      // Clear any existing error messages
      setError(null);
    }
  };

  const handleUploadResume = async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.doc,.docx,.txt';
    input.onchange = async (e: any) => {
      const file: File | undefined = e.target.files?.[0];
      if (!file) return;
      setUploading(true);
      try {
        const form = new FormData();
        form.append('file', file);
        await api.postForm('/api/resume/upload', form);
        await refresh();
      } catch (e) {
        // ignore UI error toast here; RecommendedJobs is secondary upload path
      } finally {
        setUploading(false);
      }
    };
    input.click();
  };

  const handleRecommendJobs = async () => {
    // Allow recommendations even without LinkedIn; backend will use resume/profile data
    try {
      setError(null);
      setLoading(true);
      const res = await api.postJson('/api/jobs/recommendations', { 
        keywords: [],
        location: null,
        limit: 25,
        force_refresh: true
      });
      setJobs(res.jobs || []);
      
      // Show success message
      if (res.jobs && res.jobs.length > 0) {
        setLinkedinMessage(`Found ${res.jobs.length} job recommendations! ${res.user_profile_updated ? 'Profile updated with resume data.' : 'Upload a resume for better matching.'}`);
      }
    } catch (err: any) {
      console.error('Failed to get job recommendations:', err);
      setError(err.message || 'Failed to get job recommendations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check for LinkedIn callback parameters
    const urlParams = new URLSearchParams(window.location.search);
    const linkedinStatus = urlParams.get('linkedin');
    const message = urlParams.get('message');
    
    if (linkedinStatus === 'connected') {
      setLinkedinMessage('LinkedIn connected successfully!');
      setLinkedinConnected(true);
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (linkedinStatus === 'error') {
      setLinkedinMessage(`LinkedIn connection failed: ${message || 'Unknown error'}`);
      setLinkedinConnected(false);
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    // Load existing job recommendations
    refresh().catch(() => {});
  }, []);
  return (
    <div className="p-8 space-y-8 animate-fade-in">
             <div className="flex items-center justify-between">
               <div>
                 <h1 className="text-3xl font-bold text-foreground mb-2">Recommended Jobs</h1>
                 <p className="text-muted-foreground">
                   Personalized job matches based on your resume and LinkedIn profile
                 </p>
                 {linkedinConnected && (
                   <div className="mt-2 flex items-center gap-2 text-green-600">
                     <Linkedin className="h-4 w-4" />
                     <span className="text-sm font-medium">LinkedIn Connected</span>
                   </div>
                 )}
               </div>
        <div className="flex gap-2">
        <Button variant="outline" className="gap-2" onClick={() => refresh()}>
          <TrendingUp className="h-4 w-4" />
          Refresh Matches
        </Button>
        <Button variant="outline" className="gap-2" onClick={handleUploadResume} disabled={uploading}>
          <Upload className="h-4 w-4" />
          {uploading ? 'Uploading…' : 'Upload Resume'}
        </Button>
        <Button 
          className="gap-2 bg-gradient-primary" 
          onClick={() => { handleRecommendJobs(); }}
          disabled={loading}
        >
          <Linkedin className="h-4 w-4" />
          {loading ? 'Searching Jobs...' : 'Get Job Recommendations'}
        </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {linkedinMessage && (
        <Alert 
          variant="default"
          className={(linkedinMessage.toLowerCase().includes('fail') || linkedinMessage.toLowerCase().includes('error')) 
            ? '' 
            : 'border-green-200 bg-green-50'}
        >
          <AlertDescription className={(linkedinMessage.toLowerCase().includes('fail') || linkedinMessage.toLowerCase().includes('error')) 
            ? '' 
            : 'text-green-700'}>
            {linkedinMessage}
          </AlertDescription>
        </Alert>
      )}

      {/* LinkedIn Connection Component */}
      <LinkedInConnection onConnectionChange={handleLinkedInConnectionChange} />

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Searching for job recommendations...</p>
          </div>
        </div>
      )}

      {!loading && jobs.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-xl font-semibold mb-2">No Job Recommendations Yet</h3>
          <p className="text-muted-foreground mb-4">
            {linkedinConnected 
              ? 'Click "Get LinkedIn Jobs" to find personalized job matches. Upload your resume for better matching!'
              : 'Connect your LinkedIn account and click "Get LinkedIn Jobs" to find personalized job matches.'
            }
          </p>
          <div className="flex flex-col sm:flex-row gap-2 justify-center items-center">
            {!linkedinConnected && (
              <p className="text-sm text-muted-foreground">
                Step 1: Connect LinkedIn
              </p>
            )}
            {linkedinConnected && (
              <>
                <p className="text-sm text-green-600">✓ LinkedIn Connected</p>
                <p className="text-sm text-muted-foreground">Step 2: Upload Resume (Optional but recommended)</p>
                <p className="text-sm text-muted-foreground">Step 3: Get Job Recommendations</p>
              </>
            )}
          </div>
        </div>
      )}

      {!loading && jobs.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold">Found {jobs.length} Job Recommendations</h2>
            <div className="text-sm text-muted-foreground">
              Sorted by match score
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {jobs.map((job, index) => (
          <Card
            key={job.id}
            className="border-border hover:shadow-xl transition-all duration-300 hover:-translate-y-1 animate-fade-in-up"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <CardTitle className="text-xl mb-2">{job.title}</CardTitle>
                  <CardDescription className="flex items-center gap-2 text-base">
                    <Briefcase className="h-4 w-4" />
                    {job.company}
                  </CardDescription>
                </div>
                <Badge variant={getMatchColor(Math.round(job.match_score || 0))} className="text-lg px-3 py-1">
                  {Math.round(job.match_score || 0)}%
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <MapPin className="h-4 w-4" />
                  {job.location || 'Location not specified'}
                </div>
                {job.seniority_level && <Badge variant="outline">{job.seniority_level}</Badge>}
                {job.remote_friendly && <Badge variant="outline">{job.remote_friendly}</Badge>}
              </div>

                         {job.salary_range && (
                           <div className="text-sm text-green-600 font-medium">
                             💰 {job.salary_range}
                           </div>
                         )}

              {job.description && (
                <div className="text-sm text-muted-foreground line-clamp-3">
                  {job.description.substring(0, 200)}...
                </div>
              )}

                         <div className="flex items-center justify-between text-sm">
                           <div className="flex items-center gap-2">
                             {job.source && <Badge variant="secondary">{job.source}</Badge>}
                             {job.skills_required && job.skills_required.length > 0 && (
                               <Badge variant="outline">{job.skills_required.length} skills</Badge>
                             )}
                           </div>
                           <span className="text-muted-foreground">
                             {job.posted_at ? new Date(job.posted_at).toLocaleDateString() : 'Recently'}
                           </span>
                         </div>

              <div className="pt-2">
                <Button
                  className="w-full bg-gradient-primary hover:opacity-90 transition-opacity"
                  onClick={() => job.linkedin_url && window.open(job.linkedin_url, "_blank")}
                  disabled={!job.linkedin_url}
                >
                  {job.linkedin_url ? 'Apply on LinkedIn' : 'Apply Link Not Available'}
                  <ExternalLink className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
