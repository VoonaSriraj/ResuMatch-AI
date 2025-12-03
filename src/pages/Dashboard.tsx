import { TrendingUp, Target, FileCheck, Activity, RefreshCw } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useState, useEffect } from "react";
import { api } from "@/lib/utils";

type DashboardStats = {
  total_matches: number;
  recommended_jobs: number;
  average_resume_score: number;
  active_applications: number;
  recent_activity: number;
  resume_count: number;
  job_descriptions_count: number;
  activity_trend: "up" | "down" | "neutral";
  activity_change: string;
  last_updated: string;
};

type RecentMatch = {
  id: number;
  job_title: string;
  company: string;
  match_score: number;
  status: "high" | "medium" | "low";
  date: string;
  created_at: string;
};

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentMatches, setRecentMatches] = useState<RecentMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch statistics and recent matches in parallel
      const [statsResponse, matchesResponse] = await Promise.all([
        api.get('/api/dashboard/stats'),
        api.get('/api/dashboard/recent-matches')
      ]);
      
      setStats(statsResponse);
      setRecentMatches(matchesResponse.matches || []);
      
    } catch (err: any) {
      console.error('Failed to fetch dashboard data:', err);
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const getMatchColor = (status: string) => {
    switch (status) {
      case "high": return "default";
      case "medium": return "secondary";
      case "low": return "outline";
      default: return "outline";
    }
  };

  const metrics = stats ? [
    {
      title: "Total Matches",
      value: stats.total_matches.toString(),
      change: stats.activity_change,
      icon: Target,
      trend: stats.activity_trend,
    },
    {
      title: "Recommended Jobs",
      value: stats.recommended_jobs.toString(),
      change: "+0",
      icon: TrendingUp,
      trend: "neutral" as const,
    },
    {
      title: "Resume Score",
      value: `${stats.average_resume_score}%`,
      change: "+0%",
      icon: FileCheck,
      trend: "neutral" as const,
    },
    {
      title: "Active Applications",
      value: stats.active_applications.toString(),
      change: "0 new",
      icon: Activity,
      trend: "neutral" as const,
    },
  ] : [];
  if (loading) {
    return (
      <div className="p-8 space-y-8 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Dashboard</h1>
          <p className="text-muted-foreground">Loading your career progress overview...</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-muted rounded w-3/4"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-muted rounded w-1/2 mb-2"></div>
                <div className="h-4 bg-muted rounded w-1/3"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 space-y-8 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Dashboard</h1>
          <p className="text-muted-foreground">Welcome back! Here's your career progress overview.</p>
        </div>
        <Alert variant="destructive">
          <AlertDescription>
            {error}
            <Button 
              variant="outline" 
              size="sm" 
              className="ml-2"
              onClick={fetchDashboardData}
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Dashboard</h1>
          <p className="text-muted-foreground">Welcome back! Here's your career progress overview.</p>
        </div>
        <Button 
          variant="outline" 
          size="sm"
          onClick={fetchDashboardData}
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <Card
            key={metric.title}
            className="relative overflow-hidden border-border hover:shadow-lg transition-all duration-300 hover:-translate-y-1 animate-fade-in-up"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {metric.title}
                </CardTitle>
                <metric.icon className="h-4 w-4 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline justify-between">
                <p className="text-3xl font-bold text-foreground">{metric.value}</p>
                <Badge
                  variant={metric.trend === "up" ? "default" : metric.trend === "down" ? "destructive" : "secondary"}
                  className="text-xs"
                >
                  {metric.change}
                </Badge>
              </div>
            </CardContent>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-primary" />
          </Card>
        ))}
      </div>

      <Card className="border-border shadow-md">
        <CardHeader>
          <CardTitle className="text-xl">Recent Job Matches</CardTitle>
          <CardDescription>Your latest job matching results and scores</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Job Title</TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Match Score</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentMatches.length > 0 ? (
                recentMatches.map((match) => (
                  <TableRow key={match.id} className="hover:bg-muted/50 transition-colors">
                    <TableCell className="font-medium">{match.job_title}</TableCell>
                    <TableCell className="text-muted-foreground">{match.company}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-primary transition-all duration-500"
                            style={{ width: `${match.match_score}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">{match.match_score}%</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{match.date}</TableCell>
                    <TableCell>
                      <Badge
                        variant={getMatchColor(match.status)}
                        className="capitalize"
                      >
                        {match.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No recent matches found. Upload a resume and job description to get started!
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
