"use client";

import { useTranslations } from "next-intl";
import { usePathname } from "@/i18n/navigation";
import { Link } from "@/i18n/navigation";
import {
  LayoutDashboard,
  FileText,
  Building2,
  Users,
  BarChart3,
  FileBarChart,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { key: "dashboard", href: "/dashboard", icon: LayoutDashboard },
  { key: "tenders", href: "/tenders", icon: FileText },
  { key: "companies", href: "/companies", icon: Building2 },
  { key: "buyers", href: "/buyers", icon: Users },
  { key: "analytics", href: "/analytics", icon: BarChart3 },
  { key: "reports", href: "/reports", icon: FileBarChart },
  { key: "settings", href: "/settings", icon: Settings },
] as const;

export function Sidebar() {
  const t = useTranslations("nav");
  const tc = useTranslations("common");
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 border-r border-border bg-card lg:block">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center gap-3 border-b border-border px-4">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/emblem.png" alt="AI Prozorro" className="h-9 w-9 rounded-full" />
          <span className="text-sm font-semibold text-foreground">
            AI Prozorro
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => {
            const isActive = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.key}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {t(item.key)}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="border-t border-border px-6 py-4">
          <p className="text-xs text-muted-foreground">
            v1.0.0 &middot; {tc("openSource")}
          </p>
        </div>
      </div>
    </aside>
  );
}
