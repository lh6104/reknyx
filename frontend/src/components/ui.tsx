"use client";

import { useEffect, useId, useRef, type ReactNode, type ButtonHTMLAttributes } from "react";
import { createPortal } from "react-dom";
import { ArrowUpRight, Inbox, X } from "lucide-react";
import type { Severity } from "@/lib/types";

export const buttonClass = "inline-flex min-h-10 shrink-0 items-center justify-center gap-2 rounded-full border border-line bg-surface px-4 py-2 text-[13px] font-bold text-ink transition-colors hover:bg-soft disabled:cursor-not-allowed disabled:opacity-45";
export function Button({ children, variant = "default", small, className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "default" | "lime" | "dark" | "danger"; small?: boolean }) {
  const variants = { default: "", lime: "!border-lime !bg-lime !text-[#141a14] hover:!bg-[#b0dc67]", dark: "!border-ink !bg-ink !text-surface hover:opacity-90", danger: "!border-[#edc3b5] !bg-[#fae7df] !text-[#873c27]" };
  return <button type="button" {...props} className={`${buttonClass} ${variants[variant]} ${small ? "!min-h-8 !px-3 !py-1 text-xs" : ""} ${className}`}>{children}</button>;
}

export function Card({ children, className = "", ...props }: React.HTMLAttributes<HTMLElement>) {
  return <section className={`min-w-0 rounded-[20px] bg-surface p-5 sm:p-6 ${className}`} {...props}>{children}</section>;
}
export function Heading({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="mb-6 flex flex-wrap items-center justify-between gap-4"><div><h1 className="text-[26px] font-extrabold tracking-[-.04em] sm:text-[30px]">{title}</h1><p className="mt-1 max-w-[75ch] text-[13px] text-muted">{description}</p></div>{action}</div>;
}
export function CardTitle({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return <div className="mb-4 flex items-start justify-between gap-3"><div><h2 className="text-[15px] font-extrabold tracking-[-.02em]">{title}</h2>{description && <p className="mt-1 text-xs leading-relaxed text-muted">{description}</p>}</div>{action}</div>;
}

export const severityColors: Record<Severity, string> = { Critical: "#ef8f6b", High: "#f8b46a", Medium: "#f1ea5f", Low: "#9fd04f" };
export function Badge({ children, tone = "neutral", className = "" }: { children: ReactNode; tone?: "neutral" | "success" | "warning" | "danger" | Severity; className?: string }) {
  const colors: Record<string, string> = { neutral: "bg-soft text-muted", success: "bg-[#e6f0d8] text-[#365a1d]", warning: "bg-[#f8f2ce] text-[#695a11]", danger: "bg-[#fae3d9] text-[#863b26]", Critical: "bg-[#fae3d9] text-[#863b26]", High: "bg-[#fce9d1] text-[#805019]", Medium: "bg-[#f7f3c5] text-[#685e16]", Low: "bg-[#e6f0d8] text-[#365a1d]" };
  return <span className={`inline-flex w-fit shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold leading-tight ${colors[tone]} ${className}`}>{children}</span>;
}
export function StateBadge({ state }: { state: string }) {
  return <Badge tone={state === "Failed" || state === "Declined" ? "danger" : state === "Pending" || state.includes("approve") ? "warning" : state === "Done" || state === "Approved" ? "success" : "neutral"}>{state}</Badge>;
}
export function EmptyState({ title, description, children }: { title: string; description: string; children?: ReactNode }) {
  return <div className="flex flex-col items-center px-4 py-12 text-center"><span className="mb-4 rounded-2xl bg-soft p-3 text-muted"><Inbox size={24} /></span><h3 className="font-bold">{title}</h3><p className="mt-2 max-w-[45ch] text-[13px] leading-relaxed text-muted">{description}</p>{children && <div className="mt-5">{children}</div>}</div>;
}
export function Progress({ value, warning = false, label }: { value: number; warning?: boolean; label: string }) {
  return <div role="progressbar" aria-label={label} aria-valuenow={value} aria-valuemin={0} aria-valuemax={100} className="h-2.5 overflow-hidden rounded-full bg-soft"><div className={`h-full rounded-full ${warning ? "bg-[#f8b46a]" : "bg-lime"}`} style={{ width: `${value}%` }} /></div>;
}
export function Notice({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "warning" | "danger" }) {
  return <div className={`rounded-xl border p-3 text-xs leading-relaxed ${tone === "warning" ? "border-[#eadfac] bg-[#fbf6dc] text-[#695a11]" : tone === "danger" ? "border-[#edc3b5] bg-[#fae7df] text-[#873c27]" : "border-line bg-soft text-muted"}`}>{children}</div>;
}
export function Field({ label, children, error, hint, htmlFor }: { label: string; children: ReactNode; error?: string; hint?: string; htmlFor: string }) {
  return <div className="space-y-2"><label htmlFor={htmlFor} className="block text-[13px] font-bold">{label}</label>{children}{hint && <p className="text-xs text-muted">{hint}</p>}{error && <p role="alert" className="text-xs font-semibold text-[#a4432c]">{error}</p>}</div>;
}
export function DetailList({ items }: { items: [string, ReactNode][] }) {
  return <dl className="grid gap-x-6 gap-y-3 text-[13px] sm:grid-cols-[145px_minmax(0,1fr)]">{items.map(([label, value]) => <div key={label} className="contents"><dt className="text-muted">{label}</dt><dd className="min-w-0 break-words font-medium">{value}</dd></div>)}</dl>;
}
export function OpenIcon() { return <ArrowUpRight size={15} aria-hidden="true" />; }

export function Dialog({ title, description, children, onClose, wide = false, printable = false }: { title: string; description: string; children: ReactNode; onClose: () => void; wide?: boolean; printable?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descriptionId = useId();
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    const dialog = ref.current;
    const opener = document.activeElement as HTMLElement | null;
    dialog?.showModal();
    const before = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      dialog?.close();
      document.body.style.overflow = before;
      if (opener?.isConnected) opener.focus();
    };
  }, []);
  return createPortal(<dialog ref={ref} aria-labelledby={titleId} aria-describedby={descriptionId} data-print-report={printable || undefined}
    className={`reknyx-dialog m-auto max-h-[90dvh] w-[calc(100%-24px)] overflow-y-auto rounded-[24px] border border-line bg-surface p-5 text-ink shadow-2xl sm:p-7 ${wide ? "max-w-[850px]" : "max-w-[600px]"}`}
    onCancel={(event) => { event.preventDefault(); closeRef.current(); }}
    onKeyDown={(event) => {
      if (event.key !== "Tab") return;
      const focusable = Array.from(ref.current?.querySelectorAll<HTMLElement>('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),summary,[tabindex="0"]') || []).filter((element) => element.getClientRects().length > 0);
      const first = focusable[0];
      const last = focusable.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }}
    onClick={(event) => {
      if (event.target !== ref.current) return;
      const box = ref.current.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) closeRef.current();
    }}>
    <div className="mb-5 flex items-start justify-between gap-4 print:hidden"><div><h2 id={titleId} className="text-xl font-extrabold tracking-[-.03em]">{title}</h2><p id={descriptionId} className="mt-2 text-[13px] leading-relaxed text-muted">{description}</p></div><button type="button" onClick={onClose} aria-label="Close dialog" className="rounded-full bg-soft p-2 hover:bg-line"><X size={18} /></button></div>
    {children}
  </dialog>, document.body);
}
