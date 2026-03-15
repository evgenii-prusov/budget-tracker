import { useState, useEffect } from "react";
import { BarChart2, AlertCircle } from "lucide-react";
import { format } from "date-fns";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageLoader } from "@/components/shared/PageLoader";
import { EmptyState } from "@/components/shared/EmptyState";
import { PeriodSelector } from "@/components/reports/PeriodSelector";
import { SpendingChart } from "@/components/reports/SpendingChart";
import { SpendingTable } from "@/components/reports/SpendingTable";
import { useSpendingReport } from "@/api/hooks";
import { parseApiError } from "@/lib/errors";
import type { ReportPeriod } from "@/api/types";

export default function ReportsPage() {
  const [period, setPeriod] = useState<ReportPeriod>("month");
  const [referenceDate, setReferenceDate] = useState<Date | undefined>(
    undefined,
  );
  const [excludeSavings, setExcludeSavings] = useState(true);

  const referenceDateStr = referenceDate
    ? format(referenceDate, "yyyy-MM-dd")
    : undefined;

  const { data, isLoading, isError, error } = useSpendingReport(
    period,
    referenceDateStr,
    excludeSavings,
  );

  const currencies = data
    ? [...new Set(data.rows.map((row) => row.currency))]
    : [];

  const [selectedCurrency, setSelectedCurrency] = useState<string>("");

  useEffect(() => {
    if (currencies.length > 0 && !currencies.includes(selectedCurrency)) {
      setSelectedCurrency(currencies[0]);
    }
  }, [currencies, selectedCurrency]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Spending Reports</h1>
        <p className="text-sm text-muted-foreground">
          View your spending breakdown by category
        </p>
      </div>

      <PeriodSelector
        period={period}
        onPeriodChange={setPeriod}
        referenceDate={referenceDate}
        onReferenceDateChange={setReferenceDate}
        excludeSavings={excludeSavings}
        onExcludeSavingsChange={setExcludeSavings}
        startDate={data?.start_date}
        endDate={data?.end_date}
      />

      {isLoading && <PageLoader />}

      {isError && (
        <EmptyState
          icon={AlertCircle}
          title="Failed to load report"
          description={parseApiError(error)}
        />
      )}

      {!isLoading && !isError && data && currencies.length === 0 && (
        <EmptyState
          icon={BarChart2}
          title="No data"
          description="No expenses recorded for this period."
        />
      )}

      {!isLoading && !isError && data && currencies.length > 0 && (
        <Tabs value={selectedCurrency} onValueChange={setSelectedCurrency}>
          <TabsList>
            {currencies.map((currency) => (
              <TabsTrigger key={currency} value={currency}>
                {currency}
              </TabsTrigger>
            ))}
          </TabsList>

          {currencies.map((currency) => {
            const currencyRows = data.rows.filter(
              (row) => row.currency === currency,
            );
            return (
              <TabsContent key={currency} value={currency} className="space-y-6">
                <SpendingChart rows={currencyRows} currency={currency} />
                <SpendingTable rows={currencyRows} currency={currency} />
              </TabsContent>
            );
          })}
        </Tabs>
      )}
    </div>
  );
}
