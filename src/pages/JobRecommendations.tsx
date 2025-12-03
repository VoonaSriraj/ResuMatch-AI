import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ExternalLink, MapPin, Briefcase, TrendingUp, RefreshCw } from "lucide-react";
import { api } from "@/lib/utils";

type JobRecommendation = {
  id: number;
  title: string;
  company: string;
  location?: string;
  description?: string;
  linkedin_url?: string;
  match_score: number;
  posted_at?: string;
  job_type?: string;
  seniority_level?: string;
  salary_range?: string;
  remote_friendly?: string;
  skills_required?: string[];
  source: string;
};

type JobRecommendationsResponse = {
  jobs: JobRecommendation[];
  total_count: number;
  user_profile_updated: boolean;
};

const getMatchColor = (score: number) => {
  if (score >= 85) return "default";
  if (score >= 70) return "secondary";
  return "outline";
};

export default function JobRecommendations() {
  const [jobs, setJobs] = useState<JobRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [profileUpdated, setProfileUpdated] = useState(false);

  const fetchRecommendations = async (forceRefresh = false) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.postJson<JobRecommendationsResponse>('/api/jobs/recommendations', {
        limit: 10,
        force_refresh: forceRefresh
      });
      
      setJobs(response.jobs || []);
      setTotalCount(response.total_count || 0);
      setProfileUpdated(response.user_profile_updated || false);
      
    } catch (err: any) {
      console.error('Failed to get job recommendations:', err);
      setError(err.message || 'Failed to get job recommendations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const refreshRecommendations = () => {
    fetchRecommendations(true);
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">AI-Powered Job Recommendations</h1>
          <p className="text-muted-foreground">
            Personalized job matches ranked by AI based on your resume and profile
          </p>
          {profileUpdated && (
            <div className="mt-2 text-sm text-green-600">
              ✅ Profile updated from latest resume
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => fetchRecommendations(false)}
            disabled={loading}
            className="gap-2"
          >
            <TrendingUp className="h-4 w-4" />
            Refresh
          </Button>
          <Button 
            onClick={refreshRecommendations}
            disabled={loading}
            className="gap-2 bg-gradient-primary"
          >
            {loading ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Force Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Fetching personalized job recommendations...</p>
          </div>
        </div>
      )}

      {!loading && jobs.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-xl font-semibold mb-2">No Job Recommendations Yet</h3>
          <p className="text-muted-foreground mb-4">
            Upload your resume and click "Force Refresh" to get AI-powered job recommendations.
          </p>
        </div>
      )}

      {!loading && jobs.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold">
              Found {jobs.length} Job Recommendations
              {totalCount > jobs.length && ` (${totalCount} total)`}
            </h2>
            <div className="text-sm text-muted-foreground">
              Ranked by AI match score
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
                    <Badge variant={getMatchColor(Math.round(job.match_score))} className="text-lg px-3 py-1">
                      {Math.round(job.match_score)}%
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

                  {job.skills_required && job.skills_required.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {job.skills_required.slice(0, 5).map((skill, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                      {job.skills_required.length > 5 && (
                        <Badge variant="secondary" className="text-xs">
                          +{job.skills_required.length - 5} more
                        </Badge>
                      )}
                    </div>
                  )}

                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{job.source}</Badge>
                      <Badge variant="outline">{job.job_type}</Badge>
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
