"use client";

import { useRouter } from "next/navigation";
import { LogOut, User } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "./theme-toggle";
import { NotificationBell } from "@/components/notifications/notification-bell";

export function Navbar() {
  const router = useRouter();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    router.push("/auth/login");
  };

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center justify-between px-4">
        <div className="md:hidden">
          <span className="text-xl font-bold">Agora</span>
        </div>
        <div className="hidden md:block" />
        <div className="flex items-center gap-2">
          <ThemeToggle />
          {user && <NotificationBell />}
          {user && (
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-2 text-sm">
                <User className="h-4 w-4" />
                <span>{user.name}</span>
              </div>
              <Button variant="ghost" size="icon" onClick={handleLogout}>
                <LogOut className="h-5 w-5" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
