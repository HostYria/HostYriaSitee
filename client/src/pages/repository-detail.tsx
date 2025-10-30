import { useEffect, useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { useRoute, Link } from "wouter";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Play, Square, ChevronLeft, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { Repository, File as FileType, EnvironmentVariable } from "@shared/schema";
import { FilesTab } from "@/components/files-tab";
import { LogsTab } from "@/components/logs-tab";
import { SettingsTab } from "@/components/settings-tab";
import { TerminalTab } from "@/components/terminal-tab";
import { Skeleton } from "@/components/ui/skeleton";

export default function RepositoryDetail() {
  const [, params] = useRoute("/repositories/:id");
  const repositoryId = params?.id;
  const { toast } = useToast();
  
  const searchParams = new URLSearchParams(window.location.search);
  const [activeTab, setActiveTab] = useState(searchParams.get("tab") || "files");

  const { data: repository, isLoading } = useQuery<Repository>({
    queryKey: ["/api/repositories", repositoryId],
    enabled: !!repositoryId,
  });

  const { data: files = [] } = useQuery<FileType[]>({
    queryKey: ["/api/repositories", repositoryId, "files"],
    enabled: !!repositoryId,
  });

  const { data: envVars = [] } = useQuery<EnvironmentVariable[]>({
    queryKey: ["/api/repositories", repositoryId, "env"],
    enabled: !!repositoryId,
  });

  const startMutation = useMutation({
    mutationFn: async () => {
      return await apiRequest("POST", `/api/repositories/${repositoryId}/start`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/repositories", repositoryId] });
      setActiveTab("logs");
      toast({
        title: "Repository started",
        description: "Your application is now running",
      });
    },
    onError: (error: Error) => {
      queryClient.invalidateQueries({ queryKey: ["/api/repositories", repositoryId] });
      toast({
        title: "Error starting repository",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const stopMutation = useMutation({
    mutationFn: async () => {
      return await apiRequest("POST", `/api/repositories/${repositoryId}/stop`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/repositories", repositoryId] });
      toast({
        title: "Repository stopped",
        description: "Your application has been stopped",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Error stopping repository",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!repository) {
    return (
      <div className="p-6">
        <Card className="p-12 text-center">
          <h2 className="text-2xl font-semibold">Repository not found</h2>
          <p className="text-muted-foreground mt-2">
            The repository you're looking for doesn't exist
          </p>
          <Button asChild className="mt-4">
            <Link href="/repositories">Back to Repositories</Link>
          </Button>
        </Card>
      </div>
    );
  }

  const isRunning = repository.status === "running";
  const canStart = repository.status === "stopped" || repository.status === "error" || repository.status === "completed";

  return (
    <div className="p-6 space-y-6">
      <div className="space-y-4">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink asChild>
                <Link href="/repositories">Repositories</Link>
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>{repository.name}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold" data-testid="text-repository-name">
              {repository.name}
            </h1>
            {repository.description && (
              <p className="text-muted-foreground">{repository.description}</p>
            )}
          </div>
        </div>

        <Card className="p-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div
                className={`h-3 w-3 rounded-full ${
                  isRunning
                    ? "bg-status-online animate-pulse"
                    : repository.status === "error"
                    ? "bg-status-busy"
                    : repository.status === "completed"
                    ? "bg-green-500"
                    : "bg-status-offline"
                }`}
              />
              <span className="font-medium">Status:</span>
              <Badge
                variant="outline"
                className="capitalize"
                data-testid="badge-repository-status"
              >
                {repository.status}
              </Badge>
            </div>
            <div className="h-4 w-px bg-border" />
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Python Version:</span>
              <Badge variant="secondary" className="font-mono">
                {repository.pythonVersion}
              </Badge>
            </div>
          </div>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex items-center justify-between border-b">
          <TabsList>
            <TabsTrigger value="files" data-testid="tab-files">
              Files
            </TabsTrigger>
            <TabsTrigger value="logs" data-testid="tab-logs">
              Logs
            </TabsTrigger>
            <TabsTrigger value="terminal" data-testid="tab-terminal">
              Terminal
            </TabsTrigger>
            <TabsTrigger value="settings" data-testid="tab-settings">
              Settings
            </TabsTrigger>
          </TabsList>
          <div className="flex items-center gap-2 pb-px">
            <Button
              onClick={() => startMutation.mutate()}
              disabled={startMutation.isPending || isRunning}
              data-testid="button-start-repository"
              size="sm"
              variant={canStart ? "default" : "outline"}
            >
              {startMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              Start
            </Button>
            <Button
              variant="destructive"
              onClick={() => stopMutation.mutate()}
              disabled={stopMutation.isPending || !isRunning}
              data-testid="button-stop-repository"
              size="sm"
            >
              {stopMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Square className="h-4 w-4 mr-2" />
              )}
              Stop
            </Button>
          </div>
        </div>

        <TabsContent value="files" className="mt-6">
          <FilesTab repositoryId={repositoryId!} files={files} />
        </TabsContent>

        <TabsContent value="logs" className="mt-6">
          <LogsTab repositoryId={repositoryId!} isRunning={isRunning} />
        </TabsContent>

        <TabsContent value="terminal" className="mt-6">
          <TerminalTab repositoryId={repositoryId!} isRunning={isRunning} />
        </TabsContent>

        <TabsContent value="settings" className="mt-6">
          <SettingsTab
            repository={repository}
            files={files}
            environmentVariables={envVars}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
