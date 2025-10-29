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
import { Loader2, Check, X } from "lucide-react";

interface BalanceRequest {
  id: string;
  userId: string;
  amount: number;
  paymentMethodId: string;
  proofImageUrl: string;
  status: string;
  createdAt: Date;
  user?: {
    username: string;
    email: string;
  };
  paymentMethod?: {
    name: string;
  };
}

export default function BalanceRequestsTab() {
  const { toast } = useToast();

  const { data: requests = [], isLoading } = useQuery<BalanceRequest[]>({
    queryKey: ["/api/balance-requests"],
  });

  const updateStatusMutation = useMutation({
    mutationFn: async (data: { id: string; status: string }) => {
      return await apiRequest("PATCH", `/api/balance-requests/${data.id}/status`, {
        status: data.status,
      });
    },
    onSuccess: () => {
      toast({ title: "Request status updated successfully" });
      queryClient.invalidateQueries({ queryKey: ["/api/balance-requests"] });
    },
    onError: (error: Error) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Balance Requests</h2>
        <p className="text-muted-foreground mt-1">
          Review and approve/reject user balance top-up requests
        </p>
      </div>

      {requests.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          No balance requests yet.
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Payment Method</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Date</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {requests.map((request) => (
              <TableRow key={request.id}>
                <TableCell>
                  <div>
                    <div className="font-medium">{request.user?.username}</div>
                    <div className="text-sm text-muted-foreground">
                      {request.user?.email}
                    </div>
                  </div>
                </TableCell>
                <TableCell className="font-medium">${request.amount.toFixed(2)}</TableCell>
                <TableCell>{request.paymentMethod?.name}</TableCell>
                <TableCell>
                  <span
                    className={`px-2 py-1 rounded-full text-xs ${
                      request.status === "approved"
                        ? "bg-green-100 text-green-700"
                        : request.status === "rejected"
                        ? "bg-red-100 text-red-700"
                        : "bg-yellow-100 text-yellow-700"
                    }`}
                  >
                    {request.status}
                  </span>
                </TableCell>
                <TableCell>
                  {new Date(request.createdAt).toLocaleDateString()}
                </TableCell>
                <TableCell className="text-right">
                  {request.status === "pending" && (
                    <div className="flex gap-2 justify-end">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          window.open(request.proofImageUrl, "_blank")
                        }
                        data-testid={`button-view-proof-${request.id}`}
                      >
                        View Proof
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          updateStatusMutation.mutate({
                            id: request.id,
                            status: "approved",
                          })
                        }
                        data-testid={`button-approve-${request.id}`}
                      >
                        <Check className="h-4 w-4 text-green-600" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          updateStatusMutation.mutate({
                            id: request.id,
                            status: "rejected",
                          })
                        }
                        data-testid={`button-reject-${request.id}`}
                      >
                        <X className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Card>
  );
}
