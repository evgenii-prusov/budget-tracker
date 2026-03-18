import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { format, parseISO } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/format";
import type { DashboardPeriod, SpendingTimelineResponse } from "@/api/types";

interface Props {
  data: SpendingTimelineResponse;
  period?: DashboardPeriod;
}

interface ChartEntry {
  day: number;
  label: string;
  current: number;
  previous: number | null;
}

function buildChartData(data: SpendingTimelineResponse): ChartEntry[] {
  const currentMap = new Map<number, number>();
  const previousMap = new Map<number, number>();

  for (const entry of data.current_period) {
    const d = parseISO(entry.spending_date);
    currentMap.set(d.getDate(), Number(entry.cumulative_total));
  }

  for (const entry of data.previous_period) {
    const d = parseISO(entry.spending_date);
    previousMap.set(d.getDate(), Number(entry.cumulative_total));
  }

  // Build entries for all days that have data in either period
  const allDays = new Set([...currentMap.keys(), ...previousMap.keys()]);
  const sortedDays = [...allDays].sort((a, b) => a - b);

  let lastCurrent = 0;
  let lastPrevious: number | null = null;

  return sortedDays.map((day) => {
    if (currentMap.has(day)) lastCurrent = currentMap.get(day)!;
    if (previousMap.has(day)) lastPrevious = previousMap.get(day)!;

    return {
      day,
      label: `Day ${day}`,
      current: currentMap.has(day) ? currentMap.get(day)! : lastCurrent,
      previous: previousMap.has(day)
        ? previousMap.get(day)!
        : lastPrevious,
    };
  });
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number | null; dataKey: string; color: string }>;
  label?: string;
  currency: string;
  periodLabel: string;
}

function TimelineTooltip({
  active,
  payload,
  label,
  currency,
  periodLabel,
}: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border bg-background px-3 py-2 text-sm shadow-md">
      <p className="mb-1 font-medium">{label}</p>
      {payload.map((entry) => {
        if (entry.value == null) return null;
        return (
          <p key={entry.dataKey} style={{ color: entry.color }}>
            {entry.dataKey === "current" ? `This ${periodLabel}` : `Last ${periodLabel}`}:{" "}
            {formatCurrency(String(entry.value), currency)}
          </p>
        );
      })}
    </div>
  );
}

export function SpendingTimelineWidget({ data, period = "month" }: Props) {
  const periodLabel = period;
  const chartData = buildChartData(data);
  const projectedTotal = data.projected_total
    ? Number(data.projected_total)
    : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Spending Timeline</CardTitle>
        <div className="flex items-baseline gap-4">
          <p className="text-sm text-muted-foreground">
            {format(parseISO(data.start_date), "MMM d")} –{" "}
            {format(parseISO(data.end_date), "MMM d, yyyy")}
          </p>
          {projectedTotal !== null && (
            <p className="text-sm text-muted-foreground">
              Projected:{" "}
              <span className="font-medium text-foreground">
                {formatCurrency(String(projectedTotal), data.currency)}
              </span>
            </p>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No spending data for this period
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 16, bottom: 0, left: 0 }}
            >
              <XAxis
                dataKey="label"
                tick={{ fill: "hsl(var(--foreground))", fontSize: 11 }}
              />
              <YAxis
                tick={{ fill: "hsl(var(--foreground))", fontSize: 11 }}
                tickFormatter={(val: number) =>
                  formatCurrency(String(val), data.currency)
                }
              />
              <Tooltip
                content={(props) => (
                  <TimelineTooltip
                    active={props.active}
                    payload={
                      props.payload as Array<{
                        value: number;
                        dataKey: string;
                        color: string;
                      }>
                    }
                    label={props.label as string}
                    currency={data.currency}
                    periodLabel={periodLabel}
                  />
                )}
              />
              {projectedTotal !== null && (
                <ReferenceLine
                  y={projectedTotal}
                  stroke="hsl(var(--muted-foreground))"
                  strokeDasharray="4 4"
                  label={{
                    value: "Projected",
                    position: "right",
                    fill: "hsl(var(--muted-foreground))",
                    fontSize: 11,
                  }}
                />
              )}
              <Area
                type="monotone"
                dataKey="previous"
                stroke="#94a3b8"
                fill="#94a3b8"
                fillOpacity={0.1}
                strokeWidth={1.5}
                strokeDasharray="4 4"
                connectNulls
                name={`Last ${periodLabel}`}
              />
              <Area
                type="monotone"
                dataKey="current"
                stroke="#2563eb"
                fill="#2563eb"
                fillOpacity={0.15}
                strokeWidth={2}
                name={`This ${periodLabel}`}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
