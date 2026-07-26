"use client";

import { useTranslations, useLocale } from "next-intl";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeft, Brain, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, TenderResponse, BuyerResponse, CompanyResponse } from "@/services/api";
import { RiskBadge } from "@/components/risk-badge";
import { StatusBadge } from "@/components/status-badge";
import { Link } from "@/i18n/navigation";

interface TenderDetail extends TenderResponse {
  buyer?: BuyerResponse | null;
  winner?: CompanyResponse | null;
}

interface RiskFactor {
  key: string;
  weight: number;
  description_uk: string;
  description_en: string;
}

function formatAmount(amount: number | null): string {
  if (!amount) return "—";
  return amount.toLocaleString("uk-UA");
}

export default function TenderDetailPage() {
  const t = useTranslations("tenders");
  const tc = useTranslations("common");
  const locale = useLocale();
  const params = useParams();
  const [tender, setTender] = useState<TenderDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const id = Number(params.id);
    if (!id) return;
    api.getTender(id)
      .then((data) => setTender(data as TenderDetail))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return <p className="text-sm text-muted-foreground">{tc("loading")}</p>;
  }

  if (!tender) {
    return <p className="text-sm text-muted-foreground">{t("noResults")}</p>;
  }

  let riskFactors: RiskFactor[] = [];
  try {
    riskFactors = tender.risk_factors ? JSON.parse(tender.risk_factors) : [];
  } catch {
    riskFactors = [];
  }

  return (
    <div className="space-y-6">
      {/* Back + title */}
      <div className="space-y-2">
        <Link href="/tenders" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> {tc("back")}
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold leading-snug">{tender.title}</h1>
            <a
              href={`https://prozorro.gov.ua/tender/${tender.prozorro_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
            >
              {tender.prozorro_id} <ExternalLink className="h-3 w-3" />
            </a>
          </div>
          <RiskBadge score={tender.risk_score} />
        </div>
      </div>

      {/* Key facts */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">{t("amount")}</p>
            <p className="text-lg font-bold font-mono">{formatAmount(tender.amount)} {tender.currency}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">{t("region")}</p>
            <p className="text-lg font-semibold">{tender.region ?? "—"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">{t("participants")}</p>
            <p className="text-lg font-bold">{tender.participants_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">{t("status")}</p>
            <div className="mt-1"><StatusBadge status={tender.status} /></div>
          </CardContent>
        </Card>
      </div>

      {/* AI Analysis - full text */}
      {tender.ai_analysis && (
        <Card className="border-primary/30">
          <CardHeader className="flex flex-row items-center gap-2">
            <Brain className="h-4 w-4 text-primary" />
            <CardTitle className="text-base">{t("aiAnalysis")}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/90">
              {tender.ai_analysis}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Risk factors */}
      {riskFactors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("riskFactors")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {riskFactors.map((f) => (
                <div key={f.key} className="flex items-center justify-between rounded-md border border-border p-3">
                  <span className="text-sm">
                    {locale === "en" ? f.description_en : f.description_uk}
                  </span>
                  <span className="font-mono text-sm font-semibold text-destructive">+{f.weight}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Buyer / Winner */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("buyer")}</CardTitle>
          </CardHeader>
          <CardContent>
            {tender.buyer ? (
              <div className="space-y-1 text-sm">
                <p className="font-medium">{tender.buyer.name}</p>
                {tender.buyer.edrpou && <p className="text-muted-foreground">ЄДРПОУ: {tender.buyer.edrpou}</p>}
                {tender.buyer.region && <p className="text-muted-foreground">{tender.buyer.region}</p>}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">{tc("noData")}</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("winner")}</CardTitle>
          </CardHeader>
          <CardContent>
            {tender.winner ? (
              <div className="space-y-1 text-sm">
                <p className="font-medium">{tender.winner.name}</p>
                {tender.winner.edrpou && <p className="text-muted-foreground">ЄДРПОУ: {tender.winner.edrpou}</p>}
                {tender.winner.region && <p className="text-muted-foreground">{tender.winner.region}</p>}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">{tc("noData")}</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Description */}
      {tender.description && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("category")}: {tender.cpv_code ?? "—"}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-line text-sm text-muted-foreground">{tender.description}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
