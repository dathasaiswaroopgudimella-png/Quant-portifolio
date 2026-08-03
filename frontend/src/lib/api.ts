function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const host = window.location.hostname || "127.0.0.1";
    return `http://${host}:8000/api/v1`;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
}

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: "Network request failed" }));
    throw new Error(errorBody.detail || `HTTP Error ${res.status}`);
  }

  return res.json();
}

export interface ModelData {
  id: string;
  name: string;
  description?: string;
  asset_class: string;
  code: string;
  version: string;
  created_at: string;
}

export interface AssumptionData {
  id: string;
  name: string;
  category: string;
  mathematical_form: string;
  description: string;
  is_violated_in_stress: boolean;
}

export interface HexagonalScoresData {
  conceptual_soundness: number;
  numerical_stability: number;
  parameter_robustness: number;
  boundary_condition_safety: number;
  greek_fidelity: number;
  benchmark_alignment: number;
}

export interface ValidationRunData {
  id: string;
  model_id: string;
  status: string;
  fragility_score?: number;
  classification?: string;
  max_pricing_error?: number;
  breaking_parameters?: {
    spot: number;
    volatility: number;
    risk_free_rate: number;
    user_price: number;
    quantlib_price: number;
    absolute_error: number;
    percentage_error: number;
  };
  greek_drifts?: {
    delta: number;
    gamma: number;
    vega: number;
    theta: number;
    rho: number;
    [key: string]: number;
  };
  fragility_surface?: {
    spot_axis: number[];
    volatility_axis: number[];
    error_matrix: number[][];
  };
  hexagonal_scores?: HexagonalScoresData;
  created_at: string;
}

export interface MarketQuoteData {
  ticker: string;
  spot_price: number;
  historical_volatility_21d: number;
  risk_free_rate: number;
  timestamp: string;
}

export interface ReportData {
  id: string;
  run_id: string;
  executive_summary: string;
  sr11_7_compliance: any;
  report_data: any;
  created_at: string;
}

