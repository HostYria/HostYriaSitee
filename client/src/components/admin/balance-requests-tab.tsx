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
import { Loader2, Check, X, ExternalLink } from "lucide-react";
import type { BalanceRequest, PaymentMethod } from "@shared/schema";

interface ExtendedBalanceRequest extends BalanceRequest {
  user?: {
    username: string;
    email: string;
  };
  paymentMethod?: PaymentMethod;
}

export default function BalanceRequestsTab() {
  const { toast } = useToast();

  const { data: requests = [], isLoading } = useQuery<ExtendedBalanceRequest[]>({
    queryKey: ["/api/balance-requests"],
  });

  const { data: paymentMethods = [] } = useQuery<PaymentMethod[]>({
    queryKey: ["/api/payment-methods"],
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

  const getPaymentMethodById = (id: string) => {
    return paymentMethods.find((m) => m.id === id);
  };

  const calculateUsdAmount = (request: ExtendedBalanceRequest) => {
    const method = getPaymentMethodById(request.paymentMethodId);
    if (!method) return "0.00";
    const amountSent = parseFloat(request.amountSent);
    const usdRate = parseFloat(method.usdRate);
    return (amountSent / usdRate).toFixed(2);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const pendingCount = requests.filter(r => r.status === 'pending').length;
  const approvedCount = requests.filter(r => r.status === 'approved').length;
  const rejectedCount = requests.filter(r => r.status === 'rejected').length;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Pending</p>
              <h3 className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{pendingCount}</h3>
            </div>
            <div className="h-12 w-12 rounded-full bg-yellow-100 dark:bg-yellow-900 flex items-center justify-center">
              <Loader2 className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Approved</p>
              <h3 className="text-2xl font-bold text-green-600 dark:text-green-400">{approvedCount}</h3>
            </div>
            <div className="h-12 w-12 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
              <Check className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Rejected</p>
              <h3 className="text-2xl font-bold text-red-600 dark:text-red-400">{rejectedCount}</h3>
            </div>
            <div className="h-12 w-12 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center">
              <X className="h-6 w-6 text-red-600 dark:text-red-400" />
            </div>
          </div>
        </Card>
      </div>

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
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Amount Sent</TableHead>
                <TableHead>USD Value</TableHead>
                <TableHead>Payment Method</TableHead>
                <TableHead>Transaction ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {requests.map((request) => {
                const method = getPaymentMethodById(request.paymentMethodId);
                return (
                  <TableRow key={request.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{request.user?.username || "Unknown"}</div>
                        <div className="text-sm text-muted-foreground">
                          {request.user?.email || ""}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="font-medium">
                      {request.amountSent} {method?.currency || ""}
                    </TableCell>
                    <TableCell className="font-medium text-green-600 dark:text-green-400">
                      ${calculateUsdAmount(request)} USD
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {method?.imageUrl && (
                          <img
                            src={method.imageUrl}
                            alt={method.name}
                            className="h-6 w-6 object-contain"
                          />
                        )}
                        {method?.name || "Unknown"}
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {request.transactionId}
                    </TableCell>
                    <TableCell>
                      <span
                        className={`px-2 py-1 rounded-full text-xs ${
                          request.status === "approved"
                            ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                            : request.status === "rejected"
                            ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
                            : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
                        }`}
                        data-testid={`status-request-${request.id}`}
                      >
                        {request.status}
                      </span>
                    </TableCell>
                    <TableCell>
                      {new Date(request.createdAt).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-2 justify-end">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(request.screenshotUrl, "_blank")}
                          data-testid={`button-view-proof-${request.id}`}
                        >
                          <ExternalLink className="h-4 w-4 mr-1" />
                          View
                        </Button>
                        {request.status === "pending" && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                updateStatusMutation.mutate({
                                  id: request.id,
                                  status: "approved",
                                })
                              }
                              disabled={updateStatusMutation.isPending}
                              data-testid={`button-approve-${request.id}`}
                              className="text-green-600 hover:text-green-700 dark:text-green-400"
                            >
                              <Check className="h-4 w-4" />
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
                              disabled={updateStatusMutation.isPending}
                              data-testid={`button-reject-${request.id}`}
                              className="text-red-600 hover:text-red-700 dark:text-red-400"
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
      </Card>
    </div>
  );
}
