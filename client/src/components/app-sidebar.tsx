import { Folder, User, DollarSign, MessageSquare, LogOut, Code, Shield, Server, StickyNote } from "lucide-react";
import { Link, useLocation } from "wouter";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from "@/components/ui/sidebar";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import NotificationsPopover from "./notifications-popover";

export function AppSidebar() {
  const [location] = useLocation();
  const { user } = useAuth();

  const menuItems = [
    {
      title: "Repositories",
      url: "/repositories",
      icon: Folder,
    },
    {
      title: "Account",
      url: "/account",
      icon: User,
    },
    {
      title: "Top Up Balance",
      url: "/top-up",
      icon: DollarSign,
    },
    {
      title: "Support",
      url: "/support",
      icon: MessageSquare,
    },
    {
      title: "Notes",
      url: "/notes",
      icon: StickyNote,
    },
  ];

  const adminMenuItems = user?.isAdmin ? [
    {
      title: "Admin Panel",
      url: "/admin",
      icon: Shield,
    },
  ] : [];

  return (
    <Sidebar>
      <SidebarHeader>
          <SidebarMenu>
            <SidebarMenuItem>
              <div className="flex items-center justify-between w-full gap-2">
                <SidebarMenuButton size="lg" asChild className="flex-1">
                  <a href="/">
                    <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                      <Server className="size-4" />
                    </div>
                    <div className="grid flex-1 text-left text-sm leading-tight">
                      <span className="truncate font-semibold">HostYria Bot</span>
                      <span className="truncate text-xs">Bot Management</span>
                    </div>
                  </a>
                </SidebarMenuButton>
                <NotificationsPopover />
              </div>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={location === item.url}
                    data-testid={`link-${item.title.toLowerCase()}`}
                  >
                    <Link href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        {adminMenuItems.length > 0 && (
          <SidebarGroup>
            <SidebarGroupLabel>Administration</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {adminMenuItems.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={location === item.url}
                      data-testid={`link-${item.title.toLowerCase()}`}
                    >
                      <Link href={item.url}>
                        <item.icon className="h-4 w-4" />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>
      <SidebarFooter className="p-4 space-y-4">
        {user && (
          <>
            <div className="flex items-center gap-3 px-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback>
                  {user.username?.[0] || user.email?.[0] || "U"}
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-col flex-1">
                <span className="font-medium">
                  {user.username}
                </span>
              </div>
            </div>
            <div className="px-2 py-3 bg-primary/10 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Balance</span>
                <span className="text-lg font-bold text-primary">
                  ${parseFloat(user.balance || '0').toFixed(2)}
                </span>
              </div>
            </div>
          </>
        )}
        <Button
          variant="outline"
          className="w-full"
          onClick={async () => {
            try {
              const response = await fetch("/api/auth/logout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
              });
              if (response.ok) {
                window.location.href = "/login";
              }
            } catch (error) {
              console.error("Logout error:", error);
            }
          }}
          data-testid="button-logout"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Sign Out
        </Button>
      </SidebarFooter>
    </Sidebar>
  );
}