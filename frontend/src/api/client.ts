import Ajv from 'ajv/dist/2020';
import addFormats from 'ajv-formats';
import schema from './schemas.generated.json';
import type { components } from '../../../contracts/generated/api';
export type Schemas = components['schemas'];
const ajv = new Ajv({strict: false, allowUnionTypes: true, allErrors: false});
addFormats(ajv);
ajv.addSchema({...schema, $id: 'reknyx'});
export function validate<K extends keyof Schemas>(name: K, value: unknown): Schemas[K] {
  const check = ajv.getSchema(`reknyx#/components/schemas/${name}`);
  if (!check || !check(value)) throw new Error(`Invalid ${name} response from API`);
  return value as Schemas[K];
}
export class ApiError extends Error {
  constructor(public status: number, public code: string, public requestId: string, message: string) { super(`${message} (${code}${requestId ? `; request ${requestId}` : ''})`); }
}
export class ApiClient {
  csrf = '';
  private pending = new Map<string, string>();
  private generation = 0;
  clear() { this.generation++; this.csrf = ''; this.pending.clear(); }
  async request<K extends keyof Schemas>(path: string, name: K, options: { method?: string; body?: unknown; signal?: AbortSignal } = {}): Promise<Schemas[K]> {
    if (!path.startsWith('/api/v1/') || path.includes('://')) throw new Error('Invalid API resource');
    const generation = this.generation;
    const method = options.method || 'GET';
    const headers: Record<string, string> = {};
    let body: BodyInit | undefined;
    let fingerprint = '';
    if (options.body instanceof FormData) {
      body = options.body;
      const parts = [];
      for (const [key, item] of options.body.entries()) parts.push([key, typeof item === 'string' ? item : Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', await item.arrayBuffer()))).map(v => v.toString(16).padStart(2, '0')).join('')]);
      fingerprint = JSON.stringify(parts);
    } else if (options.body !== undefined) { body = JSON.stringify(options.body); fingerprint = body; headers['Content-Type'] = 'application/json'; }
    const identity = method + path + fingerprint;
    if (method !== 'GET') {
      if (this.csrf) headers['X-CSRF-Token'] = this.csrf;
      if (!['/api/v1/auth/login', '/api/v1/auth/logout'].includes(path)) {
        if (!this.pending.has(identity)) this.pending.set(identity, crypto.randomUUID());
        headers['Idempotency-Key'] = this.pending.get(identity)!;
      }
    }
    if (generation !== this.generation) throw new DOMException('Obsolete session request', 'AbortError');
    const response = await fetch(path, { method, headers, body, credentials: 'same-origin', cache: 'no-store', signal: options.signal });
    if (generation !== this.generation) throw new DOMException('Obsolete session response', 'AbortError');
    if (!response.ok) {
      if (response.status === 401) this.csrf = '';
      const result = await response.json().catch(() => null);
      const error = result?.error;
      throw new ApiError(response.status, typeof error?.code === 'string' ? error.code : 'http_error', typeof error?.request_id === 'string' ? error.request_id : '', typeof error?.message === 'string' ? error.message : `HTTP ${response.status}`);
    }
    if (response.status === 204) { this.pending.delete(identity); return undefined as unknown as Schemas[K]; }
    const value = await response.json();
    if (generation !== this.generation) throw new DOMException('Obsolete session response', 'AbortError');
    const result = validate(name, value);
    this.pending.delete(identity);
    if (name === 'Session') this.csrf = (result as Schemas['Session']).csrf_token;
    return result;
  }
}
