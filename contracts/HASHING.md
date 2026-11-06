# Authority JSON v1

The offline Python and JavaScript implementations bind the complete `ScopeAuthority`
or `ActionAuthority` object to lowercase SHA-256. This is a domain-specific encoding,
not an RFC 8785/JCS implementation. It grants no execution authority and does not
replace schema validation, scope policy, approval, revision checks or start checks.

Use `canonical_bytes(kind, payload)` and `authority_hash(kind, payload)` from
[`scripts/contract_hashes.py`](../scripts/contract_hashes.py). JavaScript exports
`normalize`, `canonicalBytes` (a Node Buffer) and `authorityHash` from
[`scripts/check_contract_hashes.mjs`](../scripts/check_contract_hashes.mjs).
Both accept `kind` equal to `scope` or `action`; other values fail. Normalization
returns a copy and never changes caller-owned data.

## Encoding

1. Reject missing and extra fields recursively. All authority fields are required;
   only `asset.hostname` and `target.hostname` may be null. Reject unsupported
   profiles and parameter fields that belong to another profile.
2. Accept ASCII strings only. UUID input must use the canonical hyphen grouping;
   hexadecimal case is normalized to lowercase. DNS names are validated by label
   (1–63 ASCII letters, digits or interior hyphens, total at most 253 characters),
   lowercased, and have at most one terminal dot removed. Do not trim whitespace,
   encode Unicode hostnames, resolve DNS or interpret a name as an authorization.
3. IPv4 input must already be four canonical decimal octets, 0–255, with no
   leading zeros except the octet `0`. Reject IPv6, CIDR, shortened, integer,
   hexadecimal, whitespace and other ambiguous spellings. No network traffic occurs.
4. Accept real Gregorian timestamps with whole seconds and `Z` or an explicit
   `±HH:MM` offset (hours 00–23, minutes 00–59). Normalize to
   `YYYY-MM-DDTHH:MM:SSZ`, within years 0001–9999. Reject fractions, leap seconds,
   missing offsets and unknown offset `-00:00`.
5. Numbers must be integers in the safe range 0–9007199254740991 and their narrower
   field bounds. Python rejects every float, including `1.0`, NaN and infinity;
   booleans are accepted only for `origin_wide`. Strings never coerce to numbers.
6. Sort numeric port sets numerically. Sort aliases, profile IDs and basis UUIDs
   lexicographically after normalization. Reject duplicates after normalization;
   never deduplicate silently. Empty arrays remain explicit. Ports are 1–65535;
   allowed/action ports contain 1–16 entries, excluded ports 0–16, aliases 0–16,
   profiles 0–2 and basis observation IDs 0–32.
7. Recursively sort object keys in ASCII order; preserve the normalized array order.
   Emit compact JSON with commas and colons, no spaces, no newline, no BOM, no
   prefix and no envelope. Output is UTF-8; all allowed characters are ASCII.
8. Compute SHA-256 over exactly those bytes. The `kind` selects the validated shape;
   it is not separately prefixed to the bytes. The two strict top-level shapes
   are disjoint. Hashes are 64 lowercase hexadecimal characters.

Scope budgets allow actions/model calls 0–8, runtime 0–3600 seconds and each token
budget 0–1000000. Scope versions, action state revisions and scope versions are
positive safe integers. Action budgets reserve exactly one action and 1–180
seconds. Nmap deadlines are 1–120 seconds; ZAP deadlines are 1–180. ZAP accepts
`http` or `https` and only root path `/`; profile version is exactly string `1`.
Authority hashes themselves must already be lowercase hexadecimal.

The wire schemas require their documented canonical forms. The hash API also
accepts the normalization equivalents above; that does not expand the wire API.
Contextual ownership, allowed/excluded relationships, authorization references,
scope windows, profile preconditions and budget availability remain independent
semantic checks. Normalization alone does not establish these facts.

## JavaScript numbers and JSON boundaries

JavaScript represents numeric `1` and `1.0` identically after parsing. The exported
object API can enforce `Number.isSafeInteger` and reject negative zero and
nonfinite values, but cannot recover a discarded numeric spelling. The vector
CLI additionally checks numeric tokens before `JSON.parse` and rejects decimal
or exponent spellings. Integrators must enforce lexical integer rules at their
JSON boundary if they accept raw JSON through another parser. An already parsed
object cannot retain duplicate JSON object members either; the transport parser
must reject duplicate member names before authority normalization. Duplicate set
entries are always rejected by both normalizers.

## Offline vectors and checks

[`examples/hash-vectors.json`](examples/hash-vectors.json) contains three separately
specified normalized authorities with exact canonical UTF-8 strings and SHA-256
digests: scope, Nmap action and ZAP action. Equivalence cases change input order,
UUID/hostname case, terminal DNS dots and UTC offsets without changing the hash.
Valid mutations individually change every variable authority leaf. Fixed-value
fields (`profile_version`, action count and root path), incompatible profile
changes, missing/extra fields, Unicode, malformed numbers, times and IPs are
rejection cases. No fixture authorizes its documentation-range sample address.

```bash
.venv/bin/python -m pytest contracts/tests/test_hashes.py
node scripts/check_contract_hashes.mjs contracts/examples/hash-vectors.json
```

The Node checker uses only Node built-ins and performs no Python subprocess call.
Omitting its argument locates the vector file relative to the script, regardless
of the current directory. Tests also corrupt a golden digest and require a
nonzero result. These are offline encoding checks, with no backend, provider,
scanner, authorization or platform acceptance claim.
