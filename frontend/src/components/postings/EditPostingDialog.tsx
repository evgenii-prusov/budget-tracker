import { useState, useEffect, type FormEvent } from "react";
import { Loader2, CalendarIcon } from "lucide-react";
import { format, parseISO } from "date-fns";
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
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useAccounts, useCategoryParents, useUpdatePosting } from "@/api/hooks";
import { PayeeCombobox } from "@/components/postings/PayeeCombobox";
import { parseApiError } from "@/lib/errors";
import { showToast } from "@/lib/toast";
import type { PostingResponse, PostingType, PostingUpdate } from "@/api/types";

interface EditPostingDialogProps {
  posting: PostingResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EditPostingDialog({
  posting,
  open,
  onOpenChange,
}: EditPostingDialogProps) {
  const [postingType, setPostingType] = useState<PostingType>("EXPENSE");
  const [parentCategoryId, setParentCategoryId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState<Date>(new Date());
  const [payee, setPayee] = useState("");
  const [description, setDescription] = useState("");

  const { data: accounts } = useAccounts();
  const { data: categoryParents } = useCategoryParents();
  const updatePosting = useUpdatePosting();

  // Build a map from child category_id -> parent category_id
  const childToParentMap = new Map(
    (categoryParents ?? []).flatMap((parent) =>
      parent.children.map((child) => [child.category_id, parent.category_id]),
    ),
  );

  // Initialize form from posting props
  useEffect(() => {
    if (!posting) return;

    setPostingType(posting.posting_type);
    setAmount(String(Math.abs(Number(posting.amount))));
    setDate(parseISO(posting.posting_date));
    setPayee(posting.payee ?? "");
    setDescription(posting.description ?? "");

    if (posting.category_id) {
      const parentId = childToParentMap.get(posting.category_id);
      if (parentId) {
        // It's a subcategory
        setParentCategoryId(parentId);
        setCategoryId(posting.category_id);
      } else {
        // It's a parent category (leaf) or unknown
        setParentCategoryId(posting.category_id);
        setCategoryId("");
      }
    } else {
      setParentCategoryId("");
      setCategoryId("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [posting, categoryParents]);

  const filteredParents = (categoryParents ?? []).filter(
    (p) => p.category_type === postingType,
  );

  const selectedParent = filteredParents.find(
    (p) => p.category_id === parentCategoryId,
  );

  const subcategories = selectedParent?.children ?? [];
  const hasSubcategories = subcategories.length > 0;
  const effectiveCategoryId = hasSubcategories ? categoryId : parentCategoryId;

  const account = posting
    ? (accounts ?? []).find((a) => a.account_id === posting.account_id)
    : null;

  const handleTypeChange = (values: string[]) => {
    const val = values[0] as PostingType | undefined;
    if (val) {
      setPostingType(val);
      setParentCategoryId("");
      setCategoryId("");
    }
  };

  const handleParentCategoryChange = (value: string | null) => {
    if (!value) return;
    setParentCategoryId(value);
    setCategoryId("");
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!posting) return;

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0 || parsedAmount > 1_000_000_000) {
      showToast.error("Amount must be between 0 and 1,000,000,000");
      return;
    }

    const data: PostingUpdate = {
      amount: parsedAmount.toString(),
      posting_date: format(date, "yyyy-MM-dd"),
      posting_type: postingType,
      category_id: effectiveCategoryId || null,
      payee: payee.trim() || null,
      description: description.trim() || null,
    };

    updatePosting.mutate(
      { id: posting.posting_id, data },
      {
        onSuccess: () => {
          showToast.success("Posting updated");
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
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Edit Posting</DialogTitle>
          <DialogDescription>
            Update the posting details.
            {account && ` Account: ${account.name} (${account.currency}).`}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Type */}
          <div className="space-y-2">
            <Label>Type</Label>
            <ToggleGroup
              value={[postingType]}
              onValueChange={handleTypeChange}
              variant="outline"
            >
              <ToggleGroupItem value="EXPENSE">Expense</ToggleGroupItem>
              <ToggleGroupItem value="INCOME">Income</ToggleGroupItem>
            </ToggleGroup>
          </div>

          {/* Amount */}
          <div className="space-y-2">
            <Label htmlFor="edit-posting-amount">Amount</Label>
            <Input
              id="edit-posting-amount"
              type="number"
              step="0.01"
              min="0.01"
              max="1000000000"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              required
            />
          </div>

          {/* Date */}
          <div className="space-y-2">
            <Label>Date</Label>
            <Popover>
              <PopoverTrigger className="flex h-9 w-full items-center justify-start rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
                {date ? format(date, "PPP") : "Pick a date"}
                <CalendarIcon className="ml-auto size-4 opacity-50" />
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={(d) => d && setDate(d)}
                />
              </PopoverContent>
            </Popover>
          </div>

          {/* Parent Category */}
          <div className="space-y-2">
            <Label htmlFor="edit-posting-parent-category">Category</Label>
            <Select
              value={parentCategoryId}
              onValueChange={handleParentCategoryChange}
            >
              <SelectTrigger id="edit-posting-parent-category" className="w-full">
                <SelectValue placeholder="No category">
                  {(value: string | null) => {
                    if (!value) return null;
                    const match = filteredParents.find((p) => p.category_id === value);
                    return match?.name ?? "Loading…";
                  }}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {filteredParents.map((p) => (
                  <SelectItem key={p.category_id} value={p.category_id} label={p.name}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Subcategory */}
          {hasSubcategories && (
            <div className="space-y-2">
              <Label htmlFor="edit-posting-subcategory">Subcategory</Label>
              <Select
                value={categoryId}
                onValueChange={(v) => v && setCategoryId(v)}
                disabled={!parentCategoryId}
              >
                <SelectTrigger id="edit-posting-subcategory" className="w-full">
                  <SelectValue placeholder="Select subcategory">
                    {(value: string | null) => {
                      if (!value) return null;
                      const match = subcategories.find((c) => c.category_id === value);
                      return match?.name ?? "Loading…";
                    }}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {subcategories.map((child) => (
                    <SelectItem
                      key={child.category_id}
                      value={child.category_id}
                      label={child.name}
                    >
                      {child.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Payee */}
          <div className="space-y-2">
            <Label htmlFor="edit-posting-payee">Payee (optional)</Label>
            <PayeeCombobox
              id="edit-posting-payee"
              value={payee}
              onChange={setPayee}
              placeholder="e.g. Supermarket, Employer"
              maxLength={200}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="edit-posting-description">Description (optional)</Label>
            <Textarea
              id="edit-posting-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional notes"
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
            <Button type="submit" disabled={updatePosting.isPending}>
              {updatePosting.isPending && (
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
