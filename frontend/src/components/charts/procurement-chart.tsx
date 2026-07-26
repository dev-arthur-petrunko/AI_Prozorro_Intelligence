"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import { ChartDataPoint } from "@/services/api";

interface ProcurementChartProps {
  data: ChartDataPoint[];
}

export function ProcurementChart({ data }: ProcurementChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        No chart data available
      </div>
    );
  }

  const chartData = data.map((point) => ({
    date: point.date.slice(5), // MM-DD format
    tenders: point.tenders_count,
    volume: point.volume / 1_000_000, // in millions
  }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="tendersGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          {/* Кольори задаємо напряму: CSS-змінні теми у форматі oklch,
              тому hsl(var(--...)) дає невалідний (чорний) колір */}
          <CartesianGrid strokeDasharray="3 3" stroke="#8b949e" strokeOpacity={0.25} />
          <XAxis
            dataKey="date"
            tick={{ fill: "#8b949e", fontSize: 11 }}
            stroke="#8b949e"
          />
          <YAxis
            tick={{ fill: "#8b949e", fontSize: 11 }}
            stroke="#8b949e"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--card)",
              color: "var(--card-foreground)",
              border: "1px solid var(--border)",
              borderRadius: "6px",
              fontSize: "12px",
            }}
            labelStyle={{ color: "var(--card-foreground)" }}
          />
          <Area
            type="monotone"
            dataKey="tenders"
            stroke="#3b82f6"
            fill="url(#tendersGradient)"
            strokeWidth={2.5}
            dot={{ r: 3, fill: "#3b82f6" }}
            activeDot={{ r: 5, fill: "#60a5fa" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
