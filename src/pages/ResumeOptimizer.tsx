import { useState } from "react";
import { Upload, Sparkles, CheckCircle2, AlertCircle, Target, CheckCircle2 as CheckIcon } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/utils";

export default function ResumeOptimizer() {
  const [uploaded, setUploaded] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [fileName, setFileName] = useState<string>("");
  const [missingKeywords, setMissingKeywords] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const { toast } = useToast();
  const [resumeId, setResumeId] = useState<number | null>(null);
  const [jobFileName, setJobFileName] = useState<string>("");
  // Removed JD upload in analyzer flow
  const [matchScore, setMatchScore] = useState<number | null>(null);
  const [atsFindings, setAtsFindings] = useState<string[]>([]);
  const [readabilityNotes, setReadabilityNotes] = useState<string[]>([]);
  const [strengthHighlights, setStrengthHighlights] = useState<string[]>([]);
  const [weaknesses, setWeaknesses] = useState<string[]>([]);
  const [atsScore, setAtsScore] = useState<number | null>(null);
  const [uploadedExtractedText, setUploadedExtractedText] = useState<string>("");
  const [uploadedParsedSkills, setUploadedParsedSkills] = useState<string[]>([]);
  const [uploadedParsedExperience, setUploadedParsedExperience] = useState<string[]>([]);
  const [uploadedEducation, setUploadedEducation] = useState<string[]>([]);

  const handleUploadClick = async () => {
    // Open file picker
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.doc,.docx,.txt';
    input.onchange = async (e: any) => {
      const file: File | undefined = e.target.files?.[0];
      if (!file) return;
      setAnalyzing(true);
      try {
        const form = new FormData();
        form.append('file', file);
        const res = await api.postForm('/api/resume/upload', form);
        setUploaded(true);
        setFileName(res.resume.filename || file.name);
        setResumeId(res.resume.id);
        // Show minimal AI-driven suggestions from parsed fields
        const parsedSkills: string[] = res.resume.parsed_skills || [];
        const parsedExperience: string[] = res.resume.parsed_experience || [];
        const parsedEducation: string[] = res.resume.parsed_education || [];
        const extractedText: string = res.resume.extracted_text || "";
        setUploadedParsedSkills(parsedSkills);
        setUploadedParsedExperience(parsedExperience);
        setUploadedEducation(parsedEducation);
        setUploadedExtractedText(extractedText);
        setMissingKeywords([]);
        const autoSuggestions: string[] = [];
        if (parsedSkills.length === 0) {
          autoSuggestions.push('Consider adding a focused skills section with relevant keywords.');
        }
        if (parsedExperience.length === 0) {
          autoSuggestions.push('Detail past roles with metrics (impact, scale, tech stack).');
        }
        setSuggestions(autoSuggestions.length ? autoSuggestions : [
          'Review AI-parsed skills and ensure important ones are explicit.',
        ]);
        toast({ title: 'Resume uploaded successfully!', description: 'AI analysis complete.' });
        // Auto-run analysis with fresh ID immediately
        try { await handleAnalyzeResume(res.resume.id); } catch {}
      } catch (err: any) {
        toast({ title: 'Upload failed', description: err?.message || 'Please try again', variant: 'destructive' });
      } finally {
        setAnalyzing(false);
      }
    };
    input.click();
  };

  const handleAnalyzeResume = async (overrideResumeId?: number | null) => {
    const effectiveResumeId = overrideResumeId ?? resumeId;
    if (!effectiveResumeId) {
      toast({ title: 'Resume missing', description: 'Upload a resume first', variant: 'destructive' });
      return;
    }
    setAnalyzing(true);
    try {
      // Try a resume-only insights endpoint; gracefully fallback to heuristics
      try {
        const insights = await api.get(`/api/resume/insights/${effectiveResumeId}`);
        setMissingKeywords(insights?.missing_keywords || []);
        const imp = insights?.suggestions || insights?.improvement_suggestions || [];
        const enriched = imp.length ? imp : [];
        if (!enriched.length) {
          enriched.push('Quantify achievements with concrete metrics (%, $, time saved).');
          enriched.push('Lead with strong action verbs and prioritize relevant experience.');
        }
        // Add extra role-agnostic guidance
        enriched.push('Ensure consistent formatting: titles, dates, and bullet punctuation.');
        enriched.push('Group skills by category (Languages, Frameworks, Tools) for scanability.');
        setSuggestions(Array.from(new Set(enriched)));
        setAtsFindings(insights?.ats_findings || [
          'Use standard headings and avoid images or tables.',
          'Ensure all keywords are in selectable text.',
        ]);
        setReadabilityNotes(insights?.readability || [
          'Use bullet points starting with action verbs.',
          'Target concise sentences and quantify impact.',
        ]);
        setStrengthHighlights(insights?.strengths || []);
        if (typeof insights?.overall_match_score === 'number') {
          setMatchScore(Math.round(insights.overall_match_score));
        } else if (typeof insights?.fit_score === 'number') {
          setMatchScore(Math.round(insights.fit_score));
        } else {
          setMatchScore(null);
        }
        // Derive ATS score if backend provides or compute heuristically
        const providedAts: number | undefined = insights?.ats_score;
        setAtsScore(typeof providedAts === 'number' ? Math.max(0, Math.min(100, Math.round(providedAts))) : null);
        // Build weaknesses if provided
        const backendWeaknesses: string[] = insights?.weaknesses || [];
        if (backendWeaknesses.length) setWeaknesses(backendWeaknesses);
      } catch (e) {
        // Heuristic fallback: estimate based on parsed content presence
        const basicAts = [
          'Use standard section headings (Summary, Skills, Experience, Education, Projects).',
          'Avoid images or unusual fonts; keep layout simple.',
          'Use single-column layout; ensure text is machine-readable.',
        ];
        setAtsFindings(basicAts);
        setReadabilityNotes([
          'Start bullets with action verbs (Implemented, Led, Optimized).',
          'Keep bullets concise (12–20 words) and quantify outcomes.',
          'Maintain consistent tense and formatting across sections.',
        ]);
        const dynStrengths: string[] = [];
        if ((uploadedParsedSkills || []).length >= 8) dynStrengths.push('Strong skills coverage');
        if ((uploadedParsedExperience || []).some((s) => /managed|built|implemented|optimized|led/i.test(s))) dynStrengths.push('Good action-oriented experience');
        if ((uploadedEducation || []).length > 0) dynStrengths.push('Education details present');
        if (!dynStrengths.length) dynStrengths.push('Clear baseline skills present.', 'Room to emphasize accomplishments and metrics.');
        setStrengthHighlights(dynStrengths);
        // No JD, so missing keywords unknown; leave empty.
        setMissingKeywords([]);
        const heuristicSuggestions: string[] = [];
        if ((uploadedParsedExperience || []).length < 3) heuristicSuggestions.push('Add 3–5 concise bullets per role focusing on results.');
        heuristicSuggestions.push('Quantify impact (e.g., Increased throughput by 25%).');
        heuristicSuggestions.push('Prioritize recent, relevant experience near the top.');
        if ((uploadedParsedSkills || []).length < 10) heuristicSuggestions.push('Expand the skills section with role-relevant tools and frameworks.');
        heuristicSuggestions.push('Standardize formatting: consistent dates, titles, and bullet style.');
        setSuggestions(heuristicSuggestions);
        // Weaknesses (client-side)
        const weak: string[] = [];
        if ((uploadedParsedSkills || []).length < 8) weak.push('Limited skills coverage; add more relevant tools/technologies.');
        if ((uploadedParsedExperience || []).length < 4) weak.push('Experience bullets are sparse; expand with quantified outcomes.');
        if (!/\b(\d+%|\d+\b)/.test(uploadedExtractedText || '')) weak.push('Few/no metrics detected; quantify achievements.');
        if (!/(led|mentored|owned|architected)/i.test(uploadedExtractedText || '')) weak.push('Leadership/ownership signals are weak; highlight initiatives you drove.');
        if (!/(python|java|javascript|react|node|sql|aws|azure|gcp|docker|kubernetes|ml|ai)/i.test(uploadedExtractedText || '')) weak.push('Consider listing core industry tools to pass ATS keyword filters.');
        setWeaknesses(weak);
        // ATS score heuristic based on structure richness
        const sectionsPresent = (
          (uploadedParsedSkills?.length ? 1 : 0) +
          (uploadedParsedExperience?.length ? 1 : 0) +
          (uploadedEducation?.length ? 1 : 0)
        );
        let score = 50 + (uploadedParsedSkills?.length || 0) * 3 + (uploadedParsedExperience?.length || 0) * 4 + sectionsPresent * 5;
        if ((uploadedExtractedText || '').length > 1200) score += 5;
        score = Math.max(20, Math.min(95, Math.round(score)));
        setAtsScore(score);
        // We no longer show match score for resume-only flow
        setMatchScore(null);
      }
      toast({ title: 'Resume analyzed', description: 'Insights generated for your resume.' });
    } catch (err: any) {
      toast({ title: 'Analysis failed', description: err?.message || 'Please try again', variant: 'destructive' });
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Resume Optimizer</h1>
        <p className="text-muted-foreground">
          Upload your resume and get AI-powered suggestions to improve your chances
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-border shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Upload Resume
            </CardTitle>
            <CardDescription>
              Drag and drop your resume or click to browse
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div
              className={`border-2 border-dashed rounded-lg p-12 text-center transition-all duration-300 cursor-pointer ${
                uploaded
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary hover:bg-muted/50"
              }`}
              onClick={handleUploadClick}
            >
              {analyzing ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                  <p className="text-muted-foreground">Analyzing your resume...</p>
                </div>
              ) : uploaded ? (
                <div className="flex flex-col items-center gap-3">
                  <CheckCircle2 className="h-12 w-12 text-primary" />
                  <p className="font-medium text-foreground">Resume uploaded successfully!</p>
                  <p className="text-sm text-muted-foreground">Click to upload a new version</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <Upload className="h-12 w-12 text-muted-foreground" />
                  <p className="font-medium text-foreground">Click to upload resume</p>
                  <p className="text-sm text-muted-foreground">PDF, DOC, or DOCX (max 5MB)</p>
                </div>
              )}
            </div>

            {uploaded && (
              <div className="space-y-3 animate-fade-in-up">
                <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <span className="text-sm font-medium">{fileName || 'resume'}</span>
                  <Badge variant="default">Analyzed</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Button className="w-full bg-gradient-primary hover:opacity-90 transition-opacity" onClick={handleAnalyzeResume} disabled={analyzing}>
                    <Sparkles className="h-4 w-4 mr-2" />
                    {analyzing ? 'Analyzing…' : 'Analyze Resume'}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Missing Keywords card removed per requirement */}
      </div>

      {/* Hide large suggestions block per updated requirement */}

      {uploaded && atsScore !== null && (
        <Card className="border-border shadow-lg animate-fade-in-up" style={{ animationDelay: "200ms" }}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckIcon className="h-5 w-5 text-success" />
              ATS Score
            </CardTitle>
            <CardDescription>How well your resume adheres to ATS best practices</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex-1"><Progress value={atsScore} className="h-3" /></div>
              <div className="text-3xl font-bold text-primary">{atsScore}%</div>
            </div>
          </CardContent>
        </Card>
      )}

        {uploaded && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border-border shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Strengths
              </CardTitle>
              <CardDescription>What your resume does well</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {strengthHighlights.map((s, i) => (
                  <Badge key={`str-${i}`} variant="secondary" className="text-sm">{s}</Badge>
                ))}
                {strengthHighlights.length === 0 && (
                  <p className="text-sm text-muted-foreground">No specific strengths detected yet.</p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-border shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-warning" />
                Weaknesses
            </CardTitle>
              <CardDescription>Areas to improve next</CardDescription>
          </CardHeader>
          <CardContent>
              <ul className="list-disc pl-6 space-y-1 text-sm text-muted-foreground">
                {weaknesses.map((w, i) => (
                  <li key={`weak-${i}`}>{w}</li>
                ))}
                {weaknesses.length === 0 && (
                  <li>No critical weaknesses detected.</li>
                )}
              </ul>
          </CardContent>
        </Card>
        </div>
      )}

      {/* Removed duplicate strengths section */}
    </div>
  );
}
