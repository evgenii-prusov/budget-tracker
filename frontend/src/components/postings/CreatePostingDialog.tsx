import { useState, useEffect, type FormEvent } from "react";
import { Loader2, CalendarIcon } from "lucide-react";
import { format } from "date-fns";
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
import { useAccounts, useCategoryParents, useCreatePosting } from "@/api/hooks";
import { parseApiError } from "@/lib/errors";
import { showToast } from "@/lib/toast";
import type { PostingType } from "@/api/types";

interface CreatePostingDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultAccountId?: string;
}

export function CreatePostingDialog({
  open,
  onOpenChange,
  defaultAccountId,
}: CreatePostingDialogProps) {
  const today = new Date();

  const [postingType, setPostingType] = useState<PostingType>("EXPENSE");
  const [accountId, setAccountId] = useState(defaultAccountId ?? "");
  const [parentCategoryId, setParentCategoryId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState<Date>(today);
  const [payee, setPayee] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    setAccountId(defaultAccountId ?? "");
  }, [defaultAccountId]);

  const { data: accounts } = useAccounts();
  const { data: categoryParents } = useCategoryParents();
  const createPosting = useCreatePosting();

  const filteredParents = (categoryParents ?? []).filter(
    (p) => p.category_type === postingType,
  );

  const selectedParent = filteredParents.find(
    (p) => p.category_id === parentCategoryId,
  );

  const subcategories = selectedParent?.children ?? [];
  const hasSubcategories = subcategories.length > 0;
  const effectiveCategoryId = hasSubcategories ? categoryId : parentCategoryId;

  const resetForm = () => {
    setPostingType("EXPENSE");
    setAccountId(defaultAccountId ?? "");
    setParentCategoryId("");
    setCategoryId("");
    setAmount("");
    setDate(today);
    setPayee("");
    setDescription("");
  };

  const handleTypeChange = (values: string[]) => {
    const val = values[0] as PostingType | undefined;
    if (val) {
      setPostingType(val);
      setParentCategoryId("");
      setCategoryId("");
    }
  };

  const handleParentCategoryChange = (value: string) => {
    setParentCategoryId(value);
    setCategoryId("");
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0 || parsedAmount > 1_000_000_000) {
      showToast.error("Amount must be between 0 and 1,000,000,000");
      return;
    }

    if (!accountId) {
      showToast.error("Please select an account");
      return;
    }

    if (!effectiveCategoryId) {
      showToast.error(hasSubcategories ? "Please select a subcategory" : "Please select a category");
      return;
    }

    createPosting.mutate(
      {
        account_id: accountId,
        amount: parsedAmount.toString(),
        posting_date: format(date, "yyyy-MM-dd"),
        posting_type: postingType,
        category_id: effectiveCategoryId,
        payee: payee.trim() || null,
        description: description.trim() || null,
      },
      {
        onSuccess: () => {
          showToast.success("Posting created");
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
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Add Posting</DialogTitle>
          <DialogDescription>Record an income or expense transaction.</DialogDescription>
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

          {/* Account */}
          <div className="space-y-2">
            <Label htmlFor="posting-account">Account</Label>
            <Select value={accountId} onValueChange={setAccountId} required>
              <SelectTrigger id="posting-account" className="w-full">
                <SelectValue placeholder="Select account" />
              </SelectTrigger>
              <SelectContent>
                {(accounts ?? []).map((a) => (
                  <SelectItem key={a.account_id} value={a.account_id} label={`${a.name} (${a.currency})`}>
                    {a.name} ({a.currency})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Parent Category */}
          <div className="space-y-2">
            <Label htmlFor="posting-parent-category">Category</Label>
            <Select
              value={parentCategoryId}
              onValueChange={handleParentCategoryChange}
              required
            >
              <SelectTrigger id="posting-parent-category" className="w-full">
                <SelectValue placeholder="Select category" />
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

          {/* Subcategory — only shown when the selected parent has children */}
          {hasSubcategories && (
            <div className="space-y-2">
              <Label htmlFor="posting-subcategory">Subcategory</Label>
              <Select
                value={categoryId}
                onValueChange={setCategoryId}
                disabled={!parentCategoryId}
                required
              >
                <SelectTrigger id="posting-subcategory" className="w-full">
                  <SelectValue placeholder="Select subcategory" />
                </SelectTrigger>
                <SelectContent>
                  {subcategories.map((child) => (
                    <SelectItem key={child.category_id} value={child.category_id} label={child.name}>
                      {child.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Amount */}
          <div className="space-y-2">
            <Label htmlFor="posting-amount">Amount</Label>
            <Input
              id="posting-amount"
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

          {/* Payee */}
          <div className="space-y-2">
            <Label htmlFor="posting-payee">Payee (optional)</Label>
            <Input
              id="posting-payee"
              value={payee}
              onChange={(e) => setPayee(e.target.value)}
              placeholder="e.g. Supermarket, Employer"
              maxLength={200}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="posting-description">Description (optional)</Label>
            <Textarea
              id="posting-description"
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
            <Button type="submit" disabled={createPosting.isPending}>
              {createPosting.isPending && (
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
