"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Instagram,
  Facebook,
  Linkedin,
  Twitter,
  Check,
  X,
  AlertTriangle,
  RefreshCw,
  Loader2,
  Unplug,
  Plug,
  Link2,
} from "lucide-react";
import {
  useIntegrations,
  useConnectPlatform,
  useDisconnectPlatform,
  platformInfo,
  type Platform,
  type ConnectionStatus,
} from "@/hooks/use-integrations";
import { useToast } from "@/hooks/use-toast";
import { formatDistanceToNow } from "date-fns";
import { pl } from "date-fns/locale";

const platformIcons: Record<Platform, typeof Instagram> = {
  instagram: Instagram,
  facebook: Facebook,
  linkedin: Linkedin,
  twitter: Twitter,
};

const statusConfig: Record<ConnectionStatus, {
  label: string;
  variant: "default" | "secondary" | "destructive" | "outline";
  icon: typeof Check;
}> = {
  connected: {
    label: "Połączono",
    variant: "default",
    icon: Check,
  },
  disconnected: {
    label: "Niepołączono",
    variant: "secondary",
    icon: X,
  },
  expired: {
    label: "Wygasło",
    variant: "destructive",
    icon: AlertTriangle,
  },
  error: {
    label: "Błąd",
    variant: "destructive",
    icon: AlertTriangle,
  },
};

export function IntegrationsSettings() {
  const { toast } = useToast();
  const { data, isLoading, error } = useIntegrations();
  const connectPlatform = useConnectPlatform();
  const disconnectPlatform = useDisconnectPlatform();

  const [disconnectDialog, setDisconnectDialog] = useState<Platform | null>(null);

  // Get connection for a platform
  const getConnection = (platform: Platform) => {
    return data?.connections.find(c => c.platform === platform);
  };

  // Check if Meta is connected (for showing linked status)
  const isMetaConnected = () => {
    const instagram = getConnection("instagram");
    return instagram?.status === "connected";
  };

  const handleConnect = (platform: Platform) => {
    connectPlatform.mutate(platform, {
      onError: () => {
        toast({
          title: "Błąd",
          description: `Nie udało się połączyć z ${platformInfo[platform].label}`,
          variant: "destructive",
        });
      },
    });
  };

  const handleDisconnect = (platform: Platform) => {
    // For Instagram/Facebook, we disconnect the meta integration
    const platformToDisconnect = platform === "instagram" || platform === "facebook" ? "instagram" : platform;

    disconnectPlatform.mutate(platformToDisconnect, {
      onSuccess: () => {
        toast({
          title: "Rozłączono",
          description: platform === "instagram" || platform === "facebook"
            ? "Rozłączono z Meta (Instagram i Facebook)"
            : `Rozłączono z ${platformInfo[platform].label}`,
        });
        setDisconnectDialog(null);
      },
      onError: () => {
        toast({
          title: "Błąd",
          description: "Nie udało się rozłączyć",
          variant: "destructive",
        });
      },
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
          <p className="text-lg font-medium">Nie udało się załadować integracji</p>
          <p className="text-sm text-muted-foreground">Spróbuj odświeżyć stronę</p>
        </CardContent>
      </Card>
    );
  }

  const connectedCount = data?.connections.filter(c => c.status === "connected").length ?? 0;
  const metaConnected = isMetaConnected();

  return (
    <div className="space-y-6">
      {/* Summary */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Plug className="h-5 w-5 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Połączone platformy:
              </span>
              <span className="font-medium">{connectedCount > 0 ? Math.ceil(connectedCount / 2) : 0} z 3</span>
            </div>
            {connectedCount > 0 && (
              <Badge variant="secondary" className="bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                <Check className="h-3 w-3 mr-1" />
                Auto-publikacja aktywna
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Meta (Instagram + Facebook) Card */}
      <Card className="overflow-hidden">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="flex -space-x-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 text-white z-10">
                  <Instagram className="h-4 w-4" />
                </div>
                <div className="p-2 rounded-lg bg-blue-600 text-white">
                  <Facebook className="h-4 w-4" />
                </div>
              </div>
              <div>
                <CardTitle className="text-lg">Meta (Instagram + Facebook)</CardTitle>
                <CardDescription className="text-sm">
                  Jedno połączenie dla obu platform
                </CardDescription>
              </div>
            </div>
            <Badge variant={metaConnected ? "default" : "secondary"} className="shrink-0">
              {metaConnected ? (
                <>
                  <Check className="h-3 w-3 mr-1" />
                  Połączono
                </>
              ) : (
                <>
                  <X className="h-3 w-3 mr-1" />
                  Niepołączono
                </>
              )}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Connection Info */}
          {metaConnected && (
            <div className="space-y-2 text-sm">
              {getConnection("instagram")?.platform_username && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Konto:</span>
                  <span className="font-medium">{getConnection("instagram")?.platform_username}</span>
                </div>
              )}
              <div className="flex items-center gap-2 text-muted-foreground">
                <Link2 className="h-4 w-4" />
                <span>Publikuj na Instagram i Facebook jednocześnie</span>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            {!metaConnected ? (
              <Button
                onClick={() => handleConnect("instagram")}
                disabled={connectPlatform.isPending}
                className="flex-1"
              >
                {connectPlatform.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Plug className="h-4 w-4 mr-2" />
                )}
                Połącz z Meta
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={() => setDisconnectDialog("instagram")}
                className="flex-1"
              >
                <Unplug className="h-4 w-4 mr-2" />
                Rozłącz
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Other Platforms */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* LinkedIn */}
        {(() => {
          const connection = getConnection("linkedin");
          const info = platformInfo.linkedin;
          const status = connection?.status ?? "disconnected";
          const statusInfo = statusConfig[status];
          const StatusIcon = statusInfo.icon;
          const isConnected = status === "connected";

          return (
            <Card className="overflow-hidden">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2.5 rounded-lg ${info.bgColor} text-white`}>
                      <Linkedin className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{info.label}</CardTitle>
                      <CardDescription className="text-sm">
                        {info.description}
                      </CardDescription>
                    </div>
                  </div>
                  <Badge variant={statusInfo.variant} className="shrink-0">
                    <StatusIcon className="h-3 w-3 mr-1" />
                    {statusInfo.label}
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {isConnected && connection?.platform_username && (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Konto:</span>
                      <span className="font-medium">@{connection.platform_username}</span>
                    </div>
                  </div>
                )}

                <div className="flex gap-2">
                  {!isConnected ? (
                    <Button
                      onClick={() => handleConnect("linkedin")}
                      disabled={connectPlatform.isPending}
                      className="flex-1"
                      variant="outline"
                    >
                      {connectPlatform.isPending ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Plug className="h-4 w-4 mr-2" />
                      )}
                      Wkrótce
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      onClick={() => setDisconnectDialog("linkedin")}
                      className="flex-1"
                    >
                      <Unplug className="h-4 w-4 mr-2" />
                      Rozłącz
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })()}

        {/* Twitter/X */}
        {(() => {
          const connection = getConnection("twitter");
          const info = platformInfo.twitter;
          const status = connection?.status ?? "disconnected";
          const statusInfo = statusConfig[status];
          const StatusIcon = statusInfo.icon;
          const isConnected = status === "connected";

          return (
            <Card className="overflow-hidden">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2.5 rounded-lg ${info.bgColor} text-white`}>
                      <Twitter className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{info.label}</CardTitle>
                      <CardDescription className="text-sm">
                        {info.description}
                      </CardDescription>
                    </div>
                  </div>
                  <Badge variant={statusInfo.variant} className="shrink-0">
                    <StatusIcon className="h-3 w-3 mr-1" />
                    {statusInfo.label}
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {isConnected && connection?.platform_username && (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Konto:</span>
                      <span className="font-medium">@{connection.platform_username}</span>
                    </div>
                  </div>
                )}

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    disabled
                    className="flex-1"
                  >
                    <Plug className="h-4 w-4 mr-2" />
                    Wkrótce
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })()}
      </div>

      {/* Info Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Jak działa auto-publikacja?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-muted-foreground">
          <div className="flex gap-3">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-medium">
              1
            </div>
            <p>
              Połącz swoje konta social media za pomocą bezpiecznej autoryzacji OAuth.
              Nigdy nie przechowujemy Twoich haseł.
            </p>
          </div>
          <div className="flex gap-3">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-medium">
              2
            </div>
            <p>
              Zaplanuj treści w kolejce z datą i godziną publikacji.
            </p>
          </div>
          <div className="flex gap-3">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-medium">
              3
            </div>
            <p>
              System automatycznie opublikuje treści o zaplanowanej porze.
              Otrzymasz powiadomienie o sukcesie lub błędzie.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Disconnect Confirmation Dialog */}
      <AlertDialog open={!!disconnectDialog} onOpenChange={() => setDisconnectDialog(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {disconnectDialog === "instagram" || disconnectDialog === "facebook"
                ? "Rozłączyć Meta (Instagram i Facebook)?"
                : `Rozłączyć ${disconnectDialog && platformInfo[disconnectDialog].label}?`
              }
            </AlertDialogTitle>
            <AlertDialogDescription>
              {disconnectDialog === "instagram" || disconnectDialog === "facebook"
                ? "Po rozłączeniu nie będziesz mógł automatycznie publikować treści na Instagramie ani Facebooku. Zaplanowane treści dla tych platform nie zostaną opublikowane."
                : "Po rozłączeniu nie będziesz mógł automatycznie publikować treści na tej platformie. Zaplanowane treści dla tej platformy nie zostaną opublikowane."
              }
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Anuluj</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => disconnectDialog && handleDisconnect(disconnectDialog)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {disconnectPlatform.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Unplug className="h-4 w-4 mr-2" />
              )}
              Rozłącz
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
