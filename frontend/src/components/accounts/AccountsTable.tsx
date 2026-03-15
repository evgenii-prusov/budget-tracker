import { useNavigate } from "react-router-dom";
import type { KeyboardEvent } from "react";
import { Pencil, Trash2, PiggyBank } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { AccountResponse } from "@/api/types";
import { formatCurrency } from "@/lib/format";

interface AccountsTableProps {
  accounts: AccountResponse[];
  onEdit: (account: AccountResponse) => void;
  onDelete: (account: AccountResponse) => void;
}

export function AccountsTable({
  accounts,
  onEdit,
  onDelete,
}: AccountsTableProps) {
  const navigate = useNavigate();

  const navigateToPostings = (accountId: string) => {
    navigate(`/postings?account_id=${accountId}`);
  };

  const handleRowKeyDown = (e: KeyboardEvent, accountId: string) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      navigateToPostings(accountId);
    }
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Currency</TableHead>
          <TableHead className="text-right">Balance</TableHead>
          <TableHead>Type</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {accounts.map((account) => (
          <TableRow
            key={account.account_id}
            className="cursor-pointer"
            role="link"
            tabIndex={0}
            onClick={() => navigateToPostings(account.account_id)}
            onKeyDown={(e) => handleRowKeyDown(e, account.account_id)}
          >
            <TableCell className="font-medium">{account.name}</TableCell>
            <TableCell>{account.currency}</TableCell>
            <TableCell className="text-right">
              {formatCurrency(account.balance, account.currency)}
            </TableCell>
            <TableCell>
              {account.is_savings && (
                <Badge variant="secondary">
                  <PiggyBank className="mr-1 size-3" />
                  Savings
                </Badge>
              )}
            </TableCell>
            <TableCell className="text-right">
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(account);
                }}
              >
                <Pencil className="size-4" />
                <span className="sr-only">Edit</span>
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(account);
                }}
              >
                <Trash2 className="size-4" />
                <span className="sr-only">Delete</span>
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
