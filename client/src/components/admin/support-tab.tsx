import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Eye } from "lucide-react";
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface SupportMessage {
  id: string;
  userId: string;
  subject: string;
  message: string;
  isRead: boolean;
  createdAt: Date;
  user?: {
    username: string;
    email: string;
  };
}

export default function SupportTab() {
  const { toast } = useToast();
  const [selectedMessage, setSelectedMessage] = useState<SupportMessage | null>(null);
  const [showDialog, setShowDialog] = useState(false);

  const { data: messages = [], isLoading } = useQuery<SupportMessage[]>({
    queryKey: ["/api/support/messages"],
  });

  const markAsReadMutation = useMutation({
    mutationFn: async (id: string) => {
      return await apiRequest("PATCH", `/api/support/messages/${id}/read`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/support/messages"] });
    },
    onError: (error: Error) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const handleViewMessage = (message: SupportMessage) => {
    setSelectedMessage(message);
    setShowDialog(true);
    if (!message.isRead) {
      markAsReadMutation.mutate(message.id);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <>
      <Card className="p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold">Support Messages</h2>
          <p className="text-muted-foreground mt-1">
            View and respond to user support requests
          </p>
        </div>

        {messages.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No support messages yet.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Status</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Subject</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {messages.map((message) => (
                <TableRow key={message.id}>
                  <TableCell>
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${
                        message.isRead
                          ? "bg-gray-100 text-gray-700"
                          : "bg-blue-100 text-blue-700"
                      }`}
                    >
                      {message.isRead ? "Read" : "Unread"}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">{message.user?.username}</div>
                      <div className="text-sm text-muted-foreground">
                        {message.user?.email}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="font-medium">{message.subject}</TableCell>
                  <TableCell>
                    {new Date(message.createdAt).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewMessage(message)}
                      data-testid={`button-view-message-${message.id}`}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedMessage?.subject}</DialogTitle>
            <DialogDescription>
              From: {selectedMessage?.user?.username} ({selectedMessage?.user?.email})
              <br />
              Date: {selectedMessage && new Date(selectedMessage.createdAt).toLocaleString()}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="bg-muted p-4 rounded-lg whitespace-pre-wrap">
              {selectedMessage?.message}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
