import type { Metadata } from "next";
import { PreviewProvider } from "@/lib/preview-context";
import { AppShell } from "@/components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Reknyx · Assessment workspace", template: "%s · Reknyx" },
  description: "An analyst-controlled security assessment workspace. Synthetic frontend preview; no scanners or models are connected.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en" suppressHydrationWarning><body><PreviewProvider><AppShell>{children}</AppShell></PreviewProvider></body></html>;
}
