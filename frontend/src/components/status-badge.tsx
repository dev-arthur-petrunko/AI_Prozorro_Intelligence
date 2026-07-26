"use client";

import { useLocale } from "next-intl";
import { Badge } from "@/components/ui/badge";

// Переклади статусів Prozorro (ключі містять крапки, тому не через next-intl messages)
const STATUS_LABELS: Record<string, { uk: string; en: string }> = {
  "draft": { uk: "Чернетка", en: "Draft" },
  "active": { uk: "Активний", en: "Active" },
  "active.enquiries": { uk: "Період уточнень", en: "Enquiries" },
  "active.tendering": { uk: "Подання пропозицій", en: "Tendering" },
  "active.auction": { uk: "Аукціон", en: "Auction" },
  "active.qualification": { uk: "Кваліфікація", en: "Qualification" },
  "active.awarded": { uk: "Визначено переможця", en: "Awarded" },
  "active.pre-qualification": { uk: "Прекваліфікація", en: "Pre-qualification" },
  "active.pre-qualification.stand-still": { uk: "Прекваліфікація (пауза)", en: "Pre-qualification (stand-still)" },
  "complete": { uk: "Завершено", en: "Complete" },
  "cancelled": { uk: "Скасовано", en: "Cancelled" },
  "unsuccessful": { uk: "Не відбувся", en: "Unsuccessful" },
};

export function statusLabel(status: string, locale: string): string {
  const entry = STATUS_LABELS[status];
  if (!entry) return status;
  return locale === "en" ? entry.en : entry.uk;
}

export function StatusBadge({ status }: { status: string }) {
  const locale = useLocale();
  return (
    <Badge variant="secondary" className="text-xs">
      {statusLabel(status, locale)}
    </Badge>
  );
}
