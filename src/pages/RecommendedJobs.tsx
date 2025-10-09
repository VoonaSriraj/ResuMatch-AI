import { ExternalLink, MapPin, Briefcase, TrendingUp, Upload } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useEffect, useState } from "react";
import { api } from "@/lib/utils";

type JobItem = {
  id: number;
  title: string;
  company: string;
  location?: string;
  match_score?: number;
  apply_link?: string;
  job_type?: string;
  posted_date?: string;
};

const getMatchColor = (score: number) => {
  if (score >= 85) return "default";
  if (score >= 70) return "secondary";
  return "outline";
};

export default function RecommendedJobs() {
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [uploading, setUploading] = useState(false);

  const refresh = async () => {
    // If LinkedIn not connected, we can at least load stored recommendations (may be empty)
    const res = await api.get('/api/recommendations/recommended');
    setJobs(res.jobs || []);
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
    try {
      const res = await api.postJson('/api/recommendations/search', { limit: 25 });
      setJobs(res.jobs || []);
    } catch (e) {
      // ignore, backend will enforce LinkedIn connection
    }
  };

  useEffect(() => {
    refresh().catch(() => {});
  }, []);
  return (
    <div className="p-8 space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Recommended Jobs</h1>
          <p className="text-muted-foreground">
            Personalized job matches based on your resume and preferences
          </p>
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
        <Button className="gap-2 bg-gradient-primary" onClick={handleRecommendJobs}>
          <TrendingUp className="h-4 w-4" />
          Recommend Jobs
        </Button>
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
                  {job.location}
                </div>
                {job.job_type && <Badge variant="outline">{job.job_type}</Badge>}
              </div>

              <div className="flex items-center justify-between text-sm">
                <span />
                <span className="text-muted-foreground">{job.posted_date ? new Date(job.posted_date).toDateString() : ''}</span>
              </div>

              <div className="pt-2">
                <Button
                  className="w-full bg-gradient-primary hover:opacity-90 transition-opacity"
                  onClick={() => job.apply_link && window.open(job.apply_link, "_blank")}
                >
                  Apply on LinkedIn
                  <ExternalLink className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
