"use client";

import { useTranslations } from "next-intl";
import { Heart, Target, Cpu, Copy, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const JAR_URL = "https://send.monobank.ua/jar/AZ9XsVXgGU";
const CARD_NUMBER = "4874 1000 3119 6366";
const DASHBOARD_URL = "https://ai-prozorro-intelligence.vercel.app/uk/dashboard";

// 9 рядків кошторису; текст береться з перекладів за індексом
const BUDGET_ROWS = [1, 2, 3, 4, 5, 6, 7, 8, 9] as const;

export default function SupportPage() {
  const t = useTranslations("nav");
  const s = useTranslations("support");

  const copyCard = () => {
    navigator.clipboard?.writeText(CARD_NUMBER.replace(/\s/g, ""));
  };

  const bold = (chunks: React.ReactNode) => (
    <span className="font-medium text-foreground">{chunks}</span>
  );

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="flex items-center gap-2 text-2xl font-bold">
        <Heart className="h-6 w-6 text-red-500" />
        {t("support")}
      </h1>

      {/* Місія автора */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Target className="h-4 w-4 text-primary" />
            {s("missionTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm leading-relaxed text-muted-foreground">
          <p>{s.rich("missionP1", { b: bold })}</p>
          <p>{s("missionP2")}</p>
        </CardContent>
      </Card>

      {/* Поточний стан */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Cpu className="h-4 w-4 text-primary" />
            {s("stateTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm leading-relaxed text-muted-foreground">
          <p>
            {s.rich("stateP1", {
              link: (chunks) => (
                <a
                  href={DASHBOARD_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-primary hover:underline"
                >
                  {chunks}
                  <ExternalLink className="h-3 w-3" />
                </a>
              ),
            })}
          </p>
        </CardContent>
      </Card>

      {/* Приклад переплати */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{s("whyTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm leading-relaxed text-muted-foreground">
          <p>{s("whyIntro")}</p>
          <ul className="space-y-1 rounded-md border border-border bg-muted/30 p-4">
            <li>{s.rich("whyPaid", { b: bold })}</li>
            <li>{s.rich("whyMarket", { b: bold })}</li>
            <li className="text-foreground">
              {s.rich("whyOverpay", {
                red: (chunks) => <span className="font-semibold text-red-500">{chunks}</span>,
              })}
            </li>
          </ul>
          <p>{s("whyP2")}</p>
          <p>{s.rich("whyP3", { b: bold })}</p>
          <p>{s("whyP4")}</p>
        </CardContent>
      </Card>

      {/* Кошторис */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{s("budgetTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm leading-relaxed text-muted-foreground">{s("budgetIntro")}</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="px-3 py-2 font-medium text-muted-foreground">{s("colComponent")}</th>
                  <th className="px-3 py-2 font-medium text-muted-foreground">{s("colPurpose")}</th>
                  <th className="px-3 py-2 text-right font-medium text-muted-foreground">{s("colCost")}</th>
                </tr>
              </thead>
              <tbody>
                {BUDGET_ROWS.map((i) => (
                  <tr key={i} className="border-b border-border/50">
                    <td className="px-3 py-2 font-medium text-foreground">{s(`b${i}c`)}</td>
                    <td className="px-3 py-2 text-muted-foreground">{s(`b${i}p`)}</td>
                    <td className="px-3 py-2 text-right font-mono text-foreground">{s(`b${i}v`)}</td>
                  </tr>
                ))}
                <tr className="bg-muted/30">
                  <td className="px-3 py-2 font-semibold text-foreground">{s("total")}</td>
                  <td className="px-3 py-2 text-muted-foreground">{s("totalPurpose")}</td>
                  <td className="px-3 py-2 text-right font-mono font-semibold text-foreground">{s("totalCost")}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Реквізити */}
      <Card className="border-primary/40">
        <CardHeader>
          <CardTitle className="text-base">{s("goalTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <a
            href={JAR_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 font-medium text-primary-foreground hover:opacity-90"
          >
            <Heart className="h-4 w-4" />
            {s("supportBtn")}
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
          <div className="space-y-1">
            <p className="text-muted-foreground">{s("jarLabel")}</p>
            <a
              href={JAR_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="break-all text-primary hover:underline"
            >
              {JAR_URL}
            </a>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground">{s("cardLabel")}</p>
            <div className="flex items-center gap-2">
              <code className="rounded bg-muted px-2 py-1 font-mono text-foreground">{CARD_NUMBER}</code>
              <button
                onClick={copyCard}
                className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs text-muted-foreground hover:bg-accent"
              >
                <Copy className="h-3 w-3" />
                {s("copy")}
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
