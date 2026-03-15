import { useState } from "react";
import { Plus, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageLoader } from "@/components/shared/PageLoader";
import { EmptyState } from "@/components/shared/EmptyState";
import { CategoryList } from "@/components/categories/CategoryList";
import { CreateCategoryDialog } from "@/components/categories/CreateCategoryDialog";
import { EditCategoryDialog } from "@/components/categories/EditCategoryDialog";
import { DeleteCategoryDialog } from "@/components/categories/DeleteCategoryDialog";
import { useCategoryParents } from "@/api/hooks";
import type { CategoryResponse } from "@/api/types";
import { parseApiError } from "@/lib/errors";

export default function CategoriesPage() {
  const { data: categories, isLoading, isError, error, refetch } = useCategoryParents();

  const [createOpen, setCreateOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<CategoryResponse | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<CategoryResponse | null>(null);

  if (isLoading) return <PageLoader />;

  if (isError) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="Failed to load categories"
        description={parseApiError(error)}
        action={{ label: "Retry", onClick: () => refetch() }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Categories</h1>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 size-4" />
          Add Category
        </Button>
      </div>

      <CategoryList
        categories={categories ?? []}
        onEdit={setEditTarget}
        onDelete={setDeleteTarget}
        onCreateNew={() => setCreateOpen(true)}
      />

      <CreateCategoryDialog open={createOpen} onOpenChange={setCreateOpen} />

      <EditCategoryDialog
        category={editTarget}
        open={!!editTarget}
        onOpenChange={(open) => !open && setEditTarget(null)}
      />

      <DeleteCategoryDialog
        category={deleteTarget}
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      />
    </div>
  );
}
