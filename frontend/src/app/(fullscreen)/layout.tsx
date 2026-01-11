"use client";

import { ProtectedRoute } from "@/components/layout/protected-route";

export default function FullscreenLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        {children}
      </div>
    </ProtectedRoute>
  );
}
