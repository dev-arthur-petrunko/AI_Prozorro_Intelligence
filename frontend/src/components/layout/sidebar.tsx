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
  Scale,
  Heart,
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
  { key: "legal", href: "/legal", icon: Scale },
  { key: "support", href: "/support", icon: Heart },
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
          <img src="/emblem.png" alt="AI ProZorro" className="h-9 w-9 rounded-full" />
          <span className="text-sm font-semibold text-foreground">
            AI ProZorro
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

        {/* Компактний юридичний дисклеймер + посилання на повну сторінку */}
        <div className="mx-3 mb-3 rounded-md border border-border bg-muted/30 p-3">
          <div className="flex items-start gap-2">
            <Scale className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <div className="text-[11px] leading-relaxed text-muted-foreground">
              <p>{tc("aiDisclaimer")}</p>
              <Link href="/legal" className="mt-1 inline-block text-primary hover:underline">
                {tc("legalMore")} →
              </Link>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-border px-6 py-4">
          <p className="text-xs text-muted-foreground">
            v1.6.0 &middot; {tc("openSource")}
          </p>
        </div>
      </div>
    </aside>
  );
}
