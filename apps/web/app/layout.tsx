import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "API Discovery | Workspace", description: "Evidence-backed exploration of authorized API targets" };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" data-type="software"><body>{children}</body></html>;
}
