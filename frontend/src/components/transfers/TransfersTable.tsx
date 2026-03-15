import { Trash2 } from "lucide-react";
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

function getAccount(
  accounts: AccountResponse[],
  id: string,
): AccountResponse | undefined {
  return accounts.find((a) => a.account_id === id);
}

export function TransfersTable({
  transfers,
  accounts,
  onDelete,
}: TransfersTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Date</TableHead>
          <TableHead>From Account</TableHead>
          <TableHead>To Account</TableHead>
          <TableHead className="text-right">Debit Amount</TableHead>
          <TableHead className="text-right">Credit Amount</TableHead>
          <TableHead>Description</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {transfers.map((transfer) => {
          const sourceAccount = getAccount(accounts, transfer.source_account_id);
          const destAccount = getAccount(accounts, transfer.dest_account_id);
          const sourceName = sourceAccount
            ? `${sourceAccount.name} (${sourceAccount.currency})`
            : transfer.source_account_id;
          const destName = destAccount
            ? `${destAccount.name} (${destAccount.currency})`
            : transfer.dest_account_id;

          return (
            <TableRow key={transfer.transfer_id}>
              <TableCell>{transfer.transfer_date}</TableCell>
              <TableCell className="font-medium">{sourceName}</TableCell>
              <TableCell className="font-medium">{destName}</TableCell>
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
