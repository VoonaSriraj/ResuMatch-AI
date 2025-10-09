import { TrendingUp, Target, FileCheck, Activity } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

const metrics = [
  {
    title: "Total Matches",
    value: "24",
    change: "+12%",
    icon: Target,
    trend: "up",
  },
  {
    title: "Recommended Jobs",
    value: "18",
    change: "+5",
    icon: TrendingUp,
    trend: "up",
  },
  {
    title: "Resume Score",
    value: "85%",
    change: "+8%",
    icon: FileCheck,
    trend: "up",
  },
  {
    title: "Active Applications",
    value: "6",
    change: "2 new",
    icon: Activity,
    trend: "neutral",
  },
];

const recentMatches = [
  { id: 1, job: "Senior Frontend Developer", company: "TechCorp", date: "2 hours ago", score: 92, status: "high" },
  { id: 2, job: "Full Stack Engineer", company: "StartupXYZ", date: "5 hours ago", score: 88, status: "high" },
  { id: 3, job: "React Developer", company: "InnovateLab", date: "1 day ago", score: 75, status: "medium" },
  { id: 4, job: "UI/UX Engineer", company: "DesignCo", date: "2 days ago", score: 68, status: "medium" },
  { id: 5, job: "Software Engineer", company: "GlobalTech", date: "3 days ago", score: 82, status: "high" },
];

export default function Dashboard() {
  return (
    <div className="p-8 space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back! Here's your career progress overview.</p>
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
                  variant={metric.trend === "up" ? "default" : "secondary"}
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
              {recentMatches.map((match) => (
                <TableRow key={match.id} className="hover:bg-muted/50 transition-colors">
                  <TableCell className="font-medium">{match.job}</TableCell>
                  <TableCell className="text-muted-foreground">{match.company}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-primary transition-all duration-500"
                          style={{ width: `${match.score}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium">{match.score}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{match.date}</TableCell>
                  <TableCell>
                    <Badge
                      variant={match.status === "high" ? "default" : "secondary"}
                      className="capitalize"
                    >
                      {match.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
