const formatterCache = new Map<string, Intl.NumberFormat>();

function getFormatter(currency: string): Intl.NumberFormat {
  let formatter = formatterCache.get(currency);
  if (!formatter) {
    formatter = new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
    });
    formatterCache.set(currency, formatter);
  }
  return formatter;
}

export function formatCurrency(amount: string, currency: string): string {
  return getFormatter(currency).format(Number(amount));
}
