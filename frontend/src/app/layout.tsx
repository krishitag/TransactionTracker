import type { Metadata, Viewport } from "next";
import { Google_Sans } from "next/font/google";
import "./globals.css";

// Google Sans: the open successor to Product Sans (variable, 400-700). Self-hosted by next/font.
const googleSans = Google_Sans({
  variable: "--font-google-sans",
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
    <html lang="en" className={`${googleSans.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans text-body">{children}</body>
    </html>
  );
}
