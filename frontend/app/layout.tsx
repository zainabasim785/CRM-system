import type { Metadata } from "next";
import { Outfit, Source_Sans_3 } from "next/font/google";
import { AuthProvider } from "@/lib/auth/auth-context";
import { ThemeProvider } from "@/lib/theme/theme-provider";
import { ToastProvider } from "@/components/ui/toast";
import { SiteHeader } from "@/components/layout/site-header";
import "./globals.css";

const display = Outfit({
  subsets: ["latin"],
  variable: "--font-display",
});

const sans = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Front Desk — AI Reception",
  description:
    "Premium AI reception client for FAQ answers, availability, and appointment booking.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${display.variable} ${sans.variable} font-sans`}>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('crm_theme');var d=window.matchMedia('(prefers-color-scheme: dark)').matches;var m=t==='dark'||(t!=='light'&&d);if(m)document.documentElement.classList.add('dark');document.documentElement.style.colorScheme=m?'dark':'light';}catch(e){}})();`,
          }}
        />
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground"
        >
          Skip to content
        </a>
        <ThemeProvider>
          <ToastProvider>
            <AuthProvider>
              <SiteHeader />
              <main id="main-content" className="container py-8 sm:py-10">
                {children}
              </main>
            </AuthProvider>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
