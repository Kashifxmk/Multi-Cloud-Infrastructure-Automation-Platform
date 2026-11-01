const API_URL = import.meta.env.VITE_API_URL
  ?? (typeof window !== "undefined" ? `${window.location.protocol}//${window.location.hostname}:8000` : "http://127.0.0.1:8000");

export type Dashboard = {
  mode: string;
  message: string;
  metrics: {
    cloud_accounts: number;
    deployments: number;
    active_resources: number;
    monthly_spend: number | null;
  };
  provider_distribution: Array<{ provider: string; count: number }>;
  recent_activity: Array<{ message: string; timestamp: string }>;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) throw new Error((await response.json()).detail ?? "Request failed");
  return response.json();
}

export const getDashboard = () => request<Dashboard>("/api/dashboard");
export const login = (email: string, password: string) =>
  request("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
export const register = (full_name: string, email: string, password: string) =>
  request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ full_name, email, password, terms_accepted: true }),
  });

export type CurrentUser = {
  id: string;
  full_name: string;
  email: string;
  is_verified: boolean;
};

export const getCurrentUser = () => request<CurrentUser>("/api/auth/me");
export const logout = () => request<void>("/api/auth/logout", { method: "POST" });

export type CloudAccount = {
  id: string;
  provider: "aws" | "gcp" | "azure";
  display_name: string;
  status: string;
  metadata: { account_identifier?: string; verified_at?: string; simulation?: boolean };
};

export const getCloudAccounts = () =>
  request<{ mode: string; accounts: CloudAccount[] }>("/api/cloud-accounts");

export const connectCloudAccount = (provider: string, display_name: string, account_identifier: string) =>
  request("/api/cloud-accounts", {
    method: "POST",
    body: JSON.stringify({ provider, display_name, account_identifier }),
  });

export const disconnectCloudAccount = (id: string) =>
  request<void>(`/api/cloud-accounts/${id}`, { method: "DELETE" });

export const verifyCloudAccount = (id: string) =>
  request<{ message: string }>(`/api/cloud-accounts/${id}/verify`, { method: "POST" });

export type InfrastructureTemplate = {
  slug: string;
  name: string;
  description: string;
  category: string;
  difficulty: string;
  estimated_minutes: number;
  resources: string[];
  providers: string[];
};

export const getTemplates = () =>
  request<{ templates: InfrastructureTemplate[] }>("/api/infrastructure/templates");

export const saveInfrastructureConfiguration = (template_slug: string, configuration: Record<string, unknown>) =>
  request("/api/infrastructure/configurations", {
    method: "POST",
    body: JSON.stringify({ template_slug, configuration }),
  });

export type CostEstimate = {
  provider: string;
  region: string;
  monthly: number;
  annual: number;
  hourly: number;
  breakdown: Record<string, number>;
  source: string;
  is_live: boolean;
  assumptions: string[];
};

export const comparePricing = (config: { vm_count: number; storage_gb: number; database_enabled: boolean }) =>
  request<{ mode: string; estimates: CostEstimate[] }>("/api/pricing/compare", {
    method: "POST",
    body: JSON.stringify(config),
  });

export type Architecture = {
  mode: string;
  nodes: Array<{ id: string; type: string; label: string; details: Record<string, unknown> }>;
  edges: Array<{ source: string; target: string }>;
};

export const generateArchitecture = (config: Record<string, unknown>) =>
  request<Architecture>("/api/architecture/generate", {
    method: "POST",
    body: JSON.stringify(config),
  });

export type TerraformPreview = {
  mode: string;
  backend: string;
  provider: string;
  files: Record<string, string>;
  message: string;
};

export const generateTerraformPreview = (config: Record<string, unknown>) =>
  request<TerraformPreview>("/api/terraform/generate-preview", {
    method: "POST",
    body: JSON.stringify(config),
  });

export type Deployment = {
  id: string;
  status: string;
  provider: string;
  configuration: Record<string, unknown>;
  resources: Array<{ name: string; type: string; provider_id: string }>;
};

export const getDeployments = () =>
  request<{ mode: string; deployments: Deployment[] }>("/api/deployments");

export const createDeploymentPlan = (name: string, configuration: Record<string, unknown>) =>
  request<{ deployment: Deployment }>("/api/deployments/plan", {
    method: "POST",
    body: JSON.stringify({ name, configuration }),
  });

export const approveDeployment = (id: string) =>
  request<{ deployment: Deployment }>(`/api/deployments/${id}/approve`, { method: "POST" });

export const destroyDeployment = (id: string) =>
  request<{ status: string }>(`/api/deployments/${id}/destroy`, { method: "POST" });
