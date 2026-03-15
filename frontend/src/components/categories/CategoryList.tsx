import { ChevronRight, Pencil, Trash2, Tag } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { EmptyState } from "@/components/shared/EmptyState";
import type { CategoryResponse, CategoryWithChildrenResponse } from "@/api/types";

interface CategoryRowProps {
  category: CategoryResponse;
  onEdit: (category: CategoryResponse) => void;
  onDelete: (category: CategoryResponse) => void;
}

function CategoryRow({ category, onEdit, onDelete }: CategoryRowProps) {
  return (
    <div className="ml-6 flex items-center justify-between border-l border-border py-2 pl-4 pr-3 hover:bg-muted/50 dark:hover:bg-muted/30 rounded-sm">
      <div className="min-w-0 flex-1">
        <span className="text-sm font-medium">{category.name}</span>
        {category.description && (
          <p className="mt-0.5 truncate text-xs text-muted-foreground">
            {category.description}
          </p>
        )}
      </div>
      <div className="ml-2 flex shrink-0 items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => onEdit(category)}
          className="size-7"
        >
          <Pencil className="size-3.5" />
          <span className="sr-only">Edit {category.name}</span>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => onDelete(category)}
          className="size-7"
        >
          <Trash2 className="size-3.5" />
          <span className="sr-only">Delete {category.name}</span>
        </Button>
      </div>
    </div>
  );
}

interface ParentCategoryItemProps {
  category: CategoryWithChildrenResponse;
  onEdit: (category: CategoryResponse) => void;
  onDelete: (category: CategoryResponse) => void;
}

function ParentCategoryItem({
  category,
  onEdit,
  onDelete,
}: ParentCategoryItemProps) {
  const hasChildren = category.children.length > 0;

  return (
    <Collapsible className="rounded-lg border border-border bg-card dark:bg-card">
      <div className="flex items-center justify-between px-3 py-2">
        <div className="flex min-w-0 flex-1 items-center gap-2">
          {hasChildren ? (
            <CollapsibleTrigger className="group/trigger flex items-center gap-1 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <span className="sr-only">Toggle subcategories</span>
              <ChevronRight className="size-4 text-muted-foreground transition-transform duration-200 group-data-[panel-open]/trigger:rotate-90" />
            </CollapsibleTrigger>
          ) : (
            <span className="size-4 shrink-0" aria-hidden />
          )}
          <div className="min-w-0">
            <span className="text-sm font-semibold">{category.name}</span>
            {category.description && (
              <p className="mt-0.5 truncate text-xs text-muted-foreground">
                {category.description}
              </p>
            )}
          </div>
          {hasChildren && (
            <span className="ml-1 rounded-full bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
              {category.children.length}
            </span>
          )}
        </div>
        <div className="ml-2 flex shrink-0 items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onEdit(category)}
            className="size-7"
          >
            <Pencil className="size-3.5" />
            <span className="sr-only">Edit {category.name}</span>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onDelete(category)}
            className="size-7"
          >
            <Trash2 className="size-3.5" />
            <span className="sr-only">Delete {category.name}</span>
          </Button>
        </div>
      </div>

      {hasChildren && (
        <CollapsibleContent className="border-t border-border px-2 pb-2 pt-1">
          <div className="space-y-1">
            {category.children.map((child) => (
              <CategoryRow
                key={child.category_id}
                category={child}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </div>
        </CollapsibleContent>
      )}
    </Collapsible>
  );
}

interface CategoryListProps {
  categories: CategoryWithChildrenResponse[];
  onEdit: (category: CategoryResponse) => void;
  onDelete: (category: CategoryResponse) => void;
  onCreateNew: () => void;
}

export function CategoryList({
  categories,
  onEdit,
  onDelete,
  onCreateNew,
}: CategoryListProps) {
  const expenseCategories = categories.filter(
    (c) => c.category_type === "EXPENSE",
  );
  const incomeCategories = categories.filter(
    (c) => c.category_type === "INCOME",
  );

  return (
    <Tabs defaultValue="expense">
      <TabsList>
        <TabsTrigger value="expense">
          Expenses ({expenseCategories.length})
        </TabsTrigger>
        <TabsTrigger value="income">
          Income ({incomeCategories.length})
        </TabsTrigger>
      </TabsList>

      <TabsContent value="expense" className="mt-4">
        {expenseCategories.length === 0 ? (
          <EmptyState
            icon={Tag}
            title="No expense categories"
            description="Create your first expense category to organize your spending."
            action={{ label: "Add Category", onClick: onCreateNew }}
          />
        ) : (
          <div className="space-y-2">
            {expenseCategories.map((category) => (
              <ParentCategoryItem
                key={category.category_id}
                category={category}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </div>
        )}
      </TabsContent>

      <TabsContent value="income" className="mt-4">
        {incomeCategories.length === 0 ? (
          <EmptyState
            icon={Tag}
            title="No income categories"
            description="Create your first income category to track your earnings."
            action={{ label: "Add Category", onClick: onCreateNew }}
          />
        ) : (
          <div className="space-y-2">
            {incomeCategories.map((category) => (
              <ParentCategoryItem
                key={category.category_id}
                category={category}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </div>
        )}
      </TabsContent>
    </Tabs>
  );
}
