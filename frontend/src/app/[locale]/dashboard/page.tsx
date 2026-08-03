"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import {
  FileText,
  AlertTriangle,
  Building2,
  Users,
  TrendingUp,
  ExternalLink,
  Clock,
  PiggyBank,
  UserX,
  CalendarClock,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
} from "recharts";
import { api, DashboardResponse, TenderResponse } from "@/services/api";
import { ProcurementChart } from "@/components/charts/procurement-chart";
import { RiskBadge } from "@/components/risk-badge";
import { StatusBadge } from "@/components/status-badge";
import { Link } from "@/i18n/navigation";

function formatAmount(amount: number | null): string {
  if (!amount) return "—";
  if (amount >= 1_000_000_000) return `${(amount / 1_000_000_000).toFixed(1)}B`;
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(1)}K`;
  return amount.toFixed(0);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("uk-UA");
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return `${d.toLocaleDateString("uk-UA")} ${d.toLocaleTimeString("uk-UA", { hour: "2-digit", minute: "2-digit" })}`;
}

/** Повних днів до дедлайну (0 = сьогодні) */
function daysUntil(dateStr: string | null): number {
  if (!dateStr) return 0;
  const diff = new Date(dateStr).getTime() - Date.now();
  return Math.max(0, Math.floor(diff / 86_400_000));
}

// Кольори зон шкали Індексу ризику: низький/середній/високий/критичний
const RISK_BUCKET_COLORS = ["#22c55e", "#f59e0b", "#f97316", "#ef4444"];

/** Назва тендера з посиланням на картку + клікабельний Prozorro ID */
function TenderTitleCell({
  tender,
  maxWidth,
  prozorroTitle,
}: {
  tender: TenderResponse;
  maxWidth: string;
  prozorroTitle: string;
}) {
  return (
    <div>
      <Link href={`/tenders/${tender.id}`} className="hover:text-primary">
        <p className={`${maxWidth} truncate font-medium`} title={tender.title}>
          {tender.title}
        </p>
      </Link>
      <a
        href={`https://prozorro.gov.ua/tender/${tender.prozorro_id}`}
        target="_blank"
        rel="noopener noreferrer"
        title={prozorroTitle}
        className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-primary hover:underline"
      >
        {tender.prozorro_id}
        <ExternalLink className="h-3 w-3" />
      </a>
    </div>
  );
}

function SuspiciousTable({
  title,
  subtitle,
  tenders,
  emptyText,
  viewAllText,
  viewAllHref,
  prozorroTitle,
  tt,
}: {
  title: string;
  subtitle?: string;
  tenders: TenderResponse[] | undefined;
  emptyText: string;
  viewAllText: string;
  viewAllHref: string;
  prozorroTitle: string;
  tt: ReturnType<typeof useTranslations>;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">
          {title}
          {subtitle && (
            <span className="ml-2 text-xs font-normal text-muted-foreground">({subtitle})</span>
          )}
        </CardTitle>
        <Link href={viewAllHref} className="text-xs text-primary hover:underline">
          {viewAllText} →
        </Link>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">{tt("tender")}</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">{tt("region")}</th>
                <th className="px-4 py-2 text-right font-medium text-muted-foreground">{tt("amount")}</th>
                <th className="px-4 py-2 text-center font-medium text-muted-foreground">{tt("participants")}</th>
                <th className="px-4 py-2 text-center font-medium text-muted-foreground">{tt("status")}</th>
                <th className="px-4 py-2 text-right font-medium text-muted-foreground">{tt("date")}</th>
                <th className="px-4 py-2 text-center font-medium text-muted-foreground">{tt("riskScore")}</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">{tt("aiAnalysis")}</th>
              </tr>
            </thead>
            <tbody>
              {tenders?.map((tender) => (
                <tr key={tender.id} className="border-b border-border hover:bg-accent/30 transition-colors">
                  <td className="px-4 py-3">
                    <TenderTitleCell tender={tender} maxWidth="max-w-[300px]" prozorroTitle={prozorroTitle} />
                  </td>
                  <td className="px-4 py-3 text-muted-foreground text-xs">{tender.region ?? "—"}</td>
                  <td className="px-4 py-3 text-right font-mono text-xs">
                    {formatAmount(tender.amount)} {tender.currency}
                  </td>
                  <td className="px-4 py-3 text-center">{tender.participants_count}</td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge status={tender.status} />
                  </td>
                  <td className="px-4 py-3 text-right text-xs text-muted-foreground whitespace-nowrap">
                    {formatDate(tender.published_date)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <RiskBadge score={tender.risk_score} />
                  </td>
                  <td className="px-4 py-3">
                    {tender.ai_analysis ? (
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger className="block max-w-[250px] cursor-help truncate text-left text-xs text-muted-foreground">
                            {tender.ai_analysis}
                          </TooltipTrigger>
                          {/* Широка панель з прокруткою; висота обмежена доступним
                              місцем на екрані (--available-height від позиціонера),
                              тому коментар ніколи не обрізається за межами вікна */}
                          <TooltipContent
                            side="left"
                            className="max-h-[var(--available-height)] w-[min(42rem,90vw)] max-w-none overflow-y-auto whitespace-pre-line text-left text-xs leading-relaxed"
                          >
                            {tender.ai_analysis}
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    ) : (
                      <span className="text-xs text-muted-foreground/50">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {(!tenders || tenders.length === 0) && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-muted-foreground">
                    {emptyText}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

const PERIOD_OPTIONS = [7, 30, 90, 180] as const;

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const tt = useTranslations("tenders");
  const [data, setData] = useState<DashboardResponse | null>(null);
  // Період: undefined = весь час
  const [days, setDays] = useState<number | undefined>(undefined);
  // Метрика графіка тримаємо тут, щоб вибір не скидався при оновленні даних
  const [chartMetric, setChartMetric] = useState<"count" | "amount">("count");

  useEffect(() => {
    const load = () =>
      api
        .getDashboard(days)
        .then(setData)
        .catch(console.error);
    load();
    // Автооновлення кожні 15 хв: синхронізація з Prozorro йде кожні 10-30 хв,
    // тому мітка "Дані оновлено" та KPI підтягуються без перезавантаження.
    // Було 5 хв - у 2-3 рази частіше за реальну зміну даних, зайве
    // навантаження на мережевий трафік БД (Neon egress).
    const timer = setInterval(load, 15 * 60 * 1000);
    return () => clearInterval(timer);
  }, [days]);

  const kpi = data?.kpi;
  const suspiciousPct =
    kpi && kpi.total_tenders > 0
      ? ((kpi.suspicious_tenders / kpi.total_tenders) * 100).toFixed(1)
      : null;
  // Поріг суми для блоку "Топ за індексом ризику" - мікрозакупівлі до 10 тис.
  // грн відсіюються на бекенді, підпис показуємо коли список не порожній
  const suspiciousHasBigAmounts = (data?.suspicious_tenders?.[0]?.amount ?? 0) >= 10_000;

  return (
    <div className="space-y-6">
      {/* Title + period filter + data freshness */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">{t("title")}</h1>
          <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          <select
            value={days ?? ""}
            onChange={(e) => setDays(e.target.value ? Number(e.target.value) : undefined)}
            className="h-9 rounded-md border border-border bg-background px-3 text-sm"
            aria-label={t("period")}
          >
            <option value="">{t("period")}: {t("periodAll")}</option>
            {PERIOD_OPTIONS.map((d) => (
              <option key={d} value={d}>
                {t("period")}: {t(`period${d}`)}
              </option>
            ))}
          </select>
          {data?.last_updated && (
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              {t("dataUpdated")}: {formatDateTime(data.last_updated)}
            </span>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-primary/10 p-2">
                <FileText className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{t("totalTenders")}</p>
                <p className="text-2xl font-bold">{kpi?.total_tenders?.toLocaleString() ?? "—"}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-destructive/10 p-2">
                <AlertTriangle className="h-4 w-4 text-destructive" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{t("suspiciousTenders")}</p>
                <p className="text-2xl font-bold text-destructive">
                  {kpi?.suspicious_tenders ?? "—"}
                  {suspiciousPct !== null && (
                    <span className="ml-1 text-sm font-medium text-muted-foreground">
                      ({suspiciousPct}%)
                    </span>
                  )}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-blue-500/10 p-2">
                <Building2 className="h-4 w-4 text-blue-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{t("companies")}</p>
                <p className="text-2xl font-bold">{kpi?.total_companies?.toLocaleString() ?? "—"}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-green-500/10 p-2">
                <Users className="h-4 w-4 text-green-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{t("buyers")}</p>
                <p className="text-2xl font-bold">{kpi?.total_buyers?.toLocaleString() ?? "—"}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-amber-500/10 p-2">
                <TrendingUp className="h-4 w-4 text-amber-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{t("todayVolume")}</p>
                <p className="text-2xl font-bold">
                  {kpi ? formatAmount(kpi.today_volume) : "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Економія на торгах: очікувана мінус фінальна ціна завершених торгів */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-emerald-500/10 p-2">
                <PiggyBank className="h-4 w-4 text-emerald-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground" title={t("savingsNote")}>{t("savings")}</p>
                <p className="text-2xl font-bold text-emerald-500">
                  {/* Захист від старого API без цього поля (до деплою бекенда) */}
                  {kpi?.savings_total != null ? formatAmount(kpi.savings_total) : "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Частка конкурентних тендерів з одним учасником */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-orange-500/10 p-2">
                <UserX className="h-4 w-4 text-orange-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground" title={t("singleParticipantNote")}>{t("singleParticipant")}</p>
                <p className="text-2xl font-bold">
                  {kpi?.single_participant_pct != null ? `${kpi.single_participant_pct}%` : "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("chartTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          <ProcurementChart
            data={data?.chart_data ?? []}
            incompleteDayNote={t("incompleteDay")}
            competitiveLabel={t("chartCompetitive")}
            reportingLabel={t("chartReporting")}
            highRiskLabel={t("chartHighRisk")}
            metricCountLabel={t("chartMetricCount")}
            metricAmountLabel={t("chartMetricAmount")}
            metric={chartMetric}
            onMetricChange={setChartMetric}
          />
          {/* Покриття даних: за дні до початку збору в базі лише часткові дані */}
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground/70">
            {t("chartCoverageNote")}
          </p>
        </CardContent>
      </Card>

      {/* Розподіл Індексу ризику + тендери, що скоро закриваються */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* flex-колонка: гістограма розтягується на всю висоту картки,
            щоб не було порожнечі поруч із високою таблицею дедлайнів */}
        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle className="text-base">
              {t("riskDistribution")}
              <span className="ml-2 text-xs font-normal text-muted-foreground">({t("riskDistributionNote")})</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-1 flex-col">
            <div className="min-h-56 flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.risk_distribution ?? []} margin={{ top: 18 }}>
                  <XAxis dataKey="label" tick={{ fill: "#8b949e", fontSize: 11 }} stroke="#8b949e" />
                  {/* sqrt-шкала: без неї кошики з десятками тендерів невидимі
                      поряд із тисячами в зоні 0-30 */}
                  <YAxis scale="sqrt" tick={{ fill: "#8b949e", fontSize: 11 }} stroke="#8b949e" allowDecimals={false} />
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor: "var(--card)",
                      color: "var(--card-foreground)",
                      border: "1px solid var(--border)",
                      borderRadius: "6px",
                      fontSize: "12px",
                    }}
                    itemStyle={{ color: "var(--card-foreground)" }}
                    labelStyle={{ color: "var(--card-foreground)" }}
                    cursor={{ fill: "#8b949e", fillOpacity: 0.08 }}
                    formatter={(v) => [String(v ?? 0), t("riskTendersCount")]}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    <LabelList dataKey="count" position="top" style={{ fontSize: 10, fill: "#8b949e" }} />
                    {(data?.risk_distribution ?? []).map((_, i) => (
                      <Cell key={i} fill={RISK_BUCKET_COLORS[i % RISK_BUCKET_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 flex flex-wrap justify-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
              <span><span className="text-emerald-500">●</span> {t("riskLow")}</span>
              <span><span className="text-amber-500">●</span> {t("riskMedium")}</span>
              <span><span className="text-orange-500">●</span> {t("riskHigh")}</span>
              <span><span className="text-red-500">●</span> {t("riskCritical")}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">
              <span className="inline-flex items-center gap-2">
                <CalendarClock className="h-4 w-4 text-primary" />
                {t("closingSoon")}
              </span>
              <span className="ml-2 text-xs font-normal text-muted-foreground">({t("closingSoonNote")})</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/30">
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">{tt("tender")}</th>
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">{tt("region")}</th>
                    <th className="px-4 py-2 text-right font-medium text-muted-foreground">{tt("amount")}</th>
                    <th className="px-4 py-2 text-center font-medium text-muted-foreground">{tt("riskScore")}</th>
                    <th className="px-4 py-2 text-right font-medium text-muted-foreground">{t("deadline")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.closing_soon?.map((tender) => {
                    const left = daysUntil(tender.end_date);
                    return (
                      <tr key={tender.id} className="border-b border-border hover:bg-accent/30 transition-colors">
                        <td className="px-4 py-3">
                          <TenderTitleCell tender={tender} maxWidth="max-w-[320px]" prozorroTitle={t("openInProzorro")} />
                        </td>
                        <td className="px-4 py-3 text-muted-foreground text-xs">{tender.region ?? "—"}</td>
                        <td className="px-4 py-3 text-right font-mono text-xs">
                          {formatAmount(tender.amount)} {tender.currency}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <RiskBadge score={tender.risk_score} />
                        </td>
                        <td className="px-4 py-3 text-right text-xs whitespace-nowrap">
                          <span className="text-muted-foreground">{formatDate(tender.end_date)}</span>
                          <span
                            className={`ml-2 rounded-full px-2 py-0.5 text-[11px] font-medium ${
                              left <= 1
                                ? "bg-destructive/10 text-destructive"
                                : left <= 3
                                ? "bg-amber-500/10 text-amber-500"
                                : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {left === 0 ? t("closesToday") : t("daysLeft", { days: left })}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                  {(!data?.closing_soon || data.closing_soon.length === 0) && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                        {t("noClosingSoon")}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Suspicious Tenders - completed (від 50 тис. грн, щоб мікрозакупівлі не забивали топ) */}
      <SuspiciousTable
        title={t("topSuspicious")}
        subtitle={suspiciousHasBigAmounts ? t("suspiciousMinAmountNote") : undefined}
        tenders={data?.suspicious_tenders}
        emptyText={t("noSuspicious")}
        viewAllText={t("viewAll")}
        viewAllHref="/tenders?risk_min=56&sort_by=risk_score&sort_order=desc"
        prozorroTitle={t("openInProzorro")}
        tt={tt}
      />

      {/* Active (open) suspicious tenders - нижчий поріг ризику (50+) */}
      <SuspiciousTable
        title={t("activeSuspicious")}
        tenders={data?.active_suspicious_tenders}
        emptyText={t("noSuspicious")}
        viewAllText={t("viewAll")}
        viewAllHref="/tenders?risk_min=50&sort_by=risk_score&sort_order=desc"
        prozorroTitle={t("openInProzorro")}
        tt={tt}
      />

      {/* Recent Procurements */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">{t("recentProcurements")}</CardTitle>
          <Link href="/tenders" className="text-xs text-primary hover:underline">
            {t("viewAll") ?? "View all"} →
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  <th className="px-4 py-2 text-left font-medium text-muted-foreground">{tt("tender")}</th>
                  <th className="px-4 py-2 text-left font-medium text-muted-foreground">{tt("region")}</th>
                  <th className="px-4 py-2 text-right font-medium text-muted-foreground">{tt("amount")}</th>
                  <th className="px-4 py-2 text-center font-medium text-muted-foreground">{tt("status")}</th>
                  <th className="px-4 py-2 text-right font-medium text-muted-foreground">{tt("date")}</th>
                  <th className="px-4 py-2 text-center font-medium text-muted-foreground">{tt("riskScore")}</th>
                </tr>
              </thead>
              <tbody>
                {data?.recent_tenders?.map((tender) => (
                  <tr key={tender.id} className="border-b border-border hover:bg-accent/30 transition-colors">
                    <td className="px-4 py-3">
                      <TenderTitleCell tender={tender} maxWidth="max-w-[350px]" prozorroTitle={t("openInProzorro")} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground text-xs">{tender.region ?? "—"}</td>
                    <td className="px-4 py-3 text-right font-mono text-xs">
                      {formatAmount(tender.amount)} {tender.currency}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StatusBadge status={tender.status} />
                    </td>
                    <td className="px-4 py-3 text-right text-xs text-muted-foreground whitespace-nowrap">
                      {formatDate(tender.published_date)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <RiskBadge score={tender.risk_score} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
