const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const moneyWhole = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});
const count = new Intl.NumberFormat("en-US");

// Backend times are naive UTC ("2020-06-28T23:48:51"); format them in UTC so the
// browser's own timezone never shifts a 23:48 transaction into another day.
const dateTime = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: "UTC",
});

export const formatMoney = (n: number) => money.format(n);
export const formatMoneyWhole = (n: number) => moneyWhole.format(n);
export const formatCount = (n: number) => count.format(n);
export const formatDateTime = (iso: string) => dateTime.format(new Date(`${iso}Z`));
export const formatPercent = (part: number, whole: number) =>
  whole ? `${Math.round((100 * part) / whole)}%` : "0%";
