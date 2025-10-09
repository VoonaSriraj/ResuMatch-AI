import { useState } from "react";
import { ArrowRight, Target, Sparkles, Upload, AlertCircle, Scale, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/utils";

export default function JobMatch() {
  const [matchScore, setMatchScore] = useState<number | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobDescFile, setJobDescFile] = useState<File | null>(null);
  const [missingKeywords, setMissingKeywords] = useState<string[]>([]);
  const [improvementSuggestions, setImprovementSuggestions] = useState<string[]>([]);
  const [atsFindings, setAtsFindings] = useState<string[]>([]);
  const [readabilityNotes, setReadabilityNotes] = useState<string[]>([]);
  const [strengthHighlights, setStrengthHighlights] = useState<string[]>([]);
  const [jobTitle, setJobTitle] = useState<string>("");

  // Optional: compare against a second resume
  const [secondaryResumeFile, setSecondaryResumeFile] = useState<File | null>(null);
  const [secondaryMatchScore, setSecondaryMatchScore] = useState<number | null>(null);
  const [comparisonMissing, setComparisonMissing] = useState<{ primaryOnly: string[]; secondaryOnly: string[] }>({ primaryOnly: [], secondaryOnly: [] });
  const { toast } = useToast();

  const handleAnalyze = async () => {
    if (!resumeFile || !jobDescFile) {
      toast({
        title: "Missing files",
        description: "Please upload both resume and job description.",
        variant: "destructive",
      });
      return;
    }
    setAnalyzing(true);
    try {
      // 1) Upload resume -> get resume.id
      const resumeForm = new FormData();
      resumeForm.append('file', resumeFile);
      const resumeRes = await api.postForm('/api/resume/upload', resumeForm);
      const resumeId = resumeRes?.resume?.id;

      // 2) Upload job -> get job.id
      const jobForm = new FormData();
      jobForm.append('file', jobDescFile);
      const jobRes = await api.postForm('/api/job/upload', jobForm);
      const jobId = jobRes?.job?.id;
      setJobTitle(jobRes?.job?.title || "");

      // 3) Calculate match
      const match = await api.postJson('/api/match/calculate', { resume_id: resumeId, job_id: jobId });
      setMatchScore(Math.round(match.overall_match_score));
      setMissingKeywords(match.missing_keywords || []);
      setImprovementSuggestions(match.suggestions || []);
      setAtsFindings(match.ats_findings || [
        'Use standard section headings (Summary, Skills, Experience, Education, Projects).',
        'Avoid images, text boxes, and unusual fonts; keep to simple PDF or DOCX.',
        'Ensure keywords appear in plain text (not inside graphics).',
      ]);
      setReadabilityNotes(match.readability || [
        'Prefer bullet points with action verbs (Implemented, Led, Optimized).',
        'Use concise sentences (12–20 words) and consistent tense.',
        'Quantify impact (e.g., Increased throughput by 25%).',
      ]);
      setStrengthHighlights(match.strengths || (
        (match.overall_match_score >= 70)
          ? ['Strong alignment with required skills.', 'Good coverage of experience relevant to the role.']
          : ['Clear baseline skills present.', 'Room to emphasize accomplishments and metrics.']
      ));
      toast({ title: 'Analysis complete!', description: `Your match score is ${Math.round(match.overall_match_score)}%.` });

      // 4) If a secondary resume is provided, run comparison
      if (secondaryResumeFile) {
        const secondaryForm = new FormData();
        secondaryForm.append('file', secondaryResumeFile);
        const secondaryRes = await api.postForm('/api/resume/upload', secondaryForm);
        const secondaryId = secondaryRes?.resume?.id;
        const match2 = await api.postJson('/api/match/calculate', { resume_id: secondaryId, job_id: jobId });
        setSecondaryMatchScore(Math.round(match2.overall_match_score));
        const missing2: string[] = match2.missing_keywords || [];
        const primaryOnly = (match.missing_keywords || []).filter((kw: string) => !(missing2 || []).includes(kw));
        const secondaryOnly = (missing2 || []).filter((kw: string) => !(match.missing_keywords || []).includes(kw));
        setComparisonMissing({ primaryOnly, secondaryOnly });
      } else {
        setSecondaryMatchScore(null);
        setComparisonMissing({ primaryOnly: [], secondaryOnly: [] });
      }
    } catch (err: any) {
      toast({ title: 'Analysis failed', description: err?.message || 'Please try again', variant: 'destructive' });
    } finally {
      setAnalyzing(false);
    }
  };

  const optimizations = [
    {
      category: "Need of improvements",
      suggestions: improvementSuggestions.length ? improvementSuggestions : [],
    },
  ];

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Job Match Analyzer</h1>
        <p className="text-muted-foreground">
          Compare your resume against job descriptions to see how well you match
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-border shadow-lg">
          <CardHeader>
            <CardTitle>Your Resume</CardTitle>
            <CardDescription>Upload your resume (PDF format)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center min-h-[300px] border-2 border-dashed border-border rounded-lg p-8 hover:border-primary/50 transition-colors">
              <Upload className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Upload Resume</h3>
              <p className="text-sm text-muted-foreground mb-4">PDF files only</p>
              <Input
                type="file"
                accept=".pdf"
                onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                className="max-w-xs"
              />
              {resumeFile && (
                <p className="mt-4 text-sm text-primary font-medium">
                  Selected: {resumeFile.name}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-lg">
          <CardHeader>
            <CardTitle>Job Description</CardTitle>
            <CardDescription>Upload the job posting (PDF format)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center min-h-[300px] border-2 border-dashed border-border rounded-lg p-8 hover:border-primary/50 transition-colors">
              <Upload className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Upload Job Description</h3>
              <p className="text-sm text-muted-foreground mb-4">PDF files only</p>
              <Input
                type="file"
                accept=".pdf"
                onChange={(e) => setJobDescFile(e.target.files?.[0] || null)}
                className="max-w-xs"
              />
              {jobDescFile && (
                <p className="mt-4 text-sm text-primary font-medium">
                  Selected: {jobDescFile.name}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Optional second resume for comparison */}
      <Card className="border-border shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Scale className="h-5 w-5" />
            Compare With Another Resume (optional)
          </CardTitle>
          <CardDescription>Upload a second resume to see which one fits better</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center border-2 border-dashed border-border rounded-lg p-6 hover:border-primary/50 transition-colors">
            <Input
              type="file"
              accept=".pdf"
              onChange={(e) => setSecondaryResumeFile(e.target.files?.[0] || null)}
              className="max-w-xs"
            />
            {secondaryResumeFile && (
              <p className="mt-3 text-sm text-primary font-medium">Selected: {secondaryResumeFile.name}</p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-center">
        <Button
          size="lg"
          className="bg-gradient-primary hover:opacity-90 transition-opacity px-8"
          onClick={handleAnalyze}
          disabled={analyzing}
        >
          {analyzing ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              Analyzing...
            </>
          ) : (
            <>
              <Target className="h-5 w-5 mr-2" />
              Analyze Match
              <ArrowRight className="h-5 w-5 ml-2" />
            </>
          )}
        </Button>
      </div>

      {matchScore !== null && (
        <Card className="border-border shadow-xl animate-scale-in">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-6 w-6 text-primary" />
              Match Score
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <Progress value={matchScore} className="h-4" />
              </div>
              <div className="text-4xl font-bold text-primary">{matchScore}%</div>
            </div>

            {secondaryMatchScore !== null && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-gradient-card rounded-lg border border-border">
                  <p className="text-sm text-muted-foreground mb-1">Primary Resume</p>
                  <p className="text-2xl font-bold text-foreground">{matchScore}%</p>
                </div>
                <div className="p-4 bg-gradient-card rounded-lg border border-border">
                  <p className="text-sm text-muted-foreground mb-1">Secondary Resume</p>
                  <p className="text-2xl font-bold text-foreground">{secondaryMatchScore}%</p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-gradient-card rounded-lg border border-border">
                <p className="text-sm text-muted-foreground mb-1">Skills Match</p>
                <p className="text-2xl font-bold text-foreground">82%</p>
              </div>
              <div className="p-4 bg-gradient-card rounded-lg border border-border">
                <p className="text-sm text-muted-foreground mb-1">Experience Match</p>
                <p className="text-2xl font-bold text-foreground">91%</p>
              </div>
              <div className="p-4 bg-gradient-card rounded-lg border border-border">
                <p className="text-sm text-muted-foreground mb-1">Keyword Match</p>
                <p className="text-2xl font-bold text-foreground">88%</p>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-warning" />
                Identify Missing Keywords
              </h3>
              <div className="flex flex-wrap gap-2">
                {missingKeywords.map((kw, i) => (
                  <Badge key={`${kw}-${i}`} variant="secondary" className="text-sm">
                    {kw}
                  </Badge>
                ))}
                {missingKeywords.length === 0 && (
                  <p className="text-sm text-muted-foreground">No critical keywords missing.</p>
                )}
              </div>
              {secondaryMatchScore !== null && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3 rounded-lg border border-border">
                    <p className="text-sm font-medium mb-2">Missing only in Primary</p>
                    <div className="flex flex-wrap gap-2">
                      {comparisonMissing.primaryOnly.map((kw) => (
                        <Badge key={`p-${kw}`} variant="outline" className="text-sm">{kw}</Badge>
                      ))}
                      {comparisonMissing.primaryOnly.length === 0 && (
                        <p className="text-sm text-muted-foreground">No differences found.</p>
                      )}
                    </div>
                  </div>
                  <div className="p-3 rounded-lg border border-border">
                    <p className="text-sm font-medium mb-2">Missing only in Secondary</p>
                    <div className="flex flex-wrap gap-2">
                      {comparisonMissing.secondaryOnly.map((kw) => (
                        <Badge key={`s-${kw}`} variant="outline" className="text-sm">{kw}</Badge>
                      ))}
                      {comparisonMissing.secondaryOnly.length === 0 && (
                        <p className="text-sm text-muted-foreground">No differences found.</p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Need of improvements
              </h3>
              {optimizations.map((opt, index) => (
                <Card
                  key={opt.category}
                  className="border-border animate-fade-in-up"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">{opt.category}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {opt.suggestions.length ? (
                      <ul className="space-y-2">
                        {opt.suggestions.map((suggestion, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm">
                            <Badge variant="default" className="mt-0.5 shrink-0">
                              {i + 1}
                            </Badge>
                            <span className="text-muted-foreground">{suggestion}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-muted-foreground">No improvements suggested by AI.</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* ATS Friendliness */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-success" />
                ATS Friendliness
              </h3>
              <ul className="list-disc pl-6 space-y-1 text-sm text-muted-foreground">
                {atsFindings.map((tip, i) => (
                  <li key={`ats-${i}`}>{tip}</li>
                ))}
              </ul>
            </div>

            {/* Resume Structure & Readability */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-warning" />
                Structure & Readability
              </h3>
              <ul className="list-disc pl-6 space-y-1 text-sm text-muted-foreground">
                {readabilityNotes.map((tip, i) => (
                  <li key={`read-${i}`}>{tip}</li>
                ))}
              </ul>
            </div>

            {/* Strengths / Highlights */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Strengths & Highlights
              </h3>
              <div className="flex flex-wrap gap-2">
                {strengthHighlights.map((s, i) => (
                  <Badge key={`str-${i}`} variant="secondary" className="text-sm">{s}</Badge>
                ))}
                {strengthHighlights.length === 0 && (
                  <p className="text-sm text-muted-foreground">No specific strengths detected yet.</p>
                )}
              </div>
            </div>

            {/* Custom Suggestions */}
            <div className="space-y-2">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Custom Suggestions{jobTitle ? ` for ${jobTitle}` : ''}
              </h3>
              <p className="text-sm text-muted-foreground">
                Tailored tips based on role and seniority: emphasize domain-specific keywords, ensure recent experience is prioritized, and quantify outcomes.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
