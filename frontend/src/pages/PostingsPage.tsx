import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Plus, Receipt, AlertCircle, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageLoader } from "@/components/shared/PageLoader";
import { EmptyState } from "@/components/shared/EmptyState";
import { TableSkeleton } from "@/components/shared/TableSkeleton";
import { PostingsTable } from "@/components/postings/PostingsTable";
import { CreatePostingDialog } from "@/components/postings/CreatePostingDialog";
import { DeletePostingDialog } from "@/components/postings/DeletePostingDialog";
import { usePostings, useDeletePosting, useAccounts } from "@/api/hooks";
import type { PostingResponse } from "@/api/types";
import { parseApiError } from "@/lib/errors";
import { showToast } from "@/lib/toast";

export default function PostingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const accountId = searchParams.get("account_id") ?? undefined;

  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<PostingResponse | null>(null);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    error,
  } = usePostings(accountId);

  const { data: accounts } = useAccounts();
  const deletePosting = useDeletePosting();

  const allPostings = data?.pages.flat() ?? [];
  const sorted = [...allPostings].sort((a, b) =>
    b.posting_date.localeCompare(a.posting_date),
  );

  const filteredAccount = accountId
    ? (accounts ?? []).find((a) => a.account_id === accountId)
    : null;

  const handleDelete = () => {
    if (!deleteTarget) return;
    deletePosting.mutate(deleteTarget.posting_id, {
      onSuccess: () => {
        showToast.success("Posting deleted");
        setDeleteTarget(null);
      },
      onError: (err) => {
        showToast.error(parseApiError(err));
      },
    });
  };

  const clearAccountFilter = () => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete("account_id");
      return next;
    });
  };

  if (isLoading) return <PageLoader />;

  if (isError) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="Failed to load postings"
        description={parseApiError(error)}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">Postings</h1>
          {filteredAccount && (
            <Badge variant="secondary" className="flex items-center gap-1">
              Filtered by: {filteredAccount.name}
              <button
                onClick={clearAccountFilter}
                className="ml-1 rounded-full hover:bg-muted-foreground/20"
                aria-label="Clear account filter"
              >
                <X className="size-3" />
              </button>
            </Badge>
          )}
          {accountId && !filteredAccount && (
            <Badge variant="secondary" className="flex items-center gap-1">
              Filtered by account
              <button
                onClick={clearAccountFilter}
                className="ml-1 rounded-full hover:bg-muted-foreground/20"
                aria-label="Clear account filter"
              >
                <X className="size-3" />
              </button>
            </Badge>
          )}
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 size-4" />
          Add Posting
        </Button>
      </div>

      {isLoading ? (
        <TableSkeleton columns={7} />
      ) : sorted.length > 0 ? (
        <>
          <PostingsTable postings={sorted} onDelete={setDeleteTarget} />
          {hasNextPage && (
            <div className="flex justify-center pt-4">
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
          icon={Receipt}
          title="No postings yet"
          description={
            accountId
              ? "No postings found for this account."
              : "Add your first income or expense to get started."
          }
          action={{ label: "Add Posting", onClick: () => setCreateOpen(true) }}
        />
      )}

      <CreatePostingDialog open={createOpen} onOpenChange={setCreateOpen} />

      <DeletePostingDialog
        posting={deleteTarget}
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        onConfirm={handleDelete}
        isPending={deletePosting.isPending}
      />
    </div>
  );
}
