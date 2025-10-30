import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { insertFileSchema, type File as FileType, type InsertFile } from "@shared/schema";
import { Upload, FileCode, FileJson, FileText, Trash2, Loader2, FolderPlus, ChevronDown, Folder, FileArchive, FilePlus, Edit, Download, RefreshCw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface FilesTabProps {
  repositoryId: string;
  files: FileType[];
}

export function FilesTab({ repositoryId, files }: FilesTabProps) {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [createType, setCreateType] = useState<"file" | "folder">("file");
  const [editFile, setEditFile] = useState<FileType | null>(null);
  const [deleteFile, setDeleteFile] = useState<FileType | null>(null);
  const [currentPath, setCurrentPath] = useState("");
  const [newItemName, setNewItemName] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const zipInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const createForm = useForm<InsertFile>({
    resolver: zodResolver(insertFileSchema),
    defaultValues: {
      name: "",
      content: "",
      size: 0,
    },
  });

  const editForm = useForm<{ content: string }>({
    defaultValues: {
      content: "",
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: InsertFile) => {
      return await apiRequest("POST", `/api/repositories/${repositoryId}/files`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/repositories", repositoryId, "files"] });
      toast({
        title: createType === "folder" ? "Folder created" : "File created",
        description: `Your ${createType} has been created successfully`,
      });
      setCreateDialogOpen(false);
      createForm.reset();
      setNewItemName("");
    },
    onError: (error: Error) => {
      toast({
        title: `Error creating ${createType}`,
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ fileId, content }: { fileId: string; content: string }) => {
      return await apiRequest("PATCH", `/api/repositories/${repositoryId}/files/${fileId}`, { content });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/repositories", repositoryId, "files"] });
      toast({
        title: "File updated",
        description: "Your file has been updated successfully",
      });
      setEditFile(null);
      editForm.reset();
    },
    onError: (error: Error) => {
      toast({
        title: "Error updating file",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (fileId: string) => {
      return await apiRequest("DELETE", `/api/repositories/${repositoryId}/files/${fileId}`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/repositories", repositoryId, "files"] });
      toast({
        title: "File deleted",
        description: "The file has been deleted successfully",
      });
      setDeleteFile(null);
    },
    onError: (error: Error) => {
      toast({
        title: "Error deleting file",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const fileUploadMutation = useMutation({
    mutationFn: async (files: FileList) => {
      const uploadPromises = Array.from(files).map(async (file) => {
        const content = await file.text();
        return apiRequest("POST", `/api/repositories/${repositoryId}/files`, {
          name: file.name,
          path: currentPath,
          content,
          size: content.length,
          isDirectory: false,
        });
      });
      return Promise.all(uploadPromises);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/repositories", repositoryId, "files"] });
      toast({
        title: "Files uploaded",
        description: "Your files have been uploaded successfully",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Error uploading files",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const zipUploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const arrayBuffer = await file.arrayBuffer();
      const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
      return apiRequest("POST", `/api/repositories/${repositoryId}/upload-zip`, {
        zipContent: base64,
        targetPath: currentPath,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/repositories", repositoryId, "files"] });
      toast({
        title: "ZIP file extracted",
        description: "The ZIP file has been extracted successfully",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Error uploading ZIP",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const syncFilesMutation = useMutation({
    mutationFn: async () => {
      return apiRequest("POST", `/api/repositories/${repositoryId}/sync-files`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/repositories", repositoryId, "files"] });
      toast({
        title: "Files synced",
        description: "Runtime files have been synced to database successfully",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Error syncing files",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const onCreateSubmit = (data: InsertFile) => {
    if (createType === "folder") {
      createMutation.mutate({
        name: newItemName,
        path: currentPath,
        content: "",
        size: 0,
        isDirectory: true,
      });
    } else {
      const size = new Blob([data.content]).size;
      createMutation.mutate({ ...data, size, path: currentPath, isDirectory: false });
    }
  };

  const onEditSubmit = (data: { content: string }) => {
    if (editFile) {
      updateMutation.mutate({ fileId: editFile.id, content: data.content });
    }
  };

  const handleOpenCreate = (type: "file" | "folder") => {
    setCreateType(type);
    setCreateDialogOpen(true);
    setNewItemName("");
    createForm.reset();
  };

  const handleOpenEdit = (file: FileType) => {
    setEditFile(file);
    editForm.setValue("content", file.content);
  };

  const handleDownloadFile = (file: FileType) => {
    const blob = new Blob([file.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({
      title: "File downloaded",
      description: `${file.name} has been downloaded successfully`,
    });
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      fileUploadMutation.mutate(files);
    }
  };

  const handleZipUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.name.endsWith('.zip')) {
      zipUploadMutation.mutate(file);
    } else {
      toast({
        title: "Invalid file",
        description: "Please select a ZIP file",
        variant: "destructive",
      });
    }
  };

  const getFileIcon = (filename: string) => {
    if (filename.endsWith(".py")) return FileCode;
    if (filename.endsWith(".json")) return FileJson;
    return FileText;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const currentFiles = files.filter(f => f.path === currentPath);
  const folders = currentFiles.filter(f => f.isDirectory);
  const regularFiles = currentFiles.filter(f => !f.isDirectory);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold">Files</h2>
          {currentPath && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                const parts = currentPath.split('/');
                parts.pop();
                setCurrentPath(parts.join('/'));
              }}
            >
              ← Back
            </Button>
          )}
        </div>
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileUpload}
          />
          <input
            ref={zipInputRef}
            type="file"
            accept=".zip"
            className="hidden"
            onChange={handleZipUpload}
          />
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button data-testid="button-upload-options">
                <Upload className="h-4 w-4 mr-2" />
                Upload
                <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => fileInputRef.current?.click()}>
                <FileText className="h-4 w-4 mr-2" />
                Upload Files
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => zipInputRef.current?.click()}>
                <FileArchive className="h-4 w-4 mr-2" />
                Upload ZIP
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <FilePlus className="h-4 w-4 mr-2" />
                New
                <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => handleOpenCreate("file")}>
                <FileCode className="h-4 w-4 mr-2" />
                New File
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleOpenCreate("folder")}>
                <FolderPlus className="h-4 w-4 mr-2" />
                New Folder
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Button
            variant="outline"
            onClick={() => syncFilesMutation.mutate()}
            disabled={syncFilesMutation.isPending}
            title="Sync runtime files to database"
          >
            {syncFilesMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Sync Files
          </Button>
        </div>
      </div>

      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-2xl" data-testid="dialog-create-item">
          <DialogHeader>
            <DialogTitle>{createType === "folder" ? "Create New Folder" : "Create New File"}</DialogTitle>
            <DialogDescription>
              {createType === "folder" 
                ? "Enter a name for the new folder" 
                : "Create a new file with custom name and content"}
            </DialogDescription>
          </DialogHeader>
          {createType === "folder" ? (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Folder Name</label>
                <Input
                  placeholder="my-folder"
                  value={newItemName}
                  onChange={(e) => setNewItemName(e.target.value)}
                  className="mt-2"
                />
              </div>
              <DialogFooter>
                <Button
                  onClick={() => onCreateSubmit({ name: "", content: "", size: 0 })}
                  disabled={!newItemName || createMutation.isPending}
                >
                  {createMutation.isPending && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  Create Folder
                </Button>
              </DialogFooter>
            </div>
          ) : (
            <Form {...createForm}>
              <form onSubmit={createForm.handleSubmit(onCreateSubmit)} className="space-y-4">
                <FormField
                  control={createForm.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>File Name</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="User.json"
                          {...field}
                          data-testid="input-file-name"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={createForm.control}
                  name="content"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>File Content</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Enter file content..."
                          className="font-mono text-sm min-h-64"
                          {...field}
                          data-testid="input-file-content"
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
                    data-testid="button-submit-create"
                  >
                    {createMutation.isPending && (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    )}
                    Create File
                  </Button>
                </DialogFooter>
              </form>
            </Form>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={!!editFile} onOpenChange={() => setEditFile(null)}>
        <DialogContent className="max-w-2xl" data-testid="dialog-edit-file">
          <DialogHeader>
            <DialogTitle>Edit File: {editFile?.name}</DialogTitle>
            <DialogDescription>
              Modify the content of your file
            </DialogDescription>
          </DialogHeader>
          <Form {...editForm}>
            <form onSubmit={editForm.handleSubmit(onEditSubmit)} className="space-y-4">
              <FormField
                control={editForm.control}
                name="content"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>File Content</FormLabel>
                    <FormControl>
                      <Textarea
                        className="font-mono text-sm min-h-96"
                        {...field}
                        data-testid="input-edit-content"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button
                  type="submit"
                  disabled={updateMutation.isPending}
                  data-testid="button-submit-edit"
                >
                  {updateMutation.isPending && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  Save Changes
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {currentFiles.length === 0 ? (
        <Card className="p-12 text-center space-y-4">
          <div className="flex justify-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
              <FileCode className="h-10 w-10 text-primary" />
            </div>
          </div>
          <div className="space-y-2">
            <h3 className="text-xl font-semibold">No files yet</h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              Upload your Python files, requirements.txt, and configuration files to get started
            </p>
          </div>
          <Button onClick={() => fileInputRef.current?.click()} data-testid="button-upload-first-file">
            <Upload className="h-4 w-4 mr-2" />
            Upload Files
          </Button>
        </Card>
      ) : (
        <div className="space-y-2">
          {folders.map((folder) => (
            <Card
              key={folder.id}
              className="p-4 flex items-center justify-between hover-elevate cursor-pointer"
              onClick={() => setCurrentPath(folder.path ? `${folder.path}/${folder.name}` : folder.name)}
              data-testid={`card-folder-${folder.id}`}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <Folder className="h-5 w-5 text-blue-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate" data-testid={`text-folder-name-${folder.id}`}>
                    {folder.name}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Updated {new Date(folder.updatedAt!).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteFile(folder);
                }}
                data-testid={`button-delete-${folder.id}`}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </Card>
          ))}
          {regularFiles.map((file) => {
            const Icon = getFileIcon(file.name);
            return (
              <Card
                key={file.id}
                className="p-4 flex items-center justify-between hover-elevate"
                data-testid={`card-file-${file.id}`}
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <Icon className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-mono font-medium truncate" data-testid={`text-file-name-${file.id}`}>
                      {file.name}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {formatFileSize(file.size)} • Updated{" "}
                      {new Date(file.updatedAt!).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDownloadFile(file)}
                    data-testid={`button-download-${file.id}`}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleOpenEdit(file)}
                    data-testid={`button-edit-${file.id}`}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setDeleteFile(file)}
                    data-testid={`button-delete-${file.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      <AlertDialog open={!!deleteFile} onOpenChange={() => setDeleteFile(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete File</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deleteFile?.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="button-cancel-delete">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteFile && deleteMutation.mutate(deleteFile.id)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              data-testid="button-confirm-delete"
            >
              {deleteMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
