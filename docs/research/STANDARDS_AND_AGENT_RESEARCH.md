# CoreVAPT: standards, prioritization data, and bounded agents

Source access date: **2026-11-01**. This is design research for a solo hackathon MVP; no product, scanner, or network test was implemented/run in that research. English translation: **2026-11-02**; original external-source checks were not rerun.

Conventions: **Verified** means read from an official source during the original research; **Recommendation** means a proposed CoreVAPT design; **Unverified** means further experiment or confirmation is needed. Schemas and policies below are proposals, not mandatory NIST/OWASP fields. Time-sensitive editions, URLs, and provider behavior remain dated observations.

## 1. Scope and Rules of Engagement (ROE)

**Verified.** NIST publishes SP 800-115, Final September 2008, as guidance for planning, conducting, analyzing, and reporting technical assessments. Running scanners does not by itself constitute a complete penetration test. [NIST SP 800-115](https://csrc.nist.gov/pubs/sp/800/115/final).

**Verified.** Appendix B covers scope, schedule, tools, communications/incidents, allowed/excluded targets, permitted/prohibited activities, data handling, reporting, and signatures. Section 3.2 **within Appendix B** concerns incident handling, stop conditions, and resumption. It is a customizable template. [Appendix B, B-1–B-3](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-115.pdf#page=67).

**Recommended contract.** Record `engagement_id`, `scope_version`, approver, validity, allowlist/exclusions, action catalog, rate/time-limited profiles, incident contacts, and artifact retention/deletion policy. Approval binds a **specific action and scope version**, rather than a conversation-wide `approved=true`. Execute a previously authorized in-scope profile within its budget; seek new approval only when authority or risk changes.

Enforce in the executor: canonicalize URLs/hosts, validate ports and post-DNS addresses, check redirects and every new destination before connecting, and prevent the agent from extending scope using discovered URLs. Exclusions take precedence. Restrict demo egress to the authorized lab. Preserve each run's immutable scope snapshot; later scope changes must not rewrite historical evidence.

Distinguish `completed`, `partial`, `failed`, `cancelled`, `skipped`, and `blocked_by_policy`. No findings means none were observed by completed checks, not proof of security. Record coverage by check and target.

## 2. OWASP: taxonomy and testing methodology have different roles

**Verified at the research date.** OWASP Top 10 **2025** is an awareness document on web risks; the research did not treat 2021 as the newest edition. [OWASP Top Ten](https://owasp.github.io/www-project-top-ten/).

**Verified.** Its 2025 categories are A01 Broken Access Control, A02 Security Misconfiguration, A03 Software Supply Chain Failures, A04 Cryptographic Failures, A05 Injection, A06 Insecure Design, A07 Authentication Failures, A08 Software or Data Integrity Failures, A09 Security Logging & Alerting Failures, and A10 Mishandling of Exceptional Conditions. [2025 introduction](https://top10.owasp.org/2025/0x00_2025-Introduction/).

**Verified at the research date.** WSTG provides test scenarios; stable pointed to **v4.2**. OWASP recommends versioned citations rather than `stable`/`latest`; the site used `wstg.owasp.org` and `/v4.2/`. [WSTG v4.2](https://wstg.owasp.org/v4.2/), [citation guidance](https://wstg.owasp.org/).

**Recommendation.** Use Top 10 for report grouping and WSTG for `test_case_id`, objectives, prerequisites, and coverage. Example: `taxonomy=OWASP_TOP10`, `edition=2025`, `category=A05:2025`; a test records `guide=WSTG`, `version=4.2`, the relevant ID, and URL. Do not combine 2021 category numbers with 2025 names.

Disclose the selected test set and limits. A few scanners do not establish “OWASP compliant” or full Top 10 coverage; role-based access, business logic, and design require evidence generally absent from unauthenticated scanning.

## 3. CVSS, risk, and reproducible ranking

**Verified.** CVSS 4.0 includes Base, Threat, Environmental, and Supplemental metrics; Supplemental metrics do not change the score. Preserve vectors alongside scores and use versioned references. [FIRST CVSS v4.0 specification](https://www.first.org/cvss/v4.0/specification-document).

**Verified.** CVSS 3.1 uses Base, Temporal, and Environmental groups, a `CVSS:3.1/` vector prefix, and Scope. CVSS 4.0 has different metrics, including Attack Requirements and separate impacts on vulnerable/subsequent systems. A 3.1 vector cannot be relabeled 4.0. [CVSS v3.1](https://www.first.org/cvss/v3.1/specification-document), [CVSS v4.0](https://www.first.org/cvss/v4.0/specification-document).

**Verified.** FIRST treats CVSS, EPSS, and decision-support methods as complementary. Severity alone does not express full exploitation probability or business context. [CVSS FAQ](https://www.first.org/cvss/faq).

**Recommended contract.** `cvss_assessments[]` records `version`, `vector`, `score`, `nomenclature`/score group, `source`, `source_updated_at`, `retrieved_at`, `calculator_version`, and `assessment_status`. Preserve parallel source assessments and select one using a versioned policy. Do not silently take the maximum across versions as a uniform measurement or infer a vector from a severity label.

For missing metrics or scanner hints, use `not_assessed`/`proposed`, record assumptions and reviewer, and never ask the LLM to invent a vector. A CVE's CVSS score does not establish that an asset is affected.

**Recommended MVP ranking.** Keep `technical_severity`, `validation_status`, `asset_context`, `threat_signals`, and `priority` separate. A conditional `corevapt-priority-v1` policy could use:

1. Unproven applicability enters a verification queue, separate from confirmed remediation work.
2. Confirmed applicability with KEV listing receives a known-exploitation reason; impact and asset context order that group.
3. Other findings use selected severity, exposure, and known asset criticality. Missing data retains `context_incomplete` and a declared fallback; it is not zero.
4. A stable key such as `finding_id` breaks ties. EPSS is optional and requires a fixed snapshot/threshold policy.

This is an internal example, **not a NIST/FIRST formula**, and it has not been calibrated. Retain `policy_version`, selected inputs, decision branch, reason codes, missing values, and enrichment snapshot. Identical inputs/policy must yield identical order. Policy changes require a new version and comparison rather than overwritten history.

## 4. CVE, CWE, and ATT&CK: evidence-backed mappings

**Verified.** CWE identifies weakness types; CVE identifies particular vulnerabilities. One CWE can relate to many CVEs. [MITRE CWE FAQ](https://cwe.mitre.org/about/faq.html). The CVE JSON record format separates production `main` from development `develop`. [CVE Record Format](https://github.com/CVEProject/cve-schema).

**Verified.** ATT&CK describes observed adversary behavior: tactics are objectives and techniques are ways to achieve them. [ATT&CK resources](https://attack.mitre.org/resources/), [FAQ](https://attack.mitre.org/resources/faq/).

**Recommendation.** Do not require all three identifiers for every finding. Misconfiguration/business-logic findings may have no CVE. A version banner cannot directly become a confirmed CVE: retain the fingerprint, applicability conditions, advisory source, and applicability status. An ATT&CK mapping describes possible behavior, not evidence that it occurred or authorization to execute it.

Each mapping records `namespace`, `id`, `catalog_version`, `source_url`, `mapping_method` (`scanner`, `reference`, `analyst`, `model_proposed`), `evidence_ids`, `confidence`, and `review_status`. Allow justified `unmapped`, `unknown`, and `not_applicable`. Models propose mappings; independent validation checks identifier existence and supporting sources before publication.

## 5. Optional CISA KEV and FIRST EPSS enrichment

**Verified.** CISA KEV is grounded in evidence of exploitation. The official `cisagov/kev-data` repository supplies CSV/JSON/schema/history. The catalog page returned HTTP 403 during original research; mirror content was not treated as official evidence. [CISA bulletin, 2026-02-10](https://content.govdelivery.com/accounts/USDHSCISA/bulletins/4093c1e), [official KEV repository](https://github.com/cisagov/kev-data).

**Verified.** EPSS estimates a CVE's probability of exploitation in the wild over the next 30 days and is updated daily. It is not full risk and does not establish asset applicability. FIRST recommends prioritizing known-exploitation evidence even when EPSS is low. [EPSS FAQ](https://www.first.org/epss/faq). Data includes score/percentile, history, and model versions. [EPSS data](https://www.first.org/epss/data).

**Recommended contract.** KEV uses `listed`, `not_listed_at_snapshot`, `unknown`, and `not_applicable`, with `snapshot_id`, snapshot/retrieval time, and entry metadata. Absence at snapshot X does not mean unexploitable. Timeout, malformed JSON, unidentified CVE, or missing snapshot must not become `false`.

EPSS retains `score` and `percentile` (both 0–1), `score_date`, `model_version` when supplied, source, and fetch status. Percentile is relative rank, not probability. Missing EPSS is not zero. Freeze reranking snapshots because later API calls can change results. Core reporting must work offline; enrichment failure must neither discard findings nor block reports.

## 6. LangGraph versus a custom state machine

**Verified.** LangGraph distinguishes predefined workflows from agents deciding their process/tools. [Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents).

**Verified.** Checkpointers persist per-thread state; stores handle cross-thread data. `InMemorySaver` loses state on restart. The `durable-execution` documentation URL redirected to persistence during the original research. [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence).

**Verified.** `interrupt()` requires a checkpointer and `thread_id`; resume uses `Command(resume=...)` on the same thread. The interrupt-containing node restarts from its beginning, so earlier side effects can repeat. [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts).

**Verified.** Functional API restores stored task results; wrap nondeterministic work/side effects in tasks, but unfinished tasks can rerun and need idempotency. Graph API checkpoints at supersteps, not every source line. [Functional API](https://docs.langchain.com/oss/python/langgraph/functional-api), [official Graph API source](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/graph-api.mdx).

**Recommendation.** For a few branches across `scope → collect → normalize → prioritize → report`, a Python state machine backed by PostgreSQL may be easier for one developer. It still needs transitions, journal, job lifecycle, bounded retries, and recovery tests. Choose LangGraph for concrete pause/resume and evidence-dependent branching needs, not pitch vocabulary. Both remain candidates; CoreVAPT complexity/recovery was not benchmarked.

**Safe replay recommendation.** Separate `propose_action`, `authorize_action`, `dispatch_action`, and `record_result`. Approval binds target/profile/arguments/scope/budget hashes. Persist `action_id`, `attempt_id`, `idempotency_key`, receipt, and artifact. Crash between dispatch and receipt produces `execution_unknown`; reconcile before replay. Checkpointing does not make HTTP scans exactly-once. Distinguish artifact reprocessing from another live scan.

## 7. Prompt injection through scanner output

**Verified.** OWASP distinguishes direct injection from indirect injection through websites/files; RAG/fine-tuning do not eliminate the risk. [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/). OWASP recommends least privilege, action controls, and boundary tests; a prompt requesting human review cannot itself stop tool execution. [Prevention cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html).

**Recommendation.** Banners, HTML titles/bodies, logs, and scanner evidence may be target-controlled. Text telling the agent to ignore scope, contact another URL, or reveal a token remains target data. Mark `trust=untrusted_external`, preserve raw/hash, and redact, escape, and bound previews before sending them to the model. Parse through schema-aware adapters and send only necessary fields, not secrets or full dumps.

LLM outputs should be action enums/profile IDs with typed parameters. Independent policy/executor checks scope, permissions, budget, and allowlists. Do not pass arbitrary model shell strings or let artifacts determine tool names, destinations, or approvals. Keep credentials out of prompts/reports and escape rendered HTML/Markdown. These controls reduce impact; they do not prove immunity.

## 8. Auditable decision traces and adaptive choices

**Recommendation.** Reasoning visibility means concise rationale and verifiable evidence, not hidden chain-of-thought collection. A decision record includes:

| Field | Meaning |
| --- | --- |
| `decision_id`, `run_id`, `state_version` | Owning run/state |
| `input_artifact_ids`, `input_hashes` | Evidence actually used |
| `candidate_actions`, `selected_action` | Catalog alternatives and selection |
| `policy_version`, `scope_version`, `budget_remaining` | Authority and resource boundaries |
| `reason_codes`, `rationale_summary`, `uncertainties` | Concise reasons, missing data, assumptions |
| `model_id`, `prompt_template_version`, `response_id` | LLM provenance; identical prompts need not reproduce outputs |
| `authorization_result`, `executor_receipt` | Proposed versus authorized versus executed |

Set `max_steps`, wall-clock/request/concurrency/token/cost limits, retry caps, and stop conditions. The agent chooses among authorized profiles from evidence; the executor rejects invalid actions. If none remain or budget is exhausted, finish partial with reasons instead of looping to manufacture a finding.

Example reportable rationale: “Selected header profile H1 because artifact E12 establishes an HTTP service in scope S3; authenticated coverage is unknown; eight requests remain; the active profile was excluded by ROE.” This is a checkable decision explanation.

## 9. NIST CSF 2.0 at the governance layer

**Verified.** CSF 2.0 is a taxonomy of cybersecurity risk-management outcomes rather than one mandated implementation. Its six Functions are Govern, Identify, Protect, Detect, Respond, and Recover. [NIST CSF 2.0](https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf).

**Recommendation.** Use CSF in the executive summary where justified, alongside SP 800-115 for methodology/ROE. Do not build a CSF-scoring module in the MVP or claim organization-wide compliance from a scan/report. Specific mappings need an outcome/reference and supporting basis; otherwise omit them.

## 10. Acceptance evidence required before completion claims

The following remain proposed checks; they were **not performed** in the original research:

- Identical artifacts/snapshot/policy yield identical ranking; policy changes retain history and reason differences.
- CVSS 3.1/4.0 version/vector semantics remain intact; absent sources do not produce invented scores/vectors.
- KEV/EPSS timeout, offline, empty CVE, not-listed, and unknown remain distinct.
- Runner blocks out-of-scope targets/redirects and prohibited profiles before connection, including model proposals.
- Resume does not repeat receipted live actions; missing receipts after crash produce execution unknown and reconciliation.
- Injected artifact content cannot alter scope/permissions/tools; reports render safely without secrets.
- Reports distinguish observations, model proposals, validated findings, partial coverage, and untested areas; major claims cite evidence.
