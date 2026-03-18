import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/format";
import type { DashboardPeriod, IncomeVsSpendingResponse } from "@/api/types";

interface Props {
  data: IncomeVsSpendingResponse;
  period?: DashboardPeriod;
}

function TrendIndicator({
  current,
  previous,
  upIsGood = false,
  periodLabel = "month",
}: {
  current: string;
  previous: string;
  /** When true, an increase is colored green (good). Default: false (increase = red = bad, for spending). */
  upIsGood?: boolean;
  periodLabel?: string;
}) {
  const curr = Number(current);
  const prev = Number(previous);
  if (prev === 0) return null;
  const pctChange = ((curr - prev) / prev) * 100;
  const isUp = pctChange > 0;
  const Icon = pctChange === 0 ? Minus : isUp ? TrendingUp : TrendingDown;

  const isPositive = upIsGood ? isUp : !isUp;

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs ${
        isPositive ? "text-green-500" : "text-red-500"
      }`}
    >
      <Icon className="size-3" />
      {Math.abs(pctChange).toFixed(0)}% vs prev {periodLabel}
    </span>
  );
}

export function IncomeVsSpendingWidget({ data, period = "month" }: Props) {
  const netPositive = Number(data.net_income) >= 0;

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Income
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
            {formatCurrency(data.total_income, data.currency)}
          </p>
          <TrendIndicator
            current={data.total_income}
            previous={data.prev_total_income}
            upIsGood
            periodLabel={period}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Spending
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-red-600 dark:text-red-400">
            {formatCurrency(data.total_spending, data.currency)}
          </p>
          {data.spending_ratio && (
            <span className="text-xs text-muted-foreground">
              {Number(data.spending_ratio).toFixed(0)}% of income
            </span>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Net Income
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p
            className={`text-2xl font-bold ${
              netPositive
                ? "text-green-600 dark:text-green-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            {formatCurrency(data.net_income, data.currency)}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
