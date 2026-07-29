const ENV_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Динамічне визначення адреси API:
// якщо сторінку відкрито не з localhost (напр. з телефона за IP комп'ютера),
// звертаємось до бекенда за тим самим хостом на порту 8000
function getApiUrl(): string {
  if (
    typeof window !== "undefined" &&
    window.location.hostname !== "localhost" &&
    window.location.hostname !== "127.0.0.1" &&
    ENV_API_URL.includes("localhost")
  ) {
    return `http://${window.location.hostname}:8000`;
  }
  return ENV_API_URL;
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiUrl()}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// Types
export interface DashboardKPI {
  total_tenders: number;
  suspicious_tenders: number;
  total_companies: number;
  total_buyers: number;
  today_volume: number;
  today_new: number;
}

export interface ChartDataPoint {
  date: string;
  tenders_count: number;
  reports_count?: number;
  tenders_volume?: number;
  reports_volume?: number;
  high_risk_count?: number;
  volume: number;
  new_tenders: number;
}

export interface TenderResponse {
  id: number;
  prozorro_id: string;
  title: string;
  description: string | null;
  status: string;
  cpv_code: string | null;
  region: string | null;
  published_date: string | null;
  end_date: string | null;
  amount: number | null;
  currency: string;
  participants_count: number;
  buyer_id: number | null;
  winner_id: number | null;
  risk_score: number | null;
  ai_analysis: string | null;
  risk_factors: string | null;
  created_at: string;
  updated_at: string;
  buyer_name?: string | null;
  winner_name?: string | null;
}

export interface TenderListResponse {
  items: TenderResponse[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface CompanyResponse {
  id: number;
  name: string;
  edrpou: string | null;
  region: string | null;
  wins_count: number;
  total_amount: number;
  avg_amount: number;
  created_at: string;
  updated_at: string;
}

export interface CompanyListResponse {
  items: CompanyResponse[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface BuyerResponse {
  id: number;
  name: string;
  edrpou: string | null;
  region: string | null;
  tenders_count: number;
  total_amount: number;
  avg_participants: number;
  created_at: string;
  updated_at: string;
}

export interface BuyerListResponse {
  items: BuyerResponse[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface DashboardResponse {
  kpi: DashboardKPI;
  chart_data: ChartDataPoint[];
  suspicious_tenders: TenderResponse[];
  active_suspicious_tenders: TenderResponse[];
  recent_tenders: TenderResponse[];
  last_updated: string | null;
}

export interface AnalyticsResponse {
  categories: { cpv_code: string; name?: string | null; tenders_count: number; total_amount: number }[];
  regions: { region: string; tenders_count: number; total_amount: number; contracted_amount: number }[];
  top_companies: CompanyResponse[];
  top_buyers: BuyerResponse[];
  price_dynamics: ChartDataPoint[];
  last_updated: string | null;
}

export interface DailyReportResponse {
  date: string;
  total_new_tenders: number;
  suspicious_count: number;
  highest_risk_score: number;
  largest_tender_amount: number;
  top_category: string | null;
  top_region: string | null;
  suspicious_tenders: TenderResponse[];
}

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
  tenders_count: number;
  last_sync: string | null;
}

// API Functions
export const api = {
  getDashboard: (days?: number) =>
    fetchAPI<DashboardResponse>(`/dashboard${days ? `?days=${days}` : ""}`),
  
  getTenders: (params?: Record<string, string | number>) => {
    const query = params ? "?" + new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString() : "";
    return fetchAPI<TenderListResponse>(`/tenders${query}`);
  },
  
  getTender: (id: number) => fetchAPI<TenderResponse>(`/tenders/${id}`),
  
  getCompanies: (params?: Record<string, string | number>) => {
    const query = params ? "?" + new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString() : "";
    return fetchAPI<CompanyListResponse>(`/companies${query}`);
  },
  
  getCompany: (id: number) => fetchAPI<CompanyResponse>(`/companies/${id}`),
  
  getBuyers: (params?: Record<string, string | number>) => {
    const query = params ? "?" + new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString() : "";
    return fetchAPI<BuyerListResponse>(`/buyers${query}`);
  },
  
  getBuyer: (id: number) => fetchAPI<BuyerResponse>(`/buyers/${id}`),
  
  getAnalytics: (days?: number) =>
    fetchAPI<AnalyticsResponse>(`/analytics${days ? `?days=${days}` : ""}`),
  
  getDailyReport: () => fetchAPI<DailyReportResponse>("/daily-report"),
  
  getHealth: () => fetchAPI<HealthResponse>("/health"),
};
