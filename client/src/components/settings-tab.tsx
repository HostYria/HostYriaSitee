import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormDescription,
  FormMessage,
} from "@/components/ui/form";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import type {
  Repository,
  File as FileType,
  EnvironmentVariable,
  InsertEnvironmentVariable,
} from "@shared/schema";
import { Save, Trash2, Plus, Loader2, Download } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useLocation } from "wouter";

const settingsSchema = z.object({
  mainFile: z.string().optional(),
  pythonVersion: z.string(),
  autoInstallRequirements: z.boolean().default(false),
});

type SettingsForm = z.infer<typeof settingsSchema>;

interface SettingsTabProps {
  repository: Repository;
  files: FileType[];
  environmentVariables: EnvironmentVariable[];
}

export function SettingsTab({
  repository,
  files,
  environmentVariables,
}: SettingsTabProps) {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [envVars, setEnvVars] = useState<Array<{ key: string; value: string }>>(
    environmentVariables.map((ev) => ({ key: ev.key, value: ev.value }))
  );
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const form = useForm<SettingsForm>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      mainFile: repository.mainFile || "",
      pythonVersion: repository.pythonVersion,
      autoInstallRequirements: repository.autoInstallRequirements || false,
    },
  });

  const pythonFiles = files.filter((f) => f.name.endsWith(".py"));

  const updateMutation = useMutation({
    mutationFn: async (data: SettingsForm) => {
      return await apiRequest("PATCH", `/api/repositories/${repository.id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/repositories", repository.id] });
      toast({
        title: "Settings updated",
        description: "Your repository settings have been saved",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Error updating settings",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const updateEnvVarsMutation = useMutation({
    mutationFn: async (vars: Array<{ key: string; value: string }>) => {
      return await apiRequest("POST", `/api/repositories/${repository.id}/env`, { variables: vars });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/repositories", repository.id, "env"] });
      toast({
        title: "Environment variables updated",
        description: "Your environment variables have been saved",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Error updating environment variables",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      return await apiRequest("DELETE", `/api/repositories/${repository.id}`, {});
    },
    onSuccess: () => {
      toast({
        title: "Repository deleted",
        description: "Your repository has been deleted successfully",
      });
      setLocation("/repositories");
    },
    onError: (error: Error) => {
      toast({
        title: "Error deleting repository",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: SettingsForm) => {
    updateMutation.mutate(data);
  };

  const addEnvVar = () => {
    setEnvVars([...envVars, { key: "", value: "" }]);
  };

  const removeEnvVar = (index: number) => {
    setEnvVars(envVars.filter((_, i) => i !== index));
  };

  const updateEnvVar = (index: number, field: "key" | "value", value: string) => {
    const updated = [...envVars];
    updated[index][field] = value;
    setEnvVars(updated);
  };

  const saveEnvVars = () => {
    const validVars = envVars.filter((v) => v.key.trim() && v.value.trim());
    updateEnvVarsMutation.mutate(validVars);
  };

  const handleDownloadAllFiles = async () => {
    try {
      const JSZip = (await import('jszip')).default;
      const zip = new JSZip();

      files.forEach((file) => {
        const filePath = file.path ? `${file.path}/${file.name}` : file.name;
        if (!file.isDirectory) {
          zip.file(filePath, file.content);
        }
      });

      const content = await zip.generateAsync({ type: 'blob' });
      const url = URL.createObjectURL(content);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${repository.name}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Files downloaded",
        description: `All files have been downloaded as ${repository.name}.zip`,
      });
    } catch (error: any) {
      toast({
        title: "Error downloading files",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Download Project</h2>
          <Button
            onClick={handleDownloadAllFiles}
            disabled={files.length === 0}
            data-testid="button-download-all-files"
          >
            <Download className="h-4 w-4 mr-2" />
            Download All Files
          </Button>
        </div>
        <p className="text-sm text-muted-foreground">
          تحميل جميع ملفات المشروع كملف ZIP مضغوط على الهاتف أو الكمبيوتر
        </p>
      </Card>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Execution Settings</h2>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="mainFile"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Main File</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                    disabled={pythonFiles.length === 0}
                  >
                    <FormControl>
                      <SelectTrigger data-testid="select-main-file">
                        <SelectValue placeholder="Select main Python file" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {pythonFiles.map((file) => (
                        <SelectItem key={file.id} value={file.name}>
                          {file.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    The Python file to execute when starting the application
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="pythonVersion"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Python Version</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger data-testid="select-python-version">
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="3.8">Python 3.8</SelectItem>
                      <SelectItem value="3.9">Python 3.9</SelectItem>
                      <SelectItem value="3.10">Python 3.10</SelectItem>
                      <SelectItem value="3.11">Python 3.11</SelectItem>
                      <SelectItem value="3.12">Python 3.12</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    The Python version to use for running your application
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="autoInstallRequirements"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
                  <FormControl>
                    <input
                      type="checkbox"
                      checked={field.value}
                      onChange={field.onChange}
                      className="h-4 w-4 rounded border-gray-300"
                      data-testid="checkbox-auto-install-requirements"
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none mr-3">
                    <FormLabel className="text-base">
                      Do you have requirements.txt file?
                    </FormLabel>
                    <FormDescription>
                      عند التفعيل، سيتم تثبيت المكتبات المطلوبة تلقائياً من ملف requirements.txt عند بدء التشغيل.
                      <br />
                      عند عدم التفعيل، يجب تثبيت المكتبات يدوياً من قائمة Terminal.
                    </FormDescription>
                  </div>
                </FormItem>
              )}
            />

            <Button
              type="submit"
              disabled={updateMutation.isPending}
              data-testid="button-save-settings"
            >
              {updateMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Save Settings
            </Button>
          </form>
        </Form>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold">Environment Variables</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Add DATABASE_URL or other configuration variables
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={addEnvVar}
            data-testid="button-add-env-var"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Variable
          </Button>
        </div>

        {envVars.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No environment variables configured
          </div>
        ) : (
          <div className="space-y-3">
            {envVars.map((envVar, index) => (
              <div
                key={index}
                className="flex items-center gap-2"
                data-testid={`env-var-${index}`}
              >
                <Input
                  placeholder="KEY"
                  value={envVar.key}
                  onChange={(e) => updateEnvVar(index, "key", e.target.value)}
                  className="font-mono"
                  data-testid={`input-env-key-${index}`}
                />
                <Input
                  placeholder="value"
                  value={envVar.value}
                  onChange={(e) => updateEnvVar(index, "value", e.target.value)}
                  className="font-mono"
                  data-testid={`input-env-value-${index}`}
                />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeEnvVar(index)}
                  data-testid={`button-remove-env-${index}`}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}

        <Button
          onClick={saveEnvVars}
          disabled={updateEnvVarsMutation.isPending}
          className="mt-4"
          data-testid="button-save-env-vars"
        >
          {updateEnvVarsMutation.isPending ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Save className="h-4 w-4 mr-2" />
          )}
          Save Environment Variables
        </Button>
      </Card>

      <Card className="p-6 border-destructive/50">
        <h2 className="text-xl font-semibold mb-2 text-destructive">Danger Zone</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Once you delete a repository, there is no going back. Please be certain.
        </p>
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogTrigger asChild>
            <Button variant="destructive" data-testid="button-delete-repository">
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Repository
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Repository</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete "{repository.name}"? This will permanently
                delete all files, settings, and logs. This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel data-testid="button-cancel-delete-repo">
                Cancel
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={() => deleteMutation.mutate()}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                data-testid="button-confirm-delete-repo"
              >
                {deleteMutation.isPending && (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                )}
                Delete Repository
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </Card>
    </div>
  );
}
