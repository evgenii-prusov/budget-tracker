import { useState } from "react";
import { format } from "date-fns";
import { AlertCircle, LayoutDashboard } from "lucide-react";
import { PageLoader } from "@/components/shared/PageLoader";
import { EmptyState } from "@/components/shared/EmptyState";
import { IncomeVsSpendingWidget } from "@/components/dashboard/IncomeVsSpendingWidget";
import { SpendingByCategoriesWidget } from "@/components/dashboard/SpendingByCategoriesWidget";
import { SpendingTimelineWidget } from "@/components/dashboard/SpendingTimelineWidget";
import { PeriodSelector } from "@/components/dashboard/PeriodSelector";
import {
  useIncomeVsSpending,
  useSpendingByCategories,
  useSpendingTimeline,
  useSettings,
} from "@/api/hooks";
import { parseApiError } from "@/lib/errors";
import type { DashboardPeriod } from "@/api/types";

export default function DashboardPage() {
  const [period, setPeriod] = useState<DashboardPeriod>("month");
  const [referenceDate, setReferenceDate] = useState(new Date());

  const refDateStr = format(referenceDate, "yyyy-MM-dd");

  const {
    data: settings,
    isLoading: settingsLoading,
    isError: settingsError,
    error: settingsErr,
  } = useSettings();
  const currency = settings?.primary_currency ?? "EUR";

  const {
    data: incomeData,
    isLoading: incomeLoading,
    isError: incomeError,
    error: incomeErr,
  } = useIncomeVsSpending(currency, refDateStr, true, period);

  const {
    data: categoriesData,
    isLoading: categoriesLoading,
    isError: categoriesError,
    error: categoriesErr,
  } = useSpendingByCategories(currency, refDateStr, true, period);

  const {
    data: timelineData,
    isLoading: timelineLoading,
    isError: timelineError,
    error: timelineErr,
  } = useSpendingTimeline(currency, refDateStr, true, period);

  const isLoading =
    settingsLoading || incomeLoading || categoriesLoading || timelineLoading;
  const hasError = settingsError || incomeError || categoriesError || timelineError;
  const firstError = settingsErr || incomeErr || categoriesErr || timelineErr;

  if (isLoading) return <PageLoader />;

  if (hasError) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="Failed to load dashboard"
        description={parseApiError(firstError)}
      />
    );
  }

  const hasNoData =
    incomeData &&
    Number(incomeData.total_income) === 0 &&
    Number(incomeData.total_spending) === 0 &&
    (!categoriesData || categoriesData.length === 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Your financial overview ({currency})
        </p>
      </div>

      <PeriodSelector
        period={period}
        referenceDate={referenceDate}
        onPeriodChange={setPeriod}
        onReferenceDateChange={setReferenceDate}
      />

      {hasNoData ? (
        <EmptyState
          icon={LayoutDashboard}
          title="No data yet"
          description="Start adding postings to see your dashboard come alive."
        />
      ) : (
        <>
          {incomeData && <IncomeVsSpendingWidget data={incomeData} period={period} />}
          {categoriesData && categoriesData.length > 0 && (
            <SpendingByCategoriesWidget rows={categoriesData} currency={currency} />
          )}
          {timelineData && <SpendingTimelineWidget data={timelineData} period={period} />}
        </>
      )}
    </div>
  );
}
