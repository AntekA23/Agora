"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  useCalendarEvents,
  CalendarEvent,
  getEventTypeColor,
} from "@/hooks/use-suggestions";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Plus,
  Gift,
  TrendingUp,
  Sun,
  Loader2,
  AlertCircle,
} from "lucide-react";

// Event type icons
const eventTypeIcons: Record<string, typeof Gift> = {
  holiday: Gift,
  commercial: TrendingUp,
  seasonal: Sun,
};

interface ContentCalendarProps {
  daysAhead?: number;
}

export function ContentCalendar({ daysAhead = 30 }: ContentCalendarProps) {
  const router = useRouter();
  const { data: events, isLoading, error } = useCalendarEvents(daysAhead);

  const [currentWeekStart, setCurrentWeekStart] = React.useState(() => {
    const today = new Date();
    const day = today.getDay();
    const diff = today.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(today.setDate(diff));
  });

  const getWeekDays = () => {
    const days = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(currentWeekStart);
      date.setDate(currentWeekStart.getDate() + i);
      days.push(date);
    }
    return days;
  };

  const weekDays = getWeekDays();

  const goToPreviousWeek = () => {
    const newStart = new Date(currentWeekStart);
    newStart.setDate(newStart.getDate() - 7);
    setCurrentWeekStart(newStart);
  };

  const goToNextWeek = () => {
    const newStart = new Date(currentWeekStart);
    newStart.setDate(newStart.getDate() + 7);
    setCurrentWeekStart(newStart);
  };

  const goToCurrentWeek = () => {
    const today = new Date();
    const day = today.getDay();
    const diff = today.getDate() - day + (day === 0 ? -6 : 1);
    setCurrentWeekStart(new Date(today.setDate(diff)));
  };

  const getEventsForDate = (date: Date): CalendarEvent[] => {
    if (!events) return [];
    const dateStr = date.toISOString().split("T")[0];
    return events.filter((event) => event.date_full === dateStr);
  };

  const isToday = (date: Date): boolean => {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  const handleCreatePost = (event: CalendarEvent) => {
    const params = new URLSearchParams();
    params.set("brief", `Post z okazji ${event.name}`);
    router.push(`/marketing?${params.toString()}`);
  };

  const formatWeekRange = () => {
    const start = weekDays[0];
    const end = weekDays[6];
    const startMonth = start.toLocaleDateString("pl-PL", { month: "short" });
    const endMonth = end.toLocaleDateString("pl-PL", { month: "short" });

    if (startMonth === endMonth) {
      return `${start.getDate()} - ${end.getDate()} ${startMonth}`;
    }
    return `${start.getDate()} ${startMonth} - ${end.getDate()} ${endMonth}`;
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12 text-muted-foreground">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span>Nie mozna zaladowac kalendarza</span>
        </CardContent>
      </Card>
    );
  }

  const dayNames = ["Pon", "Wto", "Sro", "Czw", "Pia", "Sob", "Nie"];

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Kalendarz contentu
          </CardTitle>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" onClick={goToPreviousWeek}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={goToCurrentWeek}
              className="text-xs"
            >
              {formatWeekRange()}
            </Button>
            <Button variant="ghost" size="icon" onClick={goToNextWeek}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Week grid */}
        <div className="grid grid-cols-7 gap-1">
          {/* Day headers */}
          {dayNames.map((day) => (
            <div
              key={day}
              className="text-center text-xs text-muted-foreground py-1"
            >
              {day}
            </div>
          ))}

          {/* Day cells */}
          {weekDays.map((date, idx) => {
            const dayEvents = getEventsForDate(date);
            const today = isToday(date);

            return (
              <div
                key={idx}
                className={`min-h-[80px] p-1 rounded-lg border transition-colors ${
                  today
                    ? "border-primary bg-primary/5"
                    : "border-transparent hover:bg-muted/50"
                }`}
              >
                <div
                  className={`text-xs font-medium text-center mb-1 ${
                    today ? "text-primary" : "text-muted-foreground"
                  }`}
                >
                  {date.getDate()}
                </div>

                {/* Events */}
                <div className="space-y-1">
                  {dayEvents.map((event, eventIdx) => {
                    const EventIcon = eventTypeIcons[event.type] || Calendar;
                    return (
                      <button
                        key={eventIdx}
                        onClick={() => handleCreatePost(event)}
                        className={`w-full text-left p-1 rounded text-xs transition-colors ${getEventTypeColor(
                          event.type
                        )} hover:opacity-80`}
                        title={event.marketing_tip}
                      >
                        <div className="flex items-center gap-1">
                          <EventIcon className="h-3 w-3 shrink-0" />
                          <span className="truncate">{event.name}</span>
                        </div>
                      </button>
                    );
                  })}

                  {/* Add button for days without events */}
                  {dayEvents.length === 0 && !today && (
                    <button
                      onClick={() => {
                        const params = new URLSearchParams();
                        params.set(
                          "brief",
                          `Post na ${date.toLocaleDateString("pl-PL")}`
                        );
                        router.push(`/marketing?${params.toString()}`);
                      }}
                      className="w-full flex items-center justify-center p-1 rounded text-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/50 transition-colors"
                    >
                      <Plus className="h-3 w-3" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-4 mt-4 pt-3 border-t">
          <div className="flex items-center gap-1 text-xs">
            <div className="w-3 h-3 rounded bg-red-500/10" />
            <span className="text-muted-foreground">Swieta</span>
          </div>
          <div className="flex items-center gap-1 text-xs">
            <div className="w-3 h-3 rounded bg-green-500/10" />
            <span className="text-muted-foreground">Komercyjne</span>
          </div>
          <div className="flex items-center gap-1 text-xs">
            <div className="w-3 h-3 rounded bg-blue-500/10" />
            <span className="text-muted-foreground">Sezonowe</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
