
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Users, CreditCard, MessageSquare, DollarSign } from "lucide-react";
import { useLocation } from "wouter";

import UsersTab from "@/components/admin/users-tab";
import PaymentMethodsTab from "@/components/admin/payment-methods-tab";
import BalanceRequestsTab from "@/components/admin/balance-requests-tab";
import SupportTab from "@/components/admin/support-tab";

export default function AdminPanel() {
  const { user } = useAuth();
  const [, setLocation] = useLocation();

  if (!user?.isAdmin) {
    setLocation("/repositories");
    return null;
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Admin Panel</h1>
        <p className="text-muted-foreground mt-1">
          Manage users, payment methods, and support requests
        </p>
      </div>

      <Tabs defaultValue="users">
        <TabsList className="grid w-full grid-cols-4 lg:w-auto">
          <TabsTrigger value="users">
            <Users className="h-4 w-4 mr-2" />
            Users
          </TabsTrigger>
          <TabsTrigger value="payments">
            <CreditCard className="h-4 w-4 mr-2" />
            Payment Methods
          </TabsTrigger>
          <TabsTrigger value="balance-requests">
            <DollarSign className="h-4 w-4 mr-2" />
            Balance Requests
          </TabsTrigger>
          <TabsTrigger value="support">
            <MessageSquare className="h-4 w-4 mr-2" />
            Support
          </TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="mt-6">
          <UsersTab />
        </TabsContent>

        <TabsContent value="payments" className="mt-6">
          <PaymentMethodsTab />
        </TabsContent>

        <TabsContent value="balance-requests" className="mt-6">
          <BalanceRequestsTab />
        </TabsContent>

        <TabsContent value="support" className="mt-6">
          <SupportTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
