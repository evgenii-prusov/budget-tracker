import { ConfirmDeleteDialog } from "@/components/shared/ConfirmDeleteDialog";
import type { PostingResponse } from "@/api/types";

interface DeletePostingDialogProps {
  posting: PostingResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isPending?: boolean;
}

export function DeletePostingDialog({
  posting,
  open,
  onOpenChange,
  onConfirm,
  isPending = false,
}: DeletePostingDialogProps) {
  const details = posting
    ? [
        posting.posting_date,
        posting.posting_type,
        posting.payee ? `Payee: ${posting.payee}` : null,
        `Amount: ${posting.amount}`,
      ]
        .filter(Boolean)
        .join(" · ")
    : "";

  return (
    <ConfirmDeleteDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Delete Posting"
      description={`Are you sure you want to delete this posting? ${details}`}
      onConfirm={onConfirm}
      isPending={isPending}
    />
  );
}
