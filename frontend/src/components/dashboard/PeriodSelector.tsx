import { ChevronLeft, ChevronRight } from "lucide-react";
import { format, addMonths, addYears } from "date-fns";
import { Button } from "@/components/ui/button";
import {
  ToggleGroup,
  ToggleGroupItem,
} from "@/components/ui/toggle-group";
import type { DashboardPeriod } from "@/api/types";

interface PeriodSelectorProps {
  period: DashboardPeriod;
  referenceDate: Date;
  onPeriodChange: (p: DashboardPeriod) => void;
  onReferenceDateChange: (d: Date) => void;
}

function formatPeriodLabel(period: DashboardPeriod, ref: Date): string {
  switch (period) {
    case "month":
      return format(ref, "MMMM yyyy");
    case "quarter": {
      const q = Math.ceil((ref.getMonth() + 1) / 3);
      return `Q${q} ${format(ref, "yyyy")}`;
    }
    case "year":
      return format(ref, "yyyy");
  }
}

function stepDate(ref: Date, period: DashboardPeriod, direction: 1 | -1): Date {
  switch (period) {
    case "month":
      return addMonths(ref, direction);
    case "quarter":
      return addMonths(ref, direction * 3);
    case "year":
      return addYears(ref, direction);
  }
}

function isNextDisabled(ref: Date, period: DashboardPeriod): boolean {
  const next = stepDate(ref, period, 1);
  return next > new Date();
}

const VALID_PERIODS: DashboardPeriod[] = ["month", "quarter", "year"];

export function PeriodSelector({
  period,
  referenceDate,
  onPeriodChange,
  onReferenceDateChange,
}: PeriodSelectorProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => onReferenceDateChange(stepDate(referenceDate, period, -1))}
        >
          <ChevronLeft className="size-4" />
        </Button>
        <span className="min-w-[140px] text-center text-sm font-medium">
          {formatPeriodLabel(period, referenceDate)}
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          disabled={isNextDisabled(referenceDate, period)}
          onClick={() => onReferenceDateChange(stepDate(referenceDate, period, 1))}
        >
          <ChevronRight className="size-4" />
        </Button>
      </div>

      <ToggleGroup
        value={[period]}
        onValueChange={(values: string[]) => {
          const newValue = values.find((v) => v !== period);
          const selected = newValue ?? values[0];
          if (selected && VALID_PERIODS.includes(selected as DashboardPeriod)) {
            onPeriodChange(selected as DashboardPeriod);
          }
        }}
        size="sm"
      >
        <ToggleGroupItem value="month">Month</ToggleGroupItem>
        <ToggleGroupItem value="quarter">Quarter</ToggleGroupItem>
        <ToggleGroupItem value="year">Year</ToggleGroupItem>
      </ToggleGroup>
    </div>
  );
}
