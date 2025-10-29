
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Upload, ArrowLeft } from "lucide-react";
import type { PaymentMethod } from "@shared/schema";

export default function TopUp() {
  const { toast } = useToast();
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod | null>(null);
  const [amountSent, setAmountSent] = useState("");
  const [transactionId, setTransactionId] = useState("");
  const [screenshot, setScreenshot] = useState<File | null>(null);

  const { data: paymentMethods = [], isLoading } = useQuery<PaymentMethod[]>({
    queryKey: ["/api/payment-methods"],
  });

  const submitRequestMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      return await apiRequest("POST", "/api/balance-requests", formData);
    },
    onSuccess: () => {
      toast({
        title: "Request submitted",
        description: "Your balance request has been submitted for review",
      });
      setSelectedMethod(null);
      setAmountSent("");
      setTransactionId("");
      setScreenshot(null);
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedMethod || !screenshot) return;

    const formData = new FormData();
    formData.append("paymentMethodId", selectedMethod.id);
    formData.append("amountSent", amountSent);
    formData.append("transactionId", transactionId);
    formData.append("screenshot", screenshot);

    submitRequestMutation.mutate(formData);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (selectedMethod) {
    return (
      <div className="p-6 space-y-6">
        <Button
          variant="ghost"
          onClick={() => setSelectedMethod(null)}
          className="mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to payment methods
        </Button>

        <div className="max-w-2xl mx-auto">
          <Card className="p-6 space-y-6">
            <div className="text-center">
              <img
                src={selectedMethod.imageUrl}
                alt={selectedMethod.name}
                className="h-24 w-24 object-contain mx-auto mb-4"
              />
              <h2 className="text-2xl font-bold">{selectedMethod.name}</h2>
            </div>

            <div className="bg-muted p-4 rounded-lg">
              <h3 className="font-semibold mb-2">Payment Instructions:</h3>
              <p className="whitespace-pre-wrap text-sm">{selectedMethod.instructions}</p>
              <p className="mt-2 text-sm font-medium">
                Rate: {selectedMethod.usdRate} {selectedMethod.currency} = 1 USD
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="amount">Amount you sent ({selectedMethod.currency})</Label>
                <Input
                  id="amount"
                  type="number"
                  value={amountSent}
                  onChange={(e) => setAmountSent(e.target.value)}
                  required
                  className="mt-1"
                  placeholder={`Enter amount in ${selectedMethod.currency}`}
                />
              </div>

              <div>
                <Label htmlFor="transaction-id">Transaction ID</Label>
                <Input
                  id="transaction-id"
                  value={transactionId}
                  onChange={(e) => setTransactionId(e.target.value)}
                  required
                  className="mt-1"
                  placeholder="Enter transaction ID"
                />
              </div>

              <div>
                <Label htmlFor="screenshot">Screenshot</Label>
                <Input
                  id="screenshot"
                  type="file"
                  accept="image/*"
                  onChange={(e) => setScreenshot(e.target.files?.[0] || null)}
                  required
                  className="mt-1"
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={submitRequestMutation.isPending}
              >
                {submitRequestMutation.isPending && (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                )}
                Submit Request
              </Button>
            </form>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Top Up Balance</h1>
        <p className="text-muted-foreground mt-1">
          Choose a payment method to add balance to your account
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {paymentMethods.filter(m => m.isActive).map((method) => (
          <Card
            key={method.id}
            className="p-6 cursor-pointer hover-elevate transition-all"
            onClick={() => setSelectedMethod(method)}
          >
            <div className="flex flex-col items-center text-center space-y-4">
              <img
                src={method.imageUrl}
                alt={method.name}
                className="h-20 w-20 object-contain"
              />
              <h3 className="font-semibold text-lg">{method.name}</h3>
              <p className="text-sm text-muted-foreground">
                {method.usdRate} {method.currency} = 1 USD
              </p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
