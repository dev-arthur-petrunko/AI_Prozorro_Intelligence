"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, DailyReportResponse } from "@/services/api";
import { RiskBadge } from "@/components/risk-badge";

function formatAmount(amount: number): string {
  if (amount >= 1_000_000_000) return `${(amount / 1_000_000_000).toFixed(1)}B`;
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(1)}K`;
  return amount.toFixed(0);
}

export default function ReportsPage() {
  const t = useTranslations("reports");
  const [report, setReport] = useState<DailyReportResponse | null>(null);

  useEffect(() => {
    api.getDailyReport().then(setReport).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        {report && (
          <span className="text-sm text-muted-foreground">
            {t("reportFor")}: {new Date(report.date).toLocaleDateString("uk-UA")}
          </span>
        )}
      </div>

      {report && (
        <>
          {/* Report KPIs */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground">{t("newTenders")}</p>
                <p className="text-2xl font-bold">{report.total_new_tenders}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground">{t("suspicious")}</p>
                <p className="text-2xl font-bold text-destructive">{report.suspicious_count}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground">{t("highestRisk")}</p>
                <p className="text-2xl font-bold">{report.highest_risk_score}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground">{t("largestTender")}</p>
                <p className="text-2xl font-bold">{formatAmount(report.largest_tender_amount)} UAH</p>
              </CardContent>
            </Card>
          </div>

          {/* Extra info */}
          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground">{t("topCategory")}</p>
                <p className="text-lg font-semibold">{report.top_category ?? "—"}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground">{t("topRegion")}</p>
                <p className="text-lg font-semibold">{report.top_region ?? "—"}</p>
              </CardContent>
            </Card>
          </div>

          {/* Suspicious tenders from report */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">{t("suspicious")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {report.suspicious_tenders.map((tender) => (
                  <div key={tender.id} className="flex items-center justify-between rounded-md border border-border p-3">
                    <div className="flex-1 min-w-0">
                      <p className="truncate text-sm font-medium" title={tender.title}>{tender.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {tender.amount ? `${formatAmount(tender.amount)} ${tender.currency}` : "—"}
                        {tender.region && ` · ${tender.region}`}
                      </p>
                    </div>
                    <RiskBadge score={tender.risk_score} />
                  </div>
                ))}
                {report.suspicious_tenders.length === 0 && (
                  <p className="text-sm text-muted-foreground">{t("noSuspicious")}</p>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
