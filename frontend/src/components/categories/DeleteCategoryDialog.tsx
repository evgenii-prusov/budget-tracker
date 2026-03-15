import { ConfirmDeleteDialog } from "@/components/shared/ConfirmDeleteDialog";
import { useDeleteCategory } from "@/api/hooks";
import type { CategoryResponse } from "@/api/types";
import { parseApiError } from "@/lib/errors";
import { showToast } from "@/lib/toast";

interface DeleteCategoryDialogProps {
  category: CategoryResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DeleteCategoryDialog({
  category,
  open,
  onOpenChange,
}: DeleteCategoryDialogProps) {
  const deleteCategory = useDeleteCategory();

  const handleConfirm = () => {
    if (!category) return;
    deleteCategory.mutate(category.category_id, {
      onSuccess: () => {
        showToast.success("Category deleted");
        onOpenChange(false);
      },
      onError: (err) => {
        showToast.error(parseApiError(err));
      },
    });
  };

  return (
    <ConfirmDeleteDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Delete Category"
      description={
        category
          ? `Are you sure you want to delete "${category.name}"? This will fail if the category has subcategories or is used by postings.`
          : ""
      }
      onConfirm={handleConfirm}
      isPending={deleteCategory.isPending}
    />
  );
}
