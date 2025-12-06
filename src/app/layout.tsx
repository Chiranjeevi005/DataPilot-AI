import { Inter } from "next/font/google";
import "./globals.css";
import { clsx } from 'clsx';

const inter = Inter({ subsets: ["latin"], variable: '--font-inter' });

export const metadata = {
  title: "DataPilot AI - AI Data Intelligence & Automation Agent for SMEs",
  description: "Turn messy files into instant insights.",
  icons: {
    icon: '/icon.svg',
  },
};

import { ToastProvider } from '@/components/ui/ToastContext';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={clsx(inter.className, "antialiased bg-background text-slate-800")}
        suppressHydrationWarning
      >
        <ToastProvider>
          {children}
        </ToastProvider>
      </body>
    </html>
  );
}
