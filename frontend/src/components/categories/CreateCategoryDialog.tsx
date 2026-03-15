import { useState, type FormEvent } from "react";
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
import { useCreateCategory, useCategories } from "@/api/hooks";
import type { CategoryType } from "@/api/types";
import { parseApiError } from "@/lib/errors";
import { showToast } from "@/lib/toast";

interface CreateCategoryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateCategoryDialog({
  open,
  onOpenChange,
}: CreateCategoryDialogProps) {
  const [name, setName] = useState("");
  const [categoryType, setCategoryType] = useState<CategoryType>("EXPENSE");
  const [parentId, setParentId] = useState<string>("");
  const [description, setDescription] = useState("");

  const createCategory = useCreateCategory();
  const { data: allCategories } = useCategories();

  // Root categories of the selected type (no parent_id) for parent dropdown
  const parentOptions =
    allCategories?.filter(
      (c) => c.category_type === categoryType && c.parent_id === null,
    ) ?? [];

  const resetForm = () => {
    setName("");
    setCategoryType("EXPENSE");
    setParentId("");
    setDescription("");
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    if (trimmedName.length < 2) {
      showToast.error("Name must be at least 2 characters");
      return;
    }

    createCategory.mutate(
      {
        name: trimmedName,
        category_type: categoryType,
        parent_id: parentId || null,
        description: description.trim() || null,
      },
      {
        onSuccess: () => {
          showToast.success("Category created");
          resetForm();
          onOpenChange(false);
        },
        onError: (err) => {
          showToast.error(parseApiError(err));
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create Category</DialogTitle>
          <DialogDescription>Add a new expense or income category.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="category-name">Name</Label>
            <Input
              id="category-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Food, Transport"
              required
              minLength={2}
              maxLength={100}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="category-type">Type</Label>
            <Select
              value={categoryType}
              onValueChange={(val) => {
                if (val) {
                  setCategoryType(val as CategoryType);
                  setParentId("");
                }
              }}
            >
              <SelectTrigger id="category-type" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="EXPENSE">Expense</SelectItem>
                <SelectItem value="INCOME">Income</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="category-parent">Parent Category</Label>
            <Select
              value={parentId}
              onValueChange={(val) => setParentId(val ?? "")}
            >
              <SelectTrigger id="category-parent" className="w-full">
                <SelectValue placeholder="None (root category)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">None (root category)</SelectItem>
                {parentOptions.map((c) => (
                  <SelectItem key={c.category_id} value={c.category_id}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="category-description">Description</Label>
            <Textarea
              id="category-description"
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
            <Button type="submit" disabled={createCategory.isPending}>
              {createCategory.isPending && (
                <Loader2 className="mr-2 size-4 animate-spin" />
              )}
              Create
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
