"use client";

import { useTranslations } from "next-intl";
import { Scale, Database, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LegalPage() {
  const t = useTranslations("legal");

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">{t("title")}</h1>

      {/* Джерело даних та правові засади */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Database className="h-4 w-4 text-primary" />
            {t("dataSourceTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm leading-relaxed text-muted-foreground">
          <p>{t("dataSourceP1")}</p>
          <p>{t("dataSourceP2")}</p>
          <div>
            <p className="mb-2">{t("lawsIntro")}</p>
            <ul className="list-disc space-y-1 pl-5">
              <li>{t("law1")}</li>
              <li>{t("law2")}</li>
              <li>{t("law3")}</li>
            </ul>
          </div>
          <p className="text-foreground">
            <span className="font-medium">{t("sourceLabel")}</span>{" "}
            <a
              href="https://prozorro.gov.ua"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-primary hover:underline"
            >
              {t("sourceValue")}
              <ExternalLink className="h-3 w-3" />
            </a>
          </p>
        </CardContent>
      </Card>

      {/* Дисклеймер щодо AI-аналізу та індексу ризику */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Scale className="h-4 w-4 text-primary" />
            {t("aiTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm leading-relaxed text-muted-foreground">
          <p>{t("aiP1")}</p>
          <p>{t("aiP2")}</p>
          <p>{t("aiP3")}</p>
        </CardContent>
      </Card>
    </div>
  );
}
