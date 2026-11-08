"use client";

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';
import { ApiClient, ApiError, type Schemas } from '@/api/client';
import { Bell, Search, Sparkles, Plus, ChevronLeft, ChevronRight, CheckCheck, ClipboardList, FileText, LayoutDashboard, ListFilter, RefreshCw, Settings, ShieldCheck } from 'lucide-react';

import { Dialog } from './ui';
import {ApiSettings, API_PREFERENCES_KEY, DEFAULT_API_PREFERENCES, parsePreferences, type ApiPreferences} from './api-settings';
import { ApiDashboard, Implementing } from './api-dashboard';

const BASE = '/api/v1';
const card = 'rounded-[18px] bg-surface p-5';
const button = 'rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-surface disabled:opacity-40';
const links = [['/', 'Dashboard', LayoutDashboard], ['/assessments', 'Assessments', ClipboardList], ['/approvals', 'Approvals', CheckCheck], ['/findings', 'Findings', ListFilter], ['/reports', 'Reports', FileText], ['/settings', 'Settings', Settings]] as const;
type Detail = Schemas['AssessmentDetail'];
function Field({name, label, type = 'text', required = true, defaultValue, maxLength}: {name: string; label: string; type?: string; required?: boolean; defaultValue?: string; maxLength?: number}) {
  return <label className="grid gap-1 text-sm">{label}<input name={name} type={type} required={required} defaultValue={defaultValue} maxLength={maxLength} /></label>;
}
function Json({value}: {value: unknown}) {
  if (value === null || value === undefined) return <span className="text-muted">Unknown / not recorded</span>;
  if (Array.isArray(value)) return value.length ? <div className="space-y-3">{value.map((item,index) => <div key={index} className="border-l-2 border-line pl-3"><Json value={item}/></div>)}</div> : <span className="text-muted">None recorded</span>;
  if (typeof value === 'object') return <dl className="grid gap-3 rounded-xl bg-soft p-4 text-sm">{Object.entries(value).map(([key,item]) => <div key={key} className="min-w-0"><dt className="mb-1 font-semibold capitalize">{key.replaceAll('_',' ')}</dt><dd className="break-words"><Json value={item}/></dd></div>)}</dl>;
  return <span className="whitespace-pre-wrap break-all text-sm">{String(value)}</span>;
}

export function ApiWorkspace() {
  const pathname = usePathname();
  const router = useRouter();
  const client = useRef(new ApiClient()).current;
  const [session, setSession] = useState<Schemas['Session'] | null>(null);
  const [preferences,setPreferences]=useState<ApiPreferences>({...DEFAULT_API_PREFERENCES});
  useEffect(()=>{try{const raw=localStorage.getItem(API_PREFERENCES_KEY);if(raw)setPreferences(parsePreferences(JSON.parse(raw)));}catch{/* Invalid or unavailable browser preferences use explicit defaults. */}},[]);
  useEffect(()=>{if(preferences.theme==='system')delete document.documentElement.dataset.theme;else document.documentElement.dataset.theme=preferences.theme;},[preferences.theme]);
  function savePreferences(next:ApiPreferences){localStorage.setItem(API_PREFERENCES_KEY,JSON.stringify(next));setPreferences(next);}
  const [panel, setPanel] = useState<'agents'|'search'|'notifications'|'new'|null>(null);
  const [query, setQuery] = useState('');
  const [collapsed, setCollapsed] = useState(false);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [capabilities, setCapabilities] = useState<Schemas['Capabilities'] | null>(null);
  const [refresh, setRefresh] = useState(0);
  const refreshPage = () => setRefresh(v => v + 1);
  const available = (id: string) => capabilities?.capabilities.some(item => item.id === id && item.availability === 'available') || false;
  const epoch = useRef(0);
  const [data, setData] = useState<{summary?: Schemas['WorkspaceSummary']; assessments?: Schemas['Assessment'][]; detail?: Detail; messages?: Schemas['ConversationMessage'][]; findings?: Schemas['Finding'][]; reports?: Schemas['Report'][]; timeline?: Schemas['TimelineEvent'][]; observations?: Schemas['Observation'][]; artifacts?: Schemas['Artifact'][]; decisions?: Schemas['DecisionRecord'][]; next?: string | null}>({});
  const [loadedPath, setLoadedPath] = useState('');
  const [snapshot, setSnapshot] = useState<Schemas['ReportSnapshot'] | null>(null);
  const [importState, setImportState] = useState<Schemas['Import'] | null>(null);
  const [importUrl, setImportUrl] = useState('');
  const [notice, setNotice] = useState('');
  const parts = pathname.split('/');
  const assessmentId = parts[1] === 'assessments' && parts[2] ? parts[2] : '';
  const tab = parts[3] || 'plan';
  const resource = assessmentId ? `${BASE}/assessments/${assessmentId}` : '';
  const hasPendingReports = data.reports?.some(report => report.state === 'pending' || report.state === 'rendering') || false;

  function failed(reason: unknown) {
    if (reason instanceof DOMException && reason.name === 'AbortError') return;
    if (reason instanceof ApiError && reason.status === 401) { epoch.current++; client.clear(); setSession(null); setCapabilities(null); setData({}); setSnapshot(null); }
    setError(reason instanceof Error ? reason.message : 'API request failed');
  }
  async function establish(signal?: AbortSignal) {
    const current = await client.request(`${BASE}/auth/me`, 'Session', {signal});
    const caps = await client.request(`${BASE}/capabilities`, 'Capabilities', {signal});
    setCapabilities(caps); setSession(current);
  }
  useEffect(() => {
    const controller = new AbortController();
    establish(controller.signal).catch(reason => { if (!(reason instanceof ApiError && reason.status === 401)) failed(reason); }).finally(() => setChecking(false));
    return () => controller.abort();
  }, []);
  async function pages<K extends keyof Schemas, T>(path: string, name: K, items: (page: Schemas[K]) => T[], signal?: AbortSignal): Promise<T[]> {
    const records: T[] = [];
    let cursor: string | null = null;
    const seen = new Set<string>();
    do {
      const page: Schemas[K] = await client.request(`${path}?limit=100${cursor ? '&cursor=' + encodeURIComponent(cursor) : ''}`, name, {signal});
      records.push(...items(page));
      cursor = (page as {next_cursor: string | null}).next_cursor;
      if (records.length > 10000 || (cursor && seen.has(cursor))) throw new Error('Collection exceeds this view limit or repeats a cursor; narrow the assessment.');
      if(cursor) seen.add(cursor);
    } while(cursor);
    return records;
  }
  useEffect(() => {
    const controller = new AbortController();
    const version = ++epoch.current;
    setError('');
    if (!session) return;
    async function load() {
      if (pathname === '/settings') {
        const caps=await client.request(`${BASE}/capabilities`,'Capabilities',{signal:controller.signal});
        if(version===epoch.current){setCapabilities(caps);setData({});}
      } else if (assessmentId) {
        const detail = await client.request(resource, 'AssessmentDetail', {signal: controller.signal});
        const [messages, findings, reports, timeline, observations, artifacts, decisions] = await Promise.all([
          pages(`${resource}/messages`, 'ConversationMessagePage', page => page.items, controller.signal),
          pages(`${resource}/findings`, 'FindingPage', page => page.items, controller.signal),
          pages(`${resource}/reports`, 'ReportPage', page => page.items, controller.signal),
          pages(`${resource}/timeline`, 'TimelineEventPage', page => page.items, controller.signal),
          pages(`${resource}/observations`, 'ObservationPage', page => page.items, controller.signal),
          pages(`${resource}/artifacts`, 'ArtifactPage', page => page.items, controller.signal),
          pages(`${resource}/decisions`, 'DecisionRecordPage', page => page.items, controller.signal),
        ]);
        if (version === epoch.current) setData({detail, messages, findings, reports, timeline, observations, artifacts, decisions});
      } else if (pathname === '/findings') {
        const page = await pages(`${BASE}/workspace/findings`, 'WorkspaceFindingPage', page => page.items, controller.signal);
        if (version === epoch.current) setData({findings: page.map(row => row.finding)});
      } else if (pathname === '/reports') {
        const page = await pages(`${BASE}/workspace/reports`, 'WorkspaceReportPage', page => page.items, controller.signal);
        if (version === epoch.current) setData({reports: page.map(row => row.report)});
      } else {
        const [summary, page] = await Promise.all([client.request(`${BASE}/workspace/summary`, 'WorkspaceSummary', {signal: controller.signal}), pages(`${BASE}/assessments`, 'AssessmentPage', page => page.items, controller.signal)]);
        const dashboard = pathname === '/' || pathname === '/dashboard';
        if (dashboard) {
          const [findings, observations, timeline, detail] = await Promise.all([
            pages(`${BASE}/workspace/findings`, 'WorkspaceFindingPage', p => p.items.map(r=>r.finding), controller.signal),
            page.length ? pages(`${BASE}/assessments/${page[0].id}/observations`, 'ObservationPage', p=>p.items, controller.signal) : Promise.resolve([]),
            pages(`${BASE}/workspace/timeline`, 'TimelineEventPage', p=>p.items, controller.signal),
            page.length ? client.request(`${BASE}/assessments/${page[0].id}`, 'AssessmentDetail', {signal:controller.signal}) : Promise.resolve(undefined),
          ]);
          if (version === epoch.current) setData({summary, assessments:page, findings, observations, timeline, detail});
        } else if (version === epoch.current) setData({summary, assessments: page});
      }
      if (version === epoch.current) setLoadedPath(pathname);
    }
    load().catch(reason => { if (version === epoch.current) failed(reason); });
    return () => controller.abort();
  }, [pathname, session, refresh]);

  useEffect(() => {setSnapshot(null); setImportState(null); setImportUrl(''); setNotice('');}, [assessmentId, session]);

  // Read-only status polling; mutations are always explicit analyst commands.
  useEffect(() => {
    if (!session || !assessmentId || (!importUrl && !hasPendingReports)) return;
    let active = true;
    const controller = new AbortController();
    let timeout: ReturnType<typeof setTimeout>;
    let delay = 1000;
    const version = epoch.current;
    async function poll() {
      if (!active) return;
      if (!document.hidden) {
        try {
          if (importUrl) {
            const state = await client.request(importUrl, 'Import', {signal: controller.signal});
            if (!active || version !== epoch.current) return;
            setImportState(state);
            if (['succeeded', 'partial', 'failed'].includes(state.state)) { setImportUrl(''); refreshPage(); return; }
          }
          const reports = await pages(`${resource}/reports`, 'ReportPage', page => page.items, controller.signal);
          if (!active || version !== epoch.current) return;
          setData(current => ({...current, reports}));
        } catch (reason) { if (active) failed(reason); }
      }
      delay = Math.min(delay * 2, 5000);
      if (active) timeout = setTimeout(poll, delay);
    }
    timeout = setTimeout(poll, delay);
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
  }, [session, pathname, assessmentId, importUrl, refresh, hasPendingReports]);

  async function command(action: (current: () => boolean) => Promise<void>) {
    if (busy) return;
    const version = epoch.current;
    setBusy(true); setError('');
    try { await action(() => version === epoch.current); } catch (reason) { if (version === epoch.current) failed(reason); } finally { setBusy(false); }
  }
  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget);
    await command(async (current) => { await client.request(`${BASE}/auth/login`, 'Session', {method: 'POST', body: {username: form.get('username'), password: form.get('password')}}); await establish(); });
  }
  async function analyzeEvidence(priorId?:string){
    if(!assessmentId || !data.detail){setError('Open an assessment before requesting evidence review.');return;}
    await command(async current=>{try{const result=await client.request(`${resource}/plans`,'PlanResult',{method:'POST',body:{expected_revision:data.detail!.assessment.state_revision,retry:priorId?{kind:'decision',prior_id:priorId,reason:'Analyst explicitly requested a new evidence review attempt.'}:null}});if(current()){setPanel(null);setNotice(`Evidence review recorded; source: ${result.decision.source}. No action was proposed.`);refreshPage();}}catch(reason){if(current()){try{const [decisions,detail]=await Promise.all([pages(`${resource}/decisions`,'DecisionRecordPage',p=>p.items),client.request(resource,'AssessmentDetail')]);if(current())setData(d=>({...d,decisions,detail}));}catch{/* Preserve the original request failure. */}}throw reason;}});
  }
  const contentReady = loadedPath === pathname;
  const findingRows = data.findings || [];
  const reportRows = data.reports || [];

  if (checking) return <main className="m-8" aria-live="polite">Checking authenticated session…</main>;
  if (!session) return <main className="mx-auto my-16 max-w-md space-y-4 p-5"><Link href="/" className="text-3xl font-extrabold">Reknyx.</Link><h1 className="text-xl font-bold">Sign in to your workspace</h1><p className="text-sm text-muted">Persistent API mode. Use the account configured by your operator.</p>{error && <p role="alert" className="text-red-700">{error}</p>}<form onSubmit={login} className={`${card} grid gap-4`}><Field name="username" label="Username" /><Field name="password" label="Password" type="password" /><button className={button} disabled={busy}>Sign in</button></form><button type="button" onClick={() => command(async (current) => { await establish(); })} className="underline">Retry session connection</button></main>;
  return <div className="app-shell flex min-h-screen flex-col gap-4 p-3 sm:p-4 md:flex-row">
    <aside className={`shrink-0 rounded-[24px] bg-surface px-3 py-5 md:sticky md:top-4 md:flex md:h-[calc(100dvh-32px)] md:flex-col md:py-6 ${collapsed ? 'md:w-[76px]' : 'md:w-[232px]'}`}>
      <Link href="/" className="flex items-center gap-2.5 px-2 py-1" aria-label="Reknyx home"><span className="grid size-9 place-items-center rounded-xl bg-lime text-lg font-extrabold text-[#141a14]">R</span><span className={`text-[23px] font-extrabold tracking-[-.06em] ${collapsed ? 'md:hidden' : ''}`}>Reknyx</span></Link>
      <div className="my-5 flex items-center gap-2.5 rounded-xl bg-soft p-2"><span className="grid size-8 shrink-0 place-items-center rounded-[10px] bg-[#e3edcf] font-extrabold text-[#365a1d]">{session.actor.display_name.charAt(0).toUpperCase()}</span><span className={`min-w-0 ${collapsed ? 'md:hidden' : ''}`}><b className="block truncate text-xs">{session.actor.display_name}</b><span className="block text-[10px] text-muted">Security analyst</span></span></div>
      <nav className="flex flex-wrap gap-1.5 md:flex-col" aria-label="Main navigation">{links.map(([href,label,Icon]) => {const child = ['/approvals','/findings','/reports'].includes(href); const active = href === '/' ? pathname === '/' || pathname === '/dashboard' : pathname.startsWith(href); return <Link key={href} href={href} aria-label={label} title={label} aria-current={active ? 'page' : undefined} className={`flex items-center gap-3 rounded-xl px-3 ${child ? `min-h-9 text-xs font-medium text-muted ${collapsed ? 'md:justify-center md:px-0 pl-8' : 'pl-8'}` : 'min-h-11 text-[13px] font-semibold'} ${active ? 'bg-soft text-ink' : 'text-muted hover:bg-soft hover:text-ink'}`}><Icon size={child ? 16 : 19} strokeWidth={1.7}/><span className={collapsed ? 'md:hidden' : ''}>{label}</span></Link>;})}</nav>
      <div className="mt-auto pt-6"><button type="button" onClick={()=>setCollapsed(v=>!v)} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} className="mb-3 hidden items-center gap-2 rounded-xl p-2 text-xs text-muted md:flex">{collapsed ? <ChevronRight size={17}/> : <><ChevronLeft size={17}/>Collapse sidebar</>}</button><div className={`mb-4 rounded-2xl border border-line p-3.5 ${collapsed ? 'md:hidden' : ''}`}><ShieldCheck size={17} className="mb-2 text-forest"/><p className="text-xs font-bold">Persistent workspace</p><p className="mt-1.5 text-[11px] leading-relaxed text-muted">Imported evidence and analyst review. Scanner execution and AI planning are in development.</p></div><button className={button} disabled={busy} onClick={() => command(async (current) => { await client.request(`${BASE}/auth/logout`, 'Session', {method: 'POST'}); epoch.current++; client.clear(); setSession(null); setCapabilities(null); setData({}); setSnapshot(null); })}>Sign out</button></div>
    </aside>
    <main className="min-w-0 flex-1 space-y-5 pb-8 sm:px-1" id="main-content">
      <div className="flex flex-wrap items-center gap-3"><button type="button" onClick={()=>setPanel('search')} className="flex min-h-14 min-w-0 flex-1 items-center gap-3 rounded-[18px] border border-lime/60 bg-surface p-1.5 text-left text-muted"><span className="grid size-9 shrink-0 place-items-center rounded-xl bg-lime text-[#141a14]"><Search size={18}/></span><span className="truncate text-xs">Quick search assessments, findings, tools</span></button><button type="button" aria-label="Notifications" onClick={()=>setPanel('notifications')} className="grid size-12 place-items-center rounded-2xl bg-surface"><Bell size={19}/></button><button type="button" onClick={()=>setPanel('agents')} className="flex min-h-11 items-center gap-2 rounded-full bg-lime px-5 text-xs font-bold text-[#141a14]"><Sparkles size={17}/>Ask Agents</button></div>
      <header className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-[10px] font-bold text-forest">Authenticated API mode</p><h1 className="text-[28px] font-extrabold tracking-[-.04em]">{assessmentId && contentReady ? data.detail?.assessment.name : links.find(([href])=>href===pathname)?.[1] || 'Dashboard'}</h1></div><div className="flex gap-2"><button className="flex min-h-9 items-center gap-2 rounded-full border border-line px-3 text-xs" disabled={busy} onClick={refreshPage}><RefreshCw size={14}/>Refresh</button>{!assessmentId && (pathname==='/' || pathname==='/dashboard' || pathname==='/assessments') && <button className="flex items-center gap-2 rounded-full bg-ink px-4 py-2 text-xs font-bold text-surface" onClick={()=>setPanel('new')}><Plus size={16}/>New assessment</button>}</div></header>
      {error && <div role="alert" className="rounded-xl border border-red-300 bg-red-50 p-4 text-sm text-red-900">{error}<p>Known data and drafts are retained. Retry the same operation explicitly if its outcome is uncertain.</p></div>}
      {notice && <p role="status" className={card}>{notice}</p>}
      {!contentReady ? <p>Loading server state…</p> : <>
      {assessmentId && data.detail ? <>
        <nav className="flex flex-wrap gap-3" aria-label="Assessment navigation">{['scope','plan','findings','report','audit'].map(view => <Link key={view} href={`/assessments/${assessmentId}/${view}`} className={`rounded-xl px-4 py-2 text-sm ${tab === view ? 'bg-lime text-black' : 'bg-surface'}`}>{view === 'plan' ? 'Conversation' : view.charAt(0).toUpperCase()+view.slice(1)}</Link>)}</nav>
        <p className="text-xs text-muted">Assessment {assessmentId} · revision {data.detail.assessment.state_revision}. Scope records do not authorize execution.</p>
        {tab === 'scope' && <section className={card}><h2 className="mb-3 font-bold">Recorded scope</h2><Json value={data.detail.scope}/></section>}
        {tab === 'plan' && <section className={`${card} space-y-4`}><h2 className="font-bold">Assessment conversation</h2><p className="text-sm">{data.detail.assessment.request}</p>{(data.messages || []).map(message => <article key={message.id} className="rounded-xl bg-soft p-3"><p className="text-xs text-muted">{message.role} · {message.created_at} · source: {message.source}</p><p className="whitespace-pre-wrap text-sm">{message.content}</p></article>)}<form className="grid gap-3" onSubmit={event => { event.preventDefault(); const form = event.currentTarget; const body = new FormData(form); command(async (current) => { await client.request(`${resource}/messages`, 'ConversationMessage', {method:'POST',body:{expected_revision:data.detail!.assessment.state_revision, content:body.get('content')}}); if(!current()) return; form.reset(); refreshPage(); }); }}><label>Message<textarea name="content" required maxLength={4000}/></label><button className={button} disabled={busy}>Append message</button></form><button type="button" disabled={busy || !available('planner')} className={button} onClick={()=>analyzeEvidence()}>Review evidence</button><p className="text-xs text-muted">Appending a message persists it. It does not invoke a model.</p></section>}
        {(tab === 'findings' || tab === 'plan') && <section className={`${card} space-y-3`}><h2 className="font-bold">Import source evidence</h2><p className="text-sm text-muted">Original bytes are retained before parsing. Queued imports have no findings until processing completes.</p><form className="grid gap-3 sm:grid-cols-2" onSubmit={event => {event.preventDefault(); const form = event.currentTarget; const fields = new FormData(form); const file = fields.get('file'); if (!(file instanceof File) || file.size > 20*1024*1024) {setError('Select a source file up to 20 MiB'); return;} command(async (current) => {const accepted = await client.request(`${resource}/imports`, 'AsyncAccepted', {method:'POST', body:fields}); if(!current()) return; setImportUrl(accepted.status_url); setNotice('Import queued; processing status will be polled.');});}}><label>Native format<select name="kind"><option value="zap_json" disabled={!available('imports.zap_json')}>ZAP traditional JSON</option><option value="nmap_xml" disabled={!available('imports.nmap_xml')}>Nmap XML</option><option value="greenbone_xml" disabled={!available('imports.greenbone_xml')}>Greenbone XML</option></select></label><label>Declared provenance<select name="provenance"><option value="synthetic_fixture">Synthetic fixture</option><option value="public_format_reference">Public format reference</option><option value="native_capture">Native capture</option></select></label><Field name="source_label" label="Source label" maxLength={200}/><Field name="observed_at" label="Observed at (ISO UTC; empty if unknown)" required={false}/><label className="sm:col-span-2">Source file<input name="file" type="file" required/></label><button className={button} disabled={busy || (!available('imports.zap_json') && !available('imports.nmap_xml') && !available('imports.greenbone_xml'))}>Upload evidence</button></form>{importState && <Json value={importState}/>}</section>}
        {tab === 'findings' && <Findings rows={findingRows} observations={data.observations} artifacts={data.artifacts} busy={busy || !available('findings.review')} review={(finding, disposition, rationale) => command(async (current) => {await client.request(`${resource}/findings/${finding.id}/review`, 'ReviewRecord', {method:'POST', body:{expected_revision:finding.revision, disposition, rationale, evidence_ids:finding.observation_ids}}); if(current()) refreshPage();})}/>}
        {tab === 'report' && <section className={`${card} space-y-4`}><h2 className="font-bold">Immutable reports</h2><form onSubmit={event => {event.preventDefault(); const fields = new FormData(event.currentTarget); command(async (current) => {await client.request(`${resource}/reports`, 'AsyncAccepted', {method:'POST',body:{expected_revision:data.detail!.assessment.state_revision, include_suspected:fields.has('include_suspected')}}); if(!current()) return; refreshPage(); setNotice('Report snapshot frozen and rendering queued.');});}} className="flex flex-wrap items-center gap-4"><label className="flex items-center gap-2"><input type="checkbox" name="include_suspected" defaultChecked={preferences.includeSuspected}/>Include suspected findings</label><button className={button} disabled={busy || !available('reports.pdf')}>Create report</button></form><Reports rows={reportRows} preview={report => command(async (current) => {const frozen = await client.request(`${BASE}/assessments/${report.assessment_id}/reports/${report.id}/snapshot`, 'ReportSnapshot'); if(current()) setSnapshot(frozen);})}/>{snapshot && <div><h3 className="font-bold">Frozen snapshot {snapshot.id}</h3><Json value={snapshot}/></div>}</section>}
        {tab === 'plan' && <section className={card}><h2 className="mb-3 font-bold">Evidence review decisions</h2>{!data.decisions?.length && <p className="text-xs text-muted">No explicit review has been requested.</p>}{data.decisions?.map(d=><article key={d.id} className="space-y-2 border-t border-line py-3"><p className="text-xs font-bold">{d.outcome} · source: {d.source}</p><p className="text-sm">{d.rationale}</p><p className="text-xs text-muted">{d.limitations.join(' ')}</p>{d.outcome==='failed'&&<button type="button" disabled={busy} onClick={()=>analyzeEvidence(d.id)} className="rounded-full border border-line px-3 py-2 text-xs font-bold">Retry review as new intent</button>}<p className="break-all text-[10px] text-muted">Decision {d.id} · scope {d.scope_version} · revision {d.state_revision}</p></article>)}</section>}
        {tab === 'audit' && <section className={card}><h2 className="mb-3 font-bold">Audit timeline</h2>{data.timeline?.map(event => <article key={event.id} className="border-b border-line py-3 text-sm"><b>{event.kind}</b><p>{event.reason}</p><p className="text-xs text-muted">{event.at} · {event.actor_type} · {event.outcome}</p></article>)}</section>}
      </> : pathname === '/findings' ? <Findings rows={findingRows} busy={busy}/> : pathname === '/reports' ? <section className={card}><Reports rows={reportRows}/></section> : pathname === '/approvals' ? <section className={card}><h2 className="font-bold">Approvals</h2><Implementing/></section> : pathname === '/settings' ? <ApiSettings actorName={session.actor.display_name} capabilities={capabilities} preferences={preferences} onSave={savePreferences}/> : <>
      {(pathname==='/' || pathname==='/dashboard') && <ApiDashboard findings={findingRows} assessments={data.assessments||[]} observations={data.observations||[]} timeline={data.timeline||[]} scope={data.detail}/>}
      {pathname==='/assessments' && <>
      <section className="space-y-4"><div><h2 className="text-lg font-extrabold">Assessments</h2><p className="text-xs text-muted">Open a workspace for scope, conversation, findings, reports and audit.</p></div><div className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">{data.assessments?.map(a => <Link className={`${card} block space-y-4 transition-colors hover:bg-soft`} href={`/assessments/${a.id}/plan`} key={a.id}><div className="flex flex-wrap items-start justify-between gap-2"><b className="text-sm">{a.name}</b><span className="rounded-full bg-soft px-2.5 py-1 text-[10px] font-bold">{a.status.replaceAll('_',' ')}</span></div><p className="line-clamp-2 text-xs leading-relaxed text-muted">{a.request}</p><div className="flex flex-wrap justify-between gap-2 border-t border-line pt-3 text-[10px] text-muted"><span>Revision {a.state_revision}</span><span>Open workspace →</span></div></Link>)}</div>{!data.assessments?.length && <div className={card}><p className="font-semibold">No assessments yet</p><p className="mt-1 text-xs text-muted">Create your first assessment below to begin reviewing imported evidence.</p></div>}</section>
      <button type="button" onClick={()=>setPanel('new')} className="min-h-28 w-full rounded-[20px] border-2 border-dashed border-line text-sm font-bold">+ New assessment</button>
      </>}
      </>}
      {data.next && <p className="text-sm text-muted">More records are available on the server; this view shows the first page.</p>}
      </>}
      {panel && <Dialog title={panel==='agents'?'Ask Agents':panel==='new'?'New assessment':panel==='search'?'Quick search':'Notifications'} description={panel==='new'?'Record a scope and request for imported evidence.':''} onClose={()=>setPanel(null)}>
        {panel==='agents' && <div className="space-y-4"><p className="text-sm">Explicit evidence review uses the recorded observations in an assessment. It does not run scans or change findings.</p><p className="text-xs text-muted">{capabilities?.capabilities.find(c=>c.id==='planner')?.message}</p>{assessmentId?<button className={button} disabled={busy||!available('planner')} onClick={()=>analyzeEvidence()}>Review evidence</button>:<><p className="text-sm">Open an assessment to request evidence review.</p><Link href="/assessments" onClick={()=>setPanel(null)} className="inline-block rounded-full bg-lime px-4 py-2 text-sm font-bold text-[#141a14]">Open assessments</Link></>}</div>}
        {panel==='notifications' && <Implementing/>}
        {panel==='search' && <><input aria-label="Search workspace" autoFocus value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search pages and loaded assessments"/><div className="mt-4 grid gap-2">{links.filter(([,name])=>name.toLowerCase().includes(query.toLowerCase())).map(([href,label])=><Link key={href} href={href} onClick={()=>setPanel(null)} className="rounded-xl p-3 hover:bg-soft">{label}</Link>)}{data.assessments?.filter(a=>a.name.toLowerCase().includes(query.toLowerCase())).map(a=><Link key={a.id} href={`/assessments/${a.id}/plan`} onClick={()=>setPanel(null)} className="rounded-xl p-3 hover:bg-soft">{a.name}</Link>)}</div></>}
        {panel==='new' && <CreateAssessment defaultPorts={preferences.ports} busy={busy} submit={body=>command(async current=>{const detail=await client.request(`${BASE}/assessments`,'AssessmentDetail',{method:'POST',body});if(current()){setPanel(null);router.push(`/assessments/${detail.assessment.id}/plan`);}})}/>}
      </Dialog>}
    </main>
  </div>;
}

function Findings({rows,busy,review,observations = [], artifacts = []}: {rows:Schemas['Finding'][];busy:boolean; observations?:Schemas['Observation'][];artifacts?:Schemas['Artifact'][];review?:(finding:Schemas['Finding'],disposition:string,rationale:string)=>void}) {
  return <section className="space-y-4"><h2 className="font-bold">Findings</h2>{!rows.length && <p>No findings in this page.</p>}{rows.map(f => <article key={f.id} className={`${card} space-y-3`}><Link href={`/assessments/${f.assessment_id}/findings`} className="font-bold">{f.title}</Link><p className="text-sm">{f.severity} · {f.priority} · {f.validation_status} · {f.analyst_disposition}</p><p className="text-xs text-muted">Confidence: {f.confidence_method} / {String(f.confidence_value ?? 'Unknown')} · CVSS: {f.cvss ?? 'Unknown'}</p><p className="text-sm">{f.remediation}</p><details><summary className="cursor-pointer text-sm">Source references and uncertainty</summary><Json value={f}/>{observations.filter(observation => f.observation_ids.includes(observation.id)).map(observation => <div key={observation.id} className="mt-4 space-y-2"><h3 className="font-semibold">Source observation {observation.id}</h3><Json value={observation}/>{artifacts.filter(artifact => artifact.id === observation.artifact_id).map(artifact => <div key={artifact.id}><p className="break-all text-xs">SHA-256: {artifact.sha256}</p><p className="text-xs">Declared provenance: {artifact.provenance}</p><a className="text-sm underline" href={artifact.download_url} download>Download original source bytes</a></div>)}</div>)}</details>{review && <form className="grid gap-3 sm:grid-cols-2" onSubmit={event => {event.preventDefault();const form = new FormData(event.currentTarget);review(f,String(form.get('disposition')),String(form.get('rationale')));}}><label>Disposition<select name="disposition" defaultValue={f.analyst_disposition}><option value="needs_review">Needs review</option><option value="accepted">Accepted</option><option value="rejected">Rejected</option></select></label><Field name="rationale" label="Review rationale" maxLength={2000}/><button className={button} disabled={busy}>Save review</button><p className="text-xs text-muted">Review changes disposition; technical validation remains separate.</p></form>}</article>)}</section>;
}
function Reports({rows,preview}: {rows:Schemas['Report'][];preview?:(report:Schemas['Report'])=>void}) {
  return <div className="space-y-3">{!rows.length && <p>No reports in this page.</p>}{rows.map(report => <article key={report.id} className="space-y-2 rounded-xl border border-line p-4"><Link className="font-bold" href={`/assessments/${report.assessment_id}/report`}>Report {report.id}</Link><p className="text-sm">{report.state} · {report.release_status}{report.failure_code && ` · ${report.failure_code}`}</p><p className="text-xs text-muted">Snapshot {report.snapshot_id} · {report.created_at}</p><div className="flex flex-wrap gap-4">{preview && <button type="button" className="text-sm underline" onClick={() => preview(report)}>View frozen snapshot</button>}{report.state === 'ready' ? <a className="text-sm underline" href={`${BASE}/assessments/${report.assessment_id}/reports/${report.id}/download`} download>Download stored PDF</a> : <span className="text-sm text-muted">PDF download unavailable until ready</span>}</div></article>)}</div>;
}
function CreateAssessment({busy,submit,defaultPorts}: {busy:boolean;defaultPorts:string;submit:(body:Schemas['AssessmentCreate'])=>void}) {
  const [error,setError] = useState('');
  const assetId = useRef<string | null>(null);
  return <form className="grid gap-4 sm:grid-cols-2" onSubmit={event => {event.preventDefault();const form = new FormData(event.currentTarget);const text = (key:string) => String(form.get(key)||'');try{const modelCalls=Number(text('model_calls'));const inputTokens=Number(text('model_input_tokens'));const outputTokens=Number(text('model_output_tokens'));if(!Number.isInteger(modelCalls)||modelCalls<0||modelCalls>8||![inputTokens,outputTokens].every(n=>Number.isInteger(n)&&n>=0&&n<=1000000))throw new Error('Enter bounded integer model budgets (0–8 calls and up to 1,000,000 tokens).');const ports = text('ports').split(',').map(p => Number(p.trim()));if(!ports.length || ports.length>16 || ports.some(p=>!Number.isInteger(p)||p<1||p>65535)||new Set(ports).size!==ports.length)throw new Error('Enter 1–16 distinct explicit TCP ports.');if(!/^\d{1,3}(\.\d{1,3}){3}$/.test(text('ipv4'))||text('ipv4').split('.').some(p=>Number(p)>255))throw new Error('Enter one IPv4 address.');const ref=text('authorization');const from=new Date(text('valid_from')).toISOString().replace('.000Z','Z');const until=new Date(text('valid_until')).toISOString().replace('.000Z','Z');if(until<=from)throw new Error('Scope end must be later than start.');setError('');submit({name:text('name'),request:text('request'),scope:{authorization_ref_id:ref,asset:{id:assetId.current ||= crypto.randomUUID(),hostname:null,ipv4:text('ipv4'),aliases:[],authorization_ref_id:ref},allowed_ports:ports,excluded_ports:[],allowed_profiles:[],valid_from:from,valid_until:until,budget:{max_actions:1,max_runtime_seconds:120,max_model_calls:modelCalls,max_input_tokens:modelCalls?inputTokens:0,max_output_tokens:modelCalls?outputTokens:0},origin_wide:false}});}catch(reason){setError(reason instanceof Error?reason.message:'Invalid scope');}}}>
    <details className="rounded-xl bg-soft p-3 sm:col-span-2"><summary className="cursor-pointer text-sm font-bold">Optional model analysis budget</summary><p className="my-3 text-xs text-muted">Groq requires operator configuration and synthetic data-use coverage. Zero calls disables model transmission for this assessment. Local deterministic review uses no model budget.</p><div className="grid gap-3 sm:grid-cols-3"><Field name="model_calls" label="Maximum model calls" type="number" defaultValue="0"/><Field name="model_input_tokens" label="Input token allowance" type="number" defaultValue="10000"/><Field name="model_output_tokens" label="Output token allowance" type="number" defaultValue="2048"/></div></details>
    <Field name="name" label="Assessment name" maxLength={200}/><Field name="ipv4" label="Dedicated IPv4 asset"/><Field name="ports" label="Explicit TCP ports (comma separated)" defaultValue={defaultPorts}/><Field name="authorization" label="Existing authorization reference UUID"/><Field name="valid_from" label="Scope valid from" type="datetime-local"/><Field name="valid_until" label="Scope valid until" type="datetime-local"/><label className="sm:col-span-2">Assessment request<textarea name="request" required maxLength={4000}/></label><p className="text-xs text-muted sm:col-span-2">Scope references are recorded for review. Live profiles remain disabled; this workflow imports existing evidence.</p>{error && <p role="alert" className="text-red-700 sm:col-span-2">{error}</p>}<button className={button} disabled={busy}>Create assessment</button>
  </form>;
}
