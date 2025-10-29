import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Code, Server, Activity, Shield, Database, Clock } from "lucide-react";

export default function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
              <Code className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold">HostYria</span>
          </div>
          <Button asChild data-testid="button-login">
            <a href="/login">Sign In</a>
          </Button>
        </div>
      </header>

      <main>
        <section className="py-20 md:py-32">
          <div className="container px-4">
            <div className="grid gap-12 lg:grid-cols-2 lg:gap-16 items-center">
              <div className="space-y-6">
                <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
                  Host & Run Python Projects in the Cloud
                </h1>
                <p className="text-lg text-muted-foreground">
                  Deploy bots, scripts, and applications with real-time logs and environment management. Run your Python projects 24/7 with zero configuration.
                </p>
                <div className="flex flex-wrap gap-4">
                  <Button size="lg" asChild data-testid="button-get-started">
                    <a href="/register">Get Started Free</a>
                  </Button>
                  <Button size="lg" variant="outline" asChild data-testid="button-view-docs">
                    <a href="#features">View Features</a>
                  </Button>
                </div>
              </div>
              <div className="relative">
                <Card className="overflow-hidden border-2 p-0">
                  <div className="bg-card-foreground/5 px-4 py-2 border-b flex items-center gap-2">
                    <div className="flex gap-1.5">
                      <div className="h-3 w-3 rounded-full bg-destructive/60" />
                      <div className="h-3 w-3 rounded-full bg-chart-3/60" />
                      <div className="h-3 w-3 rounded-full bg-status-online/60" />
                    </div>
                    <span className="text-xs font-mono text-muted-foreground">terminal</span>
                  </div>
                  <div className="bg-card-foreground/[0.02] p-6 font-mono text-sm space-y-2">
                    <div className="text-muted-foreground">$ python main.py</div>
                    <div className="text-status-online">[INFO] Bot started successfully</div>
                    <div className="text-status-online">[INFO] Connected to Telegram API</div>
                    <div className="text-status-online">[INFO] Listening for messages...</div>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 bg-status-online rounded-full animate-pulse" />
                      <span className="text-status-online">Running</span>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="py-20 bg-card/30">
          <div className="container px-4">
            <div className="text-center space-y-4 mb-12">
              <h2 className="text-3xl font-bold sm:text-4xl">Everything You Need</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Professional Python hosting with powerful features for developers
              </p>
            </div>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <Card className="p-6 space-y-3 hover-elevate">
                <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary/10">
                  <Server className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold">Real-time Execution</h3>
                <p className="text-muted-foreground">
                  Run your Python applications 24/7 with instant start/stop controls and live process management.
                </p>
              </Card>
              <Card className="p-6 space-y-3 hover-elevate">
                <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary/10">
                  <Activity className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold">Live Logs</h3>
                <p className="text-muted-foreground">
                  Monitor your application with real-time log streaming and terminal-style output viewing.
                </p>
              </Card>
              <Card className="p-6 space-y-3 hover-elevate">
                <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary/10">
                  <Code className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold">Environment Variables</h3>
                <p className="text-muted-foreground">
                  Securely manage API keys, database URLs, and configuration through an intuitive interface.
                </p>
              </Card>
              <Card className="p-6 space-y-3 hover-elevate">
                <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary/10">
                  <Shield className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold">Multiple Python Versions</h3>
                <p className="text-muted-foreground">
                  Choose from Python 3.8, 3.9, 3.10, 3.11, or 3.12 for each project with seamless switching.
                </p>
              </Card>
              <Card className="p-6 space-y-3 hover-elevate">
                <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary/10">
                  <Database className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold">Database Integration</h3>
                <p className="text-muted-foreground">
                  Connect to any database by adding DATABASE_URL and other connection variables.
                </p>
              </Card>
              <Card className="p-6 space-y-3 hover-elevate">
                <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary/10">
                  <Clock className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold">24/7 Uptime</h3>
                <p className="text-muted-foreground">
                  Keep your bots and applications running continuously with reliable cloud infrastructure.
                </p>
              </Card>
            </div>
          </div>
        </section>

        <section className="py-20">
          <div className="container px-4">
            <div className="text-center space-y-4 mb-12">
              <h2 className="text-3xl font-bold sm:text-4xl">How It Works</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Deploy your Python projects in three simple steps
              </p>
            </div>
            <div className="grid gap-8 md:grid-cols-3">
              <div className="relative">
                <div className="space-y-3">
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary text-primary-foreground text-2xl font-bold">
                      1
                    </div>
                    <h3 className="text-xl font-semibold">Create Repository</h3>
                  </div>
                  <p className="text-muted-foreground ml-16">
                    Set up a new project repository and give it a name
                  </p>
                </div>
              </div>
              <div className="relative">
                <div className="space-y-3">
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary text-primary-foreground text-2xl font-bold">
                      2
                    </div>
                    <h3 className="text-xl font-semibold">Upload Files</h3>
                  </div>
                  <p className="text-muted-foreground ml-16">
                    Upload your Python files, requirements.txt, and any configuration files
                  </p>
                </div>
              </div>
              <div className="relative">
                <div className="space-y-3">
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary text-primary-foreground text-2xl font-bold">
                      3
                    </div>
                    <h3 className="text-xl font-semibold">Configure & Deploy</h3>
                  </div>
                  <p className="text-muted-foreground ml-16">
                    Set your main file, Python version, environment variables, and hit start
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="py-16 bg-primary/5">
          <div className="container px-4 text-center space-y-6">
            <h2 className="text-3xl font-bold sm:text-4xl">Ready to Deploy Your Python Projects?</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Start hosting your Python applications today. No credit card required.
            </p>
            <Button size="lg" asChild data-testid="button-cta-start">
              <a href="/register">Get Started Free</a>
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t py-8">
        <div className="container px-4 text-center text-sm text-muted-foreground">
          <p>&copy; 2025 HostYria. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}