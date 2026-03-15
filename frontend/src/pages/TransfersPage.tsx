import { useState } from "react";
import { Plus, ArrowLeftRight, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageLoader } from "@/components/shared/PageLoader";
import { EmptyState } from "@/components/shared/EmptyState";
import { TransfersTable } from "@/components/transfers/TransfersTable";
import { CreateTransferDialog } from "@/components/transfers/CreateTransferDialog";
import { DeleteTransferDialog } from "@/components/transfers/DeleteTransferDialog";
import {
  useTransfers,
  useDeleteTransfer,
  useAccounts,
} from "@/api/hooks";
import type { TransferResponse } from "@/api/types";
import { parseApiError } from "@/lib/errors";
import { showToast } from "@/lib/toast";

export default function TransfersPage() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    error,
  } = useTransfers();
  const { data: accounts = [] } = useAccounts();
  const deleteTransfer = useDeleteTransfer();

  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<TransferResponse | null>(null);

  const allTransfers = data?.pages.flat() ?? [];
  const sorted = [...allTransfers].sort((a, b) =>
    b.transfer_date.localeCompare(a.transfer_date),
  );

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteTransfer.mutate(deleteTarget.transfer_id, {
      onSuccess: () => {
        showToast.success("Transfer deleted");
        setDeleteTarget(null);
      },
      onError: (err) => {
        showToast.error(parseApiError(err));
      },
    });
  };

  if (isLoading) return <PageLoader />;

  if (isError) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="Failed to load transfers"
        description={parseApiError(error)}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Transfers</h1>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 size-4" />
          Add Transfer
        </Button>
      </div>

      {sorted.length > 0 ? (
        <>
          <TransfersTable
            transfers={sorted}
            accounts={accounts}
            onDelete={setDeleteTarget}
          />
          {hasNextPage && (
            <div className="flex justify-center pt-2">
              <Button
                variant="outline"
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
              >
                {isFetchingNextPage && (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                )}
                Load More
              </Button>
            </div>
          )}
        </>
      ) : (
        <EmptyState
          icon={ArrowLeftRight}
          title="No transfers yet"
          description="Record a transfer to move funds between accounts."
          action={{ label: "Add Transfer", onClick: () => setCreateOpen(true) }}
        />
      )}

      <CreateTransferDialog open={createOpen} onOpenChange={setCreateOpen} />

      <DeleteTransferDialog
        transfer={deleteTarget}
        accounts={accounts}
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        onConfirm={handleDelete}
        isPending={deleteTransfer.isPending}
      />
    </div>
  );
}
