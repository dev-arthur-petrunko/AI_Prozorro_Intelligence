import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  // Прибираємо круглу кнопку Next.js DevTools у лівому нижньому куті (dev-режим)
  devIndicators: false,
};

export default withNextIntl(nextConfig);
