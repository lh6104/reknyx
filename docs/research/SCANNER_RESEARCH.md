# Scanner integration research for the CoreVAPT MVP

Documentation access date: **2026-11-01**. Scope: official-documentation research for a solo hackathon project. No scanner installation/execution, target requests, or runtime verification occurred in that research. **Documentation-verified** facts are separate from **design recommendations**. English translation on **2026-11-02** did not rerun the original external-source checks.

## 1. Proposed decision

**Design recommendation:** constrain the MVP to live Nmap → XML; live ZAP baseline → JSON, optionally controlled through an internal API; and Greenbone/OpenVAS native XML import. Keep full Greenbone operations, Nessus, and Burp off the demonstration's critical path. Demonstrate a traceable scan/import → observation/finding → explanation → report chain.

| Source | Proposed MVP role | Accepted output | Evidence boundary |
| --- | --- | --- | --- |
| Nmap | Observe authorized lab hosts, ports, and services | XML `-oX` | Open ports/banners do not prove an exploitable CVE |
| ZAP | Bounded baseline crawl and passive analysis | Full JSON from `-J`; API alerts require a separate adapter | Alerts are rule judgments; retain confidence and evidence |
| Greenbone/OpenVAS | Import a report with provenance | Native XML | Import demonstrates file processing, not scanner orchestration |

## 2. Nmap

### Documentation-verified

Nmap supports XML `-oX` with a DTD. `service.method` distinguishes `table` and `probed`; `conf` is service-name confidence on a 1–10 scale, not exploitation probability. XML includes scanner version and Unix timestamps. [Nmap XML output](https://nmap.org/book/output-formats-xml-output.html).

`-sV` sends service probes. `--version-light` lowers intensity to 2 but still sends active traffic and may reduce identification coverage. Nmap excludes some printer ports from version detection because probes may be printed. `-A` enables other functionality beyond version detection. [Service/version detection](https://nmap.org/book/man-version-detection.html), [probe-file format](https://nmap.org/book/vscan-fileformat.html).

### Design recommendations

- Name the profile `network-service-discovery` and state that it sends packets and service probes; do not label it passive or universally safe.
- One authorized lab host, a bounded TCP-port list, low concurrency, and a hard deadline are sufficient for the demo. Do not default to `-A`, arbitrary scripts, or entire networks.
- Accept structured targets and build subprocess argv without a shell. Do not accept arbitrary Nmap option strings.
- Preserve host status, address/type, protocol, port, state/reason, service name/product/version/extrainfo, CPE, method, and confidence when available. Keep missing versions `null`; do not infer them from ports.
- Separate **observations** from **vulnerability findings**. Later CVE matching must record its source, applicability conditions, and unconfirmed status.
- Consider scan timestamps, exit code, and XML completion together. Deadline expiry or truncated XML means incomplete scanning, not “zero vulnerabilities.”

## 3. ZAP: baseline, passive, and active

### Documentation-verified

Baseline runs a spider for approximately one minute by default, waits for passive analysis, and supports JSON output with `-J`. The spider makes requests to the target. [ZAP baseline](https://www.zaproxy.org/docs/docker/baseline-scan/).

Passive scanning analyzes messages without modifying requests/responses. The API exposes spider status, `recordsToScan`, and alert endpoints; wait until the passive queue finishes. API actions generally need an API key; missing add-ons can produce `no_implementor`. Risk and confidence are distinct, and confidence includes user-assigned states. [ZAP API](https://www.zaproxy.org/docs/api/).

Full scan crawls and then actively scans. Packaged-scan documentation warns about unauthenticated APIs exposed to the host and default limits on reported passive instances. [Docker user guide](https://www.zaproxy.org/docs/docker/about/). **API Scan** imports OpenAPI/SOAP/GraphQL definitions and actively scans by default; “API” does not mean passive. [ZAP API Scan](https://www.zaproxy.org/docs/docker/api-scan/).

### Design recommendations

**Default:** baseline against a disposable authorized lab application. The run control must disclose crawling and HTTP requests. A crawler can reach state-changing endpoints in poorly designed applications; absence of an active scanner is not a guarantee of no impact.

**Active profile:** require recorded permission bound to scope, profile, validity, and approver. Baseline approval does not authorize active scanning. Show expected impact/deadline and recheck at worker dispatch. This is a proposed CoreVAPT control, not a claim that ZAP supplies that exact workflow.

**Minimal option:** start with packaged baseline and `-J` to reduce daemon orchestration. If API use is required, implement one adapter: separate session → context/scope → crawl → poll → drain passive queue → paginate alerts → store artifact → close session. Inspect the pinned version's actual schema before freezing the parser. Do not build both orchestration methods during the hackathon unless they satisfy different acceptance requirements.

Full-report JSON grouped by site/alert/instance and API alert records require different adapters. A single JSON path cannot cover every endpoint. Preserve plugin/rule ID, alert reference when present, raw risk/confidence, URI, method, parameter, evidence, description, solution, references, CWE, and message ID. Retain reported-instance counts and limits so they are not mistaken for complete coverage.

Use a separate session/container per job to avoid stale alerts. Keep the API on the internal worker network with an API key; never expose the key to the browser/logs. Enforce network scope, including DNS/redirects; scanner context is an additional layer. Defer authenticated crawling and Ajax/browser spiders because login state, browser dependencies, and SPA coverage make the demo less predictable.

## 4. Greenbone/OpenVAS native XML import

### Documentation-verified

Greenbone Community Edition is a software stack commonly associated with OpenVAS. Documentation distinguishes stable releases from changing source checkouts. [Community documentation](https://greenbone.github.io/docs/latest/).

Native XML preserves report data and supports appliance interchange. Quality of Detection (QoD), 0–100, expresses detection confidence; the interface normally displays QoD ≥70. It is not severity/CVSS. [Greenbone reports](https://docs.greenbone.net/GSM-Manual/gos-22.04/en/reports.html).

At the original access date, the GMP 22.6 URL redirected to **22.7**. `get_reports` returns native XML directly; other formats use Base64. `ignore_pagination` is available; `lean` can omit fields and change between releases. Results include `qod/value`, `qod/type`, severity, and original severity when overridden. [GMP 22.7](https://docs.greenbone.net/API/GMP/gmp-22.7.html).

### Design recommendations

- Accept native XML exported from a recorded version; do not claim support for every `.xml` file, OpenVAS generation, PDF, or HTML report.
- Explicitly support native report roots and selected GMP response wrappers. Identify the data-bearing report structurally when `<report>` elements nest; collecting every `<result>` blindly risks duplicates or delta contamination.
- Preserve report/task/result UUIDs, host/hostname, original port, NVT OID/name, description, severity, QoD/value/type, references, and solution. Use NVT OID as rule identity, not the display name.
- Do not convert `general/tcp` into port 0 or split IPv6 incorrectly. A normalized port may be `null`; preserve the original location string.
- QoD 80 is not “80% probability of exploitation.” Display “Source QoD: 80”; any CoreVAPT confidence mapping is separately versioned and retains the source value.
- Missing severity is not zero. Special/error values must not silently become informational; preserve original and displayed severity when overridden.
- Request export filters, scan status, feed timestamp/version, and omitted-data flags. Parsed result count alone does not prove completeness; reconcile counts, filters, and pagination with the source.
- Reject unsupported formats explicitly. Optional missing fields produce warnings with provenance. Label anonymized XML; substituted addresses must not merge into live assets.

## 5. Proposed minimum integration contract

This is a contract CoreVAPT must implement, not a universal scanner API.

| Group | Minimum fields | Purpose |
| --- | --- | --- |
| Run | Run ID, tool/version, `live/import` mode, profile/version, scope snapshot/hash, status, timestamps, deadline | Distinguish execution, import, and incomplete runs |
| Artifact | Artifact ID, raw SHA-256, size, content type, source, acquisition time, parser/version | Identify the exact interpreted bytes |
| Observation/finding | Source record ID, rule ID, asset/location, title, raw/normalized severity, raw confidence, evidence pointer | Review sources and correct mappings safely |
| Coverage | Requested/observed targets, completed phases, filters, truncation, authentication state, parse warnings | Avoid equating empty results with security |
| Approval | Actor, scope/profile hash, grant/expiry timestamps, approval reference | Execute only the authorized action |

Proposed lifecycle: `queued → running → succeeded | partial | failed | cancelled | timed_out`; imports also validate format before normalization. `succeeded` means the integration completed its profile, not that no vulnerabilities exist. Store raw artifacts before normalization; parser failure must retain raw bytes and diagnostics.

Proposed idempotency: artifact hash plus parser version prevents duplicate ingestion of identical bytes. Tool/rule/asset/location fingerprints group findings without deleting run-specific observations. Do not merge findings solely by CVE or similar titles. Related Nmap observations and ZAP alerts can be linked without treating them as duplicate exploitation evidence.

## 6. Proposed failure modes and acceptance evidence

| Situation | Required behavior | Evidence after implementation |
| --- | --- | --- |
| Missing tool, wrong version, absent add-on | Specific preflight failure before scanning | Tool/version/component identified; no “0 findings” result |
| Deadline/cancellation | Stop relevant process/task; retain artifacts/logs | No orphan background work; partial/timed_out state |
| Out-of-scope DNS/redirect | Reject egress outside approved scope | Changed DNS/redirect lab cases produce no external request |
| Pending ZAP passive queue or stale alerts | Do not conclude completion; isolate sessions | Jobs for different targets never mix alerts |
| Scanner exit code signals warnings/findings | Separate alert-bearing runs from technical failure | Cases for warning, finding, and startup failure |
| Empty/truncated JSON/XML, BOM, missing fields, unusual encoding | Reject or mark partial with diagnostics | No silent successful empty import |
| XML entities/DTD/XInclude or oversized input | No external network/file fetch; resource limits | Adversarial fixtures cannot read files or resolve external entities |
| Duplicate results within a report | Count by source identity; preserve provenance | Reimport is idempotent; different runs remain traceable |
| Low QoD, null severity, overrides, generic ports | Retain raw values and transparent mapping | UI/export preserve source semantics and confidence |
| Tokens/cookies/HTML in HTTP evidence | Restrict raw access, record redaction, escape UI | No leaked secrets in lists/logs or executed report HTML |

Valid Nmap XML can declare a DTD. Do not fetch external DTD/stylesheets. If validation is needed, pin a local schema or use safely configured parsing; external resolution must not be enabled merely to accept a formally valid document.

## 7. Proposed fixtures and provenance

Never label a hand-written scanner-like file as real output. Maintain two distinct sets:

1. **Synthetic:** small authored files labeled synthetic for parser edge cases; they do not prove runtime compatibility.
2. **Captured lab:** genuine output from a lab with recorded scope/configuration; this demonstrates compatibility with the pinned tool. Competition assessments must use organizer-authorized targets. Owning a local lab does not replace organizer permission. No captured fixture was created in the original research session.

Each manifest should record fixture type, source URL/lab ID, external usage/distribution permission, tool/version/image digest, add-on/feed version, redacted profile/argv, creation date, raw and shared-redacted hashes, redaction description, expected parse results, and reviewer. Do not invent missing feed/scan dates. Documentation examples need a source and “documentation example” label; they do not demonstrate a current scanner release.

Minimum fixture coverage: Nmap multiple hosts, IPv6, `table/probed`, absent version, filtered port, truncated XML; separate ZAP report/API JSON, multiple instances, confidence variants, API errors, incomplete queue; Greenbone native/wrapper XML, low QoD/missing type, override, absent NVT references, filtered reports, and `general/tcp`. Record parsed/skipped counts and reasons.

## 8. Versions and licensing

**Documentation-verified at the original access date:** Nmap's NPSL includes additional conditions and OEM licensing provisions. Review LICENSE/COPYING for the actual distributed version; invoking a separate process does not itself resolve licensing. [Nmap NPSL](https://nmap.org/npsl/).

ZAP uses Apache 2.0; bundled components have their own licenses. [ZAP legal notice](https://github.com/zaproxy/zaproxy/blob/main/LEGALNOTICE.md). Pin release/image digest and inspect the actual build's licenses/SBOM; a moving `stable` tag is not immutable.

Greenbone includes multiple components and feeds. The Community label does not establish one license or unrestricted feed redistribution. [Community glossary](https://greenbone.github.io/docs/latest/glossary.html). Inspect the exact component/file terms before packaging. Import-only MVP support need not embed the scanner/feed.

Burp Scanner is available in Professional and DAST, not Community. Do not promise free automated Burp scanning based on Community. [PortSwigger first scan](https://portswigger.net/burp/documentation/desktop/getting-started/running-your-first-scan).

The Tenable FAQ read on 2026-11-01 stated **5 IPs**, **30-day** delayed plugins, and disabled reporting for Essentials; Essentials Plus differed. This historical reading was not refreshed during translation and must not serve as a current licensing guarantee. Do not rely on older 16-IP guides. [Nessus FAQ](https://www.tenable.com/products/nessus/nessus-faq). Check API/export/redistribution/commercial rights against the exact edition/terms. Live Nessus API orchestration rights were not verified. Keep it outside the MVP; add Nessus/Burp import only with lawful artifacts and explicit acceptance criteria.

## 9. Unproven capabilities

The original research did not demonstrate scanner execution on this machine, pin binaries/images, capture lab fixtures, verify runtime schemas, benchmark time/CPU/RAM, or test authenticated scanning, cancellation, scope enforcement, or parser security. Frontend synthetic fixtures do not resolve these gaps. The contracts, failure cases, and acceptance tables are design inputs, not implementation results.
