import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import JobMatch from "./pages/JobMatch";
import ResumeOptimizer from "./pages/ResumeOptimizer";
import InterviewPrep from "./pages/InterviewPrep";
import RecommendedJobs from "./pages/RecommendedJobs";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import OAuthCallback from "./pages/OAuthCallback";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/job-match" element={<JobMatch />} />
            <Route path="/resume-optimizer" element={<ResumeOptimizer />} />
            <Route path="/interview-prep" element={<InterviewPrep />} />
            <Route path="/recommended-jobs" element={<RecommendedJobs />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/login" element={<Login />} />
            <Route path="/auth/google/callback" element={<OAuthCallback />} />
            <Route path="/auth/github/callback" element={<OAuthCallback />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
