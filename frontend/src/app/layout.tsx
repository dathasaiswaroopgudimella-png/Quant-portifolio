import type { Metadata } from "next";
import "./globals.css";
import { TopNav } from "@/components/TopNav";

export const metadata: Metadata = {
  title: "FRAGMENT — Adversarial Model Risk Validation Platform",
  description:
    "FRAGMENT finds the smallest realistic market shift that breaks your Black-Scholes pricing model. QuantLib ground truth · SymPy symbolic extraction · SR 11-7 compliance.",
  keywords: [
    "quantitative finance",
    "model risk",
    "Black-Scholes",
    "adversarial testing",
    "QuantLib",
    "SR 11-7",
    "options pricing",
    "fragility scoring",
  ],
  openGraph: {
    title: "FRAGMENT — Adversarial Model Risk Validation",
    description:
      "The first platform that asks: what is the smallest market shift that breaks your pricing model? Deterministic. Reproducible. SR 11-7 compliant.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[#0e0e10] text-[#e5e1e4] min-h-screen">
        <TopNav />
        <main className="pt-14">{children}</main>
      </body>
    </html>
  );
}
