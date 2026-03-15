import { useMemo } from "react";
import { Trash2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { TransferResponse, AccountResponse } from "@/api/types";
import { formatCurrency } from "@/lib/format";

interface TransfersTableProps {
  transfers: TransferResponse[];
  accounts: AccountResponse[];
  onDelete: (transfer: TransferResponse) => void;
}

export function TransfersTable({
  transfers,
  accounts,
  onDelete,
}: TransfersTableProps) {
  const accountsById = useMemo(() => {
    const map = new Map<string, AccountResponse>();
    for (const a of accounts) map.set(a.account_id, a);
    return map;
  }, [accounts]);

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Date</TableHead>
          <TableHead>Transfer</TableHead>
          <TableHead className="text-right">Debit Amount</TableHead>
          <TableHead className="text-right">Credit Amount</TableHead>
          <TableHead>Description</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {transfers.map((transfer) => {
          const sourceAccount = accountsById.get(transfer.source_account_id);
          const destAccount = accountsById.get(transfer.dest_account_id);
          const sourceName = sourceAccount
            ? `${sourceAccount.name} (${sourceAccount.currency})`
            : transfer.source_account_id;
          const destName = destAccount
            ? `${destAccount.name} (${destAccount.currency})`
            : transfer.dest_account_id;

          return (
            <TableRow key={transfer.transfer_id}>
              <TableCell>{transfer.transfer_date}</TableCell>
              <TableCell className="font-medium">
                <span className="inline-flex items-center gap-1.5">
                  {sourceName}
                  <ArrowRight className="size-3.5 shrink-0 text-muted-foreground" />
                  {destName}
                </span>
              </TableCell>
              <TableCell className="text-right">
                {sourceAccount
                  ? formatCurrency(transfer.debit_amount, sourceAccount.currency)
                  : transfer.debit_amount}
              </TableCell>
              <TableCell className="text-right">
                {destAccount
                  ? formatCurrency(transfer.credit_amount, destAccount.currency)
                  : transfer.credit_amount}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {transfer.description ?? "—"}
              </TableCell>
              <TableCell className="text-right">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onDelete(transfer)}
                >
                  <Trash2 className="size-4" />
                  <span className="sr-only">Delete</span>
                </Button>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
