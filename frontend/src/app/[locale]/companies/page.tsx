"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, CompanyListResponse } from "@/services/api";

function formatAmount(amount: number): string {
  if (amount >= 1_000_000_000) return `${(amount / 1_000_000_000).toFixed(1)}B`;
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(1)}K`;
  return amount.toFixed(0);
}

// Знеособлені постачальники Prozorro: оборонні закупівлі приховують переможця
// під записом "Оборонний постачальник" з фіктивним ЄДРПОУ
const ANONYMIZED_EDRPOUS = ["88888888", "00000000"];

export default function CompaniesPage() {
  const t = useTranslations("companies");
  const [data, setData] = useState<CompanyListResponse | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const params: Record<string, string | number> = { page, per_page: 20 };
    if (search) params.search = search;
    api.getCompanies(params).then(setData).catch(console.error);
  }, [page, search]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("title")}</h1>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder={t("search")}
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="pl-9"
        />
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t("title")}</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t("region")}</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">{t("wins")}</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">{t("totalAmount")}</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">{t("avgAmount")}</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((company) => {
                const isAnonymized = !!company.edrpou && ANONYMIZED_EDRPOUS.includes(company.edrpou);
                return (
                <tr key={company.id} className="border-b border-border hover:bg-accent/50 transition-colors">
                  <td className="px-4 py-3">
                    {/* Сторінки деталей компанії поки немає - без посилання, щоб не було 404 */}
                    <p className="font-medium">
                      {company.name}
                      {isAnonymized && (
                        <span
                          className="ml-2 inline-flex cursor-help items-center rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[10px] font-normal text-amber-500"
                          title={t("anonymizedNote")}
                        >
                          {t("anonymized")}
                        </span>
                      )}
                    </p>
                    {company.edrpou && (
                      <p className="text-xs text-muted-foreground">EDRPOU: {company.edrpou}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{company.region ?? "—"}</td>
                  <td className="px-4 py-3 text-right font-mono">{company.wins_count}</td>
                  <td className="px-4 py-3 text-right font-mono">{formatAmount(company.total_amount)}</td>
                  <td className="px-4 py-3 text-right font-mono">{formatAmount(company.avg_amount)}</td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        </CardContent>
      </Card>

      {data && data.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}
            className="rounded-md border border-border px-3 py-1.5 text-sm disabled:opacity-50">&larr;</button>
          <span className="text-sm text-muted-foreground">{page} / {data.pages}</span>
          <button onClick={() => setPage(Math.min(data.pages, page + 1))} disabled={page === data.pages}
            className="rounded-md border border-border px-3 py-1.5 text-sm disabled:opacity-50">&rarr;</button>
        </div>
      )}
    </div>
  );
}
