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
  const [qaPairs, setQaPairs] = useState<{ question: string; sample_answer: string }[]>([]);
  const [answerText, setAnswerText] = useState<Record<string, string>>({});
  const [extracted, setExtracted] = useState<{ core_skills?: string[]; languages?: string[]; tools_frameworks?: string[]; key_responsibilities?: string[] }>({});
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
      const uploadedSkills: string[] = Array.isArray(jobRes?.job?.extracted_skills) ? jobRes.job.extracted_skills.filter(Boolean) : [];

      // 2) Generate technical questions WITH AI answers in one call
      const gen = await api.postJson('/api/interview/generate-with-answers', { job_id: jobId });
      const items: { question: string; key_points?: string[]; tailoring_tips?: string[]; answer_text?: string }[] = gen.items || [];
      let list: string[] = items.map(it => it.question).filter(Boolean).slice(0, 12);
      // If backend produced none, synthesize from uploaded skills
      if (!list.length && uploadedSkills.length) {
        list = Array.from(new Set(uploadedSkills))
          .slice(0, 12)
          .map((s: string) => `Describe your hands-on experience with ${s}. What challenges did you face and how did you solve them?`);
      }
      setQuestions(list);
      // Map AI bullets and paragraphs directly from response
      const fromItemsBullets: Record<string, string[]> = {};
      const fromItemsText: Record<string, string> = {};
      for (const it of items) {
        if (it.question) {
          const b = [...(it.key_points || []), ...(it.tailoring_tips || [])].filter(Boolean).slice(0,5);
          if (b.length) fromItemsBullets[it.question] = b;
          if (it.answer_text) fromItemsText[it.question] = it.answer_text;
        }
      }
      setAnswers(fromItemsBullets);
      setAnswerText(fromItemsText);

      // If some questions are still missing answers, call per-question suggestions as a fallback
      const missing = list.filter(q => !fromItemsText[q] && !(fromItemsBullets[q]?.length));
      if (missing.length) {
        const answered: Record<string, string[]> = {};
        await Promise.all(missing.map(async (q) => {
          try {
            const res = await api.postJson('/api/interview/answer-suggestions', {
              question: q,
              user_experience: '',
              job_id: jobId,
              job_context: gen?.job_context || {}
            });
            const r = res?.result;
            const pts: string[] = [ ...(r?.key_points || []) ];
            const tips: string[] = [ ...(r?.tailoring_tips || []) ];
            const merged = [...pts, ...tips].filter(Boolean).slice(0, 5);
            if (merged.length) answered[q] = merged;
            const structure: string = r?.answer_structure || '';
            const kp = (r?.key_points || []).slice(0, 3);
            const para = [structure, ...kp].filter(Boolean).join(' ');
            if (para) setAnswerText(prev => ({ ...prev, [q]: para }));
          } catch (e) {
            console.warn('fallback answer-suggestions failed', q, e);
          }
        }));
        if (Object.keys(answered).length) setAnswers(prev => ({ ...prev, ...answered }));
      }

      // 3) Generate Q&A pairs (10–15) tailored to the JD
      try {
        const qa = await api.postJson('/api/interview/generate-qa', { job_id: jobId });
        setQaPairs(qa.qa || []);
        setExtracted(qa.extracted || {});
        // Map best-matching sample answers to our generated questions as a fallback
        const qaList: { question: string; sample_answer: string }[] = qa.qa || [];
        if (qaList.length) {
          const toWords = (s: string) => new Set((s || '').toLowerCase().replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).filter(Boolean));
          const jaccard = (a: Set<string>, b: Set<string>) => {
            const inter = new Set([...a].filter(x => b.has(x))).size;
            const uni = new Set([...a, ...b]).size || 1;
            return inter / uni;
          };
          const textMap: Record<string, string> = {};
          const qaTokens = qaList.map(q => ({ q, tokens: toWords(q.question) }));
          for (const q of list) {
            let best = { score: 0, ans: '' };
            const qTok = toWords(q);
            for (const item of qaTokens) {
              const s = jaccard(qTok, item.tokens);
              if (s > best.score) best = { score: s, ans: item.q.sample_answer };
            }
            if (best.ans) {
              if (best.score >= 0.2) textMap[q] = best.ans; // lower threshold
            }
            // If still no mapping, fallback to the first QA sample answer
            if (!textMap[q] && qaList[0]?.sample_answer) {
              textMap[q] = qaList[0].sample_answer;
            }
          }
          setAnswerText(textMap);

          // Do not synthesize bullets; rely only on AI-provided key_points/tailoring_tips

          // Final fallback: if we still have zero questions (e.g., technical empty and no suitable fallbacks), use QA questions themselves
          if (!list.length) {
            const qaQuestions = qaList.map(x => x.question).filter(Boolean);
            list = qaQuestions.slice(0, 12);
            setQuestions(list);
            // Seed fallback answers directly from QA
            const seeded: Record<string, string> = {};
            for (let i = 0; i < list.length; i++) {
              const q = list[i];
              const src = qaList.find(x => x.question === q);
              if (src?.sample_answer) seeded[q] = src.sample_answer;
            }
            setAnswerText(prev => ({ ...seeded, ...prev }));
          }
        }
        // If still no questions, synthesize from extracted skills
        if (!list.length) {
          const skills: string[] = [
            ...((qa.extracted?.core_skills as string[]) || []),
            ...((qa.extracted?.tools_frameworks as string[]) || []),
            ...((qa.extracted?.languages as string[]) || []),
          ].filter(Boolean);
          if (skills.length) {
            const synthetic = Array.from(new Set(skills))
              .slice(0, 12)
              .map((s) => `Describe your hands-on experience with ${s}. What challenges did you face and how did you solve them?`);
            list = synthetic;
            setQuestions(list);
          }
        }
        // Last-resort generic technical prompts
        if (!list.length) {
          list = [
            "Walk me through a challenging technical problem you solved recently.",
            "How do you design scalable and maintainable systems?",
            "Explain a performance optimization you implemented and its impact.",
            "How do you ensure code quality (testing, reviews, CI/CD)?",
            "Describe how you debug complex production issues.",
            "How do you approach API design and versioning?",
            "What security considerations do you include in your work?",
            "Explain how you handle data modeling and migrations.",
            "Describe a time you improved developer productivity.",
            "How do you monitor and observe services in production?",
          ];
          setQuestions(list);
        }
        if (!(qa.qa || []).length) {
          console.warn('Empty Q&A returned from AI.');
          toast({ title: 'AI returned no Q&A', description: 'Try another JD or re-run in a moment.' });
        }
      } catch (e: any) {
        console.error('Failed to generate JD Q&A', e);
        toast({ title: 'Q&A generation failed', description: e?.message || 'Please try again', variant: 'destructive' });
      }
      // Do not synthesize default bullets; show only AI-generated answers
      // Absolute last fallback outside QA try/catch, in case QA failed before providing any alternatives
      if (!list.length) {
        list = [
          "Walk me through a challenging technical problem you solved recently.",
          "How do you design scalable and maintainable systems?",
          "Explain a performance optimization you implemented and its impact.",
          "How do you ensure code quality (testing, reviews, CI/CD)?",
          "Describe how you debug complex production issues.",
          "How do you approach API design and versioning?",
          "What security considerations do you include in your work?",
          "Explain how you handle data modeling and migrations.",
          "Describe a time you improved developer productivity.",
          "How do you monitor and observe services in production?",
        ];
        setQuestions(list);
      }
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
                      {answerText[question] ? (
                        <div className="pl-6 text-sm text-muted-foreground">
                          {answerText[question]}
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

      {qaPairs.length > 0 && (
        <Card className="border-border shadow-xl animate-scale-in">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-6 w-6 text-primary" />
              JD-tailored Q&A (10–15)
            </CardTitle>
            <CardDescription>
              Use these sample answers to tailor your resume and prepare
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {qaPairs.map((qa, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex gap-3 items-start">
                  <Badge className="shrink-0 h-6 w-6 rounded-full flex items-center justify-center">{idx + 1}</Badge>
                  <p className="font-medium text-foreground">{qa.question}</p>
                </div>
                <div className="pl-9 text-sm text-muted-foreground">
                  {qa.sample_answer}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {(extracted.core_skills?.length || extracted.languages?.length || extracted.tools_frameworks?.length || extracted.key_responsibilities?.length) ? (
        <Card className="border-border shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-6 w-6 text-primary" />
              JD Key Signals (from AI)
            </CardTitle>
            <CardDescription>Core skills and responsibilities parsed from your JD</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium mb-2">Core Skills</p>
              <div className="flex flex-wrap gap-2">
                {(extracted.core_skills || []).map((s, i) => (<Badge key={`cs-${i}`} variant="secondary">{s}</Badge>))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Languages</p>
              <div className="flex flex-wrap gap-2">
                {(extracted.languages || []).map((s, i) => (<Badge key={`lg-${i}`} variant="secondary">{s}</Badge>))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Tools & Frameworks</p>
              <div className="flex flex-wrap gap-2">
                {(extracted.tools_frameworks || []).map((s, i) => (<Badge key={`tf-${i}`} variant="secondary">{s}</Badge>))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Key Responsibilities</p>
              <ul className="list-disc pl-6 text-sm text-muted-foreground space-y-1">
                {(extracted.key_responsibilities || []).map((s, i) => (<li key={`kr-${i}`}>{s}</li>))}
              </ul>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
