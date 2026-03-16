import { useState, useEffect, type FormEvent } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateCategory } from "@/api/hooks";
import type {
  CategoryResponse,
  CategoryWithChildrenResponse,
} from "@/api/types";
import { parseApiError } from "@/lib/errors";
import { showToast } from "@/lib/toast";

interface EditCategoryDialogProps {
  category: CategoryResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  categories: CategoryWithChildrenResponse[];
}

export function EditCategoryDialog({
  category,
  open,
  onOpenChange,
  categories,
}: EditCategoryDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [parentId, setParentId] = useState<string>("");

  const updateCategory = useUpdateCategory();

  // Root categories of the same type, excluding the category being edited
  const parentOptions = categories.filter(
    (c) =>
      category &&
      c.category_type === category.category_type &&
      c.category_id !== category.category_id,
  );

  useEffect(() => {
    if (category) {
      setName(category.name);
      setDescription(category.description ?? "");
      setParentId(category.parent_id ?? "");
    }
  }, [category]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!category) return;
    const trimmedName = name.trim();
    if (trimmedName.length < 2) {
      showToast.error("Name must be at least 2 characters");
      return;
    }

    updateCategory.mutate(
      {
        id: category.category_id,
        data: {
          name: trimmedName,
          description: description.trim() || null,
          parent_id: parentId || null,
        },
      },
      {
        onSuccess: () => {
          showToast.success("Category updated");
          onOpenChange(false);
        },
        onError: (err) => {
          showToast.error(parseApiError(err));
        },
      },
    );
  };

  // Subcategories (have a parent) can change parent; root categories with children cannot
  const isRootWithChildren =
    category &&
    !category.parent_id &&
    categories.some(
      (c) =>
        c.category_id === category.category_id && c.children.length > 0,
    );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Category</DialogTitle>
          <DialogDescription>
            Update the category name, description, or parent.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-category-name">Name</Label>
            <Input
              id="edit-category-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              minLength={2}
              maxLength={100}
            />
          </div>

          {!isRootWithChildren && (
            <div className="space-y-2">
              <Label htmlFor="edit-category-parent">Parent Category</Label>
              <Select
                value={parentId}
                onValueChange={(val) => setParentId(val ?? "")}
              >
                <SelectTrigger id="edit-category-parent" className="w-full">
                  <SelectValue placeholder="None (root category)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="" label="None (root category)">
                    None (root category)
                  </SelectItem>
                  {parentOptions.map((c) => (
                    <SelectItem
                      key={c.category_id}
                      value={c.category_id}
                      label={c.name}
                    >
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="edit-category-description">Description</Label>
            <Textarea
              id="edit-category-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              maxLength={500}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={updateCategory.isPending}>
              {updateCategory.isPending && (
                <Loader2 className="mr-2 size-4 animate-spin" />
              )}
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
