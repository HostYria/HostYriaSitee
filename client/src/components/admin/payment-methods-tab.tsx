import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Plus, Edit, Trash2 } from "lucide-react";
import type { PaymentMethod } from "@shared/schema";

export default function PaymentMethodsTab() {
  const { toast } = useToast();
  const [showDialog, setShowDialog] = useState(false);
  const [editingMethod, setEditingMethod] = useState<PaymentMethod | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    imageUrl: "",
    instructions: "",
    currency: "USD",
    usdRate: "1",
    isActive: true,
  });

  const { data: methods = [], isLoading } = useQuery<PaymentMethod[]>({
    queryKey: ["/api/payment-methods"],
  });

  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      return await apiRequest("POST", "/api/payment-methods", data);
    },
    onSuccess: () => {
      toast({ title: "Payment method created successfully" });
      queryClient.invalidateQueries({ queryKey: ["/api/payment-methods"] });
      setShowDialog(false);
      resetForm();
    },
    onError: (error: Error) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (data: { id: string } & typeof formData) => {
      return await apiRequest("PATCH", `/api/payment-methods/${data.id}`, {
        name: data.name,
        imageUrl: data.imageUrl,
        instructions: data.instructions,
        currency: data.currency,
        usdRate: data.usdRate,
        isActive: data.isActive,
      });
    },
    onSuccess: () => {
      toast({ title: "Payment method updated successfully" });
      queryClient.invalidateQueries({ queryKey: ["/api/payment-methods"] });
      setShowDialog(false);
      setEditingMethod(null);
      resetForm();
    },
    onError: (error: Error) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return await apiRequest("DELETE", `/api/payment-methods/${id}`);
    },
    onSuccess: () => {
      toast({ title: "Payment method deleted successfully" });
      queryClient.invalidateQueries({ queryKey: ["/api/payment-methods"] });
    },
    onError: (error: Error) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const resetForm = () => {
    setFormData({
      name: "",
      imageUrl: "",
      instructions: "",
      currency: "USD",
      usdRate: "1",
      isActive: true,
    });
  };

  const handleSubmit = () => {
    if (!formData.name || !formData.imageUrl || !formData.instructions) {
      toast({
        title: "Error",
        description: "Please fill all required fields",
        variant: "destructive",
      });
      return;
    }

    if (editingMethod) {
      updateMutation.mutate({ id: editingMethod.id, ...formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleEdit = (method: PaymentMethod) => {
    setEditingMethod(method);
    setFormData({
      name: method.name,
      imageUrl: method.imageUrl,
      instructions: method.instructions,
      currency: method.currency,
      usdRate: method.usdRate,
      isActive: method.isActive,
    });
    setShowDialog(true);
  };

  const handleAdd = () => {
    setEditingMethod(null);
    resetForm();
    setShowDialog(true);
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
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold">Payment Methods</h2>
            <p className="text-muted-foreground mt-1">
              Manage available payment methods for balance top-ups
            </p>
          </div>
          <Button onClick={handleAdd} data-testid="button-add-payment-method">
            <Plus className="h-4 w-4 mr-2" />
            Add Method
          </Button>
        </div>

        {methods.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No payment methods available. Add one to get started.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Image</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Currency</TableHead>
                <TableHead>USD Rate</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {methods.map((method) => (
                <TableRow key={method.id}>
                  <TableCell>
                    <img
                      src={method.imageUrl}
                      alt={method.name}
                      className="h-10 w-10 object-contain"
                    />
                  </TableCell>
                  <TableCell className="font-medium">{method.name}</TableCell>
                  <TableCell>{method.currency}</TableCell>
                  <TableCell>
                    {method.usdRate} {method.currency} = 1 USD
                  </TableCell>
                  <TableCell>
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${
                        method.isActive
                          ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                          : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
                      }`}
                      data-testid={`status-method-${method.id}`}
                    >
                      {method.isActive ? "Active" : "Inactive"}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(method)}
                      data-testid={`button-edit-method-${method.id}`}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteMutation.mutate(method.id)}
                      data-testid={`button-delete-method-${method.id}`}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingMethod ? "Edit Payment Method" : "Add Payment Method"}
            </DialogTitle>
            <DialogDescription>
              {editingMethod
                ? "Update the payment method details"
                : "Add a new payment method for balance top-ups"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Method Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Vodafone Cash, PayPal"
                data-testid="input-method-name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="imageUrl">Image URL *</Label>
              <Input
                id="imageUrl"
                value={formData.imageUrl}
                onChange={(e) => setFormData({ ...formData, imageUrl: e.target.value })}
                placeholder="https://example.com/image.png"
                data-testid="input-method-image"
              />
              {formData.imageUrl && (
                <div className="mt-2">
                  <img
                    src={formData.imageUrl}
                    alt="Preview"
                    className="h-20 w-20 object-contain border rounded"
                  />
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="currency">Currency *</Label>
              <Select
                value={formData.currency}
                onValueChange={(value) => setFormData({ ...formData, currency: value })}
              >
                <SelectTrigger data-testid="select-currency">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD</SelectItem>
                  <SelectItem value="EUR">EUR</SelectItem>
                  <SelectItem value="SYP">SYP</SelectItem>
                  <SelectItem value="RUB">RUB</SelectItem>
                  <SelectItem value="EGP">EGP</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="usdRate">Exchange Rate (to USD) *</Label>
              <Input
                id="usdRate"
                type="number"
                step="0.0001"
                value={formData.usdRate}
                onChange={(e) =>
                  setFormData({ ...formData, usdRate: e.target.value })
                }
                placeholder="e.g., 85 (means 85 RUB = 1 USD)"
                data-testid="input-usd-rate"
              />
              <p className="text-sm text-muted-foreground">
                {formData.usdRate} {formData.currency} = 1 USD
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="instructions">Payment Instructions *</Label>
              <Textarea
                id="instructions"
                value={formData.instructions}
                onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                placeholder="Enter payment instructions, account details, etc."
                rows={5}
                data-testid="input-method-instructions"
              />
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="isActive"
                checked={formData.isActive}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, isActive: checked })
                }
                data-testid="switch-active"
              />
              <Label htmlFor="isActive">Active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDialog(false)}
              data-testid="button-cancel"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={createMutation.isPending || updateMutation.isPending}
              data-testid="button-save"
            >
              {createMutation.isPending || updateMutation.isPending
                ? "Saving..."
                : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
