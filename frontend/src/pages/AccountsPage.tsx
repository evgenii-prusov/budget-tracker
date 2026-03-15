import { useState } from "react";
import { Plus, Wallet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageLoader } from "@/components/shared/PageLoader";
import { EmptyState } from "@/components/shared/EmptyState";
import { ConfirmDeleteDialog } from "@/components/shared/ConfirmDeleteDialog";
import { AccountsTable } from "@/components/accounts/AccountsTable";
import { CreateAccountDialog } from "@/components/accounts/CreateAccountDialog";
import { EditAccountDialog } from "@/components/accounts/EditAccountDialog";
import { useAccounts, useDeleteAccount } from "@/api/hooks";
import type { AccountResponse } from "@/api/types";
import { parseApiError } from "@/lib/errors";
import { showToast } from "@/lib/toast";

export default function AccountsPage() {
  const { data: accounts, isLoading } = useAccounts();
  const deleteAccount = useDeleteAccount();

  const [createOpen, setCreateOpen] = useState(false);
  const [editAccount, setEditAccount] = useState<AccountResponse | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<AccountResponse | null>(
    null,
  );

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteAccount.mutate(deleteTarget.account_id, {
      onSuccess: () => {
        showToast.success("Account deleted");
        setDeleteTarget(null);
      },
      onError: (err) => {
        showToast.error(parseApiError(err));
      },
    });
  };

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Accounts</h1>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 size-4" />
          Add Account
        </Button>
      </div>

      {accounts && accounts.length > 0 ? (
        <AccountsTable
          accounts={accounts}
          onEdit={setEditAccount}
          onDelete={setDeleteTarget}
        />
      ) : (
        <EmptyState
          icon={Wallet}
          title="No accounts yet"
          description="Create your first account to start tracking your finances."
          action={{ label: "Add Account", onClick: () => setCreateOpen(true) }}
        />
      )}

      <CreateAccountDialog open={createOpen} onOpenChange={setCreateOpen} />

      <EditAccountDialog
        account={editAccount}
        open={!!editAccount}
        onOpenChange={(open) => !open && setEditAccount(null)}
      />

      <ConfirmDeleteDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Account"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This will fail if the account has postings or transfers.`}
        onConfirm={handleDelete}
        isPending={deleteAccount.isPending}
      />
    </div>
  );
}
