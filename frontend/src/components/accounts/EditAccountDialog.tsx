import { useState, useEffect, type FormEvent } from "react";
import { Loader2 } from "lucide-react";
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
import { Textarea } from "@/components/ui/textarea";
import { useUpdateAccount } from "@/api/hooks";
import type { AccountResponse } from "@/api/types";
import { parseApiError } from "@/lib/errors";
import { showToast } from "@/lib/toast";

interface EditAccountDialogProps {
  account: AccountResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EditAccountDialog({
  account,
  open,
  onOpenChange,
}: EditAccountDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [initialBalance, setInitialBalance] = useState("");

  const updateAccount = useUpdateAccount();

  useEffect(() => {
    if (account) {
      setName(account.name);
      setDescription(account.description ?? "");
      setInitialBalance(account.initial_balance);
    }
  }, [account]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!account) return;
    const trimmedName = name.trim();
    if (trimmedName.length < 3) {
      showToast.error("Name must be at least 3 characters");
      return;
    }

    const data: Record<string, unknown> = {
      name: trimmedName,
      description: description.trim() || null,
    };
    if (Number(initialBalance) !== Number(account.initial_balance)) {
      data.initial_balance = initialBalance;
    }

    updateAccount.mutate(
      {
        id: account.account_id,
        data: data as import("@/api/types").AccountUpdate,
      },
      {
        onSuccess: () => {
          showToast.success("Account updated");
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
          <DialogTitle>Edit Account</DialogTitle>
          <DialogDescription>
            Update the account name, initial balance, or description.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-name">Name</Label>
            <Input
              id="edit-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              minLength={3}
              maxLength={100}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-initial-balance">Initial Balance</Label>
            <Input
              id="edit-initial-balance"
              type="number"
              step="0.01"
              min="0"
              required
              value={initialBalance}
              onChange={(e) => setInitialBalance(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-description">Description</Label>
            <Textarea
              id="edit-description"
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
            <Button type="submit" disabled={updateAccount.isPending}>
              {updateAccount.isPending && (
                <Loader2 className="mr-2 size-4 animate-spin" />
              )}
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
