"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { APP_VERSION } from "@/lib/version";

export default function SettingsPage() {
  const t = useTranslations("nav");
  const s = useTranslations("settings");

  const changelogLatest = [
    s("v163_1"),
    s("v163_2"),
    s("v163_3"),
  ];

  const changelog160 = [
    s("v160_1"),
    s("v160_2"),
    s("v160_3"),
  ];

  const changelog146 = [
    s("v146_1"),
    s("v146_2"),
    s("v146_3"),
  ];

  // Історія старих версій зберігається - не видаляти при релізах
  const changelogOld = [
    s("changelog1"),
    s("changelog2"),
    s("changelog3"),
    s("changelog4"),
    s("changelog5"),
    s("changelog6"),
    s("changelog7"),
    s("changelog8"),
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("settings")}</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{s("apiConfig")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">{s("backendUrl")}</span>
              <code className="text-xs">{process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}</code>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">{s("version")}</span>
              <span className="font-medium">{APP_VERSION}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{s("whatsNew")}</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            {changelogLatest.map((item, i) => (
              <li key={i} className="flex gap-2">
                <span className="mt-0.5 text-primary">•</span>
                <span className="text-muted-foreground">{item}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base text-muted-foreground">{s("previousVersion")}</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            {changelog160.map((item, i) => (
              <li key={i} className="flex gap-2">
                <span className="mt-0.5 text-muted-foreground/50">•</span>
                <span className="text-muted-foreground">{item}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base text-muted-foreground">{s("version146")}</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            {changelog146.map((item, i) => (
              <li key={i} className="flex gap-2">
                <span className="mt-0.5 text-muted-foreground/50">•</span>
                <span className="text-muted-foreground">{item}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base text-muted-foreground">{s("olderVersion")}</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            {changelogOld.map((item, i) => (
              <li key={i} className="flex gap-2">
                <span className="mt-0.5 text-muted-foreground/50">•</span>
                <span className="text-muted-foreground">{item}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
