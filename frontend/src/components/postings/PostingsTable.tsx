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
import { useAccounts, useCategoryParents } from "@/api/hooks";
import type { PostingResponse } from "@/api/types";
import { formatCurrency } from "@/lib/format";

interface PostingsTableProps {
  postings: PostingResponse[];
  onDelete: (posting: PostingResponse) => void;
}

export function PostingsTable({ postings, onDelete }: PostingsTableProps) {
  const { data: accounts } = useAccounts();
  const { data: categoryParents } = useCategoryParents();

  const accountMap = new Map(
    (accounts ?? []).map((a) => [a.account_id, a]),
  );

  const categoryMap = new Map(
    (categoryParents ?? []).flatMap((parent) => [
      [parent.category_id, parent.name],
      ...parent.children.map((child) => [child.category_id, child.name] as [string, string]),
    ]),
  );

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Date</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Payee</TableHead>
          <TableHead>Category</TableHead>
          <TableHead className="text-right">Amount</TableHead>
          <TableHead>Account</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {postings.map((posting) => {
          const account = accountMap.get(posting.account_id);
          const categoryName = posting.category_id
            ? categoryMap.get(posting.category_id) ?? "—"
            : "—";
          const isExpense = posting.posting_type === "EXPENSE";
          const amountClass = isExpense
            ? "text-red-600 dark:text-red-400"
            : "text-green-600 dark:text-green-400";
          const absAmount = String(Math.abs(Number(posting.amount)));
          const amountDisplay = account
            ? formatCurrency(absAmount, account.currency)
            : absAmount;

          return (
            <TableRow key={posting.posting_id}>
              <TableCell>{posting.posting_date}</TableCell>
              <TableCell>{posting.posting_type}</TableCell>
              <TableCell>{posting.payee ?? "—"}</TableCell>
              <TableCell>{categoryName}</TableCell>
              <TableCell className={`text-right font-medium ${amountClass}`}>
                {isExpense ? "−" : "+"}
                {amountDisplay}
              </TableCell>
              <TableCell>{account?.name ?? posting.account_id}</TableCell>
              <TableCell className="text-right">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onDelete(posting)}
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
