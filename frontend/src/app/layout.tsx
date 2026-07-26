import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Prozorro Intelligence",
  description: "AI-платформа для аналізу державних закупівель України",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
