"use client";
import {useState} from 'react';
import type {Schemas} from '@/api/client';
import {Badge, Button, Card, CardTitle} from './ui';

export type ApiPreferences={includeSuspected:boolean; ports:string; theme:'system'|'light'|'dark'};
export const DEFAULT_API_PREFERENCES:ApiPreferences={includeSuspected:true,ports:'80, 443',theme:'system'};
export const API_PREFERENCES_KEY='reknyx.api.preferences.v1';
export function parsePreferences(value:unknown):ApiPreferences{
 if(!value||typeof value!=='object')throw Error('Invalid preferences');
 const p=value as Record<string,unknown>;
 if(typeof p.includeSuspected!=='boolean'||typeof p.ports!=='string'||(typeof p.theme!=='string'||!['system','light','dark'].includes(p.theme)))throw Error('Invalid preferences');
 const ports=p.ports.split(',').map(v=>v.trim());
 if(!ports.length||ports.length>16||ports.some(v=>!/^\d{1,5}$/.test(v)||Number(v)<1||Number(v)>65535)||new Set(ports.map(Number)).size!==ports.length)throw Error('Enter 1–16 distinct TCP ports from 1 to 65535.');
 return {includeSuspected:p.includeSuspected,ports:ports.map(Number).join(', '),theme:p.theme as ApiPreferences['theme']};
}
const integrations=[
 {name:'Nmap',capability:'imports.nmap_xml',description:'Import recorded Nmap XML host, port and service observations. Live scanning is in development.'},
 {name:'OWASP ZAP',capability:'imports.zap_json',description:'Import traditional ZAP JSON alerts and source instances. Live scanning is in development.'},
 {name:'OpenVAS / Greenbone',capability:'imports.greenbone_xml',description:'Import completed Greenbone XML reports with severity, QoD and source evidence. No scan is started.'},
 {name:'Nikto',capability:null,description:'Web server evidence import.'},
 {name:'Nessus',capability:null,description:'Infrastructure evidence import.'},
 {name:'Burp Suite',capability:null,description:'Analyst-assisted web assessment.'},
 {name:'Metasploit',capability:null,description:'Explicitly authorized validation.'},
];
function Row({title,detail,children}:{title:string;detail:string;children:React.ReactNode}){return <div className="flex flex-wrap items-center justify-between gap-4 border-t border-line py-4 first:border-0"><div className="min-w-0 flex-1"><p className="text-[13px] font-bold">{title}</p><p className="mt-1 text-xs leading-relaxed text-muted">{detail}</p></div>{children}</div>}
function Pending(){return <span className="text-xs text-muted">This feature is now implementing</span>}
export function ApiSettings({actorName,capabilities,preferences,onSave}:{actorName:string;capabilities:Schemas['Capabilities']|null;preferences:ApiPreferences;onSave:(next:ApiPreferences)=>void}){
 const [draft,setDraft]=useState(preferences);
 const [error,setError]=useState('');
 const [saved,setSaved]=useState(false);
 function save(value:ApiPreferences){setSaved(false);try{const next=parsePreferences(value);onSave(next);setDraft(next);setError('');setSaved(true);}catch(reason){setError(reason instanceof Error?reason.message:'Unable to save preferences');}}
 return <div className="space-y-5"><div className="flex flex-wrap items-center justify-between gap-3"><p className="max-w-[75ch] text-xs leading-relaxed text-muted">Preferences are saved in this browser. They apply to new forms and reports; existing scopes and snapshots stay unchanged.</p><Button variant="dark" onClick={()=>save(draft)}>Save preferences</Button></div>{error&&<p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-800">{error}</p>}{saved&&<p role="status" className="text-xs text-forest">Preferences saved in this browser.</p>}
 <div className="grid items-start gap-4 lg:grid-cols-2"><Card><CardTitle title="Analyst and report"/>
 <Row title="Analyst name" detail="Your authenticated identity is configured by the operator."><input aria-label="Analyst name" value={actorName} readOnly className="max-w-[180px]"/></Row>
 <Row title="Include suspected findings" detail="Default for new report forms. You can change it before freezing each report."><input aria-label="Include suspected findings by default" type="checkbox" checked={draft.includeSuspected} onChange={e=>{setDraft({...draft,includeSuspected:e.target.checked});setSaved(false);}}/></Row>
 <Row title="Include audit trail" detail="Review and provenance records are frozen with reports. Audit trail customization is not available."><Pending/></Row>
 <Row title="Theme" detail="Display preference for this browser."><select aria-label="Theme" className="max-w-[180px]" value={draft.theme} onChange={e=>{setDraft({...draft,theme:e.target.value as ApiPreferences['theme']});setSaved(false);}}><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></Row></Card>
 <Card><CardTitle title="Assessment defaults"/>
 <Row title="Rate limit" detail="Live scanner execution is not available."><Pending/></Row><Row title="Deadline per action" detail="Live scanner execution is not available."><Pending/></Row>
 <Row title="Allowed TCP ports" detail="Pre-filled for new assessments. Review the ports before creating a recorded scope."><input aria-label="Default allowed TCP ports" maxLength={120} className="max-w-[180px]" value={draft.ports} onChange={e=>{setDraft({...draft,ports:e.target.value});setSaved(false);}}/></Row><p className="text-xs leading-relaxed text-muted">Defaults do not revise existing scope or authorize any action.</p></Card>
 <Card><CardTitle title="Safety"/><Row title="Type hostname to approve active steps" detail="Approval configuration is unavailable while live execution remains in development."><Pending/></Row><p className="text-xs leading-relaxed text-muted">Imports retain previously recorded evidence. Import availability does not authorize scanner traffic or active validation.</p></Card>
 <Card className="lg:col-span-2"><CardTitle title="Tool integrations" description="Availability is reported by the server. Import-only tools accept recorded files; no scanner is launched. These status indicators are read-only."/>
 <div>{integrations.map(tool=>{const capability=capabilities?.capabilities.find(c=>c.id===tool.capability);const available=capability?.availability==='available';return <div key={tool.name} className="flex flex-wrap items-center gap-4 border-t border-line py-4"><div className="min-w-0 flex-1"><h3 className="text-[13px] font-bold">{tool.name}</h3><p className="mt-1 text-xs leading-relaxed text-muted">{tool.description}</p>{!available&&<p className="mt-2 text-xs text-muted">This feature is now implementing</p>}</div><Badge tone={available?'success':'neutral'}>{available?'Import-only':'In development'}</Badge><input type="checkbox" aria-label={`${tool.name} import available`} checked={available} disabled/></div>})}</div></Card></div>
 <div className="flex flex-wrap justify-between gap-3"><Button onClick={()=>save({...DEFAULT_API_PREFERENCES})}>Reset preferences</Button><Button variant="dark" onClick={()=>save(draft)}>Save preferences</Button></div></div>
}
