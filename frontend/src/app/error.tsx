"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return <section role="alert" className="rounded-[20px] bg-surface p-8"><h1 className="text-xl font-extrabold">This view could not be displayed</h1><p className="mt-2 text-sm text-muted">An application error occurred. Your session data has not been replaced with new sample results.</p><button onClick={reset} className="mt-5 rounded-full bg-lime px-5 py-2 font-bold text-[#141a14]">Try again</button></section>;
}
