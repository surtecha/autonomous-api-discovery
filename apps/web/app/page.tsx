"use client";
import { useState } from "react";
import Link from "next/link";
import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ReactFlow, Background, Controls } from "@xyflow/react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import "@xyflow/react/dist/style.css";
import { Button } from "@/components/button";

type Target = { id: string; disposable: boolean; max_requests: number };
type Session = { id: string; target: string; status: string; budget: number; strategy: string; created_at: string; result: null | { operations: number; requests: number; transitions: number; validation: Record<string, string> } };
type Operation = { method: string; path: string; verified: boolean; evidence: string[]; request: unknown; responses: unknown; fields: Record<string, { verified: boolean; required: boolean | null; confidence: number; evidence: string[] }> };
type Observation = { id: string; status: number; elapsed_ms: number; category: string; body: unknown; experiment: { method: string; path: string; hypothesis: string } };
type Transition = { operation: string; from: string; to: string; verified: boolean; evidence: string[] };

async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api/backend/${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!response.ok) {
    const value = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(typeof value.detail === "string" ? value.detail : `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

function Workspace() {
  const cache = useQueryClient();
  const [target, setTarget] = useState("");
  const [budget, setBudget] = useState(80);
  const [selected, setSelected] = useState<string | null>(null);
  const [tab, setTab] = useState("Operations");
  const targets = useQuery({ queryKey: ["targets"], queryFn: () => api<Target[]>("targets") });
  const sessions = useQuery({ queryKey: ["sessions"], queryFn: () => api<Session[]>("discovery-sessions"), refetchInterval: 2000 });
  const id = selected ?? sessions.data?.[0]?.id;
  const session = sessions.data?.find(item => item.id === id);
  const operations = useQuery({ queryKey: ["operations", id], queryFn: () => api<Record<string, Operation>>(`discovery-sessions/${id}/evidence/operations`), enabled: !!id, refetchInterval: 2000 });
  const observations = useQuery({ queryKey: ["observations", id], queryFn: () => api<Observation[]>(`discovery-sessions/${id}/evidence/observations`), enabled: !!id, refetchInterval: 2000 });
  const transitions = useQuery({ queryKey: ["transitions", id], queryFn: () => api<Transition[]>(`discovery-sessions/${id}/evidence/transitions`), enabled: !!id, refetchInterval: 2000 });
  const start = useMutation({ mutationFn: () => api<Session>("discovery-sessions", { target: target || targets.data?.[0]?.id, budget, strategy: "gain" }), onSuccess: (value) => { setSelected(value.id); void cache.invalidateQueries({ queryKey: ["sessions"] }); } });
  const cancel = useMutation({ mutationFn: () => api(`discovery-sessions/${id}/cancel`, {}), onSuccess: () => { void cache.invalidateQueries({ queryKey: ["sessions"] }); } });
  const error = targets.error ?? sessions.error ?? operations.error ?? observations.error ?? transitions.error ?? start.error ?? cancel.error;
  const nodes = [...new Set(transitions.data?.flatMap(t => [t.from, t.to]) ?? [])].map((label, index) => ({ id: label, data: { label }, position: { x: 100 + (index % 2) * 260, y: 50 + Math.floor(index / 2) * 130 } }));
  const edges = transitions.data?.map((t, index) => ({ id: String(index), source: t.from, target: t.to, label: t.operation.split("/").at(-1), style: { stroke: t.verified ? "#187450" : "#777" } })) ?? [];
  return <div className="shell">
    <aside><Link className="brand" href="/">API Discovery<span>Engineering workspace</span></Link><div className="sidebar-label">Discovery sessions</div>
      {sessions.data?.length === 0 && <p className="muted">No sessions recorded.</p>}
      <nav aria-label="Discovery sessions">{sessions.data?.map(item => <button className={id === item.id ? "session active" : "session"} key={item.id} onClick={() => setSelected(item.id)}><strong>{item.target}</strong><span>{item.status} · {item.id.slice(0, 8)}</span></button>)}</nav>
      <div className="policy"><span className="dot" /> Authorized targets only<p>Bounded requests. Sanitized evidence. Credentials remain server-side.</p></div>
    </aside>
    <main id="main"><header><div><span className="eyebrow">Discovery control plane</span><h1>Explore the contract.</h1><p className="muted">Inspect observed behavior, field evidence, and resource transitions.</p></div><span className="badge">{session?.status ?? "No active session"}</span></header>
      {error && <div role="alert" className="error">{error.message}</div>}
      <form className="toolbar" onSubmit={event => { event.preventDefault(); start.mutate(); }}>
        <label>Authorized target<select value={target || targets.data?.[0]?.id || ""} onChange={event => setTarget(event.target.value)}>{targets.data?.map(item => <option key={item.id} value={item.id}>{item.id}</option>)}</select></label>
        <label>Request budget<input type="number" min="1" max="100" value={budget} onChange={event => setBudget(Number(event.target.value))} /></label>
        <Button disabled={start.isPending || !targets.data?.length} type="submit">{start.isPending ? "Creating session..." : "Start discovery"}</Button>
        {session && ["running", "queued"].includes(session.status) && <Button variant="secondary" type="button" disabled={cancel.isPending} onClick={() => cancel.mutate()}>Cancel session</Button>}
      </form>
      <div className="metrics"><div><span>Observed operations</span><strong>{session?.result?.operations ?? Object.keys(operations.data ?? {}).length}</strong></div><div><span>HTTP experiments</span><strong>{session?.result?.requests ?? observations.data?.length ?? 0}</strong></div><div><span>Verified transitions</span><strong>{session?.result?.transitions ?? transitions.data?.length ?? 0}</strong></div><div><span>SDK tests</span><strong className="text-value">{session?.result?.validation.sdk_tests?.replaceAll("_", " ") ?? "Not run"}</strong></div></div>
      <div role="tablist" aria-label="Session views" className="tabs">{["Operations", "Experiments", "Resource graph", "Artifacts", "Evaluation"].map(name => <button key={name} role="tab" aria-selected={tab === name} onClick={() => setTab(name)}>{name}</button>)}</div>
      <section role="tabpanel" aria-label={tab}>
        {tab === "Operations" && <><div className="section-heading"><h2>Discovered operations</h2><span className="muted">Success requires an observation</span></div>{!Object.keys(operations.data ?? {}).length ? <div className="empty"><h3>No observed operations</h3><p>Start a session against a running local target. Verified results appear after execution.</p></div> : Object.entries(operations.data ?? {}).map(([key, op]) => <details key={key} className="operation"><summary><span className={`method ${op.method.toLowerCase()}`}>{op.method}</span><code>{op.path}</code><span className="evidence">{op.evidence.length} observations</span></summary><div className="operation-detail"><h3>Field evidence</h3>{Object.entries(op.fields).map(([field, claim]) => <p key={field}><code>{field}</code> · {claim.required === null ? "Requirement unknown" : claim.required ? "Required" : "Optional"} · {claim.verified ? "Verified" : "Inferred"} · confidence {claim.confidence}</p>)}<h3>Observed schemas</h3><pre>{JSON.stringify({ request: op.request, responses: op.responses }, null, 2)}</pre><h3>Evidence references</h3><code>{op.evidence.join(", ")}</code></div></details>)}</>}
        {tab === "Experiments" && <><h2>Experiment timeline</h2>{!observations.data?.length && <p className="empty">No completed experiments.</p>}{observations.data?.map((item, index) => <details className="operation" key={item.id}><summary><span className="muted">{String(index + 1).padStart(2, "0")}</span><span className="method">{item.experiment.method}</span><code>{item.experiment.path}</code><span className="evidence">HTTP {item.status} · {Math.round(item.elapsed_ms)} ms</span></summary><div className="operation-detail"><p>{item.experiment.hypothesis}</p><pre>{JSON.stringify(item.body, null, 2)}</pre></div></details>)}</>}
        {tab === "Resource graph" && <><h2>Observed state transitions</h2>{nodes.length ? <div className="graph"><ReactFlow nodes={nodes} edges={edges} fitView><Background /><Controls /></ReactFlow></div> : <p className="empty">No verified state transitions in this session.</p>}</>}
        {tab === "Artifacts" && <><h2>Generated artifacts</h2><p className="muted">Validation status is recorded separately from artifact generation.</p>{session?.result ? <><div className="downloads">{["openapi", "sdk", "tests", "validation", "report"].map(name => <a key={name} className="button secondary" href={`/api/backend/discovery-sessions/${id}/artifacts/${name}`}>Download {name}</a>)}</div><pre>{JSON.stringify(session.result.validation, null, 2)}</pre></> : <p className="empty">Artifacts become available after discovery completes.</p>}</>}
        {tab === "Evaluation" && <><h2>Measured execution</h2>{session?.result ? <div className="chart"><ResponsiveContainer width="100%" height={280}><BarChart data={[{ name: "Requests", count: session.result.requests }, { name: "Operations", count: session.result.operations }, { name: "Transitions", count: session.result.transitions }]}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="count" fill="#187450" radius={[3, 3, 0, 0]} /></BarChart></ResponsiveContainer></div> : <p className="empty">No completed execution measurements.</p>}<p className="muted">Precision, recall, and schema accuracy require independent ground-truth evaluation. No benchmark score is inferred from execution counts.</p></>}
      </section><footer>Evidence before inference<span>{id ? `Session ${id}` : "No session selected"}</span></footer>
    </main></div>;
}

export default function Page() {
  const [client] = useState(() => new QueryClient());
  return <QueryClientProvider client={client}><Workspace /></QueryClientProvider>;
}
