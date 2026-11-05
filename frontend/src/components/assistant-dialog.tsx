"use client";

import { useState } from "react";
import { ClipboardList, Send, Sparkles } from "lucide-react";
import { proposeAction } from "@/lib/model";
import { displayTime, makeId, timestamp, usePreview } from "@/lib/preview-context";
import { Badge, Button, Dialog, EmptyState, Field, Notice } from "./ui";

export function AssistantDialog({ assessmentId }: { assessmentId?: string }) {
  const { state, close, updateAssessment, notify } = usePreview();
  const [selectedId, setSelectedId] = useState(assessmentId || state.assessments[0]?.id || "");
  const [draft, setDraft] = useState("");
  const assessment = state.assessments.find((item) => item.id === selectedId);
  const lastRequest = assessment?.messages.findLast((message) => message.role === "analyst")?.text;

  function send() {
    if (!assessment || !draft.trim()) return;
    const text = draft.trim();
    const now = timestamp();
    updateAssessment(assessment.id, (current) => ({ ...current, messages: [...current.messages,
      { id: makeId("MSG"), role: "analyst", text, at: now },
      { id: makeId("MSG"), role: "assistant", text: `Message saved for ${current.target}. Use Generate preview proposal to check this request against the recorded scope. No proposal, model call, or scan was started.`, at: now },
    ] }));
    setDraft("");
  }

  function generate() {
    if (!assessment || !lastRequest) return;
    const now = timestamp();
    updateAssessment(assessment.id, (current) => {
      const result = proposeAction(current, lastRequest, now);
      const disabledTool = result.action && !state.preferences.tools[result.action.tool];
      const action = disabledTool ? undefined : result.action;
      const message = disabledTool ? `${result.action!.tool} is turned off in preview preferences. No proposal added.` : result.message;
      return { ...current,
        actions: action ? [...current.actions, action] : current.actions,
        messages: [...current.messages, { id: makeId("MSG"), role: "assistant", text: message, at: now }],
        audit: [...current.audit, { id: makeId("EV"), at: now, title: action ? "Deterministic proposal generated" : message.includes("rejected") ? "Preview request rejected" : "Preview request evaluated", detail: message }],
      };
    });
    notify("Preview request evaluated. Review the assistant response.");
  }

  return <Dialog title="Assessment assistant" description="Demo / deterministic. One assistant, bound to the selected assessment." onClose={close} wide>
    <div className="mb-5 flex flex-wrap gap-2"><Badge>Model: Not connected</Badge><Badge>AI planning: In development</Badge></div>
    <Field htmlFor="assistant-assessment" label="Assessment context"><select id="assistant-assessment" value={selectedId} onChange={(event) => { setSelectedId(event.target.value); setDraft(""); }}>{state.assessments.map((item) => <option key={item.id} value={item.id}>{item.name} / {item.target}</option>)}</select></Field>
    {assessment ? <>
      <div className="my-4"><Notice>Recorded scope: {assessment.target} / {assessment.ip}, TCP {assessment.ports.join(", ")}. Messages are saved separately from proposal generation, approval, and execution.</Notice></div>
      <div role="log" aria-label="Assessment conversation" aria-live="polite" className="fine-scrollbar mb-5 max-h-[34vh] space-y-3 overflow-y-auto rounded-2xl border border-line bg-soft p-3 sm:p-4">
        {!assessment.messages.length && <div className="py-4 text-center"><Sparkles size={24} className="mx-auto mb-3 text-forest" /><h3 className="text-sm font-bold">What would you like to investigate?</h3><p className="mt-2 text-xs text-muted">Start with a request for the selected target.</p></div>}
        {assessment.messages.map((message) => <div key={message.id} className={`max-w-[95%] rounded-2xl p-3 sm:max-w-[85%] ${message.role === "analyst" ? "ml-auto bg-[#e6f0d8] text-[#263e18]" : "border border-line bg-surface"}`}><b className="mb-1 block text-[10px]">{message.role === "analyst" ? "You" : "Assistant / deterministic"}</b><p className="whitespace-pre-wrap break-words text-xs leading-relaxed">{message.text}</p><span className="mt-2 block text-[9px] opacity-70">{displayTime(message.at)}</span></div>)}
      </div>
      <div className="mb-4 flex flex-wrap gap-2">{[`Discover services on ${assessment.target}`, `Check web headers on ${assessment.target}`, "Scan 203.0.113.9 (outside scope)"].map((suggestion) => <button key={suggestion} type="button" onClick={() => setDraft(suggestion)} className="rounded-full border border-line px-3 py-1.5 text-[10px] text-muted hover:bg-soft">{suggestion}</button>)}</div>
      <form onSubmit={(event) => { event.preventDefault(); send(); }}><Field htmlFor="assistant-message" label="Message"><textarea id="assistant-message" maxLength={3000} rows={3} value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={`For example: discover services on ${assessment.target}`} /></Field><div className="mt-3 flex flex-wrap items-center justify-between gap-3"><p className="max-w-[45ch] text-[10px] text-muted">Generate evaluates the last sent request using a fixed demo rule set. It never calls an AI model.</p><Button type="submit" variant="lime" disabled={!draft.trim()}><Send size={13} />Send message</Button></div></form>
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5"><Button onClick={close}>Close</Button><Button variant="dark" disabled={!lastRequest} onClick={generate}><ClipboardList size={14} />Generate preview proposal</Button></div>
    </> : <EmptyState title="No assessment selected" description="Create an assessment first so the assistant can use its recorded scope." />}
  </Dialog>;
}
