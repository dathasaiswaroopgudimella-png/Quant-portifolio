"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/editor", label: "Editor Sandbox" },
  { href: "/validations", label: "Validations" },
  { href: "/market", label: "Market Monitor" },
];

export function TopNav() {
  const path = usePathname() || "/";

  // Landing page has its own sticky nav — don't render a duplicate
  if (path === "/") return null;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[#2e2c33] bg-[#0e0e10]/95 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#c0c1ff] to-[#8083ff] flex items-center justify-center font-bold text-[#1000a9] text-base shadow-lg shadow-[#c0c1ff]/20 group-hover:scale-105 transition-transform">
            F
          </div>
          <div>
            <p className="font-bold text-sm tracking-tight text-[#e5e1e4] leading-none">FRAGMENT</p>
            <p className="text-[9px] font-mono uppercase tracking-widest text-[#908fa0] leading-none mt-0.5">
              Adversarial Model Risk Platform
            </p>
          </div>
        </Link>

        {/* Global Page Navigation */}
        <div className="flex items-center gap-1.5 font-mono">
          {NAV_LINKS.map(({ href, label }) => {
            const isActive = href === "/" ? path === "/" : path.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? "bg-[#161519] text-[#c0c1ff] border border-[#c0c1ff]/30 shadow-sm"
                    : "text-[#908fa0] hover:text-[#e5e1e4] hover:bg-[#161519]"
                }`}
              >
                {label}
              </Link>
            );
          })}
        </div>

        {/* Call to Action */}
        <div className="flex items-center gap-3 font-mono">
          <Link
            href="/editor"
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-bold bg-[#c0c1ff] text-[#1000a9] hover:bg-[#8083ff] transition-all shadow-md shadow-[#c0c1ff]/20"
          >
            ▶ Launch Sandbox
          </Link>
        </div>
      </div>
    </nav>
  );
}

