"use client";

import { useEffect, useRef, useState } from "react";
import { FileUp, Upload } from "lucide-react";
import { TOOLS } from "@/lib/fixtures";
import { makeId, timestamp, usePreview } from "@/lib/preview-context";
import type { Assessment } from "@/lib/types";
import { Button, Dialog, Field, Notice } from "./ui";

export function ImportDialog({ assessment }: { assessment: Assessment }) {
  const { state, close, updateAssessment, notify } = usePreview();
  const options = TOOLS.filter((tool) => tool.intendedMode === "Import-only" && state.preferences.tools[tool.name]);
  const [tool, setTool] = useState(options[0]?.name || "");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  async function attach() {
    setError("");
    if (!file || !tool || !options.some((option) => option.name === tool)) { setError("Choose an enabled import tool and a file."); return; }
    if (file.size === 0 || file.size > 1024 * 1024) { setError("Choose a non-empty file up to 1 MiB. The preview only attaches bytes; it does not parse native reports."); return; }
    setBusy(true);
    try {
      const bytes = await file.arrayBuffer();
      const digest = await crypto.subtle.digest("SHA-256", bytes);
      if (!mounted.current) return;
      const sha256 = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
      const now = timestamp();
      const attachment = { id: makeId("ATT"), name: file.name, tool, size: `${file.size} bytes`, sha256, excerpt: new TextDecoder().decode(bytes.slice(0, 16384)), attachedAt: now };
      updateAssessment(assessment.id, (current) => ({ ...current, attachments: [...current.attachments, attachment], audit: [...current.audit, { id: makeId("EV"), at: now, title: "Preview file attached", detail: `${file.name} / ${tool} / SHA-256 ${sha256}. Not parsed; no findings created or traffic sent.` }] }));
      notify("File attached in memory. Not parsed; no findings created."); close();
    } catch {
      if (mounted.current) setError("The file could not be read or hashed. Choose another file and try again.");
    } finally { if (mounted.current) setBusy(false); }
  }
  return <Dialog title="Attach recorded results" description={`${assessment.name} / Preview attachment only`} onClose={close}>
    <Notice>Native parsing is In development. This reads and hashes a local file into this session; it does not import findings, upload data, or execute a tool. Use synthetic sample files only.</Notice>
    <div className="my-5 space-y-5"><Field htmlFor="attachment-tool" label="Source tool"><select id="attachment-tool" value={tool} disabled={busy || !options.length} onChange={(event) => setTool(event.target.value)}>{options.map((option) => <option key={option.name}>{option.name}</option>)}</select></Field>{!options.length && <p role="alert" className="text-xs text-[#a4432c]">Enable a preview import tool in Settings first.</p>}
      <Field htmlFor="attachment-file" label="Recorded output file" hint="Maximum 1 MiB. Only the first 16 KiB are displayed as escaped text."><div className="rounded-2xl border border-dashed border-line bg-soft p-5"><FileUp size={24} className="mb-3 text-forest" /><input id="attachment-file" type="file" accept=".xml,.json,.txt,.nmap,.nessus" disabled={busy} onChange={(event) => { setFile(event.target.files?.[0] || null); setError(""); }} className="max-w-full text-xs file:mr-3 file:rounded-full file:border-0 file:bg-surface file:px-3 file:py-2 file:text-xs file:font-bold" /></div></Field></div>
    {error && <p role="alert" className="mb-4 text-xs text-[#a4432c]">{error}</p>}
    <div className="flex justify-end gap-2 border-t border-line pt-5"><Button onClick={close}>Cancel</Button><Button variant="lime" disabled={busy || !file || !options.length} onClick={attach}><Upload size={14} />{busy ? "Reading local file…" : "Attach to preview"}</Button></div>
  </Dialog>;
}
