"use client";

import type { LucideIcon } from "lucide-react";
import clsx from "clsx";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: "navy" | "blue" | "accent" | "green" | "red";
}

const borderColors = {
  navy: "border-l-dcab-navy",
  blue: "border-l-dcab-blue",
  accent: "border-l-dcab-accent",
  green: "border-l-emerald-500",
  red: "border-l-red-500",
};

const iconColors = {
  navy: "text-dcab-navy",
  blue: "text-dcab-blue",
  accent: "text-dcab-accent",
  green: "text-emerald-500",
  red: "text-red-500",
};

export function KPICard({ title, value, subtitle, icon: Icon, color = "navy" }: KPICardProps) {
  return (
    <div className={clsx("bg-white rounded-lg shadow p-5 border-l-4", borderColors[color])}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-dcab-gray uppercase tracking-wide">{title}</p>
          <p className="mt-1.5 text-2xl font-bold text-dcab-navy">{value}</p>
          {subtitle && <p className="text-sm text-dcab-gray mt-0.5">{subtitle}</p>}
        </div>
        <Icon className={clsx("w-5 h-5 mt-0.5", iconColors[color])} />
      </div>
    </div>
  );
}
