"use client";

import { useState } from "react";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  Line,
  Brush,
  ComposedChart,
} from "recharts";
import { ChartDataPoint } from "@/services/api";

type Metric = "count" | "amount";

interface ProcurementChartProps {
  data: ChartDataPoint[];
  /** Примітка для сьогоднішньої (ще неповної) точки */
  incompleteDayNote?: string;
  /** Назви серій та перемикача (i18n) */
  competitiveLabel?: string;
  reportingLabel?: string;
  highRiskLabel?: string;
  metricCountLabel?: string;
  metricAmountLabel?: string;
  /** Керований ззовні перемикач метрики (щоб не скидався при оновленні даних) */
  metric?: Metric;
  onMetricChange?: (m: Metric) => void;
}

function formatAmount(v: number): string {
  if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(1)}B`;
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(1)}K`;
  return v.toFixed(0);
}

export function ProcurementChart({
  data,
  incompleteDayNote,
  competitiveLabel,
  reportingLabel,
  highRiskLabel,
  metricCountLabel,
  metricAmountLabel,
  metric: metricProp,
  onMetricChange,
}: ProcurementChartProps) {
  // Fallback на внутрішній стан, якщо метрику не контролюють ззовні
  const [metricInner, setMetricInner] = useState<Metric>("count");
  const metric = metricProp ?? metricInner;
  const setMetric = onMetricChange ?? setMetricInner;

  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        No chart data available
      </div>
    );
  }

  // Сьогоднішній день ще не завершений - позначаємо точку окремо
  const todayShort = new Date().toISOString().slice(5, 10); // MM-DD

  const isAmount = metric === "amount";
  const chartData = data.map((point) => ({
    date: point.date.slice(5), // MM-DD
    tenders: isAmount ? (point.tenders_volume ?? 0) : point.tenders_count,
    reports: isAmount ? (point.reports_volume ?? 0) : (point.reports_count ?? 0),
    highRisk: point.high_risk_count ?? 0,
    isToday: point.date.slice(5, 10) === todayShort,
  }));

  const hasReports = chartData.some((p) => p.reports > 0);
  const hasHighRisk = !isAmount && chartData.some((p) => p.highRisk > 0);

  const tendersName = competitiveLabel ?? "tenders";
  const reportsName = reportingLabel ?? "reports";
  const highRiskName = highRiskLabel ?? "high risk";

  const fmt = (v: number) => (isAmount ? formatAmount(v) : String(v));

  const dot =
    (color: string) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (props: any) => {
      const { key, payload, cx, cy } = props as {
        key: string; cx: number; cy: number; payload: { isToday: boolean };
      };
      return payload.isToday ? (
        <circle key={key} cx={cx} cy={cy} r={4} fill="var(--card)" stroke={color} strokeWidth={2} strokeDasharray="2 2" />
      ) : (
        <circle key={key} cx={cx} cy={cy} r={3} fill={color} />
      );
    };

  const MetricBtn = ({ value, label }: { value: Metric; label: string }) => (
    <button
      onClick={() => setMetric(value)}
      className={`px-3 py-1 text-xs transition-colors ${
        metric === value
          ? "bg-primary text-primary-foreground"
          : "text-muted-foreground hover:text-foreground"
      } ${value === "count" ? "rounded-l-md" : "rounded-r-md"}`}
    >
      {label}
    </button>
  );

  return (
    <div>
      <div className="mb-2 flex justify-end">
        <div className="flex rounded-md border border-border">
          <MetricBtn value="count" label={metricCountLabel ?? "Count"} />
          <MetricBtn value="amount" label={metricAmountLabel ?? "Amount"} />
        </div>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <defs>
              <linearGradient id="tendersGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="reportsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#8b949e" strokeOpacity={0.25} />
            <XAxis dataKey="date" tick={{ fill: "#8b949e", fontSize: 11 }} stroke="#8b949e" />
            <YAxis tick={{ fill: "#8b949e", fontSize: 11 }} stroke="#8b949e" tickFormatter={fmt} />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--card)",
                color: "var(--card-foreground)",
                border: "1px solid var(--border)",
                borderRadius: "6px",
                fontSize: "12px",
              }}
              labelStyle={{ color: "var(--card-foreground)" }}
              labelFormatter={(label) =>
                label === todayShort && incompleteDayNote
                  ? `${label} (${incompleteDayNote})`
                  : label
              }
              formatter={(value) => fmt(Number(value ?? 0))}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Area
              type="monotone"
              dataKey="tenders"
              name={tendersName}
              stroke="#3b82f6"
              fill="url(#tendersGradient)"
              strokeWidth={2.5}
              dot={dot("#3b82f6")}
              activeDot={{ r: 5, fill: "#60a5fa" }}
            />
            {hasReports && (
              <Area
                type="monotone"
                dataKey="reports"
                name={reportsName}
                stroke="#f59e0b"
                fill="url(#reportsGradient)"
                strokeWidth={2}
                dot={dot("#f59e0b")}
                activeDot={{ r: 5, fill: "#fbbf24" }}
              />
            )}
            {hasHighRisk && (
              <Line
                type="monotone"
                dataKey="highRisk"
                name={highRiskName}
                stroke="#ef4444"
                strokeWidth={2}
                dot={dot("#ef4444")}
                activeDot={{ r: 5, fill: "#f87171" }}
              />
            )}
            <Brush
              dataKey="date"
              height={22}
              travellerWidth={8}
              stroke="#8b949e"
              fill="var(--card)"
              tickFormatter={() => ""}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
