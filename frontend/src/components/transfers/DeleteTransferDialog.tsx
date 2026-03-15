import { ConfirmDeleteDialog } from "@/components/shared/ConfirmDeleteDialog";
import type { TransferResponse, AccountResponse } from "@/api/types";
import { formatCurrency } from "@/lib/format";
import { format } from "date-fns";

interface DeleteTransferDialogProps {
  transfer: TransferResponse | null;
  accounts: AccountResponse[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isPending?: boolean;
}

function getAccountLabel(
  accounts: AccountResponse[],
  id: string,
): { name: string; currency: string } | undefined {
  const acc = accounts.find((a) => a.account_id === id);
  return acc ? { name: acc.name, currency: acc.currency } : undefined;
}

export function DeleteTransferDialog({
  transfer,
  accounts,
  open,
  onOpenChange,
  onConfirm,
  isPending,
}: DeleteTransferDialogProps) {
  let description = "Are you sure you want to delete this transfer?";

  if (transfer) {
    const source = getAccountLabel(accounts, transfer.source_account_id);
    const dest = getAccountLabel(accounts, transfer.dest_account_id);
    const sourceName = source
      ? `${source.name} (${source.currency})`
      : transfer.source_account_id;
    const destName = dest
      ? `${dest.name} (${dest.currency})`
      : transfer.dest_account_id;
    const debit = source
      ? formatCurrency(transfer.debit_amount, source.currency)
      : transfer.debit_amount;
    const credit = dest
      ? formatCurrency(transfer.credit_amount, dest.currency)
      : transfer.credit_amount;

    let dateStr = transfer.transfer_date;
    try {
      dateStr = format(new Date(transfer.transfer_date + "T00:00:00"), "PPP");
    } catch {
      // keep raw string
    }

    description = `Delete transfer from ${sourceName} to ${destName} of ${debit} → ${credit} on ${dateStr}? This action cannot be undone.`;
  }

  return (
    <ConfirmDeleteDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Delete Transfer"
      description={description}
      onConfirm={onConfirm}
      isPending={isPending}
    />
  );
}
