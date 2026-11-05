"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { createInitialState, DEFAULT_PREFERENCES } from "./fixtures";
import type { Assessment, Preferences, PreviewState } from "./types";

export type Overlay =
  | { type: "new" }
  | { type: "action"; assessmentId: string; actionId: string }
  | { type: "finding"; assessmentId: string; findingId: string }
  | { type: "assistant"; assessmentId?: string }
  | { type: "import"; assessmentId: string }
  | { type: "report"; reportId: string }
  | null;

type PreviewContextValue = {
  state: PreviewState;
  setState: React.Dispatch<React.SetStateAction<PreviewState>>;
  updateAssessment: (id: string, update: (assessment: Assessment) => Assessment) => void;
  overlay: Overlay;
  open: (overlay: Overlay) => void;
  close: () => void;
  notify: (message: string) => void;
  savePreferences: (preferences: Preferences) => void;
  storageError: string;
  toast: string;
};

const PreviewContext = createContext<PreviewContextValue | null>(null);
const PREFERENCES_KEY = "reknyx.preview.preferences.v1";

// Only bounded, non-sensitive preferences cross the reload boundary.
function readPreferences(value: unknown): Preferences {
  const result = structuredClone(DEFAULT_PREFERENCES);
  if (!value || typeof value !== "object") return result;
  const saved = value as Record<string, unknown>;
  for (const key of ["analyst", "rate", "deadline", "ports"] as const) {
    if (typeof saved[key] === "string" && saved[key].length <= 120) result[key] = saved[key];
  }
  for (const key of ["collapsed", "includeSuspected", "includeAudit"] as const) {
    if (typeof saved[key] === "boolean") result[key] = saved[key];
  }
  if (["system", "light", "dark"].includes(String(saved.theme))) result.theme = saved.theme as Preferences["theme"];
  if (saved.tools && typeof saved.tools === "object") {
    for (const tool of Object.keys(result.tools)) {
      const enabled = (saved.tools as Record<string, unknown>)[tool];
      if (typeof enabled === "boolean") result.tools[tool] = enabled;
    }
  }
  return result;
}

export function PreviewProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<PreviewState>(createInitialState);
  const [overlay, open] = useState<Overlay>(null);
  const [toast, setToast] = useState("");
  const [storageError, setStorageError] = useState("");

  useEffect(() => {
    try {
      const stored = localStorage.getItem(PREFERENCES_KEY);
      if (stored) {
        const preferences = readPreferences(JSON.parse(stored));
        setState((current) => ({ ...current, preferences }));
      }
    } catch {
      setStorageError("Browser preferences could not be loaded. Defaults are active; assessment data stays in memory.");
    }
  }, []);

  useEffect(() => { document.documentElement.dataset.theme = state.preferences.theme; }, [state.preferences.theme]);
  useEffect(() => {
    if (!toast) return;
    const timeout = setTimeout(() => setToast(""), 4500);
    return () => clearTimeout(timeout);
  }, [toast]);

  function savePreferences(preferences: Preferences) {
    setState((current) => ({ ...current, preferences }));
    try {
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(preferences));
      setStorageError("");
    } catch {
      setStorageError("Browser storage is unavailable. Preferences apply for this session and will reset on reload.");
    }
  }

  function updateAssessment(id: string, update: (assessment: Assessment) => Assessment) {
    setState((current) => ({
      ...current,
      assessments: current.assessments.map((assessment) => assessment.id === id ? update(assessment) : assessment),
    }));
  }

  return <PreviewContext.Provider value={{ state, setState, updateAssessment, overlay, open, close: () => open(null), notify: setToast, savePreferences, storageError, toast }}>{children}</PreviewContext.Provider>;
}

export function usePreview() {
  const context = useContext(PreviewContext);
  if (!context) throw new Error("Preview components must be rendered inside PreviewProvider.");
  return context;
}

export function timestamp() { return new Date().toISOString(); }
export function makeId(prefix: string) { return `${prefix}-${crypto.randomUUID().slice(0, 8)}`; }
export function displayTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : new Intl.DateTimeFormat("en-GB", { month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: "UTC" }).format(date) + " UTC";
}
