"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Bell, CheckCheck, ChevronLeft, ChevronRight, ClipboardList, FileText, FlaskConical, LayoutDashboard, ListFilter, Menu, Search, Settings, ShieldCheck, Sparkles } from "lucide-react";
import { usePreview, displayTime } from "@/lib/preview-context";
import { allFindings, pendingActions } from "@/lib/model";
import { TOOLS } from "@/lib/fixtures";
import { Badge, Button, Dialog, EmptyState, Notice } from "./ui";
import { OverlayHost } from "./overlays";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/assessments", label: "Assessments", icon: ClipboardList },
  { href: "/approvals", label: "Approvals", icon: CheckCheck },
  { href: "/findings", label: "Findings", icon: ListFilter },
  { href: "/reports", label: "Reports", icon: FileText },
];

function Brand({ compact = false }: { compact?: boolean }) {
  return <Link href="/" aria-label="Reknyx home" className="flex items-center gap-2.5 px-2 py-1"><span className="grid size-9 shrink-0 place-items-center rounded-xl bg-lime text-lg font-extrabold text-[#141a14]">R<span className="sr-only">eknyx</span></span>{!compact && <span className="text-[23px] font-extrabold tracking-[-.06em]">Reknyx<span className="text-forest">.</span></span>}</Link>;
}

export function AppShell({ children }: { children: ReactNode }) {
  const { state, open, close, overlay, toast, storageError, savePreferences } = usePreview();
  const pathname = usePathname();
  const [panel, setPanel] = useState<"search" | "notifications" | "menu" | null>(null);
  const collapsed = state.preferences.collapsed;
  const pending = pendingActions(state.assessments);
  const currentId = pathname.startsWith("/assessments/") ? pathname.split("/")[2] : undefined;

  useEffect(() => { setPanel(null); close(); }, [pathname]);
  useEffect(() => {
    function shortcut(event: KeyboardEvent) {
      if (overlay || (document.activeElement?.closest("input,textarea,select,[contenteditable=true]"))) return;
      if (event.key === "/" || ((event.ctrlKey || event.metaKey) && event.key === "k")) {
        event.preventDefault(); setPanel("search");
      }
    }
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, [overlay]);

  function NavLinks({ mobile = false }: { mobile?: boolean }) {
    return <nav aria-label={mobile ? "Mobile navigation" : "Main navigation"} className="flex flex-col gap-1.5">{NAV.map(({ href, label, icon: Icon }) => {
      const active = href === "/" ? pathname === "/" || pathname === "/dashboard" : pathname.startsWith(href);
      return <Link href={href} onClick={() => setPanel(null)} key={label} title={label} aria-current={active ? "page" : undefined}
        className={`relative flex min-h-11 items-center gap-3 rounded-xl px-3 text-[13px] font-semibold ${collapsed && !mobile ? "justify-center" : ""} ${active ? "bg-soft text-ink" : "text-muted hover:bg-soft hover:text-ink"}`}>
        <Icon size={19} strokeWidth={1.7} />{(!collapsed || mobile) && <span>{label}</span>}{label === "Approvals" && pending.length > 0 && <span aria-label={`${pending.length} pending`} className={`grid min-w-5 place-items-center rounded-full bg-ink px-1.5 text-[10px] leading-5 text-surface ${collapsed && !mobile ? "absolute -right-1 -top-1" : "ml-auto"}`}>{pending.length}</span>}
      </Link>;
    })}<Link href="/settings" onClick={() => setPanel(null)} aria-current={pathname === "/settings" ? "page" : undefined} title="Settings" className={`mt-3 flex min-h-11 items-center gap-3 rounded-xl px-3 text-[13px] font-semibold ${collapsed && !mobile ? "justify-center" : ""} ${pathname === "/settings" ? "bg-soft" : "text-muted hover:bg-soft"}`}><Settings size={19} strokeWidth={1.7} />{(!collapsed || mobile) && "Settings"}</Link></nav>;
  }

  return <>
    <div className="app-shell flex min-h-screen gap-4 p-3 sm:p-4">
      <aside className={`sticky top-4 hidden h-[calc(100dvh-32px)] shrink-0 flex-col rounded-[24px] bg-surface px-3 py-6 md:flex ${collapsed ? "w-[76px]" : "w-[218px]"}`}>
        <Brand compact={collapsed} />
        <Link href="/settings" title="Analyst preferences" className={`mb-7 mt-6 flex items-center gap-2.5 rounded-xl bg-soft p-2 ${collapsed ? "justify-center" : ""}`}><span className="grid size-8 shrink-0 place-items-center rounded-[10px] bg-[#e3edcf] font-extrabold text-[#365a1d]">{state.preferences.analyst.charAt(0).toUpperCase() || "A"}</span>{!collapsed && <span className="min-w-0"><b className="block truncate text-xs">{state.preferences.analyst}</b><span className="block text-[10px] text-muted">Security analyst</span></span>}</Link>
        <NavLinks />
        <div className="mt-auto pt-8">{!collapsed && <div className="mb-4 rounded-2xl border border-line p-3.5"><FlaskConical size={17} className="mb-2 text-forest" /><p className="text-xs font-bold">Your safe preview space</p><p className="mt-1.5 text-[11px] leading-relaxed text-muted">Synthetic evidence. No scanner or AI model is connected.</p><div className="mt-3 flex items-center gap-1.5 text-[10px] font-semibold text-forest"><span className="size-1.5 rounded-full bg-lime" />Demo data only</div></div>}
          <button type="button" title={collapsed ? "Expand sidebar" : "Collapse sidebar"} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} aria-expanded={!collapsed}
            onClick={() => savePreferences({ ...state.preferences, collapsed: !collapsed })} className={`flex w-full items-center gap-3 rounded-xl p-3 text-xs text-muted hover:bg-soft ${collapsed ? "justify-center" : ""}`}>
            {collapsed ? <ChevronRight size={17} /> : <><ChevronLeft size={17} />Collapse sidebar</>}
          </button>
        </div>
      </aside>
      <div className="min-w-0 flex-1 px-0 pb-8 sm:px-1">
        <header className="mb-5 flex items-center gap-2.5">
          <button type="button" aria-label="Open navigation" onClick={() => setPanel("menu")} className="grid size-11 shrink-0 place-items-center rounded-xl bg-surface md:hidden"><Menu size={20} /></button>
          <button type="button" aria-label="Quick search" onClick={() => setPanel("search")} className="flex h-[48px] min-w-0 flex-1 items-center gap-3 rounded-[14px] border border-lime/60 bg-surface p-1.5 text-left text-muted">
            <span className="grid size-[33px] shrink-0 place-items-center rounded-[10px] bg-lime text-[#141a14]"><Search size={17} /></span><span className="truncate text-xs sm:text-[13px]">Search assessments, findings, tools…</span><kbd className="ml-auto mr-2 hidden rounded border border-line px-1.5 text-[11px] sm:block">/</kbd>
          </button>
          <button type="button" aria-label="Notifications" onClick={() => setPanel("notifications")} className="relative grid size-12 shrink-0 place-items-center rounded-[14px] bg-surface"><Bell size={19} strokeWidth={1.7} />{pending.length > 0 && <span className="absolute right-3 top-3 size-1.5 rounded-full bg-[#ef8f6b]" />}</button>
          <Button variant="lime" aria-label="Ask assistant" onClick={() => open({ type: "assistant", assessmentId: currentId })} className="h-12 !rounded-[14px] !px-3 sm:!px-4"><Sparkles size={17} /><span className="hidden sm:inline">Ask assistant</span></Button>
        </header>
        <div className="mb-5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-muted"><span className="inline-flex items-center gap-1.5 font-bold text-forest"><FlaskConical size={13} />Synthetic preview</span><span className="hidden sm:inline">/</span><span>Changes stay in this session. Nothing touches a real system.</span></div>
        {storageError && <div className="mb-4" role="alert"><Notice tone="warning">{storageError}</Notice></div>}
        <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-lime focus:p-3 focus:text-[#141a14]">Skip to content</a>
        <main id="main-content" tabIndex={-1}>{children}</main>
        <footer className="mt-7 flex flex-wrap justify-between gap-2 px-1 text-[10px] text-muted"><span>Reknyx / Assessment workspace</span><span className="flex items-center gap-1"><ShieldCheck size={12} />Analyst controlled. Evidence led.</span></footer>
      </div>
    </div>
    {panel === "search" && <SearchDialog close={() => setPanel(null)} />}
    {panel === "notifications" && <Dialog title="Notifications" description="Decisions and activity across your synthetic assessments." onClose={() => setPanel(null)}>
      <p className="mb-2 text-xs font-bold text-muted">Needs your attention</p>
      {pending.map(({ assessment, action }) => <button key={`${assessment.id}-${action.id}`} onClick={() => { setPanel(null); open({ type: "action", assessmentId: assessment.id, actionId: action.id }); }} className="flex w-full gap-3 rounded-xl p-3 text-left hover:bg-soft"><span className="mt-1.5 size-2 shrink-0 rounded-full bg-[#f8b46a]" /><span><b className="block text-[13px]">{action.kind === "Active" ? "Unsupported validation proposal" : "Approval needed"}</b><span className="text-xs text-muted">{assessment.name}: {action.title}</span></span></button>)}
      {!pending.length && <p className="py-4 text-xs text-muted">No approvals waiting.</p>}
      <p className="mb-2 mt-5 text-xs font-bold text-muted">Recent activity</p>
      {state.assessments.flatMap((a) => a.audit.map((event) => ({ ...event, assessment: a }))).sort((a, b) => b.at.localeCompare(a.at)).slice(0, 5).map((event) => <Link onClick={() => setPanel(null)} key={`${event.assessment.id}-${event.id}`} href={`/assessments/${event.assessment.id}/audit`} className="block rounded-xl p-3 hover:bg-soft"><b className="block text-[13px]">{event.title}</b><p className="mt-1 text-xs text-muted">{event.assessment.name} / {displayTime(event.at)}</p></Link>)}
    </Dialog>}
    {panel === "menu" && <Dialog title="Reknyx" description="Assessment workspace" onClose={() => setPanel(null)}><NavLinks mobile /></Dialog>}
    <OverlayHost />
    <div aria-live="polite" aria-atomic="true" className="toast-message pointer-events-none fixed bottom-5 left-1/2 z-[100] w-max max-w-[calc(100%-32px)] -translate-x-1/2">{toast && <p role="status" className="rounded-2xl bg-ink px-5 py-3 text-center text-xs font-semibold text-surface shadow-xl">{toast}</p>}</div>
  </>;
}

function SearchDialog({ close }: { close: () => void }) {
  const { state, open } = usePreview();
  const router = useRouter();
  const [query, setQuery] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const match = (...values: string[]) => values.join(" ").toLowerCase().includes(query.toLowerCase().trim());
  const entries: { id: string; category: string; title: string; detail: string; run: () => void }[] = [];
  state.assessments.filter((a) => match(a.name, a.id, a.target, a.ip)).forEach((a) => entries.push({ id: a.id, category: "Assessment", title: a.name, detail: a.target, run: () => router.push(`/assessments/${a.id}/plan`) }));
  if (query.trim()) {
    allFindings(state.assessments).filter((f) => match(f.title, f.id, f.asset, f.reference)).forEach((f) => entries.push({ id: `${f.assessmentId}-${f.id}`, category: "Finding", title: f.title, detail: `${f.id} / ${f.asset}`, run: () => open({ type: "finding", assessmentId: f.assessmentId, findingId: f.id }) }));
    TOOLS.filter((tool) => match(tool.name, tool.description)).forEach((tool) => entries.push({ id: tool.name, category: "Tool", title: tool.name, detail: "In development", run: () => router.push("/settings#integrations") }));
  }
  [...NAV, { href: "/settings", label: "Settings" }].filter((nav) => match(nav.label)).forEach((nav) => entries.push({ id: nav.href, category: "Page", title: nav.label, detail: "Workspace", run: () => router.push(nav.href) }));
  const choose = (run: () => void) => { close(); run(); };
  return <Dialog title="Quick search" description="Jump to an assessment, finding, tool, or page." onClose={close}>
    <label htmlFor="global-search" className="sr-only">Search workspace</label><input ref={input} autoFocus id="global-search" type="search" placeholder="Try nginx, AST-001, or ZAP" value={query} onChange={(event) => setQuery(event.target.value)}
      onKeyDown={(event) => { if (event.key === "Enter" && entries[0]) { event.preventDefault(); choose(entries[0].run); } }} />
    <div aria-label="Search results" className="mt-4 max-h-[55vh] space-y-1 overflow-auto">{entries.slice(0, 12).map((entry) => <button key={entry.id} type="button" onClick={() => choose(entry.run)} className="flex w-full items-center justify-between gap-3 rounded-xl px-3 py-3 text-left hover:bg-soft"><div className="min-w-0"><b className="block text-[13px]">{entry.title}</b><span className="block text-xs text-muted">{entry.detail}</span></div><Badge>{entry.category}</Badge></button>)}{!entries.length && <EmptyState title="No matches" description="Try an assessment name, finding identifier, or tool name." />}</div>
  </Dialog>;
}
