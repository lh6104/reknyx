"use client";

import { useEffect, useState } from "react";
import { RotateCcw, Save } from "lucide-react";
import { DEFAULT_PREFERENCES, TOOLS } from "@/lib/fixtures";
import { usePreview } from "@/lib/preview-context";
import type { Preferences } from "@/lib/types";
import { Badge, Button, Card, CardTitle, Field, Heading, Notice } from "./ui";

export function SettingsPage() {
  const { state, savePreferences, notify } = usePreview();
  const [draft, setDraft] = useState<Preferences>(() => structuredClone(state.preferences));
  const [errors, setErrors] = useState<{ analyst?: string; ports?: string; bounds?: string }>({});

  useEffect(() => { setDraft(structuredClone(state.preferences)); }, [state.preferences]);

  function change<Key extends keyof Preferences>(key: Key, value: Preferences[Key]) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  function save() {
    const nextErrors: typeof errors = {};
    if (!draft.analyst.trim() || draft.analyst.trim().length > 80) nextErrors.analyst = "Enter an analyst name between 1 and 80 characters.";
    const parts = draft.ports.split(",").map((port) => port.trim());
    if (!draft.ports.trim() || draft.ports.length > 120 || parts.some((port) => !/^\d+$/.test(port) || Number(port) < 1 || Number(port) > 65535)) nextErrors.ports = "Enter comma-separated integer TCP ports from 1 to 65535 (up to 120 characters).";
    if (!["1 req/s", "2 req/s"].includes(draft.rate) || !["60 s", "120 s"].includes(draft.deadline)) nextErrors.bounds = "Choose one of the supported rate and deadline defaults.";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    savePreferences({ ...draft, analyst: draft.analyst.trim(), ports: [...new Set(parts.map(Number))].sort((a, b) => a - b).join(", "), tools: Object.fromEntries(TOOLS.map((tool) => [tool.name, tool.intendedMode !== "Planned" && Boolean(draft.tools[tool.name])])) });
    notify("Preferences applied.");
  }

  function reset() {
    const defaults = structuredClone(DEFAULT_PREFERENCES);
    setDraft(defaults);
    setErrors({});
    savePreferences(defaults);
    notify("Default preferences applied. Assessment data is unchanged.");
  }

  return <>
    <Heading title="Settings" description="Browser preferences for this preview. Assessment data stays in memory and resets on reload." action={<Button variant="lime" onClick={save}><Save size={15} aria-hidden="true" />Save preferences</Button>} />
    <form onSubmit={(event) => { event.preventDefault(); save(); }} className="grid gap-5 lg:grid-cols-2">
      <Card>
        <CardTitle title="Analyst and report" description="These choices are captured when you create a new report snapshot." />
        <div className="space-y-6">
          <Field label="Analyst name" htmlFor="analyst-name" error={errors.analyst} hint="Use a display name. Do not enter secrets or sensitive personal information."><input id="analyst-name" maxLength={80} autoComplete="off" value={draft.analyst} onChange={(event) => change("analyst", event.target.value)} aria-invalid={Boolean(errors.analyst)} /></Field>
          <label className="flex cursor-pointer items-start justify-between gap-4"><span><span className="block text-[13px] font-bold">Include suspected findings</span><span className="mt-1 block text-xs leading-relaxed text-muted">Keep uncertainty visible. If excluded, the sample report records how many were omitted.</span></span><input className="mt-1" type="checkbox" checked={draft.includeSuspected} onChange={(event) => change("includeSuspected", event.target.checked)} /></label>
          <label className="flex cursor-pointer items-start justify-between gap-4"><span><span className="block text-[13px] font-bold">Include audit trail</span><span className="mt-1 block text-xs leading-relaxed text-muted">Include timestamped review and decision history. Existing snapshots stay unchanged.</span></span><input className="mt-1" type="checkbox" checked={draft.includeAudit} onChange={(event) => change("includeAudit", event.target.checked)} /></label>
          <Field label="Theme" htmlFor="theme"><select id="theme" value={draft.theme} onChange={(event) => change("theme", event.target.value as Preferences["theme"])}><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></Field>
        </div>
      </Card>
      <Card>
        <CardTitle title="Assessment defaults" description="Used only when creating a new assessment. Existing scope and limits stay unchanged." />
        <div className="space-y-5">
          <Field label="Rate limit" htmlFor="default-rate"><select id="default-rate" value={draft.rate} onChange={(event) => change("rate", event.target.value)}><option>1 req/s</option><option>2 req/s</option></select></Field>
          <Field label="Deadline per action" htmlFor="default-deadline"><select id="default-deadline" value={draft.deadline} onChange={(event) => change("deadline", event.target.value)}><option>60 s</option><option>120 s</option></select></Field>
          <Field label="Allowed TCP ports" htmlFor="default-ports" error={errors.ports} hint="Comma-separated integers from 1 to 65535."><input id="default-ports" value={draft.ports} maxLength={120} onChange={(event) => change("ports", event.target.value)} aria-invalid={Boolean(errors.ports)} /></Field>
          {errors.bounds && <p role="alert" className="text-xs text-[#a4432c]">{errors.bounds}</p>}
          <Notice>Defaults do not revise existing scope or authorize any action. Explicit review and valid authorization remain separate. Active validation is In development.</Notice>
        </div>
      </Card>
      <Card id="integrations" className="lg:col-span-2">
        <CardTitle title="Tool integrations" description="All integrations are In development. Toggles only affect preview proposals and attachment choices; no tool is connected or started." />
        <div className="divide-y divide-line">{TOOLS.map((tool) => <div key={tool.name} className="flex items-start gap-3 py-5 first:pt-1 last:pb-0 sm:gap-4">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-xl text-xs font-extrabold text-[#141a14]" style={{ background: tool.color }}>{tool.initials}</span>
          <div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h3 className="text-[13px] font-bold">{tool.name}</h3><Badge>In development</Badge></div><p className="mt-1 text-xs text-muted">{tool.description}</p><p className="mt-2 text-xs leading-relaxed text-muted">{tool.limitation}</p><p className="mt-2 text-[11px] font-bold text-muted">Intended mode: {tool.intendedMode}</p></div>
          <input className="mt-2" type="checkbox" aria-label={`${tool.name} enabled`} checked={tool.intendedMode !== "Planned" && Boolean(draft.tools[tool.name])} disabled={tool.intendedMode === "Planned"} onChange={(event) => change("tools", { ...draft.tools, [tool.name]: event.target.checked })} />
        </div>)}</div>
      </Card>
      <div className="flex flex-wrap items-center justify-between gap-4 lg:col-span-2"><Button onClick={reset}><RotateCcw size={15} aria-hidden="true" />Reset preferences</Button><p className="max-w-[60ch] text-xs text-muted">Only preferences persist in this browser. Resetting preferences keeps assessments, evidence, and snapshots for the current session.</p><Button type="submit" variant="dark">Save preferences</Button></div>
    </form>
  </>;
}
