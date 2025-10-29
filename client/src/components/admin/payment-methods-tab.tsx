import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
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
import { useToast } from "@/hooks/use-toast";
import { Loader2, Plus, Edit, Trash2 } from "lucide-react";

interface PaymentMethod {
  id: string;
  name: string;
  details: string;
  isActive: boolean;
  createdAt: Date;
}

export default function PaymentMethodsTab() {
  const { toast } = useToast();
  const [showDialog, setShowDialog] = useState(false);
  const [editingMethod, setEditingMethod] = useState<PaymentMethod | null>(null);
  const [formData, setFormData] = useState({ name: "", details: "" });

  const { data: methods = [], isLoading } = useQuery<PaymentMethod[]>({
    queryKey: ["/api/payment-methods"],
  });

  const createMutation = useMutation({
    mutationFn: async (data: { name: string; details: string }) => {
      return await apiRequest("POST", "/api/payment-methods", data);
    },
    onSuccess: () => {
      toast({ title: "Payment method created successfully" });
      queryClient.invalidateQueries({ queryKey: ["/api/payment-methods"] });
      setShowDialog(false);
      setFormData({ name: "", details: "" });
    },
    onError: (error: Error) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (data: { id: string; name: string; details: string }) => {
      return await apiRequest("PATCH", `/api/payment-methods/${data.id}`, {
        name: data.name,
        details: data.details,
      });
    },
    onSuccess: () => {
      toast({ title: "Payment method updated successfully" });
      queryClient.invalidateQueries({ queryKey: ["/api/payment-methods"] });
      setShowDialog(false);
      setEditingMethod(null);
      setFormData({ name: "", details: "" });
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

  const handleSubmit = () => {
    if (!formData.name || !formData.details) {
      toast({
        title: "Error",
        description: "Please fill all fields",
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
    setFormData({ name: method.name, details: method.details });
    setShowDialog(true);
  };

  const handleAdd = () => {
    setEditingMethod(null);
    setFormData({ name: "", details: "" });
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
                <TableHead>Name</TableHead>
                <TableHead>Details</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {methods.map((method) => (
                <TableRow key={method.id}>
                  <TableCell className="font-medium">{method.name}</TableCell>
                  <TableCell>{method.details}</TableCell>
                  <TableCell>
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${
                        method.isActive
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-700"
                      }`}
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
        <DialogContent>
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
              <Label htmlFor="name">Method Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Bank Transfer, PayPal"
                data-testid="input-method-name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="details">Details/Instructions</Label>
              <Input
                id="details"
                value={formData.details}
                onChange={(e) => setFormData({ ...formData, details: e.target.value })}
                placeholder="e.g., Account number, email, etc."
                data-testid="input-method-details"
              />
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
