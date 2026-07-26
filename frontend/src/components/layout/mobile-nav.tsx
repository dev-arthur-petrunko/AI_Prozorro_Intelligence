"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { usePathname, Link } from "@/i18n/navigation";
import {
  LayoutDashboard,
  FileText,
  Building2,
  Users,
  BarChart3,
  FileBarChart,
  Settings,
  Menu,
} from "lucide-react";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet";
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

export function MobileNav() {
  const t = useTranslations("nav");
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <div className="lg:hidden">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger className="inline-flex items-center justify-center rounded-md p-2 hover:bg-accent">
          <Menu className="h-5 w-5" />
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <div className="flex h-16 items-center gap-3 border-b border-border px-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/emblem.png" alt="AI Prozorro" className="h-9 w-9 rounded-full" />
            <SheetTitle className="text-sm font-semibold text-foreground">
              AI Prozorro
            </SheetTitle>
          </div>
          <nav className="space-y-1 px-3 py-4">
            {navItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.key}
                  href={item.href}
                  onClick={() => setOpen(false)}
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
        </SheetContent>
      </Sheet>
    </div>
  );
}
