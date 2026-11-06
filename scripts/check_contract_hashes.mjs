/** Independent v1 authority encoder. No Python process or package dependencies. */
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const fail = (message) => { throw new Error(message); };
const object = (value, fields) => {
  if (value === null || typeof value !== 'object' || Array.isArray(value) ||
      Object.getPrototypeOf(value) !== Object.prototype ||
      Object.keys(value).sort().join('\0') !== Object.keys(fields).sort().join('\0')) {
    fail('authority object has missing or unknown fields');
  }
  return Object.fromEntries(Object.entries(fields).map(([key, validate]) => [key, validate(value[key])]));
};
const string = (value) => {
  if (typeof value !== 'string' || /[^\x00-\x7f]/u.test(value)) fail('authority string must be ASCII');
  return value;
};
const integer = (low, high = Number.MAX_SAFE_INTEGER) => (value) => {
  if (!Number.isSafeInteger(value) || Object.is(value, -0) || value < low || value > high) fail('invalid authority integer');
  return value;
};
const enumeration = (...values) => (value) => {
  if (typeof value !== 'string' || !values.includes(value)) fail('unsupported authority enum');
  return value;
};
const uuid = (value) => {
  if (!/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(string(value))) fail('expected hyphenated UUID');
  return value.toLowerCase();
};
const hostname = (value) => {
  value = string(value).toLowerCase().replace(/\.$/, '');
  if (!value || value.length > 253 || value.split('.').some(label => !/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(label))) {
    fail('expected ASCII DNS hostname');
  }
  return value;
};
const ipv4 = (value) => {
  value = string(value);
  const parts = value.split('.');
  if (parts.length !== 4 || parts.some(part => !/^(0|[1-9][0-9]{0,2})$/.test(part) || Number(part) > 255)) fail('expected canonical dotted IPv4');
  return value;
};
const timestamp = (value) => {
  value = string(value);
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(Z|([+-])(\d{2}):(\d{2}))$/.exec(value);
  if (!match || value.endsWith('-00:00')) fail('expected second-precision known timezone');
  const [, ys, ms, ds, hs, mins, ss, zone, sign, oh = '0', om = '0'] = match;
  const [year, month, day, hour, minute, second] = [ys, ms, ds, hs, mins, ss].map(Number);
  if (year < 1 || hour > 23 || minute > 59 || second > 59 || Number(oh) > 23 || Number(om) > 59) fail('invalid timestamp');
  const local = new Date(0);
  local.setUTCFullYear(year, month - 1, day);
  local.setUTCHours(hour, minute, second, 0);
  if (local.getUTCFullYear() !== year || local.getUTCMonth() !== month - 1 || local.getUTCDate() !== day) fail('invalid calendar date');
  const offset = zone === 'Z' ? 0 : (sign === '+' ? 1 : -1) * (Number(oh) * 60 + Number(om));
  const normalized = new Date(local.getTime() - offset * 60000);
  if (normalized.getUTCFullYear() < 1 || normalized.getUTCFullYear() > 9999) fail('timestamp UTC overflow');
  return normalized.toISOString().replace('.000Z', 'Z');
};
const unordered = (item, low = 0, high = 32, numeric = false) => (value) => {
  if (!Array.isArray(value) || value.length < low || value.length > high) fail('authority set outside allowed bounds');
  const result = value.map(item);
  if (new Set(result).size !== result.length) fail('duplicate authority set member');
  return result.sort(numeric ? (a, b) => a - b : undefined);
};
const ports = (low = 1, high = 16) => unordered(integer(1, 65535), low, high, true);
const boolean = (value) => {
  if (typeof value !== 'boolean') fail('expected boolean');
  return value;
};
const asset = (value) => object(value, {
  id: uuid, hostname: value => value === null ? null : hostname(value), ipv4,
  aliases: unordered(hostname, 0, 16), authorization_ref_id: uuid,
});
const scopeBudget = (value) => object(value, {
  max_actions: integer(0, 8), max_runtime_seconds: integer(0, 3600), max_model_calls: integer(0, 8),
  max_input_tokens: integer(0, 1000000), max_output_tokens: integer(0, 1000000),
});
const digest = (value) => {
  if (!/^[0-9a-f]{64}$/.test(string(value))) fail('expected lowercase SHA-256');
  return value;
};
const profiles = ['nmap_discovery_v1', 'zap_baseline_v1'];

export function normalize(kind, payload) {
  if (kind === 'scope') return object(payload, {
    assessment_id: uuid, version: integer(1), authorization_ref_id: uuid, asset,
    allowed_ports: ports(), excluded_ports: ports(0, 16),
    allowed_profiles: unordered(enumeration(...profiles), 0, 2),
    valid_from: timestamp, valid_until: timestamp, budget: scopeBudget, origin_wide: boolean,
  });
  if (kind === 'action') {
    if (!payload || !profiles.includes(payload.profile)) fail('unsupported action profile');
    const parameters = payload.profile === 'nmap_discovery_v1'
      ? { ports: ports(), deadline_seconds: integer(1, 120) }
      : { scheme: enumeration('http', 'https'), port: integer(1, 65535), root_path: enumeration('/'), deadline_seconds: integer(1, 180) };
    return object(payload, {
      action_id: uuid, assessment_id: uuid, state_revision: integer(1), profile: enumeration(...profiles),
      profile_version: enumeration('1'), target: asset, parameters: value => object(value, parameters),
      scope_hash: digest, scope_version: integer(1), basis_observation_ids: unordered(uuid), expires_at: timestamp,
      budget: value => object(value, { actions: integer(1, 1), runtime_seconds: integer(1, 180) }),
    });
  }
  fail('unknown authority kind');
}

function sorted(value) {
  if (Array.isArray(value)) return value.map(sorted);
  if (value !== null && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, sorted(value[key])]));
  }
  return value;
}

export function canonicalBytes(kind, payload) {
  return Buffer.from(JSON.stringify(sorted(normalize(kind, payload))), 'utf8');
}

export function authorityHash(kind, payload) {
  return createHash('sha256').update(canonicalBytes(kind, payload)).digest('hex');
}

function changed(payload, test) {
  const result = structuredClone(payload);
  const parts = test.path.split('.');
  let cursor = result;
  for (const part of parts.slice(0, -1)) cursor = cursor[part];
  if (test.remove) delete cursor[parts.at(-1)];
  else cursor[parts.at(-1)] = test.value;
  return result;
}

export function checkVectors(path) {
  const text = readFileSync(path, 'utf8');
  // JSON numbers lose their lexical integer/float distinction in JavaScript.
  // Reject decimal/exponent spellings before parsing to retain v1 wire rules.
  const tokens = text.replace(/"(?:[^"\\]|\\.)*"/gs, '""');
  if (/-?\d+(?:\.\d+|[eE][+-]?\d+)/.test(tokens) || /(?:^|[\s,:\[])-0(?=[\s,}\]])/.test(tokens)) fail('non-integer numeric token');
  const vectors = JSON.parse(text);
  const byId = new Map(vectors.golden.map(test => [test.id, test]));
  for (const test of vectors.golden) {
    assert.equal(canonicalBytes(test.kind, test.payload).toString('utf8'), test.canonical_utf8, test.id);
    assert.equal(authorityHash(test.kind, test.payload), test.sha256, test.id);
  }
  for (const test of vectors.equivalent) {
    const base = byId.get(test.base);
    assert.equal(canonicalBytes(base.kind, test.payload).toString('utf8'), base.canonical_utf8, test.id);
    assert.equal(authorityHash(base.kind, test.payload), base.sha256, test.id);
  }
  for (const test of vectors.mutations) {
    const base = byId.get(test.base);
    assert.notEqual(authorityHash(base.kind, changed(base.payload, test)), base.sha256, test.id);
  }
  for (const test of vectors.invalid) {
    const base = byId.get(test.base);
    assert.throws(() => canonicalBytes(base.kind, changed(base.payload, test)), undefined, test.id);
  }
  for (const test of vectors.invalid_json ?? []) {
    assert.throws(() => {
      const cleaned = test.json.replace(/"(?:[^"\\]|\\.)*"/gs, '""');
      if (/-?\d+(?:\.\d+|[eE][+-]?\d+)/.test(cleaned)) fail('non-integer numeric token');
      return canonicalBytes(test.kind, JSON.parse(test.json));
    }, undefined, test.id);
  }
  return Object.fromEntries(['golden', 'equivalent', 'mutations', 'invalid', 'invalid_json'].map(key => [key, (vectors[key] ?? []).length]));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const path = process.argv[2] ?? fileURLToPath(new URL('../contracts/examples/hash-vectors.json', import.meta.url));
    console.log(`Authority hash vectors PASS ${JSON.stringify(checkVectors(path))}`);
  } catch (error) {
    console.error(`Authority hash vectors FAIL: ${error.message}`);
    process.exitCode = 1;
  }
}
