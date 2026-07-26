"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, AnalyticsResponse } from "@/services/api";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
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

export default function AnalyticsPage() {
  const t = useTranslations("analytics");
  const [data, setData] = useState<AnalyticsResponse | null>(null);

  useEffect(() => {
    api.getAnalytics().then(setData).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("title")}</h1>

      <Tabs defaultValue="regions">
        <TabsList>
          <TabsTrigger value="regions">{t("byRegion")}</TabsTrigger>
          <TabsTrigger value="categories">{t("byCategory")}</TabsTrigger>
          <TabsTrigger value="companies">{t("byCompany")}</TabsTrigger>
          <TabsTrigger value="buyers">{t("byBuyer")}</TabsTrigger>
        </TabsList>

        <TabsContent value="regions" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">{t("byRegion")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data?.regions.slice(0, 10)} layout="vertical">
                    <CartesianGrid {...GRID_PROPS} />
                    <XAxis type="number" tick={AXIS_TICK} stroke="#8b949e" />
                    <YAxis dataKey="region" type="category" width={150} tick={AXIS_TICK} stroke="#8b949e" />
                    <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "#8b949e", fillOpacity: 0.08 }} />
                    <Bar dataKey="tenders_count" radius={[0, 4, 4, 0]}>
                      {(data?.regions.slice(0, 10) ?? []).map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="categories" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">{t("byCategory")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data?.categories.slice(0, 10)}>
                    <CartesianGrid {...GRID_PROPS} />
                    <XAxis dataKey="cpv_code" tick={AXIS_TICK_SM} stroke="#8b949e" />
                    <YAxis tick={AXIS_TICK} stroke="#8b949e" />
                    <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "#8b949e", fillOpacity: 0.08 }} />
                    <Bar dataKey="tenders_count" radius={[4, 4, 0, 0]}>
                      {(data?.categories.slice(0, 10) ?? []).map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="companies" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">{t("byCompany")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data?.top_companies.slice(0, 10).map((c) => ({
                      name: c.name.length > 30 ? c.name.slice(0, 30) + "…" : c.name,
                      wins: c.wins_count,
                      amount: c.total_amount,
                    }))}
                    layout="vertical"
                  >
                    <CartesianGrid {...GRID_PROPS} />
                    <XAxis type="number" tick={AXIS_TICK} stroke="#8b949e" />
                    <YAxis dataKey="name" type="category" width={220} tick={AXIS_TICK_SM} stroke="#8b949e" />
                    <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "#8b949e", fillOpacity: 0.08 }} />
                    <Bar dataKey="wins" name={t("wins")} radius={[0, 4, 4, 0]}>
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
                      <td className="px-4 py-3 font-medium">{c.name}</td>
                      <td className="px-4 py-3 text-right font-mono">{c.wins_count}</td>
                      <td className="px-4 py-3 text-right font-mono">{formatAmount(c.total_amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="buyers" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">{t("byBuyer")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data?.top_buyers.slice(0, 10).map((b) => ({
                      name: b.name.length > 30 ? b.name.slice(0, 30) + "…" : b.name,
                      tenders: b.tenders_count,
                      amount: b.total_amount,
                    }))}
                    layout="vertical"
                  >
                    <CartesianGrid {...GRID_PROPS} />
                    <XAxis type="number" tick={AXIS_TICK} stroke="#8b949e" />
                    <YAxis dataKey="name" type="category" width={220} tick={AXIS_TICK_SM} stroke="#8b949e" />
                    <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "#8b949e", fillOpacity: 0.08 }} />
                    <Bar dataKey="tenders" name={t("tendersCount")} radius={[0, 4, 4, 0]}>
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
                      <td className="px-4 py-3 font-medium">{b.name}</td>
                      <td className="px-4 py-3 text-right font-mono">{b.tenders_count}</td>
                      <td className="px-4 py-3 text-right font-mono">{formatAmount(b.total_amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
