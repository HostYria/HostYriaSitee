import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import { Loader2, MessageSquare, Send, ArrowLeft } from "lucide-react";
import { useState } from "react";

interface User {
  id: string;
  username: string;
  email: string;
}

interface SupportMessage {
  id: string;
  userId: string;
  message: string;
  isFromUser: boolean;
  createdAt: Date;
  user?: User;
}

interface UserConversation {
  userId: string;
  user: User;
  messages: SupportMessage[];
  lastMessage: SupportMessage;
  unreadCount: number;
}

export default function SupportTab() {
  const { toast } = useToast();
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [replyMessage, setReplyMessage] = useState("");

  const { data: allMessages = [], isLoading } = useQuery<SupportMessage[]>({
    queryKey: ["/api/admin/support/messages"],
    refetchInterval: 5000,
  });

  const sendReplyMutation = useMutation({
    mutationFn: async ({ userId, message }: { userId: string; message: string }) => {
      return await apiRequest("POST", `/api/admin/support/messages/${userId}/reply`, { message });
    },
    onSuccess: () => {
      setReplyMessage("");
      queryClient.invalidateQueries({ queryKey: ["/api/admin/support/messages"] });
      toast({ title: "Success", description: "Reply sent successfully" });
    },
    onError: (error: Error) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  // Group messages by user
  const userConversations: UserConversation[] = Object.values(
    allMessages.reduce((acc, msg) => {
      if (!acc[msg.userId]) {
        acc[msg.userId] = {
          userId: msg.userId,
          user: msg.user || { id: msg.userId, username: 'Unknown', email: 'Unknown' },
          messages: [],
          lastMessage: msg,
          unreadCount: 0,
        };
      }
      acc[msg.userId].messages.push(msg);
      if (new Date(msg.createdAt) > new Date(acc[msg.userId].lastMessage.createdAt)) {
        acc[msg.userId].lastMessage = msg;
      }
      if (msg.isFromUser) {
        acc[msg.userId].unreadCount++;
      }
      return acc;
    }, {} as Record<string, UserConversation>)
  ).sort((a, b) => 
    new Date(b.lastMessage.createdAt).getTime() - new Date(a.lastMessage.createdAt).getTime()
  );

  const selectedConversation = userConversations.find(c => c.userId === selectedUserId);

  const handleSendReply = (e: React.FormEvent) => {
    e.preventDefault();
    if (replyMessage.trim() && selectedUserId) {
      sendReplyMutation.mutate({ userId: selectedUserId, message: replyMessage });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (selectedConversation) {
    return (
      <Card className="p-6">
        <div className="mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSelectedUserId(null)}
            className="mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Conversations
          </Button>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold">
              {selectedConversation.user.username.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="text-xl font-bold">{selectedConversation.user.username}</h2>
              <p className="text-sm text-muted-foreground">{selectedConversation.user.email}</p>
            </div>
          </div>
        </div>

        <div className="border rounded-lg overflow-hidden">
          <div className="h-[400px] overflow-y-auto p-4 space-y-4 bg-muted/30">
            {selectedConversation.messages
              .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())
              .map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.isFromUser ? 'justify-start' : 'justify-end'}`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg p-3 ${
                      msg.isFromUser
                        ? 'bg-muted'
                        : 'bg-primary text-primary-foreground'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-semibold">
                        {msg.isFromUser ? selectedConversation.user.username : 'Support Team'}
                      </span>
                    </div>
                    <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                    <p className="text-xs opacity-70 mt-1">
                      {new Date(msg.createdAt).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
          </div>

          <form onSubmit={handleSendReply} className="p-4 border-t bg-background">
            <div className="space-y-2">
              <Textarea
                value={replyMessage}
                onChange={(e) => setReplyMessage(e.target.value)}
                placeholder="Type your reply..."
                disabled={sendReplyMutation.isPending}
                rows={3}
                className="resize-none"
              />
              <Button
                type="submit"
                disabled={sendReplyMutation.isPending || !replyMessage.trim()}
                className="w-full"
              >
                {sendReplyMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Send Reply
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Support Conversations</h2>
        <p className="text-muted-foreground mt-1">
          View and respond to user messages
        </p>
      </div>

      {userConversations.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>No support conversations yet.</p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Last Message</TableHead>
              <TableHead>Messages</TableHead>
              <TableHead>Date</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {userConversations.map((conversation) => (
              <TableRow key={conversation.userId}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-semibold">
                      {conversation.user.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-medium">{conversation.user.username}</div>
                      <div className="text-sm text-muted-foreground">
                        {conversation.user.email}
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="max-w-xs truncate">
                  {conversation.lastMessage.message}
                </TableCell>
                <TableCell>
                  <span className="text-sm">{conversation.messages.length} messages</span>
                  {conversation.unreadCount > 0 && (
                    <span className="ml-2 px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-700">
                      {conversation.unreadCount} new
                    </span>
                  )}
                </TableCell>
                <TableCell>
                  {new Date(conversation.lastMessage.createdAt).toLocaleString()}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedUserId(conversation.userId)}
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    View Chat
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Card>
  );
}
