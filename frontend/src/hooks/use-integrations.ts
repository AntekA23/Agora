"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Types matching existing API
export type Platform = "instagram" | "facebook" | "linkedin" | "twitter";
export type ApiPlatform = "meta" | "google" | "linkedin" | "twitter";
export type ConnectionStatus = "connected" | "disconnected" | "expired" | "error";

export interface IntegrationStatus {
  connected: boolean;
  platform: ApiPlatform;
  account_name?: string;
  expires_at?: string;
}

export interface PlatformConnection {
  platform: Platform;
  status: ConnectionStatus;
  platform_username?: string;
  connected_at?: string;
  expires_at?: string;
  last_used_at?: string;
  last_error?: string;
  total_posts_published?: number;
}

export interface IntegrationsResponse {
  connections: PlatformConnection[];
}

export interface OAuthUrlResponse {
  oauth_url: string;
}

// Platform display info
export const platformInfo: Record<Platform, {
  label: string;
  icon: string;
  color: string;
  bgColor: string;
  description: string;
  apiPlatform: ApiPlatform;
}> = {
  instagram: {
    label: "Instagram",
    icon: "Instagram",
    color: "text-pink-500",
    bgColor: "bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400",
    description: "Publikuj posty i stories na Instagram",
    apiPlatform: "meta",
  },
  facebook: {
    label: "Facebook",
    icon: "Facebook",
    color: "text-blue-600",
    bgColor: "bg-blue-600",
    description: "Publikuj na swoją stronę Facebook",
    apiPlatform: "meta",
  },
  linkedin: {
    label: "LinkedIn",
    icon: "Linkedin",
    color: "text-blue-700",
    bgColor: "bg-blue-700",
    description: "Publikuj posty na LinkedIn",
    apiPlatform: "linkedin",
  },
  twitter: {
    label: "X (Twitter)",
    icon: "Twitter",
    color: "text-foreground",
    bgColor: "bg-foreground",
    description: "Publikuj tweety na X",
    apiPlatform: "twitter",
  },
};

// Helper to convert API response to frontend format
function convertToConnections(statuses: IntegrationStatus[]): PlatformConnection[] {
  const connections: PlatformConnection[] = [];

  // Find meta integration (covers both Instagram and Facebook)
  const metaStatus = statuses.find(s => s.platform === "meta");

  if (metaStatus) {
    // Instagram
    connections.push({
      platform: "instagram",
      status: metaStatus.connected ? "connected" : "disconnected",
      platform_username: metaStatus.account_name,
      expires_at: metaStatus.expires_at,
    });

    // Facebook
    connections.push({
      platform: "facebook",
      status: metaStatus.connected ? "connected" : "disconnected",
      platform_username: metaStatus.account_name,
      expires_at: metaStatus.expires_at,
    });
  } else {
    connections.push(
      { platform: "instagram", status: "disconnected" },
      { platform: "facebook", status: "disconnected" }
    );
  }

  // LinkedIn (not yet implemented in API)
  const linkedinStatus = statuses.find(s => s.platform === "linkedin");
  connections.push({
    platform: "linkedin",
    status: linkedinStatus?.connected ? "connected" : "disconnected",
    platform_username: linkedinStatus?.account_name,
  });

  // Twitter (not yet implemented in API)
  const twitterStatus = statuses.find(s => s.platform === "twitter");
  connections.push({
    platform: "twitter",
    status: twitterStatus?.connected ? "connected" : "disconnected",
    platform_username: twitterStatus?.account_name,
  });

  return connections;
}

// Hooks

/**
 * Get all platform connections for the current company
 */
export function useIntegrations() {
  return useQuery({
    queryKey: ["integrations"],
    queryFn: async () => {
      const statuses = await api.get<IntegrationStatus[]>("/integrations");
      return {
        connections: convertToConnections(statuses),
      };
    },
  });
}

/**
 * Get a single platform connection status
 */
export function useIntegrationStatus(platform: Platform) {
  const { data, ...rest } = useIntegrations();

  const connection = data?.connections.find(c => c.platform === platform);

  return {
    ...rest,
    data: connection,
    isConnected: connection?.status === "connected",
  };
}

/**
 * Initiate OAuth flow for a platform
 */
export function useConnectPlatform() {
  return useMutation({
    mutationFn: async (platform: Platform) => {
      const apiPlatform = platformInfo[platform].apiPlatform;
      return api.get<OAuthUrlResponse>(
        `/integrations/${apiPlatform}/connect`
      );
    },
    onSuccess: (data) => {
      // Redirect to OAuth URL
      window.location.href = data.oauth_url;
    },
  });
}

/**
 * Disconnect a platform
 */
export function useDisconnectPlatform() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (platform: Platform) => {
      const apiPlatform = platformInfo[platform].apiPlatform;
      return api.delete<{ status: string; platform: string }>(
        `/integrations/${apiPlatform}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });
}

/**
 * Refresh token for a platform (if supported)
 */
export function useRefreshPlatformToken() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (platform: Platform) => {
      const apiPlatform = platformInfo[platform].apiPlatform;
      // Note: This endpoint may need to be implemented in the backend
      return api.post<{ success: boolean }>(
        `/integrations/${apiPlatform}/refresh`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });
}

/**
 * Test publish to a platform
 */
export function useTestPublish() {
  return useMutation({
    mutationFn: async ({ platform, message, imageUrl }: {
      platform: Platform;
      message: string;
      imageUrl?: string;
    }) => {
      return api.post<{ success: boolean; post_id?: string; error?: string }>(
        "/integrations/meta/publish",
        {
          platform,
          content: message,
          image_url: imageUrl || "",
        }
      );
    },
  });
}

// Helper to check if any platform is connected
export function useHasConnectedPlatforms() {
  const { data, isLoading } = useIntegrations();

  const connectedCount = data?.connections.filter(
    c => c.status === "connected"
  ).length ?? 0;

  return {
    hasConnected: connectedCount > 0,
    connectedCount,
    isLoading,
  };
}
