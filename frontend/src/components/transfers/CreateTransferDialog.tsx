import { useState, type FormEvent } from "react";
import { Loader2, CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { useCreateTransfer, useAccounts } from "@/api/hooks";
import { parseApiError } from "@/lib/errors";
import { showToast } from "@/lib/toast";

interface CreateTransferDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateTransferDialog({
  open,
  onOpenChange,
}: CreateTransferDialogProps) {
  const { data: accounts } = useAccounts();
  const createTransfer = useCreateTransfer();

  const [sourceAccountId, setSourceAccountId] = useState("");
  const [destAccountId, setDestAccountId] = useState("");
  const [debitAmount, setDebitAmount] = useState("");
  const [creditAmount, setCreditAmount] = useState("");
  const [date, setDate] = useState<Date>(new Date());
  const [description, setDescription] = useState("");
  const [calendarOpen, setCalendarOpen] = useState(false);

  const resetForm = () => {
    setSourceAccountId("");
    setDestAccountId("");
    setDebitAmount("");
    setCreditAmount("");
    setDate(new Date());
    setDescription("");
  };

  const handleSourceChange = (value: string) => {
    setSourceAccountId(value);
    // If same currency, sync credit amount
    if (accounts && destAccountId) {
      const source = accounts.find((a) => a.account_id === value);
      const dest = accounts.find((a) => a.account_id === destAccountId);
      if (source && dest && source.currency === dest.currency) {
        setCreditAmount(debitAmount);
      } else {
        setCreditAmount("");
      }
    }
  };

  const handleDestChange = (value: string) => {
    setDestAccountId(value);
    // If same currency, sync credit amount
    if (accounts && sourceAccountId) {
      const source = accounts.find((a) => a.account_id === sourceAccountId);
      const dest = accounts.find((a) => a.account_id === value);
      if (source && dest && source.currency === dest.currency) {
        setCreditAmount(debitAmount);
      } else {
        setCreditAmount("");
      }
    }
  };

  const handleDebitChange = (value: string) => {
    setDebitAmount(value);
    // Auto-fill credit if same currency
    if (accounts && sourceAccountId && destAccountId) {
      const source = accounts.find((a) => a.account_id === sourceAccountId);
      const dest = accounts.find((a) => a.account_id === destAccountId);
      if (source && dest && source.currency === dest.currency) {
        setCreditAmount(value);
      }
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    if (!sourceAccountId) {
      showToast.error("Please select a source account");
      return;
    }
    if (!destAccountId) {
      showToast.error("Please select a destination account");
      return;
    }
    if (sourceAccountId === destAccountId) {
      showToast.error("Source and destination accounts must differ");
      return;
    }

    const debit = parseFloat(debitAmount);
    if (isNaN(debit) || debit <= 0) {
      showToast.error("Debit amount must be greater than 0");
      return;
    }
    if (debit > 1_000_000_000) {
      showToast.error("Debit amount must not exceed 1,000,000,000");
      return;
    }

    const credit = parseFloat(creditAmount);
    if (isNaN(credit) || credit <= 0) {
      showToast.error("Credit amount must be greater than 0");
      return;
    }
    if (credit > 1_000_000_000) {
      showToast.error("Credit amount must not exceed 1,000,000,000");
      return;
    }

    createTransfer.mutate(
      {
        source_account_id: sourceAccountId,
        dest_account_id: destAccountId,
        debit_amount: debitAmount,
        credit_amount: creditAmount,
        transfer_date: format(date, "yyyy-MM-dd"),
        description: description.trim() || null,
      },
      {
        onSuccess: () => {
          showToast.success("Transfer created");
          resetForm();
          onOpenChange(false);
        },
        onError: (err) => {
          showToast.error(parseApiError(err));
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Transfer</DialogTitle>
          <DialogDescription>
            Transfer funds between two accounts.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="source-account">Source Account</Label>
            <Select value={sourceAccountId} onValueChange={handleSourceChange}>
              <SelectTrigger id="source-account" className="w-full">
                <SelectValue placeholder="Select source account" />
              </SelectTrigger>
              <SelectContent>
                {accounts?.map((account) => {
                  const displayLabel = `${account.name} (${account.currency})`;
                  return (
                    <SelectItem key={account.account_id} value={account.account_id} label={displayLabel}>
                      {displayLabel}
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="dest-account">Destination Account</Label>
            <Select value={destAccountId} onValueChange={handleDestChange}>
              <SelectTrigger id="dest-account" className="w-full">
                <SelectValue placeholder="Select destination account" />
              </SelectTrigger>
              <SelectContent>
                {accounts?.map((account) => {
                  const displayLabel = `${account.name} (${account.currency})`;
                  return (
                    <SelectItem key={account.account_id} value={account.account_id} label={displayLabel}>
                      {displayLabel}
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="debit-amount">Debit Amount</Label>
            <Input
              id="debit-amount"
              type="number"
              step="0.01"
              min="0.01"
              max="1000000000"
              value={debitAmount}
              onChange={(e) => handleDebitChange(e.target.value)}
              placeholder="Amount leaving source"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="credit-amount">Credit Amount</Label>
            <Input
              id="credit-amount"
              type="number"
              step="0.01"
              min="0.01"
              max="1000000000"
              value={creditAmount}
              onChange={(e) => setCreditAmount(e.target.value)}
              placeholder="Amount entering destination"
              required
            />
          </div>

          <div className="space-y-2">
            <Label>Date</Label>
            <Popover open={calendarOpen} onOpenChange={setCalendarOpen}>
              <PopoverTrigger asChild>
                <Button type="button" variant="outline" className="w-full justify-start">
                  {date ? format(date, "PPP") : "Pick a date"}
                  <CalendarIcon className="ml-auto size-4 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={(d) => {
                    if (d) {
                      setDate(d);
                      setCalendarOpen(false);
                    }
                  }}
                />
              </PopoverContent>
            </Popover>
          </div>

          <div className="space-y-2">
            <Label htmlFor="transfer-description">Description</Label>
            <Textarea
              id="transfer-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              maxLength={500}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createTransfer.isPending}>
              {createTransfer.isPending && (
                <Loader2 className="mr-2 size-4 animate-spin" />
              )}
              Create
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
