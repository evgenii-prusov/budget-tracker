import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createCategory, deleteCategory, listCategories, updateCategory } from '../lib/api';
import { Tag, Trash, PencilSimple, Check } from '@phosphor-icons/react';

export default function CategoriesPage() {
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: listCategories });
  const qc = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (name: string) => createCategory(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['categories'] }),
  });
  const deleteMutation = useMutation({
    mutationFn: deleteCategory,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['categories'] }),
  });
  const updateMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => updateCategory(id, name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['categories'] }),
  });

  return (
    <div className="flex flex-col gap-6">
      <AddCategoryCard
        onCreate={(name) => createMutation.mutateAsync(name)}
        loading={createMutation.isPending}
        error={createMutation.error instanceof Error ? createMutation.error.message : null}
      />

      <div className="glass-card border border-white/10">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
          <Tag size={18} className="text-neon-cyan" />
          <p className="text-sm font-semibold">Categories</p>
        </div>
        <ul className="divide-y divide-white/5">
          {(categories ?? []).map((cat) => (
            <CategoryRow
              key={cat.category_id}
              category={cat}
              onDelete={() => deleteMutation.mutate(cat.category_id)}
              onRename={(name) => updateMutation.mutate({ id: cat.category_id, name })}
            />
          ))}
          {(categories ?? []).length === 0 && (
            <li className="px-4 py-5 text-center text-slate-400">No categories yet.</li>
          )}
        </ul>
      </div>
    </div>
  );
}

function AddCategoryCard({
  onCreate,
  loading,
  error,
}: {
  onCreate: (name: string) => Promise<unknown> | void;
  loading: boolean;
  error: string | null;
}) {
  const [name, setName] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  return (
    <div className="glass-card p-4 border border-white/10">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">New category</p>
          <h3 className="text-lg font-semibold">Label your spending</h3>
        </div>
      </div>
      <form
        className="flex gap-3"
        onSubmit={async (e) => {
          e.preventDefault();
          if (!name) return;
          setLocalError(null);
          try {
            await onCreate(name);
            setName('');
          } catch (err) {
            const msg = err instanceof Error ? err.message : 'Could not create category';
            setLocalError(msg);
          }
        }}
      >
        <input
          className="flex-1 rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
          placeholder="e.g. Groceries"
          value={name}
          onChange={(e) => setName(e.target.value)}
          minLength={2}
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-neon-pink/90 text-base-900 px-4 py-2 text-sm font-semibold hover:bg-neon-pink transition shadow-glow disabled:opacity-60"
        >
          {loading ? 'Saving…' : 'Add'}
        </button>
      </form>
      {(localError || error) && (
        <p className="mt-2 text-sm text-red-200">
          {localError || error}
        </p>
      )}
    </div>
  );
}

function CategoryRow({
  category,
  onDelete,
  onRename,
}: {
  category: { category_id: string; name: string };
  onDelete: () => void;
  onRename: (name: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(category.name);

  return (
    <li className="px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        {editing ? (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              onRename(name);
              setEditing(false);
            }}
            className="flex items-center gap-2"
          >
            <input
              className="rounded-lg bg-base-700/70 border border-white/10 px-2 py-1 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
              minLength={2}
            />
            <button type="submit" className="p-1 rounded-lg bg-neon-cyan/80 text-base-900">
              <Check size={14} weight="bold" />
            </button>
          </form>
        ) : (
          <span className="font-semibold text-slate-100">{category.name}</span>
        )}
        <span className="text-[11px] text-slate-500">{category.category_id.slice(0, 8)}…</span>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={() => setEditing((v) => !v)}
          className="p-2 rounded-lg bg-white/5 text-slate-200 hover:bg-white/10"
          title="Rename"
        >
          <PencilSimple size={16} />
        </button>
        <button
          onClick={onDelete}
          className="p-2 rounded-lg bg-red-500/20 text-red-200 hover:bg-red-500/30"
          title="Delete"
        >
          <Trash size={16} />
        </button>
      </div>
    </li>
  );
}
