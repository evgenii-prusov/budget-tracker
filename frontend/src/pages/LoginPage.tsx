import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { ApiError, validateApiKey } from "@/api/client";
import { parseApiError } from "@/lib/errors";
import { showToast } from "@/lib/toast";

export default function LoginPage() {
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState("");
  const [isPending, setIsPending] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    const trimmed = apiKey.trim();
    if (!trimmed) {
      setError("API key is required");
      return;
    }

    setIsPending(true);
    try {
      await validateApiKey(trimmed);
      localStorage.setItem("api_key", trimmed);
      navigate("/accounts", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Invalid API key");
      } else if (err instanceof ApiError) {
        setError(parseApiError(err));
      } else {
        showToast.error("Unable to connect to the server");
      }
    } finally {
      setIsPending(false);
    }
  };

  return (
    <div className="flex min-h-svh items-center justify-center p-4">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Budget Tracker</CardTitle>
          <CardDescription>Enter your API key to connect</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="api-key">API Key</Label>
              <Input
                id="api-key"
                type="password"
                placeholder="Enter your API key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                disabled={isPending}
                aria-invalid={!!error}
                aria-describedby={error ? "api-key-error" : undefined}
                autoFocus
              />
              {error && (
                <p id="api-key-error" role="alert" className="text-sm text-destructive">
                  {error}
                </p>
              )}
            </div>
            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
              Connect
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
