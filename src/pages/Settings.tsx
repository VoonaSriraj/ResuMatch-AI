import { CreditCard, Link2, Bell, User } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";

export default function Settings() {
  return (
    <div className="p-8 space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account preferences and integrations
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-border shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Profile Information
            </CardTitle>
            <CardDescription>Update your personal details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input id="name" placeholder="John Doe" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="john@example.com" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="title">Job Title</Label>
              <Input id="title" placeholder="Senior Frontend Developer" />
            </div>
            <Button className="w-full bg-gradient-primary hover:opacity-90 transition-opacity">
              Save Changes
            </Button>
          </CardContent>
        </Card>

        <Card className="border-border shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Subscription
            </CardTitle>
            <CardDescription>Manage your subscription plan</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-gradient-primary rounded-lg text-primary-foreground">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold">Pro Plan</h3>
                <Badge variant="secondary" className="bg-white/20 text-white border-0">
                  Active
                </Badge>
              </div>
              <p className="text-sm opacity-90 mb-3">Unlimited job matches and resume optimizations</p>
              <p className="text-2xl font-bold">$29/month</p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Next billing date</span>
                <span className="font-medium">Jan 15, 2025</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Payment method</span>
                <span className="font-medium">•••• 4242</span>
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <Button variant="outline" className="w-full">
                Update Payment Method
              </Button>
              <Button variant="outline" className="w-full text-destructive hover:bg-destructive/10">
                Cancel Subscription
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Link2 className="h-5 w-5" />
              LinkedIn Integration
            </CardTitle>
            <CardDescription>Connect your LinkedIn account for better matches</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 border border-border rounded-lg bg-muted/30">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 bg-[#0077B5] rounded flex items-center justify-center">
                  <Link2 className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="font-medium">LinkedIn</p>
                  <p className="text-sm text-muted-foreground">Not connected</p>
                </div>
              </div>
              <Button className="w-full bg-[#0077B5] hover:bg-[#006399] text-white">
                Connect LinkedIn
              </Button>
            </div>

            <div className="text-sm text-muted-foreground space-y-2">
              <p className="font-medium text-foreground">Benefits of connecting:</p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>Auto-import your work experience</li>
                <li>Direct job applications</li>
                <li>Real-time job recommendations</li>
                <li>Network-based matches</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Notifications
            </CardTitle>
            <CardDescription>Customize your notification preferences</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="email-notif">Email Notifications</Label>
                <p className="text-sm text-muted-foreground">Receive job match alerts via email</p>
              </div>
              <Switch id="email-notif" defaultChecked />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="weekly-digest">Weekly Digest</Label>
                <p className="text-sm text-muted-foreground">Get a summary of new opportunities</p>
              </div>
              <Switch id="weekly-digest" defaultChecked />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="resume-tips">Resume Tips</Label>
                <p className="text-sm text-muted-foreground">Optimization suggestions and advice</p>
              </div>
              <Switch id="resume-tips" />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="marketing">Marketing Emails</Label>
                <p className="text-sm text-muted-foreground">Product updates and news</p>
              </div>
              <Switch id="marketing" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
