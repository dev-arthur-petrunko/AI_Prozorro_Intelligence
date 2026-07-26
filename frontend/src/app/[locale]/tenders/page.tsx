"use client";

import { useTranslations } from "next-intl";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowDown, ArrowUp, Search } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, TenderListResponse } from "@/services/api";
import { RiskBadge } from "@/components/risk-badge";
import { StatusBadge } from "@/components/status-badge";
import { Link } from "@/i18n/navigation";

function formatAmount(amount: number | null): string {
  if (!amount) return "—";
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(1)}K`;
  return amount.toFixed(0);
}

type SortField = "created_at" | "amount" | "risk_score" | "published_date";

function TendersContent() {
  const t = useTranslations("tenders");
  const tr = useTranslations("risk");
  const searchParams = useSearchParams();

  const [data, setData] = useState<TenderListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  // Ініціалізація фільтрів з URL (напр. /tenders?risk_min=61&sort_by=risk_score&sort_order=desc)
  const [riskMin, setRiskMin] = useState<string>(searchParams.get("risk_min") ?? "");
  const [region, setRegion] = useState<string>(searchParams.get("region") ?? "");
  const [sortBy, setSortBy] = useState<SortField>(
    (searchParams.get("sort_by") as SortField) || "created_at"
  );
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">(
    searchParams.get("sort_order") === "asc" ? "asc" : "desc"
  );

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string | number> = {
      page,
      per_page: 20,
      sort_by: sortBy,
      sort_order: sortOrder,
    };
    if (search) params.search = search;
    if (riskMin) params.risk_min = riskMin;
    if (region) params.region = region;

    api.getTenders(params)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [page, search, riskMin, region, sortBy, sortOrder]);

  const toggleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "desc" ? "asc" : "desc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
    setPage(1);
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortBy !== field) return null;
    return sortOrder === "desc" ? (
      <ArrowDown className="ml-1 inline h-3 w-3" />
    ) : (
      <ArrowUp className="ml-1 inline h-3 w-3" />
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        {data && (
          <span className="text-sm text-muted-foreground">
            {data.total.toLocaleString("uk-UA")}
          </span>
        )}
      </div>

      {/* Search + Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative max-w-md flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={t("search")}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-9"
          />
        </div>
        <select
          value={riskMin}
          onChange={(e) => { setRiskMin(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-border bg-background px-3 text-sm"
        >
          <option value="">{t("riskScore")}: {t("filters")}</option>
          <option value="31">{tr("medium")} (31+)</option>
          <option value="61">{tr("high")} (61+)</option>
          <option value="81">{tr("critical")} (81+)</option>
        </select>
        <Input
          placeholder={t("region")}
          value={region}
          onChange={(e) => { setRegion(e.target.value); setPage(1); }}
          className="h-9 w-44"
        />
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t("title")}</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t("region")}</th>
                  <th
                    className="cursor-pointer select-none px-4 py-3 text-right font-medium text-muted-foreground hover:text-foreground"
                    onClick={() => toggleSort("amount")}
                  >
                    {t("amount")}<SortIcon field="amount" />
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-muted-foreground">{t("participants")}</th>
                  <th
                    className="cursor-pointer select-none px-4 py-3 text-center font-medium text-muted-foreground hover:text-foreground"
                    onClick={() => toggleSort("risk_score")}
                  >
                    {t("riskScore")}<SortIcon field="risk_score" />
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-muted-foreground">{t("status")}</th>
                  <th
                    className="cursor-pointer select-none px-4 py-3 text-right font-medium text-muted-foreground hover:text-foreground"
                    onClick={() => toggleSort("published_date")}
                  >
                    {t("date")}<SortIcon field="published_date" />
                  </th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((tender) => (
                  <tr key={tender.id} className="border-b border-border hover:bg-accent/50 transition-colors">
                    <td className="px-4 py-3">
                      <Link href={`/tenders/${tender.id}`} className="hover:text-primary">
                        <p className="max-w-xs truncate font-medium">{tender.title}</p>
                        <p className="text-xs text-muted-foreground">{tender.prozorro_id}</p>
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{tender.region ?? "—"}</td>
                    <td className="px-4 py-3 text-right font-mono">
                      {formatAmount(tender.amount)} {tender.currency}
                    </td>
                    <td className="px-4 py-3 text-center">{tender.participants_count}</td>
                    <td className="px-4 py-3 text-center">
                      <RiskBadge score={tender.risk_score} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StatusBadge status={tender.status} />
                    </td>
                    <td className="px-4 py-3 text-right text-xs text-muted-foreground">
                      {tender.published_date ? new Date(tender.published_date).toLocaleDateString("uk-UA") : "—"}
                    </td>
                  </tr>
                ))}
                {!loading && data?.items.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                      {t("noResults")}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="rounded-md border border-border px-3 py-1.5 text-sm disabled:opacity-50"
          >
            &larr;
          </button>
          <span className="text-sm text-muted-foreground">
            {page} / {data.pages}
          </span>
          <button
            onClick={() => setPage(Math.min(data.pages, page + 1))}
            disabled={page === data.pages}
            className="rounded-md border border-border px-3 py-1.5 text-sm disabled:opacity-50"
          >
            &rarr;
          </button>
        </div>
      )}
    </div>
  );
}

export default function TendersPage() {
  return (
    <Suspense fallback={null}>
      <TendersContent />
    </Suspense>
  );
}
