import { FormEvent, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, AlertTriangle, BarChart3, Bell, Boxes, CheckCircle2, ChevronLeft, ChevronRight, Cloud, Globe2, LayoutDashboard, Lightbulb, LogIn, Menu, Moon, RefreshCw, Search, Settings, ShieldCheck, Sun, UserPlus } from "lucide-react";
import { approveDeployment, Architecture, comparePricing, connectCloudAccount, createDeploymentPlan, CurrentUser, destroyDeployment, disconnectCloudAccount, executeDeploymentTerraformPlan, generateArchitecture, generateTerraformPreview, getAdminAudit, getAdminOverview, getAdminUsers, getCloudAccounts, getCurrentUser, getDashboard, getDeployments, getTemplates, login, logout, register, saveInfrastructureConfiguration, streamDeploymentLogs, verifyCloudAccount, InfrastructureTemplate } from "./api";
import ReactFlow, { Background, Controls, Edge, MiniMap, Node, useEdgesState, useNodesState } from "reactflow";

type AuthMode = "login" | "register";

function App() {
  const [authMode, setAuthMode] = useState<AuthMode | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const queryClient = useQueryClient();
  const currentUser = useQuery({
    queryKey: ["current-user"],
    queryFn: getCurrentUser,
    retry: false,
  });

  async function authenticated() {
    await currentUser.refetch();
    setAuthMode(null);
  }

  async function signedOut() {
    await logout();
    queryClient.setQueryData(["current-user"], null);
    queryClient.removeQueries({ queryKey: ["cloud-accounts"] });
    setAuthMode(null);
  }

  if (authMode) {
    return <AuthPage mode={authMode} onChangeMode={setAuthMode} onComplete={authenticated} />;
  }
  return <DashboardPage user={currentUser.data ?? null} onAuth={() => setAuthMode("login")} onLogout={signedOut} menuOpen={menuOpen} setMenuOpen={setMenuOpen} sidebarCollapsed={sidebarCollapsed} setSidebarCollapsed={setSidebarCollapsed} theme={theme} setTheme={setTheme} />;
}

function DashboardPage({
  user,
  onAuth,
  onLogout,
  menuOpen,
  setMenuOpen,
  sidebarCollapsed,
  setSidebarCollapsed,
  theme,
  setTheme,
}: {
  user: CurrentUser | null;
  onAuth: () => void;
  onLogout: () => Promise<void>;
  menuOpen: boolean;
  setMenuOpen: (open: boolean) => void;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  theme: "dark" | "light";
  setTheme: (theme: "dark" | "light") => void;
}) {
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
  const accounts = useQuery({ queryKey: ["cloud-accounts"], queryFn: getCloudAccounts });
  const [accountsOpen, setAccountsOpen] = useState(false);
  const [discoveryOpen, setDiscoveryOpen] = useState(false);
  const [provider, setProvider] = useState("aws");
  const [displayName, setDisplayName] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [accountMessage, setAccountMessage] = useState("");
  const [templatesOpen, setTemplatesOpen] = useState(false);
  const templates = useQuery({ queryKey: ["templates"], queryFn: getTemplates });
  const [pricingOpen, setPricingOpen] = useState(false);
  const [architectureOpen, setArchitectureOpen] = useState(false);
  const [terraformOpen, setTerraformOpen] = useState(false);
  const [deploymentsOpen, setDeploymentsOpen] = useState(false);
  const [adminOpen, setAdminOpen] = useState(false);
  const data = dashboard.data;
  const metrics = data?.metrics;
  const connectedAccounts = accounts.data?.accounts.filter((account) => account.status === "connected").length ?? 0;
  const refreshDashboard = () => { void dashboard.refetch(); void accounts.refetch(); };

  return (
    <div className={`app-shell theme-${theme}`}>
      <aside className={`${menuOpen ? "sidebar open" : "sidebar"}${sidebarCollapsed ? " collapsed" : ""}`}>
        <div className="brand"><span className="brand-mark">C</span> CloudPilot</div>
        <nav>
          <a className="active"><LayoutDashboard size={18} /><span>Command Center</span></a>
          <a onClick={() => user ? setDiscoveryOpen(true) : onAuth()}><Cloud size={18} /><span>Discovery</span></a>
          <a onClick={() => setTemplatesOpen(true)}><Boxes size={18} /><span>Infrastructure</span></a>
          <a onClick={() => setDeploymentsOpen(true)}><Activity size={18} /><span>Provisioning</span></a>
          <a onClick={() => setTemplatesOpen(true)}><Boxes size={18} /><span>Templates</span></a>
          <a onClick={() => setArchitectureOpen(true)}><ShieldCheck size={18} /><span>Architecture Builder</span></a>
          <a onClick={() => setTerraformOpen(true)}><Settings size={18} /><span>Automation</span></a>
          <a onClick={() => setDeploymentsOpen(true)}><Activity size={18} /><span>Monitoring</span></a>
          <a onClick={() => setPricingOpen(true)}><BarChart3 size={18} /><span>FinOps</span></a>
          {user?.is_admin && <a onClick={() => setAdminOpen(true)}><ShieldCheck size={18} /><span>Security & Policies</span></a>}
          <a><Settings size={18} /><span>Settings</span></a>
        </nav>
        <button className="sidebar-toggle" onClick={() => setSidebarCollapsed(!sidebarCollapsed)} aria-label="Toggle sidebar">{sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}</button>
        <div className="sidebar-footer">LOCAL MVP<br /><span>No cloud account connected</span></div>
      </aside>
      <main className="content">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setMenuOpen(!menuOpen)} aria-label="Open menu"><Menu /></button>
          <div><p className="eyebrow">CLOUDPILOT / OPERATIONS</p><h1>Global Command Center</h1><p className="topbar-subtitle">Unified visibility and control across your cloud infrastructure.</p></div>
          <div className="top-actions"><label className="global-search"><Search size={16} /><input placeholder="Search resources..." aria-label="Search resources" /></label><button className="icon-button" aria-label="Refresh dashboard" onClick={refreshDashboard}><RefreshCw size={17} /></button><button className="icon-button" aria-label="Notifications"><Bell size={17} /></button><button className="icon-button" aria-label="Toggle theme" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>{theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}</button>{user ? <><span className="user-chip">{user.email}</span><button className="button secondary" onClick={onLogout}>Sign out</button></> : <button className="button secondary" onClick={onAuth}><LogIn size={16} /> Sign in</button>}</div>
        </header>
        <section className="welcome">
          <div><p className="eyebrow">{user ? "LOCAL WORKSPACE" : "LOCAL DEMO ENVIRONMENT"}</p><h2>Infrastructure, without the guesswork.</h2><p>{user ? `Welcome back, ${user.full_name}. Your local workspace is ready.` : "Explore the CloudPilot workflow with safe local data. Sign in to save accounts and configurations."}</p></div>
          <div className="welcome-actions"><button className="button secondary" onClick={() => setTemplatesOpen(true)}><Boxes size={16} /> Browse templates</button><button className="button secondary" onClick={() => setPricingOpen(true)}><BarChart3 size={16} /> Compare costs</button><button className="button secondary" onClick={() => setArchitectureOpen(true)}><ShieldCheck size={16} /> Architecture</button><button className="button" onClick={() => user ? setAccountsOpen(true) : onAuth()}><Cloud size={16} /> {user ? "Connect account" : "Sign in to connect"}</button></div>
        </section>
        {dashboard.isError && <div className="alert error">The API is unavailable. Start the backend with <code>python -m backend.run</code>.</div>}
        <section className="command-filters"><span className="live-dot">LOCAL</span><span>Snapshot from local API</span><select aria-label="Environment"><option>All environments</option><option>Production</option><option>Staging</option></select><select aria-label="Region"><option>All regions</option></select><select aria-label="Time range"><option>Last 24 hours</option><option>Last 7 days</option></select></section>
        <section className="metrics">
          <Metric label="Infrastructure health" value="—" detail="Monitoring integration not connected" tone="info" />
          <Metric label="Active workloads" value={metrics?.active_resources ?? "—"} detail={`${metrics?.deployments ?? 0} deployments tracked`} tone="info" />
          <Metric label="Estimated monthly cost" value={metrics?.monthly_spend == null ? "—" : `$${metrics.monthly_spend}`} detail="Demo estimate · connect billing for live data" tone="violet" />
          <Metric label="Open incidents" value="—" detail="Monitoring integration not connected" tone="info" />
        </section>
        <section className="provider-grid">
          {["aws", "azure", "gcp"].map((item) => { const connected = accounts.data?.accounts.filter((account) => account.provider === item) ?? []; return <div className="provider-card" key={item}><div className={`provider-logo ${item}`}>{item === "aws" ? "AWS" : item === "azure" ? "AZ" : "GCP"}</div><div className="provider-card-main"><strong>{item.toUpperCase()}</strong><span>{connected.length ? `${connected.length} connected account${connected.length === 1 ? "" : "s"}` : "Not connected"}</span></div><span className={`status-pill ${connected.length ? "healthy" : "neutral"}`}>{connected.length ? "Connected" : "Demo"}</span><small>{connected[0]?.metadata.regions?.[0] ?? "No region synchronized"} · {connected[0]?.metadata.verified_at ? "Verified" : "Awaiting verification"}</small></div>; })}
        </section>
        <section className="ops-grid">
          <div className="panel">
            <div className="panel-heading"><div><h3>Operations pulse</h3><p>Signals available from this local workspace</p></div><span className="demo-tag">LOCAL SIGNALS</span></div>
            <div className="pulse-list"><div className="pulse-item"><CheckCircle2 size={17} /><div><strong>API availability</strong><span>Dashboard API responded successfully</span></div><b className="pulse-good">Ready</b></div><div className="pulse-item"><AlertTriangle size={17} /><div><strong>Cloud telemetry</strong><span>{connectedAccounts ? "Provider account metadata available" : "Connect and verify an account to begin"}</span></div><b className="pulse-muted">{connectedAccounts ? "Partial" : "Unavailable"}</b></div><div className="pulse-item"><Activity size={17} /><div><strong>Monitoring integration</strong><span>Live incidents and health checks are not connected</span></div><b className="pulse-muted">Offline</b></div></div>
          </div>
          <div className="panel">
            <div className="panel-heading"><div><h3>Recommended next steps</h3><p>Actions based on current workspace state</p></div><Lightbulb size={18} className="recommendation-icon" /></div>
            <div className="recommendation-list">{!user && <div className="recommendation"><span>01</span><div><strong>Sign in to save workspace state</strong><small>Accounts, templates, and deployments are scoped to a local workspace.</small></div><button className="text-button compact" onClick={onAuth}>Sign in</button></div>}{!connectedAccounts && <div className="recommendation"><span>02</span><div><strong>Connect a provider account</strong><small>Simulation is safe by default; verification discovers capabilities.</small></div><button className="text-button compact" onClick={() => user ? setAccountsOpen(true) : onAuth()}>Open</button></div>}<div className="recommendation"><span>03</span><div><strong>Start from a validated blueprint</strong><small>Use templates to create a configuration before planning.</small></div><button className="text-button compact" onClick={() => setTemplatesOpen(true)}>Browse</button></div></div>
          </div>
        </section>
        <section className="grid-two">
          <div className="panel">
            <div className="panel-heading"><div><h3>Cloud provider distribution</h3><p>Connected accounts by provider</p></div><span className="demo-tag">DEMO DATA</span></div>
            <div className="empty-chart"><Cloud size={34} /><strong>No providers connected</strong><span>Your provider distribution will appear here.</span><button className="button secondary" onClick={() => user ? setAccountsOpen(true) : onAuth()}>Connect a cloud account</button></div>
          </div>
          <div className="panel">
            <div className="panel-heading"><div><h3>Recent activity</h3><p>Deployment and account events</p></div><span className="demo-tag">DEMO DATA</span></div>
            <div className="empty-chart"><BarChart3 size={34} /><strong>No activity yet</strong><span>Start by creating a workspace or template.</span></div>
          </div>
        </section>
        {accountsOpen && user && <div className="modal-backdrop" onClick={() => setAccountsOpen(false)}><div className="modal" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">CLOUD ACCOUNTS</p><h3>Cloud accounts</h3></div><button className="close-button" onClick={() => setAccountsOpen(false)}>×</button></div><p className="muted small">Credentials remain outside CloudPilot. Simulation is default; real verification is explicit.</p>{accountMessage && <div className="alert success">{accountMessage}</div>}<div className="account-list">{accounts.data?.accounts.map((account) => <div className="account-row" key={account.id}><div className={`provider-dot ${account.provider}`}>{account.provider[0].toUpperCase()}</div><div><strong>{account.display_name}</strong><span>{account.provider.toUpperCase()} · {account.metadata.account_identifier}</span><small>{account.metadata.regions?.length ? `${account.metadata.regions.length} regions · ${account.metadata.machine_types?.length ?? 0} machine types` : "Capabilities not discovered"}</small></div><span className="account-status">{account.status}</span><button className="text-button compact" onClick={async () => { const result = await verifyCloudAccount(account.id); setAccountMessage(result.message); accounts.refetch(); }}>Verify</button><button className="text-button compact danger" onClick={async () => { await disconnectCloudAccount(account.id); accounts.refetch(); }}>Disconnect</button></div>)}{(!accounts.data || accounts.data.accounts.length === 0) && <div className="empty-account">No accounts connected.</div>}</div><form className="account-form" onSubmit={async (event) => { event.preventDefault(); await connectCloudAccount(provider, displayName, identifier); setDisplayName(""); setIdentifier(""); setAccountMessage("Account connection created."); accounts.refetch(); }}><h4>Connect an account</h4><select value={provider} onChange={(event) => setProvider(event.target.value)}><option value="aws">AWS</option><option value="gcp">Google Cloud</option><option value="azure">Microsoft Azure</option></select><input placeholder="Account name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} required minLength={2} /><input placeholder="Account / project / subscription ID" value={identifier} onChange={(event) => setIdentifier(event.target.value)} required minLength={2} /><button className="button">Connect account</button></form></div></div>}
        {discoveryOpen && user && <DiscoveryModal accounts={accounts.data?.accounts ?? []} onClose={() => setDiscoveryOpen(false)} />}
        {templatesOpen && <TemplateWizard templates={templates.data?.templates ?? []} onClose={() => setTemplatesOpen(false)} />}
        {pricingOpen && <PricingModal onClose={() => setPricingOpen(false)} />}
        {architectureOpen && <ArchitectureModal onClose={() => setArchitectureOpen(false)} />}
        {terraformOpen && <TerraformModal onClose={() => setTerraformOpen(false)} />}
        {deploymentsOpen && <DeploymentsModal user={user} accounts={accounts.data?.accounts ?? []} onAuth={onAuth} onClose={() => setDeploymentsOpen(false)} />}
        {adminOpen && user?.is_admin && <AdminModal onClose={() => setAdminOpen(false)} />}
        <section className="panel quick-actions"><div className="panel-heading"><div><h3>Start with CloudPilot</h3><p>A guided path from idea to infrastructure plan.</p></div></div><div className="action-cards"><Action icon={<Cloud />} title="Connect an account" text="Simulate AWS, GCP or Azure connection." /><Action icon={<Boxes />} title="Browse templates" text="Choose a ready-made infrastructure blueprint." /><Action icon={<BarChart3 />} title="Compare costs" text="Review provider estimates before deployment." /></div></section>
      </main>
    </div>
  );
}

function DiscoveryModal({ accounts, onClose }: { accounts: Array<import("./api").CloudAccount>; onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [provider, setProvider] = useState("all");
  const [selectedId, setSelectedId] = useState(accounts[0]?.id ?? "");
  const filtered = accounts.filter((account) => {
    const text = `${account.display_name} ${account.provider} ${account.metadata.account_identifier ?? ""} ${(account.metadata.regions ?? []).join(" ")}`.toLowerCase();
    return (provider === "all" || account.provider === provider) && text.includes(query.toLowerCase());
  });
  const selected = accounts.find((account) => account.id === selectedId) ?? filtered[0];
  return <div className="modal-backdrop" onClick={onClose}><div className="modal wide discovery-modal" onClick={(event) => event.stopPropagation()}>
    <div className="panel-heading"><div><p className="eyebrow">RESOURCE DISCOVERY · CAPABILITY INVENTORY</p><h3>Cloud inventory</h3><p className="muted small">Verified account metadata only. Resource-level discovery is not connected.</p></div><button className="close-button" onClick={onClose}>×</button></div>
    <div className="discovery-toolbar"><label className="global-search"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search accounts or regions" aria-label="Search inventory" /></label><select value={provider} onChange={(event) => setProvider(event.target.value)} aria-label="Filter provider"><option value="all">All providers</option><option value="aws">AWS</option><option value="azure">Azure</option><option value="gcp">GCP</option></select></div>
    {filtered.length ? <div className="inventory-layout"><div className="inventory-table"><div className="inventory-head"><span>Account</span><span>Provider</span><span>Regions</span><span>Status</span></div>{filtered.map((account) => <button className={`inventory-row${selected?.id === account.id ? " selected" : ""}`} key={account.id} onClick={() => setSelectedId(account.id)}><strong>{account.display_name}</strong><span className={`provider-label ${account.provider}`}>{account.provider.toUpperCase()}</span><span>{account.metadata.regions?.length ?? 0} discovered</span><span className={`inventory-status ${account.status}`}>{account.status}</span></button>)}</div><aside className="inventory-detail">{selected ? <><div className="detail-icon"><Globe2 size={20} /></div><h4>{selected.display_name}</h4><p className="muted small">{selected.provider.toUpperCase()} · {selected.metadata.account_identifier ?? "Identifier unavailable"}</p><div className="detail-section"><span>Verification</span><strong>{selected.metadata.verified_at ? "Verified" : "Not verified"}</strong></div><div className="detail-section"><span>Regions</span><div className="chip-list">{(selected.metadata.regions ?? []).map((region) => <span key={region}>{region}</span>)}</div></div><div className="detail-section"><span>Capabilities</span><div className="chip-list">{(selected.metadata.capabilities ?? []).map((capability) => <span key={capability}>{capability}</span>)}</div></div><div className="detail-section"><span>Machine types</span><div className="chip-list">{(selected.metadata.machine_types ?? []).map((machine) => <span key={machine}>{machine}</span>)}</div></div></> : <div className="empty-account">Select an account.</div>}</aside></div> : <div className="discovery-empty"><Globe2 size={30} /><strong>No discovered accounts</strong><span>Connect and verify a cloud account to populate this inventory.</span></div>}
  </div></div>;
}

function AdminModal({ onClose }: { onClose: () => void }) {
  const overview = useQuery({ queryKey: ["admin-overview"], queryFn: getAdminOverview });
  const users = useQuery({ queryKey: ["admin-users"], queryFn: getAdminUsers });
  const audit = useQuery({ queryKey: ["admin-audit"], queryFn: getAdminAudit });
  const metrics = overview.data?.metrics ?? {};
  return <div className="modal-backdrop" onClick={onClose}><div className="modal wide" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">ADMIN CONSOLE · LOCAL</p><h3>Platform overview</h3><p className="muted small">Backend-authorized analytics for this local instance.</p></div><button className="close-button" onClick={onClose}>×</button></div>{overview.isError ? <div className="alert error">Administrator access is required.</div> : <><div className="admin-metrics">{Object.entries(metrics).map(([key, value]) => <div className="admin-metric" key={key}><span>{key.replace(/_/g, " ")}</span><strong>{value}</strong></div>)}</div><div className="admin-section"><h4>Users</h4>{users.data?.users.map((user) => <div className="admin-row" key={user.id}><span><strong>{user.full_name}</strong> · {user.email}</span><small>{user.is_admin ? "Admin" : "Member"} · {user.is_active ? "Active" : "Inactive"}</small></div>)}</div><div className="admin-section"><h4>Audit log</h4>{audit.data?.audit_logs.length ? audit.data.audit_logs.map((entry) => <div className="admin-row" key={entry.id}><span>{entry.action}</span><small>{String(entry.created_at ?? "")}</small></div>) : <p className="muted small">No audit events recorded yet.</p>}</div></>}</div></div>;
}

function DeploymentsModal({ user, accounts, onAuth, onClose }: { user: CurrentUser | null; accounts: Array<import("./api").CloudAccount>; onAuth: () => void; onClose: () => void }) {
  const deployments = useQuery({ queryKey: ["deployments"], queryFn: getDeployments, enabled: Boolean(user) });
  const [message, setMessage] = useState("");
  const [working, setWorking] = useState(false);
  const [liveOutput, setLiveOutput] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [providerFilter, setProviderFilter] = useState("all");
  const realAccounts = accounts.filter((account) => account.status === "connected" && account.metadata.simulation === false);
  const visibleDeployments = (deployments.data?.deployments ?? []).filter((deployment) =>
    (statusFilter === "all" || deployment.status === statusFilter) &&
    (providerFilter === "all" || deployment.provider === providerFilter),
  );
  async function simulatePlan() {
    if (!user) return onAuth();
    setWorking(true);
    try {
      const result = await createDeploymentPlan("cloudpilot-demo", { provider: "gcp", region: "asia-south1", vm_count: 2, machine_type: "e2-medium", vpc_cidr: "10.0.0.0/16" });
      setMessage("Plan created. Explicit approval is required before simulation.");
      deployments.refetch();
    } finally { setWorking(false); }
  }
  async function approve(id: string) {
    setWorking(true);
    try { await approveDeployment(id); setMessage("Simulated deployment completed. No cloud API was called."); deployments.refetch(); }
    finally { setWorking(false); }
  }
  async function destroy(id: string) {
    if (!window.confirm("Destroy this simulated deployment?")) return;
    await destroyDeployment(id); setMessage("Simulated destroy completed."); deployments.refetch();
  }
  async function runTerraformPlan(id: string, provider: string) {
    const account = realAccounts.find((item) => item.provider === provider);
    if (!account) {
      setMessage("A real verified account for this provider is required.");
      return;
    }
    setWorking(true);
    setLiveOutput([]);
    try {
      await Promise.all([
        streamDeploymentLogs(id, (line) => setLiveOutput((current) => [...current, line])),
        executeDeploymentTerraformPlan(id, account.id),
      ]);
      setMessage("Terraform plan completed. No resources were applied.");
      deployments.refetch();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Terraform plan failed.");
      deployments.refetch();
    } finally { setWorking(false); }
  }
  return <div className="modal-backdrop" onClick={onClose}><div className="modal wide" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">DEPLOYMENTS · SIMULATION</p><h3>Deployment history</h3><p className="muted small">Local lifecycle only. No provider credentials or resources are used.</p></div><button className="close-button" onClick={onClose}>×</button></div>{message && <div className="alert success">{message}</div>}{!user ? <div className="empty-chart architecture-empty"><Boxes size={40} /><strong>Sign in to manage deployments</strong><span>Deployment history is scoped to your local workspace.</span><button className="button" onClick={onAuth}>Sign in</button></div> : <><div className="deployment-toolbar"><button className="button" disabled={working} onClick={simulatePlan}>Create simulated plan</button><select value={providerFilter} onChange={(event) => setProviderFilter(event.target.value)}><option value="all">All providers</option><option value="aws">AWS</option><option value="gcp">GCP</option><option value="azure">Azure</option></select><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="all">All statuses</option><option value="awaiting-approval">Awaiting approval</option><option value="planning">Planning</option><option value="plan-succeeded">Plan succeeded</option><option value="plan-failed">Plan failed</option><option value="successful-simulated">Simulated success</option></select></div><div className="deployment-list">{visibleDeployments.map((deployment) => <div className="deployment-row" key={deployment.id}><div><strong>{String(deployment.configuration.name ?? "CloudPilot deployment")}</strong><span>{deployment.provider.toUpperCase()} · {deployment.resources.length} resources</span><small>{deployment.logs.length ? deployment.logs[deployment.logs.length - 1].message : "No deployment events yet."}</small></div><span className={`deployment-status ${deployment.status}`}>{deployment.status}</span>{deployment.status === "awaiting-approval" && <button className="text-button compact" onClick={() => approve(deployment.id)}>Approve</button>}{deployment.status === "awaiting-approval" && realAccounts.some((account) => account.provider === deployment.provider) && <button className="text-button compact" disabled={working} onClick={() => runTerraformPlan(deployment.id, deployment.provider)}>Real plan</button>}{deployment.status === "plan-failed" && realAccounts.some((account) => account.provider === deployment.provider) && <button className="text-button compact" disabled={working} onClick={() => runTerraformPlan(deployment.id, deployment.provider)}>Retry plan</button>}{deployment.status === "successful-simulated" && <button className="text-button compact danger" onClick={() => destroy(deployment.id)}>Destroy</button>}</div>)}{(!deployments.data || visibleDeployments.length === 0) && <div className="empty-account">No deployments match selected filters.</div>}</div>{liveOutput.length > 0 && <pre className="terraform-output">{liveOutput.join("\n")}</pre>}</>}</div></div>;
}

function TerraformModal({ onClose }: { onClose: () => void }) {
  const [provider, setProvider] = useState("gcp");
  const [preview, setPreview] = useState<Awaited<ReturnType<typeof generateTerraformPreview>> | null>(null);
  const [selectedFile, setSelectedFile] = useState("main.tf");
  async function generate() {
    setPreview(await generateTerraformPreview({ provider, region: provider === "aws" ? "ap-south-1" : provider === "azure" ? "Central India" : "asia-south1", vm_count: 2, machine_type: provider === "aws" ? "t3.micro" : provider === "azure" ? "Standard_B1s" : "e2-medium", vpc_cidr: "10.0.0.0/16" }));
  }
  return <div className="modal-backdrop" onClick={onClose}><div className="modal wide terraform-modal" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">TERRAFORM GENERATOR · LOCAL</p><h3>Configuration preview</h3><p className="muted small">Generated files are static previews. No provider plan, init, or apply is executed.</p></div><button className="close-button" onClick={onClose}>×</button></div><div className="terraform-toolbar"><select value={provider} onChange={(event) => setProvider(event.target.value)}><option value="aws">AWS</option><option value="gcp">GCP</option><option value="azure">Azure</option></select><button className="button" onClick={generate}>Generate Terraform</button></div>{preview ? <div className="terraform-preview"><div className="file-tabs">{Object.keys(preview.files).map((file) => <button className={selectedFile === file ? "file-tab active" : "file-tab"} key={file} onClick={() => setSelectedFile(file)}>{file}</button>)}</div><pre>{preview.files[selectedFile]}</pre><div className="alert success">{preview.message}</div></div> : <div className="empty-chart architecture-empty"><Settings size={40} /><strong>Generate provider-specific files</strong><span>Choose a provider to preview main.tf, variables.tf, outputs.tf, and tfvars.</span><button className="button secondary" onClick={generate}>Generate local files</button></div>}</div></div>;
}

function ArchitectureModal({ onClose }: { onClose: () => void }) {
  const [vmCount, setVmCount] = useState(2);
  const [database, setDatabase] = useState(true);
  const [architecture, setArchitecture] = useState<Architecture | null>(null);
  const [selectedNode, setSelectedNode] = useState<Architecture["nodes"][number] | null>(null);
  const [error, setError] = useState("");
  async function generate() {
    setError("");
    try {
      const result = await generateArchitecture({ provider: "gcp", region: "asia-south1", vm_count: vmCount, machine_type: "e2-medium", vpc_cidr: "10.0.0.0/16", storage_gb: 100, database_enabled: database, template_slug: "web-hosting" });
      setArchitecture(result);
      setSelectedNode(result.nodes[0] ?? null);
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : "Architecture preview could not be generated.");
    }
  }
  const nodes: Node[] = (architecture?.nodes ?? []).map((node, index) => ({ id: node.id, position: { x: (index % 4) * 190 + 30, y: Math.floor(index / 4) * 125 + 30 }, data: { label: <div><strong>{node.label}</strong><small>{node.type}</small></div> }, className: `topology-node topology-${node.type}`, type: "default" }));
  const edges: Edge[] = (architecture?.edges ?? []).map((edge, index) => ({ id: `edge-${index}`, source: edge.source, target: edge.target, animated: true }));
  return <div className="modal-backdrop" onClick={onClose}><div className="modal architecture-modal" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">TOPOLOGY BUILDER · LOCAL PREVIEW</p><h3>Infrastructure architecture</h3><p className="muted small">Generated topology only. No resources exist in a cloud account.</p></div><button className="close-button" onClick={onClose}>×</button></div><div className="architecture-controls"><label>VM count<input type="number" min="1" max="20" value={vmCount} onChange={(event) => setVmCount(Math.max(1, Number(event.target.value)))} /></label><label className="checkbox"><input type="checkbox" checked={database} onChange={(event) => setDatabase(event.target.checked)} /> Include database</label><button className="button" onClick={generate}>Generate topology</button></div>{error && <div className="alert error">{error}</div>}{architecture ? <><div className="topology-meta"><span><strong>{architecture.nodes.length}</strong> components</span><span><strong>{architecture.edges.length}</strong> connections</span><span className="topology-legend"><i className="legend-network" /> Network <i className="legend-compute" /> Compute <i className="legend-data" /> Data</span></div><div className="topology-workspace"><div className="flow-canvas"><ReactFlow nodes={nodes} edges={edges} fitView onNodeClick={(_, node) => setSelectedNode(architecture.nodes.find((item) => item.id === node.id) ?? null)}><Background /><Controls /><MiniMap /></ReactFlow></div><aside className="topology-inspector">{selectedNode ? <><span className="inspector-kicker">SELECTED COMPONENT</span><h4>{selectedNode.label}</h4><span className="node-type">{selectedNode.type}</span><div className="inspector-details">{Object.entries(selectedNode.details).map(([key, value]) => <div key={key}><span>{key.replace(/_/g, " ")}</span><strong>{String(value)}</strong></div>)}</div></> : <div className="empty-account">Select a component to inspect it.</div>}</aside></div></> : <div className="empty-chart architecture-empty"><ShieldCheck size={40} /><strong>Generate your architecture</strong><span>Nodes and relationships will reflect your selected configuration.</span><button className="button secondary" onClick={generate}>Generate local topology</button></div>}</div></div>;
}

function PricingModal({ onClose }: { onClose: () => void }) {
  const [vmCount, setVmCount] = useState(2);
  const [storageGb, setStorageGb] = useState(100);
  const [database, setDatabase] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [estimates, setEstimates] = useState<Awaited<ReturnType<typeof comparePricing>>["estimates"]>([]);
  async function calculate() {
    setLoading(true);
    setError("");
    try { setEstimates((await comparePricing({ vm_count: vmCount, storage_gb: storageGb, database_enabled: database })).estimates); }
    catch (calculationError) { setError(calculationError instanceof Error ? calculationError.message : "Cost estimate could not be calculated."); }
    finally { setLoading(false); }
  }
  const lowestMonthly = estimates.length ? Math.min(...estimates.map((estimate) => estimate.monthly)) : null;
  return <div className="modal-backdrop" onClick={onClose}><div className="modal wide" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">FINOPS · LOCAL FIXTURES</p><h3>Compare cloud costs</h3><p className="muted small">Planning estimates only. Not live provider prices, invoices, or commitments.</p></div><button className="close-button" onClick={onClose}>×</button></div><div className="pricing-controls"><label>VM count<input type="number" min="1" max="100" value={vmCount} onChange={(event) => setVmCount(Math.max(1, Number(event.target.value)))} /></label><label>Storage (GB)<input type="number" min="1" value={storageGb} onChange={(event) => setStorageGb(Math.max(1, Number(event.target.value)))} /></label><label className="checkbox"><input type="checkbox" checked={database} onChange={(event) => setDatabase(event.target.checked)} /> Include database</label><button className="button" onClick={calculate}>{loading ? "Calculating..." : "Calculate estimate"}</button></div>{error && <div className="alert error">{error}</div>}{estimates.length > 0 && <><div className="finops-summary"><div><span>Lowest monthly estimate</span><strong>${lowestMonthly}</strong></div><div><span>Compared providers</span><strong>{estimates.length}</strong></div><div><span>Annual range</span><strong>${Math.min(...estimates.map((estimate) => estimate.annual))}–${Math.max(...estimates.map((estimate) => estimate.annual))}</strong></div></div><div className="pricing-grid">{estimates.map((estimate) => <div className={`price-card${estimate.monthly === lowestMonthly ? " recommended" : ""}`} key={estimate.provider}>{estimate.monthly === lowestMonthly && <span className="recommended-badge">LOWEST ESTIMATE</span>}<span className="eyebrow">{estimate.provider.toUpperCase()}</span><strong>${estimate.monthly}<small>/month</small></strong><span>{estimate.region} · ${estimate.hourly}/hour</span><div className="price-line"><span>Compute</span><b>${estimate.breakdown.compute}</b></div><div className="price-line"><span>Storage</span><b>${estimate.breakdown.storage}</b></div><div className="price-line"><span>Database</span><b>${estimate.breakdown.database}</b></div><div className="price-line"><span>Networking</span><b>${estimate.breakdown.networking}</b></div><details><summary>Assumptions</summary><ul>{estimate.assumptions.map((assumption) => <li key={assumption}>{assumption}</li>)}</ul></details></div>)}</div><div className="alert success">Fixture source: local pricing data · 730 hours/month · discounts and taxes excluded.</div></>}</div></div>;
}

function TemplateWizard({ templates, onClose }: { templates: InfrastructureTemplate[]; onClose: () => void }) {
  const [selected, setSelected] = useState<InfrastructureTemplate | null>(null);
  const [templateQuery, setTemplateQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [step, setStep] = useState(1);
  const [provider, setProvider] = useState("gcp");
  const [region, setRegion] = useState("asia-south1");
  const [vmCount, setVmCount] = useState(1);
  const [machineType, setMachineType] = useState("e2-medium");
  const [vpcCidr, setVpcCidr] = useState("10.0.0.0/16");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const categories = [...new Set(templates.map((template) => template.category))];
  const visibleTemplates = templates.filter((template) => {
    const searchText = `${template.name} ${template.description} ${template.category} ${template.resources.join(" ")}`.toLowerCase();
    return (category === "all" || template.category === category) && searchText.includes(templateQuery.toLowerCase());
  });
  if (!selected) {
    return <div className="modal-backdrop" onClick={onClose}><div className="modal wide" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">INFRASTRUCTURE BUILDER</p><h3>Choose a template</h3><p className="muted small">Start from a validated blueprint, then tailor it to your provider.</p></div><button className="close-button" onClick={onClose}>×</button></div><div className="marketplace-toolbar"><label className="global-search"><Search size={15} /><input value={templateQuery} onChange={(event) => setTemplateQuery(event.target.value)} placeholder="Search blueprints" aria-label="Search templates" /></label><select value={category} onChange={(event) => setCategory(event.target.value)} aria-label="Filter template category"><option value="all">All categories</option>{categories.map((item) => <option key={item} value={item}>{item}</option>)}</select></div><div className="template-grid">{visibleTemplates.map((template) => <button className="template-card" key={template.slug} onClick={() => { setSelected(template); setError(""); }}><div className="template-card-top"><div className="template-icon"><Boxes size={20} /></div><span className="template-category">{template.category}</span></div><strong>{template.name}</strong><span>{template.description}</span><small>{template.difficulty} · {template.estimated_minutes} min · {template.resources.length} resources</small><div className="template-providers">{template.providers.map((item) => <span key={item}>{item.toUpperCase()}</span>)}</div></button>)}{visibleTemplates.length === 0 && <div className="discovery-empty"><Boxes size={28} /><strong>No matching blueprints</strong><span>Try another search or category.</span></div>}</div></div></div>;
  }
  async function save() {
    if (!selected) return;
    setError("");
    try {
      await saveInfrastructureConfiguration(selected.slug, { provider, region, vm_count: vmCount, machine_type: machineType, vpc_cidr: vpcCidr });
      setMessage("Configuration saved locally. No Terraform or cloud API was executed.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Configuration could not be saved.");
    }
  }
  return <div className="modal-backdrop" onClick={onClose}><div className="modal wide" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">CONFIGURATION WIZARD · STEP {step} OF 4</p><h3>{selected.name}</h3></div><button className="close-button" onClick={onClose}>×</button></div><div className="stepper"><span className={step >= 1 ? "done" : ""}>01 <b>Provider</b></span><span className={step >= 2 ? "done" : ""}>02 <b>Compute</b></span><span className={step >= 3 ? "done" : ""}>03 <b>Network</b></span><span className={step >= 4 ? "done" : ""}>04 <b>Review</b></span></div>{step === 1 && <div className="wizard-form"><label>Cloud provider<select value={provider} onChange={(event) => setProvider(event.target.value)}>{selected.providers.map((item) => <option key={item} value={item}>{item.toUpperCase()}</option>)}</select></label><label>Region<input value={region} onChange={(event) => setRegion(event.target.value)} required /></label><p className="form-hint">Choose provider and deployment region. Credentials are not requested here.</p></div>}{step === 2 && <div className="wizard-form"><label>Virtual machine count<input type="number" min={1} max={20} value={vmCount} onChange={(event) => setVmCount(Math.max(1, Number(event.target.value)))} /></label><label>Machine type<input value={machineType} onChange={(event) => setMachineType(event.target.value)} required /></label><label>Operating system<select><option>Ubuntu 22.04</option><option>Amazon Linux 2023</option><option>Windows Server 2022</option></select></label></div>}{step === 3 && <div className="wizard-form"><label>VPC/VNet CIDR<input value={vpcCidr} onChange={(event) => setVpcCidr(event.target.value)} required /></label><label>Public subnets<input defaultValue="10.0.1.0/24" /></label><label>Private subnets<input defaultValue="10.0.2.0/24" /></label><div className="security-note"><ShieldCheck size={17} /> SSH access is restricted by default.</div></div>}{step === 4 && <div className="review"><div className="review-row"><span>Template</span><strong>{selected.name}</strong></div><div className="review-row"><span>Provider</span><strong>{provider.toUpperCase()} · {region}</strong></div><div className="review-row"><span>Compute</span><strong>{vmCount} × {machineType}</strong></div><div className="review-row"><span>Network</span><strong>{vpcCidr}</strong></div><div className="alert success">Local configuration only. Deployment approval and Terraform generation are separate upcoming phases.</div>{message && <div className="alert success">{message}</div>}{error && <div className="alert error">{error}</div>}</div>}<div className="wizard-actions"><button className="button secondary" onClick={() => step === 1 ? setSelected(null) : setStep(step - 1)}>{step === 1 ? "Back to templates" : "Back"}</button>{step < 4 ? <button className="button" onClick={() => { setError(""); setStep(step + 1); }}>Continue</button> : <button className="button" onClick={save} disabled={Boolean(message)}>Save configuration</button>}</div></div></div>;
}

function Metric({ label, value, detail, tone = "info" }: { label: string; value: string | number; detail: string; tone?: "success" | "info" | "violet" }) {
  return <div className={`metric-card tone-${tone}`}><span>{label}</span><strong>{value}</strong><small>{detail}</small><i className="metric-spark" /></div>;
}

function Action({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return <div className="action-card"><div className="action-icon">{icon}</div><strong>{title}</strong><span>{text}</span></div>;
}

function AuthPage({ mode, onChangeMode, onComplete }: { mode: AuthMode; onChangeMode: (mode: AuthMode) => void; onComplete: () => void }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setLoading(true);
    try { if (mode === "login") await login(email, password); else await register(fullName, email, password); onComplete(); }
    catch (err) { setError(err instanceof Error ? err.message : "Request failed"); }
    finally { setLoading(false); }
  }
  return <div className="auth-page"><div className="auth-card"><div className="brand"><span className="brand-mark">C</span> CloudPilot</div><p className="eyebrow">LOCAL ACCOUNT</p><h1>{mode === "login" ? "Welcome back" : "Create your workspace"}</h1><p className="muted">{mode === "login" ? "Sign in to your local CloudPilot workspace." : "No email provider or cloud account is required."}</p>{error && <div className="alert error">{error}</div>}<form onSubmit={submit}>{mode === "register" && <label>Full name<input value={fullName} onChange={(e) => setFullName(e.target.value)} required minLength={2} /></label>}<label>Email address<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label><label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} /></label><button className="button full" disabled={loading}>{loading ? "Working..." : mode === "login" ? "Sign in" : "Create account"}</button></form><button className="text-button" onClick={() => onChangeMode(mode === "login" ? "register" : "login")}>{mode === "login" ? "Create a local account" : "Already have an account? Sign in"}</button><button className="text-button muted" onClick={onComplete}>Return to demo</button></div></div>;
}

export default App;
