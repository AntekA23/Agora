import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Polish timezone constant
const POLISH_TIMEZONE = "Europe/Warsaw";

/**
 * Format date to Polish time (Europe/Warsaw timezone)
 */
export function formatDatePL(
  date: string | Date | null | undefined,
  options?: Intl.DateTimeFormatOptions
): string {
  if (!date) return "";

  const dateObj = typeof date === "string" ? new Date(date) : date;

  return dateObj.toLocaleString("pl-PL", {
    timeZone: POLISH_TIMEZONE,
    ...options,
  });
}

/**
 * Format time only (HH:MM) in Polish timezone
 */
export function formatTimePL(date: string | Date | null | undefined): string {
  return formatDatePL(date, {
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Format date and time in Polish timezone
 */
export function formatDateTimePL(date: string | Date | null | undefined): string {
  return formatDatePL(date, {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Format date only in Polish timezone
 */
export function formatDateOnlyPL(date: string | Date | null | undefined): string {
  return formatDatePL(date, {
    day: "numeric",
    month: "short",
  });
}

/**
 * Format relative date (dzisiaj, wczoraj, X dni temu) in Polish timezone
 */
export function formatRelativeDatePL(date: string | Date | null | undefined): string {
  if (!date) return "";

  const dateObj = typeof date === "string" ? new Date(date) : date;
  const now = new Date();

  // Convert both dates to Polish timezone for comparison
  const dateInPL = new Date(dateObj.toLocaleString("en-US", { timeZone: POLISH_TIMEZONE }));
  const nowInPL = new Date(now.toLocaleString("en-US", { timeZone: POLISH_TIMEZONE }));

  // Get start of day for both dates
  const startOfDatePL = new Date(dateInPL.getFullYear(), dateInPL.getMonth(), dateInPL.getDate());
  const startOfNowPL = new Date(nowInPL.getFullYear(), nowInPL.getMonth(), nowInPL.getDate());

  const diffMs = startOfNowPL.getTime() - startOfDatePL.getTime();
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffDays === 0) {
    return formatTimePL(dateObj);
  } else if (diffDays === 1) {
    return "Wczoraj";
  } else if (diffDays < 7) {
    return `${diffDays} dni temu`;
  } else {
    return formatDateOnlyPL(dateObj);
  }
}
