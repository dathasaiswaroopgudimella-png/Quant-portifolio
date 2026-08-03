"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldAlert, Code2, LayoutDashboard, LineChart, Activity, Cpu } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();

  const navLinks = [
    { href: "/", label: "Overview", icon: ShieldAlert },
    { href: "/editor", label: "Model Editor", icon: Code2 },
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/validations", label: "Validations", icon: Activity },
    { href: "/market", label: "Market Monitor", icon: LineChart },
  ];

  return (
    <header className="sticky top-0 z-50 bg-stitch-surface/90 backdrop-blur border-b border-stitch-outline-variant px-6 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-8">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-8 h-8 rounded bg-stitch-primary-container flex items-center justify-center font-mono font-bold text-stitch-on-primary-container text-lg shadow-sm group-hover:scale-105 transition-transform">
            F
          </div>
          <div>
            <span className="font-semibold text-lg tracking-tight text-stitch-on-surface flex items-center gap-2">
              FRAGMENT
              <span className="w-2 h-2 rounded-full bg-stitch-secondary animate-pulse" title="System Active"></span>
            </span>
            <p className="text-[10px] text-stitch-outline font-mono uppercase tracking-wider">
              Adversarial Model Risk Platform
            </p>
          </div>
        </Link>

        <nav className="hidden md:flex items-center space-x-1">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-stitch-surface-high text-stitch-primary border border-stitch-primary/30"
                    : "text-stitch-on-surface-variant hover:bg-stitch-surface-low hover:text-stitch-on-surface"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center space-x-4">
        <div className="hidden sm:flex items-center space-x-2 px-2.5 py-1 rounded bg-stitch-surface-low border border-stitch-outline-variant text-xs font-mono text-stitch-on-surface-variant">
          <Cpu className="w-3.5 h-3.5 text-stitch-secondary" />
          <span>QuantLib 1.43 Ground Truth</span>
        </div>

        <Link
          href="/editor"
          className="px-4 py-1.5 rounded text-xs font-semibold bg-stitch-primary text-stitch-on-primary hover:bg-stitch-primary-container transition-colors shadow"
        >
          Launch Model Sandbox
        </Link>
      </div>
    </header>
  );
}
