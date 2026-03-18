import { AlertCircle, LayoutDashboard } from "lucide-react";
import { PageLoader } from "@/components/shared/PageLoader";
import { EmptyState } from "@/components/shared/EmptyState";
import { IncomeVsSpendingWidget } from "@/components/dashboard/IncomeVsSpendingWidget";
import { SpendingByCategoriesWidget } from "@/components/dashboard/SpendingByCategoriesWidget";
import { SpendingTimelineWidget } from "@/components/dashboard/SpendingTimelineWidget";
import {
  useIncomeVsSpending,
  useSpendingByCategories,
  useSpendingTimeline,
  useSettings,
} from "@/api/hooks";
import { parseApiError } from "@/lib/errors";

export default function DashboardPage() {
  const { data: settings, isLoading: settingsLoading } = useSettings();
  const currency = settings?.primary_currency ?? "EUR";

  const {
    data: incomeData,
    isLoading: incomeLoading,
    isError: incomeError,
    error: incomeErr,
  } = useIncomeVsSpending(currency);

  const {
    data: categoriesData,
    isLoading: categoriesLoading,
    isError: categoriesError,
    error: categoriesErr,
  } = useSpendingByCategories(currency);

  const {
    data: timelineData,
    isLoading: timelineLoading,
    isError: timelineError,
    error: timelineErr,
  } = useSpendingTimeline(currency);

  const isLoading =
    settingsLoading || incomeLoading || categoriesLoading || timelineLoading;
  const hasError = incomeError || categoriesError || timelineError;
  const firstError = incomeErr || categoriesErr || timelineErr;

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
          Your financial overview for the current month ({currency})
        </p>
      </div>

      {hasNoData ? (
        <EmptyState
          icon={LayoutDashboard}
          title="No data yet"
          description="Start adding postings to see your dashboard come alive."
        />
      ) : (
        <>
          {incomeData && <IncomeVsSpendingWidget data={incomeData} />}
          {categoriesData && categoriesData.length > 0 && (
            <SpendingByCategoriesWidget rows={categoriesData} currency={currency} />
          )}
          {timelineData && <SpendingTimelineWidget data={timelineData} />}
        </>
      )}
    </div>
  );
}
