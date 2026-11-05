import Link from "next/link";
export default function NotFound() {
  return <section className="rounded-[20px] bg-surface p-10 text-center"><h1 className="text-2xl font-extrabold">Page not found</h1><p className="mt-3 text-sm text-muted">This page is not part of the Reknyx workspace.</p><Link href="/" className="mt-6 inline-block rounded-full bg-lime px-5 py-3 text-xs font-bold text-[#141a14]">Back to dashboard</Link></section>;
}
