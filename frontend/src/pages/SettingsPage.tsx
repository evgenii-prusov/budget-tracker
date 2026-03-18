import { useState, useEffect } from "react";
import { Settings, AlertCircle, Check } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { PageLoader } from "@/components/shared/PageLoader";
import { EmptyState } from "@/components/shared/EmptyState";
import { useSettings, useUpdateSettings } from "@/api/hooks";
import { parseApiError } from "@/lib/errors";
import { toast } from "sonner";

const CURRENCIES = ["USD", "EUR", "GBP", "RUB", "CHF", "JPY", "CNY"];

export default function SettingsPage() {
  const { data, isLoading, isError, error } = useSettings();
  const updateSettings = useUpdateSettings();
  const [selectedCurrency, setSelectedCurrency] = useState<string>("");

  useEffect(() => {
    if (data) {
      setSelectedCurrency(data.primary_currency);
    }
  }, [data]);

  const handleSave = () => {
    updateSettings.mutate(
      { primary_currency: selectedCurrency },
      {
        onSuccess: () => {
          toast.success("Settings saved");
        },
        onError: (err) => {
          toast.error(parseApiError(err));
        },
      },
    );
  };

  if (isLoading) return <PageLoader />;

  if (isError) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="Failed to load settings"
        description={parseApiError(error)}
      />
    );
  }

  const hasChanges = data && selectedCurrency !== data.primary_currency;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Configure your budget tracker preferences
        </p>
      </div>

      <Card className="max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Settings className="size-4" />
            Primary Currency
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            The default currency used for dashboard widgets and reports.
          </p>
          <Select value={selectedCurrency} onValueChange={(v) => v && setSelectedCurrency(v)}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Select currency" />
            </SelectTrigger>
            <SelectContent>
              {CURRENCIES.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            onClick={handleSave}
            disabled={!hasChanges || updateSettings.isPending}
            size="sm"
          >
            <Check className="mr-1 size-4" />
            {updateSettings.isPending ? "Saving..." : "Save"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
