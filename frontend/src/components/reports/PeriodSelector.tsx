import { useState } from "react";
import { CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import type { ReportPeriod } from "@/api/types";

interface PeriodSelectorProps {
  period: ReportPeriod;
  onPeriodChange: (period: ReportPeriod) => void;
  referenceDate: Date | undefined;
  onReferenceDateChange: (date: Date | undefined) => void;
  excludeSavings: boolean;
  onExcludeSavingsChange: (value: boolean) => void;
  startDate?: string;
  endDate?: string;
}

function formatDateRange(startDate?: string, endDate?: string): string | null {
  if (!startDate || !endDate) return null;
  const start = new Date(startDate + "T00:00:00");
  const end = new Date(endDate + "T00:00:00");
  const fmt = new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  return `${fmt.format(start)} — ${fmt.format(end)}`;
}

export function PeriodSelector({
  period,
  onPeriodChange,
  referenceDate,
  onReferenceDateChange,
  excludeSavings,
  onExcludeSavingsChange,
  startDate,
  endDate,
}: PeriodSelectorProps) {
  const [calendarOpen, setCalendarOpen] = useState(false);
  const dateRange = formatDateRange(startDate, endDate);

  return (
    <div className="flex flex-wrap items-center gap-4">
      <ToggleGroup
        type="single"
        value={period}
        onValueChange={(val) => {
          if (val) onPeriodChange(val as ReportPeriod);
        }}
        aria-label="Select period"
      >
        <ToggleGroupItem value="week" aria-label="Week">
          Week
        </ToggleGroupItem>
        <ToggleGroupItem value="month" aria-label="Month">
          Month
        </ToggleGroupItem>
        <ToggleGroupItem value="year" aria-label="Year">
          Year
        </ToggleGroupItem>
      </ToggleGroup>

      <Popover open={calendarOpen} onOpenChange={setCalendarOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="w-[200px] justify-start gap-2">
            <CalendarIcon className="size-4" />
            {referenceDate ? format(referenceDate, "MMM d, yyyy") : "Today"}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={referenceDate}
            onSelect={(date) => {
              onReferenceDateChange(date);
              setCalendarOpen(false);
            }}
            initialFocus
          />
        </PopoverContent>
      </Popover>

      <div className="flex items-center gap-2">
        <Checkbox
          id="exclude-savings"
          checked={excludeSavings}
          onCheckedChange={(checked) =>
            onExcludeSavingsChange(checked === true)
          }
        />
        <Label htmlFor="exclude-savings" className="cursor-pointer">
          Exclude savings
        </Label>
      </div>

      {dateRange && (
        <span className="text-sm text-muted-foreground">{dateRange}</span>
      )}
    </div>
  );
}
