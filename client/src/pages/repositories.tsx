import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { insertRepositorySchema, type Repository, type InsertRepository } from "@shared/schema";
import { Folder, Plus, Play, Square, Settings, FileText, Loader2 } from "lucide-react";
import { Link } from "wouter";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";

export default function Repositories() {
  const [open, setOpen] = useState(false);
  const { toast } = useToast();

  const { data: repositories, isLoading } = useQuery<Repository[]>({
    queryKey: ["/api/repositories"],
  });

  const form = useForm<InsertRepository>({
    resolver: zodResolver(insertRepositorySchema),
    defaultValues: {
      name: "",
      description: "",
      pythonVersion: "3.11",
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: InsertRepository) => {
      return await apiRequest("POST", "/api/repositories", data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/repositories"] });
      toast({
        title: "Repository created",
        description: "Your repository has been created successfully",
      });
      setOpen(false);
      form.reset();
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: InsertRepository) => {
    createMutation.mutate(data);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Your Repositories</h1>
          <p className="text-muted-foreground mt-1">
            Manage your Python projects and deployments
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button data-testid="button-new-repository">
              <Plus className="h-4 w-4 mr-2" />
              New Repository
            </Button>
          </DialogTrigger>
          <DialogContent data-testid="dialog-new-repository">
            <DialogHeader>
              <DialogTitle>Create New Repository</DialogTitle>
              <DialogDescription>
                Create a new Python project repository to host your application
              </DialogDescription>
            </DialogHeader>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Repository Name</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="my-telegram-bot"
                          {...field}
                          data-testid="input-repository-name"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description (Optional)</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="A Telegram bot for..."
                          {...field}
                          value={field.value || ""}
                          data-testid="input-repository-description"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <DialogFooter>
                  <Button
                    type="submit"
                    disabled={createMutation.isPending}
                    data-testid="button-create-repository"
                  >
                    {createMutation.isPending && (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    )}
                    Create Repository
                  </Button>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-6 space-y-4">
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-8 w-24" />
            </Card>
          ))}
        </div>
      ) : repositories && repositories.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
          {repositories.map((repo) => (
            <Card
              key={repo.id}
              className="p-6 space-y-4 hover-elevate"
              data-testid={`card-repository-${repo.id}`}
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2">
                    <Folder className="h-5 w-5 text-muted-foreground" />
                    <h3 className="text-lg font-semibold" data-testid={`text-repository-name-${repo.id}`}>
                      {repo.name}
                    </h3>
                  </div>
                  {repo.description && (
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {repo.description}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <div
                    className={`h-2 w-2 rounded-full ${
                      repo.status === "running"
                        ? "bg-status-online animate-pulse"
                        : repo.status === "error"
                        ? "bg-status-busy"
                        : "bg-status-offline"
                    }`}
                  />
                  <Badge
                    variant="outline"
                    className="capitalize"
                    data-testid={`badge-status-${repo.id}`}
                  >
                    {repo.status}
                  </Badge>
                </div>
              </div>

              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Badge variant="secondary" className="font-mono text-xs">
                    Python {repo.pythonVersion}
                  </Badge>
                </div>
                <div>
                  Updated {new Date(repo.updatedAt!).toLocaleDateString()}
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  asChild
                  data-testid={`button-view-${repo.id}`}
                >
                  <Link href={`/repositories/${repo.id}`}>
                    <FileText className="h-4 w-4 mr-2" />
                    View
                  </Link>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  asChild
                  data-testid={`button-settings-${repo.id}`}
                >
                  <Link href={`/repositories/${repo.id}?tab=settings`}>
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                  </Link>
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="p-12 text-center space-y-4">
          <div className="flex justify-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
              <Folder className="h-10 w-10 text-primary" />
            </div>
          </div>
          <div className="space-y-2">
            <h3 className="text-xl font-semibold">No repositories yet</h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              Create your first repository to start hosting Python projects
            </p>
          </div>
          <Button onClick={() => setOpen(true)} data-testid="button-create-first-repository">
            <Plus className="h-4 w-4 mr-2" />
            Create Your First Repository
          </Button>
        </Card>
      )}
    </div>
  );
}
