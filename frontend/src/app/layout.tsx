import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Transaction Risk Monitor",
  description: "Explainable card-transaction risk scoring with grounded question answering.",
};

// Browser chrome matches the navy header (DESIGN.md navy-900); light theme only.
export const viewport: Viewport = {
  themeColor: "#0a1f3d",
  colorScheme: "light",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans text-body">{children}</body>
    </html>
  );
}
