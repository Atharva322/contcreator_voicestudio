import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Creator Voice Studio",
  description: "Learn a creator's writing style and draft platform-aware social content.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
