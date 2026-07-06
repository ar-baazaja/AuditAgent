import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "AuditAgent",
  description: "Multi-agent AI compliance monitoring & audit automation (SOC 2 + HIPAA).",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
