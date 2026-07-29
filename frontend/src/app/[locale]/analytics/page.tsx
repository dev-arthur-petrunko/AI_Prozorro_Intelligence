"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, AnalyticsResponse } from "@/services/api";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, LabelList,
} from "recharts";

const COLORS = [
  "#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#a855f7",
  "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#14b8a6",
];

// Кольори напряму: CSS-змінні теми у форматі oklch, тому hsl(var(--...))
// давало невалідний (чорний) колір на графіках
const AXIS_TICK = { fontSize: 11, fill: "#8b949e" };
const AXIS_TICK_SM = { fontSize: 10, fill: "#8b949e" };
const GRID_PROPS = { strokeDasharray: "3 3", stroke: "#8b949e", strokeOpacity: 0.25 } as const;
const BAR_LABEL = { fontSize: 10, fill: "#8b949e" } as const;
const TOOLTIP_STYLE = {
  backgroundColor: "var(--card)",
  color: "var(--card-foreground)",
  border: "1px solid var(--border)",
  borderRadius: "6px",
  fontSize: "12px",
} as const;

function formatAmount(amount: number): string {
  if (amount >= 1_000_000_000) return `${(amount / 1_000_000_000).toFixed(1)}B`;
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(1)}K`;
  return amount.toFixed(0);
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return `${d.toLocaleDateString("uk-UA")} ${d.toLocaleTimeString("uk-UA", { hour: "2-digit", minute: "2-digit" })}`;
}

type Metric = "count" | "amount";
type AmountType = "announced" | "contracted";

const PERIOD_OPTIONS = [7, 30, 90, 180] as const;

/** Перемикач між двома варіантами (загальний, для метрики та типу суми) */
function SegmentToggle({
  value,
  left,
  right,
  onChange,
}: {
  value: string;
  left: { key: string; label: string };
  right: { key: string; label: string };
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex rounded-md border border-border text-xs">
      <button
        onClick={() => onChange(left.key)}
        className={`rounded-l-md px-3 py-1.5 transition-colors ${
          value === left.key ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
        }`}
      >
        {left.label}
      </button>
      <button
        onClick={() => onChange(right.key)}
        className={`rounded-r-md px-3 py-1.5 transition-colors ${
          value === right.key ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
        }`}
      >
        {right.label}
      </button>
    </div>
  );
}

/** Перемикач метрики графіків: кількість тендерів або сума в грн */
function MetricToggle({
  metric,
  onChange,
  countLabel,
  amountLabel,
}: {
  metric: Metric;
  onChange: (m: Metric) => void;
  countLabel: string;
  amountLabel: string;
}) {
  return (
    <SegmentToggle
      value={metric}
      left={{ key: "count", label: countLabel }}
      right={{ key: "amount", label: amountLabel }}
      onChange={(v) => onChange(v as Metric)}
    />
  );
}

export default function AnalyticsPage() {
  const t = useTranslations("analytics");
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  // Перемикач метрики графіків: кількість тендерів або сума в грн
  const [metric, setMetric] = useState<Metric>("count");
  // Тип суми для регіонів: оголошена (очікувана) чи законтрактована (final)
  const [amountType, setAmountType] = useState<AmountType>("announced");
  // Період: undefined = весь час
  const [days, setDays] = useState<number | undefined>(undefined);

  useEffect(() => {
    api.getAnalytics(days).then(setData).catch(console.error);
  }, [days]);

  const metricKey = metric === "count" ? "tenders_count" : "total_amount";
  const metricLabel = metric === "count" ? t("metricCount") : t("metricAmount");
  const formatMetric = (v: number) => (metric === "count" ? String(v) : formatAmount(v));
  const metricToggle = (
    <MetricToggle
      metric={metric}
      onChange={setMetric}
      countLabel={t("metricCount")}
      amountLabel={t("metricAmount")}
    />
  );

  // Регіони: у режимі суми можна показати оголошену або законтрактовану вартість
  const regionMetricKey =
    metric === "count"
      ? "tenders_count"
      : amountType === "contracted"
      ? "contracted_amount"
      : "total_amount";
  const amountTypeToggle = (
    <SegmentToggle
      value={amountType}
      left={{ key: "announced", label: t("amountAnnounced") }}
      right={{ key: "contracted", label: t("amountContracted") }}
      onChange={(v) => setAmountType(v as AmountType)}
    />
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h1 className="text-2xl font-bold">{t("title")}</h1>
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

      <Tabs defaultValue="regions">
        {/* На вузьких екранах вкладки скролляться горизонтально */}
        <div className="max-w-full overflow-x-auto">
          <TabsList>
            <TabsTrigger value="regions">{t("byRegion")}</TabsTrigger>
            <TabsTrigger value="categories">{t("byCategory")}</TabsTrigger>
            <TabsTrigger value="companies">{t("byCompany")}</TabsTrigger>
            <TabsTrigger value="buyers">{t("byBuyer")}</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="regions" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">
                {t("allRegions")}
                <span className="ml-2 text-xs font-normal text-muted-foreground">
                  ({data?.regions.length ?? 0} • {metric === "count" ? metricLabel : amountType === "contracted" ? t("amountContracted") : t("amountAnnounced")})
                </span>
              </CardTitle>
              <div className="flex flex-wrap items-center justify-end gap-2">
                {metric === "amount" && amountTypeToggle}
                {metricToggle}
              </div>
            </CardHeader>
            <CardContent>
              {/* Висота залежить від кількості регіонів, щоб усі бари вміщались */}
              <div style={{ height: Math.max(320, (data?.regions.length ?? 0) * 30 + 40) }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data?.regions} layout="vertical" margin={{ right: 40 }}>
                    <CartesianGrid {...GRID_PROPS} />
                    <XAxis
                      type="number"
                      tick={AXIS_TICK}
                      stroke="#8b949e"
                      tickFormatter={(v) => formatMetric(Number(v))}
                      label={{ value: metricLabel, position: "insideBottom", offset: -2, style: { fill: "#8b949e", fontSize: 11 } }}
                    />
                    <YAxis dataKey="region" type="category" width={150} tick={AXIS_TICK} stroke="#8b949e" interval={0} />
                    <Tooltip
                      contentStyle={TOOLTIP_STYLE}
                      cursor={{ fill: "#8b949e", fillOpacity: 0.08 }}
                      formatter={(v) => [formatMetric(Number(v ?? 0)), metricLabel]}
                    />
                    <Bar dataKey={regionMetricKey} radius={[0, 4, 4, 0]}>
                      {/* Точні значення на барах */}
                      <LabelList dataKey={regionMetricKey} position="right" style={BAR_LABEL} formatter={(v) => formatMetric(Number(v))} />
                      {(data?.regions ?? []).map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="categories" className="mt-4 space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">
                {t("top10Categories")}
                <span className="ml-2 text-xs font-normal text-muted-foreground">(ДК 021:2015, {metricLabel})</span>
              </CardTitle>
              {metricToggle}
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data?.categories.slice(0, 10)} margin={{ top: 16 }}>
                    <CartesianGrid {...GRID_PROPS} />
                    <XAxis dataKey="cpv_code" tick={AXIS_TICK_SM} stroke="#8b949e" />
                    <YAxis
                      tick={AXIS_TICK}
                      stroke="#8b949e"
                      tickFormatter={(v) => formatMetric(Number(v))}
                      label={{ value: metricLabel, angle: -90, position: "insideLeft", style: { fill: "#8b949e", fontSize: 11, textAnchor: "middle" } }}
                    />
                    <Tooltip
                      contentStyle={TOOLTIP_STYLE}
                      cursor={{ fill: "#8b949e", fillOpacity: 0.08 }}
                      formatter={(v) => [formatMetric(Number(v ?? 0)), metricLabel]}
                      // Розшифровка CPV коду в tooltip
                      labelFormatter={(code) => {
                        const cat = data?.categories.find((c) => c.cpv_code === code);
                        return cat?.name ? `${code} — ${cat.name}` : String(code);
                      }}
                    />
                    <Bar dataKey={metricKey} radius={[4, 4, 0, 0]}>
                      <LabelList dataKey={metricKey} position="top" style={BAR_LABEL} formatter={(v) => formatMetric(Number(v))} />
                      {(data?.categories.slice(0, 10) ?? []).map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
          {/* Таблиця з розшифровкою кодів та точними числами */}
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t("category")}</th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">{t("tendersCount")}</th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">{t("totalAmount")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.categories.slice(0, 10).map((c) => (
                    <tr key={c.cpv_code} className="border-b border-border">
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs text-muted-foreground">{c.cpv_code}</span>
                        <p className="font-medium">{c.name ?? "—"}</p>
                      </td>
                      <td className="px-4 py-3 text-right font-mono">{c.tenders_count}</td>
                      <td className="px-4 py-3 text-right font-mono">{formatAmount(c.total_amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="companies" className="mt-4 space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">
                {t("byCompany")}
                <span className="ml-2 text-xs font-normal text-muted-foreground">({metric === "count" ? t("wins") : t("metricAmount")})</span>
              </CardTitle>
              {metricToggle}
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data?.top_companies.slice(0, 10).map((c) => ({
                      name: c.name.length > 30 ? c.name.slice(0, 30) + "…" : c.name,
                      fullName: c.name,
                      value: metric === "count" ? c.wins_count : c.total_amount,
                    }))}
                    layout="vertical"
                    margin={{ right: 40 }}
                  >
                    <CartesianGrid {...GRID_PROPS} />
                    <XAxis type="number" tick={AXIS_TICK} stroke="#8b949e" tickFormatter={(v) => formatMetric(Number(v))} />
                    <YAxis dataKey="name" type="category" width={220} tick={AXIS_TICK_SM} stroke="#8b949e" />
                    <Tooltip
                      contentStyle={TOOLTIP_STYLE}
                      cursor={{ fill: "#8b949e", fillOpacity: 0.08 }}
                      formatter={(v) => [formatMetric(Number(v ?? 0)), metric === "count" ? t("wins") : t("metricAmount")]}
                      // Повна назва компанії в tooltip
                      labelFormatter={(_, payload) =>
                        (payload?.[0]?.payload as { fullName?: string })?.fullName ?? ""
                      }
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      <LabelList dataKey="value" position="right" style={BAR_LABEL} formatter={(v) => formatMetric(Number(v))} />
                      {(data?.top_companies.slice(0, 10) ?? []).map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t("company")}</th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">{t("wins")}</th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">{t("totalAmount")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.top_companies.map((c) => (
                    <tr key={c.id} className="border-b border-border">
                      <td className="px-4 py-3 font-medium" title={c.name}>{c.name}</td>
                      <td className="px-4 py-3 text-right font-mono">{c.wins_count}</td>
                      <td className="px-4 py-3 text-right font-mono">{formatAmount(c.total_amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="buyers" className="mt-4 space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">
                {t("byBuyer")}
                <span className="ml-2 text-xs font-normal text-muted-foreground">({metric === "count" ? t("tendersCount") : t("metricAmount")})</span>
              </CardTitle>
              {metricToggle}
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data?.top_buyers.slice(0, 10).map((b) => ({
                      name: b.name.length > 30 ? b.name.slice(0, 30) + "…" : b.name,
                      fullName: b.name,
                      value: metric === "count" ? b.tenders_count : b.total_amount,
                    }))}
                    layout="vertical"
                    margin={{ right: 40 }}
                  >
                    <CartesianGrid {...GRID_PROPS} />
                    <XAxis type="number" tick={AXIS_TICK} stroke="#8b949e" tickFormatter={(v) => formatMetric(Number(v))} />
                    <YAxis dataKey="name" type="category" width={220} tick={AXIS_TICK_SM} stroke="#8b949e" />
                    <Tooltip
                      contentStyle={TOOLTIP_STYLE}
                      cursor={{ fill: "#8b949e", fillOpacity: 0.08 }}
                      formatter={(v) => [formatMetric(Number(v ?? 0)), metric === "count" ? t("tendersCount") : t("metricAmount")]}
                      // Повна назва замовника в tooltip
                      labelFormatter={(_, payload) =>
                        (payload?.[0]?.payload as { fullName?: string })?.fullName ?? ""
                      }
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      <LabelList dataKey="value" position="right" style={BAR_LABEL} formatter={(v) => formatMetric(Number(v))} />
                      {(data?.top_buyers.slice(0, 10) ?? []).map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t("buyer")}</th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">{t("tendersCount")}</th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">{t("totalAmount")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.top_buyers.map((b) => (
                    <tr key={b.id} className="border-b border-border">
                      <td className="px-4 py-3 font-medium" title={b.name}>{b.name}</td>
                      <td className="px-4 py-3 text-right font-mono">{b.tenders_count}</td>
                      <td className="px-4 py-3 text-right font-mono">{formatAmount(b.total_amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
