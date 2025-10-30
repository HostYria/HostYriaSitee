import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Plus, Pencil, Trash2, StickyNote } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
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
import { type Note, insertNoteSchema, type InsertNote } from "@shared/schema";

export default function Notes() {
  const { toast } = useToast();
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);

  const createForm = useForm<InsertNote>({
    resolver: zodResolver(insertNoteSchema),
    defaultValues: {
      subject: "",
      content: "",
    },
  });

  const editForm = useForm<InsertNote>({
    resolver: zodResolver(insertNoteSchema),
    defaultValues: {
      subject: "",
      content: "",
    },
  });

  const { data: notes = [], isLoading } = useQuery<Note[]>({
    queryKey: ["/api/notes"],
  });

  const createNoteMutation = useMutation({
    mutationFn: async (data: InsertNote) => {
      return await apiRequest("POST", "/api/notes", data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/notes"] });
      toast({
        title: "تم بنجاح",
        description: "تم إنشاء المذكرة بنجاح",
      });
      setIsCreateDialogOpen(false);
      createForm.reset();
    },
    onError: (error: Error) => {
      toast({
        title: "خطأ",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const updateNoteMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: InsertNote }) => {
      return await apiRequest("PATCH", `/api/notes/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/notes"] });
      toast({
        title: "تم بنجاح",
        description: "تم تحديث المذكرة بنجاح",
      });
      setIsEditDialogOpen(false);
      setSelectedNote(null);
      editForm.reset();
    },
    onError: (error: Error) => {
      toast({
        title: "خطأ",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const deleteNoteMutation = useMutation({
    mutationFn: async (id: string) => {
      return await apiRequest("DELETE", `/api/notes/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/notes"] });
      toast({
        title: "تم بنجاح",
        description: "تم حذف المذكرة بنجاح",
      });
      setIsDeleteDialogOpen(false);
      setSelectedNote(null);
    },
    onError: (error: Error) => {
      toast({
        title: "خطأ",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handleCreateNote = (data: InsertNote) => {
    createNoteMutation.mutate(data);
  };

  const handleEditNote = (note: Note) => {
    setSelectedNote(note);
    editForm.reset({
      subject: note.subject,
      content: note.content,
    });
    setIsEditDialogOpen(true);
  };

  const handleUpdateNote = (data: InsertNote) => {
    if (!selectedNote) return;

    updateNoteMutation.mutate({
      id: selectedNote.id,
      data,
    });
  };

  const handleDeleteNote = (note: Note) => {
    setSelectedNote(note);
    setIsDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (selectedNote) {
      deleteNoteMutation.mutate(selectedNote.id);
    }
  };

  const formatDate = (dateString: Date | null) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString("ar-EG", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">المذكرات</h1>
          <p className="text-muted-foreground mt-1">
            قم بإنشاء وإدارة مذكراتك الشخصية
          </p>
        </div>
        <Button
          onClick={() => setIsCreateDialogOpen(true)}
          data-testid="button-create-note"
        >
          <Plus className="h-4 w-4 mr-2" />
          إنشاء مذكرة جديدة
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : notes.length === 0 ? (
        <Card className="p-12">
          <div className="text-center space-y-3">
            <StickyNote className="h-12 w-12 mx-auto text-muted-foreground" />
            <h3 className="text-lg font-semibold">لا توجد مذكرات بعد</h3>
            <p className="text-muted-foreground">
              ابدأ بإنشاء مذكرتك الأولى للاحتفاظ بملاحظاتك وأفكارك
            </p>
            <Button onClick={() => setIsCreateDialogOpen(true)} className="mt-4">
              <Plus className="h-4 w-4 mr-2" />
              إنشاء مذكرة جديدة
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {notes.map((note) => (
            <Card key={note.id} className="p-4 space-y-3" data-testid={`card-note-${note.id}`}>
              <div className="flex items-start justify-between">
                <h3 className="font-semibold text-lg line-clamp-2" data-testid={`text-subject-${note.id}`}>
                  {note.subject}
                </h3>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEditNote(note)}
                    data-testid={`button-edit-${note.id}`}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDeleteNote(note)}
                    data-testid={`button-delete-${note.id}`}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
              <p className="text-sm text-muted-foreground line-clamp-3" data-testid={`text-content-${note.id}`}>
                {note.content}
              </p>
              <p className="text-xs text-muted-foreground">
                آخر تحديث: {formatDate(note.updatedAt)}
              </p>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>إنشاء مذكرة جديدة</DialogTitle>
            <DialogDescription>
              أضف عنوانًا ومحتوى لمذكرتك الجديدة
            </DialogDescription>
          </DialogHeader>
          <Form {...createForm}>
            <form onSubmit={createForm.handleSubmit(handleCreateNote)} className="space-y-4">
              <FormField
                control={createForm.control}
                name="subject"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>العنوان</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="أدخل عنوان المذكرة"
                        data-testid="input-create-subject"
                        {...field}
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
                    <FormLabel>المحتوى</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="أدخل محتوى المذكرة"
                        className="min-h-[150px]"
                        data-testid="input-create-content"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsCreateDialogOpen(false);
                    createForm.reset();
                  }}
                >
                  إلغاء
                </Button>
                <Button
                  type="submit"
                  disabled={createNoteMutation.isPending}
                  data-testid="button-submit-create"
                >
                  {createNoteMutation.isPending && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  إنشاء
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>تعديل المذكرة</DialogTitle>
            <DialogDescription>
              قم بتحديث عنوان ومحتوى المذكرة
            </DialogDescription>
          </DialogHeader>
          <Form {...editForm}>
            <form onSubmit={editForm.handleSubmit(handleUpdateNote)} className="space-y-4">
              <FormField
                control={editForm.control}
                name="subject"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>العنوان</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="أدخل عنوان المذكرة"
                        data-testid="input-edit-subject"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={editForm.control}
                name="content"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>المحتوى</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="أدخل محتوى المذكرة"
                        className="min-h-[150px]"
                        data-testid="input-edit-content"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsEditDialogOpen(false);
                    setSelectedNote(null);
                    editForm.reset();
                  }}
                >
                  إلغاء
                </Button>
                <Button
                  type="submit"
                  disabled={updateNoteMutation.isPending}
                  data-testid="button-submit-edit"
                >
                  {updateNoteMutation.isPending && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  حفظ التغييرات
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>هل أنت متأكد؟</AlertDialogTitle>
            <AlertDialogDescription>
              سيتم حذف المذكرة "{selectedNote?.subject}" بشكل نهائي ولا يمكن التراجع عن هذا الإجراء.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>إلغاء</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              data-testid="button-confirm-delete"
            >
              {deleteNoteMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              حذف
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
