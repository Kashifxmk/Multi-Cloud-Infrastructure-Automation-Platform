import { FormEvent, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, Boxes, Cloud, LayoutDashboard, LogIn, Menu, Settings, ShieldCheck, UserPlus } from "lucide-react";
import { approveDeployment, Architecture, comparePricing, connectCloudAccount, createDeploymentPlan, CurrentUser, destroyDeployment, disconnectCloudAccount, generateArchitecture, generateTerraformPreview, getAdminAudit, getAdminOverview, getAdminUsers, getCloudAccounts, getCurrentUser, getDashboard, getDeployments, getTemplates, login, logout, register, saveInfrastructureConfiguration, verifyCloudAccount, InfrastructureTemplate } from "./api";
import ReactFlow, { Background, Controls, Edge, MiniMap, Node, useEdgesState, useNodesState } from "reactflow";

type AuthMode = "login" | "register";

function App() {
  const [authMode, setAuthMode] = useState<AuthMode | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
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
  return <DashboardPage user={currentUser.data ?? null} onAuth={() => setAuthMode("login")} onLogout={signedOut} menuOpen={menuOpen} setMenuOpen={setMenuOpen} />;
}

function DashboardPage({
  user,
  onAuth,
  onLogout,
  menuOpen,
  setMenuOpen,
}: {
  user: CurrentUser | null;
  onAuth: () => void;
  onLogout: () => Promise<void>;
  menuOpen: boolean;
  setMenuOpen: (open: boolean) => void;
}) {
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
  const accounts = useQuery({ queryKey: ["cloud-accounts"], queryFn: getCloudAccounts });
  const [accountsOpen, setAccountsOpen] = useState(false);
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

  return (
    <div className="app-shell">
      <aside className={menuOpen ? "sidebar open" : "sidebar"}>
        <div className="brand"><span className="brand-mark">C</span> CloudPilot</div>
        <nav>
          <a className="active"><LayoutDashboard size={18} /> Overview</a>
          <a onClick={() => setAccountsOpen(true)}><Cloud size={18} /> Cloud accounts</a>
          <a onClick={() => setTemplatesOpen(true)}><Boxes size={18} /> Infrastructure</a>
          <a onClick={() => setPricingOpen(true)}><BarChart3 size={18} /> Cost management</a>
          <a onClick={() => setArchitectureOpen(true)}><ShieldCheck size={18} /> Architecture</a>
          <a onClick={() => setTerraformOpen(true)}><Settings size={18} /> Terraform preview</a>
          <a onClick={() => setDeploymentsOpen(true)}><Boxes size={18} /> Deployments</a>
          {user?.is_admin && <a onClick={() => setAdminOpen(true)}><ShieldCheck size={18} /> Admin console</a>}
          <a><Settings size={18} /> Settings</a>
        </nav>
        <div className="sidebar-footer">LOCAL MVP<br /><span>No cloud account connected</span></div>
      </aside>
      <main className="content">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setMenuOpen(!menuOpen)} aria-label="Open menu"><Menu /></button>
          <div><p className="eyebrow">Workspace / {user ? user.full_name : "Demo"}</p><h1>Overview</h1></div>
          <div className="top-actions">{user ? <><span className="user-chip">{user.email}</span><button className="button secondary" onClick={onLogout}>Sign out</button></> : <button className="button secondary" onClick={onAuth}><LogIn size={16} /> Sign in</button>}<button className="button secondary" onClick={() => user ? setAccountsOpen(true) : onAuth()}><Cloud size={16} /> Accounts</button></div>
        </header>
        <section className="welcome">
          <div><p className="eyebrow">{user ? "LOCAL WORKSPACE" : "LOCAL DEMO ENVIRONMENT"}</p><h2>Infrastructure, without the guesswork.</h2><p>{user ? `Welcome back, ${user.full_name}. Your local workspace is ready.` : "Explore the CloudPilot workflow with safe local data. Sign in to save accounts and configurations."}</p></div>
          <div className="welcome-actions"><button className="button secondary" onClick={() => setTemplatesOpen(true)}><Boxes size={16} /> Browse templates</button><button className="button secondary" onClick={() => setPricingOpen(true)}><BarChart3 size={16} /> Compare costs</button><button className="button secondary" onClick={() => setArchitectureOpen(true)}><ShieldCheck size={16} /> Architecture</button><button className="button" onClick={() => user ? setAccountsOpen(true) : onAuth()}><Cloud size={16} /> {user ? "Connect account" : "Sign in to connect"}</button></div>
        </section>
        {dashboard.isError && <div className="alert error">The API is unavailable. Start the backend with <code>python -m backend.run</code>.</div>}
        <section className="metrics">
          <Metric label="Cloud accounts" value={metrics?.cloud_accounts ?? "—"} detail="No connections yet" />
          <Metric label="Active deployments" value={metrics?.deployments ?? "—"} detail="Empty state" />
          <Metric label="Active resources" value={metrics?.active_resources ?? "—"} detail="No live data" />
          <Metric label="Estimated monthly spend" value={metrics?.monthly_spend == null ? "—" : `$${metrics.monthly_spend}`} detail="Connect an account to estimate" />
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
        {accountsOpen && user && <div className="modal-backdrop" onClick={() => setAccountsOpen(false)}><div className="modal" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">SIMULATED CONNECTIONS</p><h3>Cloud accounts</h3></div><button className="close-button" onClick={() => setAccountsOpen(false)}>×</button></div><p className="muted small">No passwords or permanent keys are collected. These connections are local simulations.</p>{accountMessage && <div className="alert success">{accountMessage}</div>}<div className="account-list">{accounts.data?.accounts.map((account) => <div className="account-row" key={account.id}><div className={`provider-dot ${account.provider}`}>{account.provider[0].toUpperCase()}</div><div><strong>{account.display_name}</strong><span>{account.provider.toUpperCase()} · {account.metadata.account_identifier}</span></div><span className="account-status">{account.status}</span><button className="text-button compact" onClick={async () => { const result = await verifyCloudAccount(account.id); setAccountMessage(result.message); accounts.refetch(); }}>Verify</button><button className="text-button compact danger" onClick={async () => { await disconnectCloudAccount(account.id); accounts.refetch(); }}>Disconnect</button></div>)}{(!accounts.data || accounts.data.accounts.length === 0) && <div className="empty-account">No simulated accounts connected.</div>}</div><form className="account-form" onSubmit={async (event) => { event.preventDefault(); await connectCloudAccount(provider, displayName, identifier); setDisplayName(""); setIdentifier(""); setAccountMessage("Simulated connection verified successfully."); accounts.refetch(); }}><h4>Connect a simulated account</h4><select value={provider} onChange={(event) => setProvider(event.target.value)}><option value="aws">AWS</option><option value="gcp">Google Cloud</option><option value="azure">Microsoft Azure</option></select><input placeholder="Account name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} required minLength={2} /><input placeholder="Account / project / subscription ID" value={identifier} onChange={(event) => setIdentifier(event.target.value)} required minLength={2} /><button className="button">Run simulated verification</button></form></div></div>}
        {templatesOpen && <TemplateWizard templates={templates.data?.templates ?? []} onClose={() => setTemplatesOpen(false)} />}
        {pricingOpen && <PricingModal onClose={() => setPricingOpen(false)} />}
        {architectureOpen && <ArchitectureModal onClose={() => setArchitectureOpen(false)} />}
        {terraformOpen && <TerraformModal onClose={() => setTerraformOpen(false)} />}
        {deploymentsOpen && <DeploymentsModal user={user} onAuth={onAuth} onClose={() => setDeploymentsOpen(false)} />}
        {adminOpen && user?.is_admin && <AdminModal onClose={() => setAdminOpen(false)} />}
        <section className="panel quick-actions"><div className="panel-heading"><div><h3>Start with CloudPilot</h3><p>A guided path from idea to infrastructure plan.</p></div></div><div className="action-cards"><Action icon={<Cloud />} title="Connect an account" text="Simulate AWS, GCP or Azure connection." /><Action icon={<Boxes />} title="Browse templates" text="Choose a ready-made infrastructure blueprint." /><Action icon={<BarChart3 />} title="Compare costs" text="Review provider estimates before deployment." /></div></section>
      </main>
    </div>
  );
}

function AdminModal({ onClose }: { onClose: () => void }) {
  const overview = useQuery({ queryKey: ["admin-overview"], queryFn: getAdminOverview });
  const users = useQuery({ queryKey: ["admin-users"], queryFn: getAdminUsers });
  const audit = useQuery({ queryKey: ["admin-audit"], queryFn: getAdminAudit });
  const metrics = overview.data?.metrics ?? {};
  return <div className="modal-backdrop" onClick={onClose}><div className="modal wide" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">ADMIN CONSOLE · LOCAL</p><h3>Platform overview</h3><p className="muted small">Backend-authorized analytics for this local instance.</p></div><button className="close-button" onClick={onClose}>×</button></div>{overview.isError ? <div className="alert error">Administrator access is required.</div> : <><div className="admin-metrics">{Object.entries(metrics).map(([key, value]) => <div className="admin-metric" key={key}><span>{key.replace(/_/g, " ")}</span><strong>{value}</strong></div>)}</div><div className="admin-section"><h4>Users</h4>{users.data?.users.map((user) => <div className="admin-row" key={user.id}><span><strong>{user.full_name}</strong> · {user.email}</span><small>{user.is_admin ? "Admin" : "Member"} · {user.is_active ? "Active" : "Inactive"}</small></div>)}</div><div className="admin-section"><h4>Audit log</h4>{audit.data?.audit_logs.length ? audit.data.audit_logs.map((entry) => <div className="admin-row" key={entry.id}><span>{entry.action}</span><small>{String(entry.created_at ?? "")}</small></div>) : <p className="muted small">No audit events recorded yet.</p>}</div></>}</div></div>;
}

function DeploymentsModal({ user, onAuth, onClose }: { user: CurrentUser | null; onAuth: () => void; onClose: () => void }) {
  const deployments = useQuery({ queryKey: ["deployments"], queryFn: getDeployments, enabled: Boolean(user) });
  const [message, setMessage] = useState("");
  const [working, setWorking] = useState(false);
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
  return <div className="modal-backdrop" onClick={onClose}><div className="modal wide" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">DEPLOYMENTS · SIMULATION</p><h3>Deployment history</h3><p className="muted small">Local lifecycle only. No provider credentials or resources are used.</p></div><button className="close-button" onClick={onClose}>×</button></div>{message && <div className="alert success">{message}</div>}{!user ? <div className="empty-chart architecture-empty"><Boxes size={40} /><strong>Sign in to manage deployments</strong><span>Deployment history is scoped to your local workspace.</span><button className="button" onClick={onAuth}>Sign in</button></div> : <><div className="deployment-toolbar"><button className="button" disabled={working} onClick={simulatePlan}>Create simulated plan</button></div><div className="deployment-list">{deployments.data?.deployments.map((deployment) => <div className="deployment-row" key={deployment.id}><div><strong>{String(deployment.configuration.name ?? "CloudPilot deployment")}</strong><span>{deployment.provider.toUpperCase()} · {deployment.resources.length} resources</span></div><span className={`deployment-status ${deployment.status}`}>{deployment.status}</span>{deployment.status === "awaiting-approval" && <button className="text-button compact" onClick={() => approve(deployment.id)}>Approve</button>}{deployment.status === "successful-simulated" && <button className="text-button compact danger" onClick={() => destroy(deployment.id)}>Destroy</button>}</div>)}{(!deployments.data || deployments.data.deployments.length === 0) && <div className="empty-account">No deployments yet. Create a simulated plan to begin.</div>}</div></>}</div></div>;
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
  async function generate() {
    setArchitecture(await generateArchitecture({ provider: "gcp", region: "asia-south1", vm_count: vmCount, machine_type: "e2-medium", vpc_cidr: "10.0.0.0/16", storage_gb: 100, database_enabled: database, template_slug: "web-hosting" }));
  }
  const nodes: Node[] = (architecture?.nodes ?? []).map((node, index) => ({ id: node.id, position: { x: (index % 4) * 190 + 30, y: Math.floor(index / 4) * 125 + 30 }, data: { label: <div><strong>{node.label}</strong><small>{node.type}</small></div> }, type: "default" }));
  const edges: Edge[] = (architecture?.edges ?? []).map((edge, index) => ({ id: `edge-${index}`, source: edge.source, target: edge.target, animated: true }));
  return <div className="modal-backdrop" onClick={onClose}><div className="modal architecture-modal" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">ARCHITECTURE BUILDER · LOCAL</p><h3>Infrastructure architecture</h3><p className="muted small">Generated from a configuration preview. No resources exist in a cloud account.</p></div><button className="close-button" onClick={onClose}>×</button></div><div className="architecture-controls"><label>VM count<input type="number" min="1" max="20" value={vmCount} onChange={(event) => setVmCount(Number(event.target.value))} /></label><label className="checkbox"><input type="checkbox" checked={database} onChange={(event) => setDatabase(event.target.checked)} /> Include database</label><button className="button" onClick={generate}>Generate diagram</button></div>{architecture ? <div className="flow-canvas"><ReactFlow nodes={nodes} edges={edges} fitView><Background /><Controls /><MiniMap /></ReactFlow></div> : <div className="empty-chart architecture-empty"><ShieldCheck size={40} /><strong>Generate your architecture</strong><span>Nodes and relationships will reflect your selected configuration.</span><button className="button secondary" onClick={generate}>Generate local diagram</button></div>}</div></div>;
}

function PricingModal({ onClose }: { onClose: () => void }) {
  const [vmCount, setVmCount] = useState(2);
  const [storageGb, setStorageGb] = useState(100);
  const [database, setDatabase] = useState(true);
  const [loading, setLoading] = useState(false);
  const [estimates, setEstimates] = useState<Awaited<ReturnType<typeof comparePricing>>["estimates"]>([]);
  async function calculate() {
    setLoading(true);
    try { setEstimates((await comparePricing({ vm_count: vmCount, storage_gb: storageGb, database_enabled: database })).estimates); }
    finally { setLoading(false); }
  }
  return <div className="modal-backdrop" onClick={onClose}><div className="modal wide" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">COST MANAGEMENT · LOCAL FIXTURES</p><h3>Compare cloud costs</h3><p className="muted small">Sample estimates only. These are not live provider prices or invoices.</p></div><button className="close-button" onClick={onClose}>×</button></div><div className="pricing-controls"><label>VM count<input type="number" min="1" max="100" value={vmCount} onChange={(event) => setVmCount(Number(event.target.value))} /></label><label>Storage (GB)<input type="number" min="1" value={storageGb} onChange={(event) => setStorageGb(Number(event.target.value))} /></label><label className="checkbox"><input type="checkbox" checked={database} onChange={(event) => setDatabase(event.target.checked)} /> Include database</label><button className="button" onClick={calculate}>{loading ? "Calculating..." : "Calculate estimate"}</button></div>{estimates.length > 0 && <><div className="pricing-grid">{estimates.map((estimate) => <div className="price-card" key={estimate.provider}><span className="eyebrow">{estimate.provider.toUpperCase()}</span><strong>${estimate.monthly}<small>/month</small></strong><span>{estimate.region}</span><div className="price-line"><span>Compute</span><b>${estimate.breakdown.compute}</b></div><div className="price-line"><span>Storage</span><b>${estimate.breakdown.storage}</b></div><div className="price-line"><span>Database</span><b>${estimate.breakdown.database}</b></div><div className="price-line"><span>Networking</span><b>${estimate.breakdown.networking}</b></div></div>)}</div><div className="alert success">Fixture source: local pricing data · 730 hours/month · discounts and taxes excluded.</div></>}</div></div>;
}

function TemplateWizard({ templates, onClose }: { templates: InfrastructureTemplate[]; onClose: () => void }) {
  const [selected, setSelected] = useState<InfrastructureTemplate | null>(null);
  const [step, setStep] = useState(1);
  const [provider, setProvider] = useState("gcp");
  const [region, setRegion] = useState("asia-south1");
  const [vmCount, setVmCount] = useState(1);
  const [machineType, setMachineType] = useState("e2-medium");
  const [vpcCidr, setVpcCidr] = useState("10.0.0.0/16");
  const [message, setMessage] = useState("");
  if (!selected) {
    return <div className="modal-backdrop" onClick={onClose}><div className="modal wide" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">INFRASTRUCTURE BUILDER</p><h3>Choose a template</h3><p className="muted small">Every template produces a saved, provider-neutral configuration.</p></div><button className="close-button" onClick={onClose}>×</button></div><div className="template-grid">{templates.map((template) => <button className="template-card" key={template.slug} onClick={() => setSelected(template)}><div className="template-icon"><Boxes size={20} /></div><strong>{template.name}</strong><span>{template.description}</span><small>{template.difficulty} · {template.estimated_minutes} min · {template.resources.length} resources</small></button>)}</div></div></div>;
  }
  async function save() {
    if (!selected) return;
    const template = selected;
    await saveInfrastructureConfiguration(template.slug, { provider, region, vm_count: vmCount, machine_type: machineType, vpc_cidr: vpcCidr });
    setMessage("Configuration saved locally. No Terraform or cloud API was executed.");
    setStep(4);
  }
  return <div className="modal-backdrop" onClick={onClose}><div className="modal wide" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">CONFIGURATION WIZARD · STEP {step} OF 4</p><h3>{selected.name}</h3></div><button className="close-button" onClick={onClose}>×</button></div><div className="stepper"><span className={step >= 1 ? "done" : ""}>1 Provider</span><span className={step >= 2 ? "done" : ""}>2 Compute</span><span className={step >= 3 ? "done" : ""}>3 Network</span><span className={step >= 4 ? "done" : ""}>4 Review</span></div>{step === 1 && <div className="wizard-form"><label>Cloud provider<select value={provider} onChange={(event) => setProvider(event.target.value)}>{selected.providers.map((item) => <option key={item} value={item}>{item.toUpperCase()}</option>)}</select></label><label>Region<input value={region} onChange={(event) => setRegion(event.target.value)} required /></label><p className="form-hint">Provider-specific options will be expanded in the next wizard iteration.</p></div>}{step === 2 && <div className="wizard-form"><label>Virtual machine count<input type="number" min={1} max={20} value={vmCount} onChange={(event) => setVmCount(Number(event.target.value))} /></label><label>Machine type<input value={machineType} onChange={(event) => setMachineType(event.target.value)} required /></label><label>Operating system<select><option>Ubuntu 22.04</option><option>Amazon Linux 2023</option><option>Windows Server 2022</option></select></label></div>}{step === 3 && <div className="wizard-form"><label>VPC/VNet CIDR<input value={vpcCidr} onChange={(event) => setVpcCidr(event.target.value)} required /></label><label>Public subnets<input defaultValue="10.0.1.0/24" /></label><label>Private subnets<input defaultValue="10.0.2.0/24" /></label><div className="security-note"><ShieldCheck size={17} /> SSH access is restricted by default.</div></div>}{step === 4 && <div className="review"><div className="review-row"><span>Template</span><strong>{selected.name}</strong></div><div className="review-row"><span>Provider</span><strong>{provider.toUpperCase()} · {region}</strong></div><div className="review-row"><span>Compute</span><strong>{vmCount} × {machineType}</strong></div><div className="review-row"><span>Network</span><strong>{vpcCidr}</strong></div><div className="alert success">Local configuration only. Deployment approval and Terraform generation are separate upcoming phases.</div>{message && <div className="alert success">{message}</div>}</div>}<div className="wizard-actions"><button className="button secondary" onClick={() => step === 1 ? setSelected(null) : setStep(step - 1)}>{step === 1 ? "Back to templates" : "Back"}</button>{step < 4 ? <button className="button" onClick={() => setStep(step + 1)}>Continue</button> : <button className="button" onClick={save} disabled={Boolean(message)}>Save configuration</button>}</div></div></div>;
}

function Metric({ label, value, detail }: { label: string; value: string | number; detail: string }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
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
