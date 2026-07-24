"use client";

import {
  Bar,
  BarChart as RBarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart as RLineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TimeSeriesPoint } from "@/lib/types";

const GRID_COLOR = "var(--border-hairline)";
const AXIS_COLOR = "var(--text-muted)";

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { name: string; value: number; color: string }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border-hairline bg-surface-raised px-3 py-2 text-xs shadow-md">
      <p className="mb-1 font-medium text-text-primary">{label}</p>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-1.5 text-text-secondary">
          <span className="h-2 w-2 rounded-full" style={{ background: p.color }} />
          <span>{p.name}:</span>
          <span className="font-medium tabular-nums text-text-primary">{p.value}</span>
        </div>
      ))}
    </div>
  );
}

export function TrendLineChart({
  series,
}: {
  series: { name: string; data: TimeSeriesPoint[]; color: string }[];
}) {
  const labels = series[0]?.data.map((d) => d.label) ?? [];
  const merged = labels.map((label, i) => {
    const row: Record<string, string | number> = { label };
    series.forEach((s) => {
      row[s.name] = s.data[i]?.value ?? 0;
    });
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={260}>
      <RLineChart data={merged} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={GRID_COLOR} vertical={false} />
        <XAxis dataKey="label" stroke={AXIS_COLOR} tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
        <YAxis stroke={AXIS_COLOR} tick={{ fontSize: 12 }} tickLine={false} axisLine={false} width={32} />
        <Tooltip content={<ChartTooltip />} />
        {series.length > 1 && <Legend wrapperStyle={{ fontSize: 12, color: AXIS_COLOR }} />}
        {series.map((s) => (
          <Line
            key={s.name}
            type="monotone"
            dataKey={s.name}
            stroke={s.color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ))}
      </RLineChart>
    </ResponsiveContainer>
  );
}

export function CategoryBarChart({
  data,
  color,
}: {
  data: { category: string; count: number }[];
  color: string;
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <RBarChart data={data} layout="vertical" margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={GRID_COLOR} horizontal={false} />
        <XAxis type="number" stroke={AXIS_COLOR} tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
        <YAxis
          type="category"
          dataKey="category"
          stroke={AXIS_COLOR}
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          width={110}
        />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "var(--surface-page)" }} />
        <Bar dataKey="count" fill={color} radius={[0, 4, 4, 0]} maxBarSize={18} />
      </RBarChart>
    </ResponsiveContainer>
  );
}
