import { useState } from "react";
import { Upload, Sparkles, MessageSquare, Lightbulb } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/utils";

export default function InterviewPrep() {
  const [jobDescFile, setJobDescFile] = useState<File | null>(null);
  const [questions, setQuestions] = useState<string[]>([]);
  const [generating, setGenerating] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string[]>>({});
  const { toast } = useToast();

  const handleGenerate = async () => {
    if (!jobDescFile) {
      toast({
        title: "Missing file",
        description: "Please upload a job description first.",
        variant: "destructive",
      });
      return;
    }
    setGenerating(true);
    try {
      // 1) Upload job description text to parse and store -> get job.id
      const form = new FormData();
      form.append('file', jobDescFile);
      const jobRes = await api.postForm('/api/job/upload', form);
      const jobId = jobRes?.job?.id;

      // 2) Generate interview questions using job_id
      const gen = await api.postJson('/api/interview/generate', { job_id: jobId });
      const list: string[] = [
        ...(gen.technical_questions || []),
        ...(gen.behavioral_questions || []),
        ...(gen.company_culture_questions || []),
        ...(gen.leadership_questions || []),
      ].slice(0, 12);
      setQuestions(list);
      // Also ask backend for suggested answers for first few questions using a generic experience context in dev
      const answered: Record<string, string[]> = {};
      const genericExp = '5 years building web apps with React/Node, led small teams, delivered features end-to-end.';
      await Promise.all(list.slice(0, 5).map(async (q) => {
        try {
          const res = await api.postJson('/api/interview/answer-suggestions', {
            question: q,
            user_experience: genericExp,
            job_context: {}
          });
          const r = res?.result;
          answered[q] = [
            ...(r?.key_points || []),
            ...(r?.tailoring_tips || [])
          ].slice(0, 5);
        } catch {}
      }));
      setAnswers(answered);
      toast({ title: 'Interview questions generated!', description: `${list.length} questions ready.` });
    } catch (err: any) {
      toast({ title: 'Generation failed', description: err?.message || 'Please try again', variant: 'destructive' });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">AI Interview Prep</h1>
        <p className="text-muted-foreground">
          Generate tailored interview questions based on job descriptions
        </p>
      </div>

      <Card className="border-border shadow-lg">
        <CardHeader>
          <CardTitle>Upload Job Description</CardTitle>
          <CardDescription>Upload PDF or Word document</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center min-h-[300px] border-2 border-dashed border-border rounded-lg p-8 hover:border-primary/50 transition-colors">
            <Upload className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Upload Job Description</h3>
            <p className="text-sm text-muted-foreground mb-4">PDF or Word files (.pdf, .doc, .docx)</p>
            <Input
              type="file"
              accept=".pdf,.doc,.docx"
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

      <div className="flex justify-center">
        <Button
          size="lg"
          className="bg-gradient-primary hover:opacity-90 transition-opacity px-8"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="h-5 w-5 mr-2" />
              Generate Interview Questions
            </>
          )}
        </Button>
      </div>

      {questions.length > 0 && (
        <Card className="border-border shadow-xl animate-scale-in">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-6 w-6 text-primary" />
              Generated Interview Questions
            </CardTitle>
            <CardDescription>
              Practice these questions to prepare for your interview
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {questions.map((question, index) => (
              <Card
                key={index}
                className="border-border animate-fade-in-up"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <CardContent className="pt-6">
                  <div className="flex gap-4">
                    <Badge className="shrink-0 h-8 w-8 rounded-full flex items-center justify-center">
                      {index + 1}
                    </Badge>
                    <div className="space-y-2">
                      <p className="text-foreground">{question}</p>
                      {answers[question]?.length ? (
                        <div className="pl-6 space-y-1">
                          {answers[question].map((tip, i) => (
                            <div key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                              <Lightbulb className="h-4 w-4 mt-0.5 text-primary" />
                              <span>{tip}</span>
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
