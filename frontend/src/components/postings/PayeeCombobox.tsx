import { Combobox } from "@base-ui/react/combobox";
import { usePayeeSuggestions } from "@/api/hooks";
import { useDebounce } from "@/hooks/use-debounce";

interface PayeeComboboxProps {
  value: string;
  onChange: (value: string) => void;
  id?: string;
  placeholder?: string;
  maxLength?: number;
}

export function PayeeCombobox({
  value,
  onChange,
  id,
  placeholder = "e.g. Supermarket, Employer",
  maxLength = 200,
}: PayeeComboboxProps) {
  const debouncedValue = useDebounce(value, 200);
  const { data: suggestions = [] } = usePayeeSuggestions(debouncedValue);

  return (
    <Combobox.Root
      items={suggestions}
      inputValue={value}
      onInputValueChange={(nextValue) => {
        onChange(nextValue);
      }}
      onValueChange={(selectedItem) => {
        if (selectedItem != null) {
          onChange(String(selectedItem));
        }
      }}
      filter={null}
    >
      <Combobox.Input
        id={id}
        placeholder={placeholder}
        maxLength={maxLength}
        autoComplete="off"
        data-slot="input"
        className="h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-base transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50 md:text-sm dark:bg-input/30"
      />
      {suggestions.length > 0 && (
        <Combobox.Portal>
          <Combobox.Positioner className="z-50 outline-none" sideOffset={4}>
            <Combobox.Popup className="max-h-48 w-[var(--anchor-width)] overflow-y-auto overscroll-contain rounded-lg bg-popover p-1 text-sm text-popover-foreground shadow-md ring-1 ring-foreground/10">
              <Combobox.List>
                {(item: string) => (
                  <Combobox.Item
                    key={item}
                    value={item}
                    className="cursor-default select-none rounded-md px-2 py-1.5 text-sm outline-none transition-colors data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground"
                  >
                    {item}
                  </Combobox.Item>
                )}
              </Combobox.List>
            </Combobox.Popup>
          </Combobox.Positioner>
        </Combobox.Portal>
      )}
    </Combobox.Root>
  );
}
