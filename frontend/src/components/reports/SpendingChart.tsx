import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import type { CategorySpendingResponse } from "@/api/types";
import { formatCurrency } from "@/lib/format";

const COLORS = [
  "#2563eb",
  "#dc2626",
  "#16a34a",
  "#ea580c",
  "#9333ea",
  "#0891b2",
  "#ca8a04",
  "#e11d48",
];

interface SpendingChartProps {
  rows: CategorySpendingResponse[];
  currency: string;
}

interface ChartDataItem {
  name: string;
  value: number;
}

function buildChartData(rows: CategorySpendingResponse[]): ChartDataItem[] {
  return rows
    .map((row) => ({
      name: row.parent_category_name,
      value: Math.abs(Number(row.total)),
    }))
    .sort((a, b) => b.value - a.value);
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
  currency: string;
}

function CustomTooltip({ active, payload, label, currency }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border bg-background px-3 py-2 text-sm shadow-md">
      <p className="font-medium">{label}</p>
      <p className="text-muted-foreground">
        {formatCurrency(String(payload[0].value), currency)}
      </p>
    </div>
  );
}

interface PieTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number }>;
  currency: string;
}

function PieTooltip({ active, payload, currency }: PieTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border bg-background px-3 py-2 text-sm shadow-md">
      <p className="font-medium">{payload[0].name}</p>
      <p className="text-muted-foreground">
        {formatCurrency(String(payload[0].value), currency)}
      </p>
    </div>
  );
}

export function SpendingChart({ rows, currency }: SpendingChartProps) {
  const chartData = buildChartData(rows);
  const total = chartData.reduce((sum, item) => sum + item.value, 0);
  const barHeight = Math.max(200, chartData.length * 44);

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-muted-foreground">Total spending</p>
        <p className="text-2xl font-bold">
          {formatCurrency(String(total), currency)}
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Horizontal Bar Chart */}
        <div>
          <p className="mb-2 text-sm font-medium text-muted-foreground">
            By category
          </p>
          <ResponsiveContainer width="100%" height={barHeight}>
            <BarChart
              layout="vertical"
              data={chartData}
              margin={{ top: 0, right: 16, bottom: 0, left: 0 }}
            >
              <XAxis
                type="number"
                tick={{ fill: "hsl(var(--foreground))", fontSize: 11 }}
                tickFormatter={(val: number) =>
                  formatCurrency(String(val), currency)
                }
              />
              <YAxis
                type="category"
                dataKey="name"
                width={120}
                tick={{ fill: "hsl(var(--foreground))", fontSize: 12 }}
              />
              <Tooltip
                content={(props) => (
                  <CustomTooltip
                    {...props}
                    label={props.label as string}
                    currency={currency}
                  />
                )}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {chartData.map((_, index) => (
                  <Cell
                    key={`bar-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div className="flex flex-col items-center">
          <p className="mb-2 self-start text-sm font-medium text-muted-foreground">
            Proportions
          </p>
          <ResponsiveContainer width="100%" height={Math.min(barHeight, 300)}>
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius="75%"
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
                labelLine={false}
              >
                {chartData.map((_, index) => (
                  <Cell
                    key={`pie-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                content={(props) => (
                  <PieTooltip
                    active={props.active}
                    payload={
                      props.payload as Array<{ name: string; value: number }>
                    }
                    currency={currency}
                  />
                )}
              />
            </PieChart>
          </ResponsiveContainer>

          {/* Legend */}
          <div className="mt-2 flex flex-wrap justify-center gap-3">
            {chartData.map((item, index) => (
              <div key={item.name} className="flex items-center gap-1.5">
                <span
                  className="inline-block size-3 rounded-sm"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-xs text-muted-foreground">
                  {item.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
