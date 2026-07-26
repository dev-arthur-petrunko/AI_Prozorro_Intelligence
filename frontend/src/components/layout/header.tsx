"use client";

import { useTheme } from "next-themes";
import { useLocale, useTranslations } from "next-intl";
import { useRouter, usePathname } from "@/i18n/navigation";
import { Moon, Sun, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MobileNav } from "@/components/layout/mobile-nav";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function Header() {
  const { setTheme, theme } = useTheme();
  const locale = useLocale();
  const tc = useTranslations("common");
  const router = useRouter();
  const pathname = usePathname();

  const switchLocale = (newLocale: "uk" | "en") => {
    router.replace(pathname, { locale: newLocale });
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-card px-6">
      <div className="flex items-center gap-4">
        <MobileNav />
        <h1 className="text-lg font-semibold text-foreground lg:hidden">
          AI Prozorro
        </h1>
      </div>

      <div className="flex items-center gap-2">
        {/* Language Switcher */}
        <DropdownMenu>
          <DropdownMenuTrigger className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent">
            <Globe className="h-4 w-4" />
            <span className="text-xs uppercase">{locale}</span>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => switchLocale("uk")}>
              🇺🇦 Українська
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => switchLocale("en")}>
              🇬🇧 English
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">{tc("toggleTheme")}</span>
        </Button>
      </div>
    </header>
  );
}
