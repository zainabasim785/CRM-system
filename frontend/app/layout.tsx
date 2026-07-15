import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { VoiceChatWidget } from "../components/shared/VoiceChatWidget";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CRM System",
  description: "Customer Relationship Management System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
        <VoiceChatWidget />
      </body>
    </html>
  );
}