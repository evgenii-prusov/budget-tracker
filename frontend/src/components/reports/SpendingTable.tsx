import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { CategorySpendingResponse } from "@/api/types";
import { formatCurrency } from "@/lib/format";

interface SpendingTableProps {
  rows: CategorySpendingResponse[];
  currency: string;
}

export function SpendingTable({ rows, currency }: SpendingTableProps) {
  const sorted = [...rows].sort(
    (a, b) => Math.abs(Number(b.total)) - Math.abs(Number(a.total)),
  );

  const grandTotal = sorted.reduce(
    (sum, row) => sum + Math.abs(Number(row.total)),
    0,
  );

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Category</TableHead>
          <TableHead className="text-right">Total</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sorted.map((row) => (
          <TableRow key={row.parent_category_id}>
            <TableCell>{row.parent_category_name}</TableCell>
            <TableCell className="text-right">
              {formatCurrency(String(Math.abs(Number(row.total))), currency)}
            </TableCell>
          </TableRow>
        ))}
        <TableRow className="border-t-2 font-semibold">
          <TableCell>Grand Total</TableCell>
          <TableCell className="text-right">
            {formatCurrency(String(grandTotal), currency)}
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
}
