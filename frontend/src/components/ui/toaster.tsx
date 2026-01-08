"use client";

import { useToast } from "@/hooks/use-toast";
import { Toast } from "./toast";

export function Toaster() {
  const { toasts, dismiss } = useToast();

  return (
    <div className="fixed bottom-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px]">
      {toasts.map((toast) => (
        <div key={toast.id} className="mb-2">
          <Toast
            title={toast.title}
            description={toast.description}
            variant={toast.variant}
            onDismiss={() => dismiss(toast.id)}
          />
        </div>
      ))}
    </div>
  );
}
