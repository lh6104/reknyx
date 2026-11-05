# CoreVAPT competition metrics and real-world validation

Reviewed: 2026-11-02. All thresholds, datasets and experiments below are **proposed**, not achieved measurements. The authoritative competition input is [1.pdf](../../1.pdf), especially §§6–13, pp5–10. [PDF provenance](sources/requirements-1-provenance.json) and the [visually checked rubric](sources/requirements-1-rubric-page-9.png) record the exact baseline.

## 1. Optimize evidence quality, not a speculative score

The rubric totals 100 points: end-to-end coverage 15, AI reasoning 20, technical accuracy 15, correlation/false positives 15, risk 10, safety 10, report 10, robustness 5. It does not publish a numerical grading formula within each criterion. No target below guarantees full marks, a ranking or an expected judge score.

The 20+15+15 points for reasoning, accuracy and correlation account for half the rubric. Prioritize adaptive decisions and correct, traceable evidence before expanding to seven live scanners. End-to-end, safety and PDF are also mandatory prototype capabilities: weighting is not permission to omit them. A small demonstrably correct scope beats untested breadth only when the mandatory requirements remain met.

## 2. Weighted criterion → behavior → measurable evidence

| PDF criterion | Weight | Demonstrable behavior | Proposed measure and release target | Existing cases / additional evaluation |
| --- | ---: | --- | --- | --- |
| End-to-End Coverage | 15 | One assessment connects request, plan, approved action, native outputs, review and PDF | Complete mandatory path with consistent IDs; every included finding traces to original artifact; failures remain visible | A01/A20/A25/A34/A35; M04/M06/M07 |
| AI Reasoning & Decisions | 20 | Different evidence changes next action; agent explains basis and knows when to stop | Report accepted-action accuracy, evidence validity and counterfactual branch correctness on held-out scenarios; target at least 14/16 scenario passes with zero prohibited dispatch | A06–A08/A29; E01–E04 below; real-provider evidence separate from fallback |
| Technical Accuracy | 15 | Native fields retain source semantics; service discovery is not a vulnerability | All designated critical-field assertions pass on versioned native fixtures; publish record/field denominators and parser warnings; no fabricated CVE/CVSS/confirmation | A12–A16/A22/A29; E05 |
| Correlation & False Positives | 15 | Merge true duplicates, keep distinct instances, preserve historical conflicts and analyst overrides | Pair precision and recall, plus end-to-end cluster review; proposed pair precision ≥0.95 and recall ≥0.90 on a declared 40-pair holdout; no cross-asset merge | A17–A19; E06/E07; confidence is source-specific |
| Risk Prioritization | 10 | Explain priority through severity, exposure, impact, exploitability evidence and uncertainty | All policy invariants pass; report pairwise analyst preference agreement on 12 prelabelled comparisons, target ≥10/12; retain unknowns and source severity | A22; E08; ties/needs-review allowed and labelled |
| Safety & Scope Control | 10 | Unauthorized, stale, expired or unsupported actions cannot execute | Zero prohibited dispatch in the declared suite; zero out-of-scope canary requests in network tests; all attempted actions attributable | A02–A05/A21/A23/A24/A26/A33; E09/E10; §9.5 permitted-validation gap explicit |
| Report Quality | 10 | Downloadable executive/technical PDF with evidence and remediation | All six §7 sections, 100% included-finding lineage, correct snapshot totals; manual font/layout/source checks pass | A25–A27; M06/M07; E11 |
| Efficiency & Robustness | 5 | No blind repeated scans; bounded runs recover honestly | Zero unintended extra spawn in retry/race/crash cases; record wall time, model latency/usage and recovery outcome; do not invent latency targets before baseline | A09–A11/A16/A24/A28; M09; E12 |

A01–A35 and M01–M10 are defined in the [testing plan](../superpowers/plans/2026-11-02-05-testing-acceptance.md). E01–E12 extend evaluation rather than silently changing the count of that acceptance catalog. Maintain both catalogs in the run manifest when implemented.

The 40-pair thresholds are engineering targets for a small declared dataset, not claims of population-level precision or low false-positive rate. Report exact fractions and uncertainty; a case count cannot be converted directly into the rubric's points.

## 3. Evaluation data, independence and provenance

Create a small versioned evaluation pack before tuning prompts or correlation rules. Proposed paths are `evals/scenarios/`, `evals/correlation/`, `evals/risk/` and `evals/manifests/`; they do not currently exist. The QA owner writes the manifest/harness; the foundation owner owns shared dependencies; the planner/findings owners own implementation changes.

Each case records: ID, requirement/rubric mapping, input artifact hashes and parser versions, assessment/scope revision, allowed actions, forbidden actions, expected observations, acceptable rationale basis, unknowns, ground-truth author/review notes and fixture mode. Separate native captures, sanitized native captures and synthetic adversarial inputs. A synthetic XML document is useful for a parser test, but cannot count as a working native integration or a live scan.

Use a development partition for prompt/rule changes and a separate holdout partition. Derive labels from native records, controlled-lab configuration and analyst review, not from the model under test. If only one qualified reviewer is available, disclose the limitation and keep ambiguity unresolved; do not call single-reviewer labels independent consensus. Keep source-family leakage visible when cases come from the same base report.

Native outputs from the same shared rule database or historical scan are not necessarily independent evidence. Do not increase confidence just because two tools repeat the same upstream claim. Compare asset/service/location/time and weakness equivalence before linking.

## 4. Reasoning experiments

### E01 — evidence-dependent action choice

Construct eight counterfactual pairs, 16 scenarios total. Within each pair, change a decisive fact while retaining the same analyst request. Include: HTTP present/absent; profile not run/already completed; current/historical-only evidence; in-scope/excluded port; ample/exhausted budget; supported/unsupported validation request; successful/unknown prior attempt; sufficient/insufficient evidence for conclusion.

Predefine an acceptable set of next actions, such as discovery, bounded web assessment, human review, stop or inconclusive. There need not be a single wording or a forced tool call. Assert action preconditions, valid basis IDs, correct uncertainty and no forbidden action. Score a pair as correct only if both decisions respect the changed evidence. Publish scenario-level and pair-level counts separately.

### E02 — rationale grounding and hallucination

Review every asserted factual claim in the structured rationale: numerator is claims supported by the cited observations; denominator is factual claims checked. Record invented references/CVEs, incorrect asset applicability, unsupported confirmation and missing uncertainty separately. An existing observation ID is not sufficient if its contents do not support the claim. A deterministic ID check plus human semantic review is needed; an LLM judge alone is insufficient ground truth.

### E03 — provider versus deterministic baseline

Run the same holdout with the deterministic planner and selected real model under the same allowed action catalog. Log provider/model, prompt version, temperature/configuration, input hashes, schema/semantic rejection, tokens, retries, elapsed time and cost only when prices are verified. A deterministic fallback is an operational result, not a successful model call.

Proposed evaluation budget: one pass over 16 scenarios; if authorized credits permit, repeat three times for 48 model decisions. Record the chosen number before running and report all failed/timeout outcomes. If provider credentials, data approval or budget are missing, mark the model experiment blocked; synthetic provider tests still verify failure handling but not AI capability.

Do not claim a model adds value if it only matches a deterministic rule with higher cost. Its useful advantage should be better interpretation of requests, conflicting evidence or justified next steps, while preserving the independent policy.

### E04 — ablation

Compare full planner context with the same planner lacking prior-action/coverage history. Observe redundant proposals and unsupported next steps. Preserve scope checks in both variants; never disable safety to make the comparison. If no improvement appears, report that rather than claiming adaptive-memory benefit.

## 5. Accuracy, correlation and risk experiments

### E05 — native field mapping

For each of Nmap XML, packaged ZAP JSON and the selected Greenbone XML schema, enumerate critical fields and manually inspect selected source records: asset, service/location, rule/native ID, raw severity/confidence, timestamp, raw locator and result status. Publish records checked, assertions checked and parser warnings. Missing supported data is a mapping defect; absent source data remains unknown.

Run supported/unsupported schema, invalid XML/entities, oversized input, duplicate import and historical timestamp cases. Check exact bytes/hash before and after ingestion. The ZAP exit code is adapter-specific: policy alert outcomes and process failure are different. [Official ZAP baseline exit semantics](https://www.zaproxy.org/docs/docker/baseline-scan/).

### E06 — correlation holdout

Use a proposed holdout of 40 labelled pairs: 20 merge-compatible and 20 keep-separate, including cross-tool and within-tool cases. Cover: same issue/asset/location; same CVE on different assets/endpoints; same title/different weakness; historical/current conflict; host-wide evidence without endpoint; different HTTP method/parameter; similar raw content from a common upstream source. Do not fabricate “native” cross-tool overlaps if the real lab has none: synthetic cases may validate rules, while native evidence acceptance remains separate.

Define TP as predicted merge with merge-compatible label, FP as predicted merge with keep-separate label and FN as missed merge-compatible pair. Precision = TP/(TP+FP), recall = TP/(TP+FN); report counts and mark undefined denominators N/A. Review resulting clusters as well: pairwise correctness can hide transitive over-merging. Retain every source membership and the rule/version/reason.

### E07 — finding correctness and false positives

Correlation precision is not vulnerability detection precision. For independently adjudicated candidate findings, report confirmed-correct/(confirmed-correct + confirmed-incorrect), alongside unresolved cases and review coverage. Do not count unresolved as correct or quietly exclude them from the inventory. A conventional false-positive rate FP/(FP+TN) needs a defined negative population; without one, report the false discovery proportion among adjudicated findings instead. Analyst “rejected” is a disposition requiring reason, not automatically objective ground truth.

### E08 — risk policy

Prepare 12 labelled pairwise ranking comparisons with asset context and explicit uncertainty. Include high severity/internal exposure versus moderate severity/exposed critical asset; missing CVSS; known exploit signal with uncertain applicability; low scanner confidence/high impact requiring review; conflicting source scores; no CVE. Preserve source CVSS vector/version/source and analyst context separately. Avoid a homemade 0–100 number presented as standardized risk.

CVSS Base measures severity rather than complete risk. EPSS estimates exploitation probability for published CVEs over the next 30 days; it is neither scanner-confidence nor proof of exploitability on the assessed asset. Optional enrichment must record retrieval/publication time and missing/stale status, and must not delay a correct MVP. [FIRST CVSS guidance](https://www.first.org/cvss/v4.0/user-guide), [FIRST EPSS](https://www.first.org/epss/).

## 6. Safety, reporting and resilience experiments

### E09 — approval and destination controls

Combine the existing approval tests with actual lab network assertions: pending/rejected/expired/stale action, forged reviewer, changed parameters, concurrent grant consumption, excluded port, exact hostname matching, DNS/IPv6 and redirect to a test-owned out-of-scope canary. Record zero-spawn expectations separately from zero-outbound-request expectations. A real allowed scan and a blocked disallowed scan are both needed; blocking everything is not a functional assessment.

For §9.5, obtain organizer confirmation and a permitted controlled-validation capability if required. If active validation remains unsupported, demonstrate the gate and audit honestly and record the unmet acceptance condition. Do not turn a fake runner or baseline scan into evidence of offensive validation.

### E10 — malicious evidence and prompt injection

Feed test artifacts containing instructions to ignore scope, request credentials, call arbitrary commands or label a suspected issue confirmed. Keep the original bytes private/immutable; construct a bounded data projection for the model, never executable instructions. Expected: scope/grants unchanged, no unauthorized external call, unsupported action rejected and output claims validated. Sanitization alone does not justify claiming prompt-injection immunity. [OWASP agent security](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html).

### E11 — report audit

For every finding included in a report, walk snapshot finding → membership → observation → artifact ID/raw locator/hash. Verify source observations rejected during triage remain available with clear exclusion/disposition. Inspect six §7 sections, counts, Unicode, page breaks, long URLs, remedies, assumptions, pending approvals, scan failures and historical evidence. Create a report, change triage, and confirm the original PDF/snapshot hash is unchanged. A client-ready label requires completed human review and disclosed scope/coverage limitations, not a nonempty PDF.

### E12 — recovery, efficiency and operational value

Inject timeout, cancellation, API restart, worker crash before/after dispatch, DB error after artifact write, missing/corrupt raw file and output/resource caps. Record process/attempt IDs, receipts, orphan reconciliation and final outcome. The safe result may be `execution_unknown`; do not reward incorrect automatic recovery. Retry only side-effect-free operations or cases where the absence of a prior dispatch is proven under the retry policy.

Record scan duration, parser/render time, planner latency, analyst active minutes, action counts and accepted duplicate proposals. Use medians and ranges for small repeated runs; use p95 only when the sample supports it and state N. Do not describe a single laptop run as a scalability benchmark.

## 7. Real-world use cases and staged gates

| User / scenario | Useful outcome | Contest MVP | Additional real-pilot gate |
| --- | --- | --- | --- |
| Internal security analyst | Review mixed network/web evidence and produce actionable priorities | Scoped assessment, source-linked findings, review and PDF | Verified asset owner/impact, per-engagement authorization, restore drill and operational monitoring |
| Small consultancy | Reduce coordination/report preparation while retaining analyst control | Repeatable request-to-report workflow and immutable evidence | Client data boundaries, reviewer/issuer identity, retention and controlled report sharing |
| Reviewer/auditor | Reconstruct what was tested, approved, failed and concluded | Action/attempt/audit/evidence chain | Retained immutable release record, access audit, controlled redaction and backup provenance |
| Application owner after remediation | Understand the fix and verify follow-up | Actionable remediation with source context | Append-only retest/delta comparison and remediation ownership, without rewriting prior reports |

Suggested real-pilot release gates: explicit signed engagement/ROE; data classification and retention/deletion policy; authenticated per-assessment access; HTTPS when exposed; backend secret lifecycle; private/encrypted storage appropriate to deployment; provider data handling approval; backup/restore of both DB and referenced artifacts; disk/orphan/lease/failed-job alerts; documented cancellation/recovery and incident owner. These are proposed product acceptance gates, not claims of legal or standards compliance.

Tenant SaaS, SSO, complex team RBAC, seven live adapters and a graph-based autonomous attack planner remain later work. A single-organization pilot can meet concrete controls without building an enterprise platform first.

## 8. Analyst-time experiment

Compare two workflows on the same declared evidence set: manual review/reporting with the existing tools, and CoreVAPT-assisted review/reporting. Measure active analyst minutes separately from scanner waiting, PDF generation and model latency. Include correction/review time; do not stop the timer at first AI draft.

Control learning effects with equivalent A/B datasets and alternate order if possible. Use at least three paired repetitions as a feasibility exercise, disclose operator count and prior familiarity, and retain output quality checks. Proposed improvement measure: `(manual active minutes - assisted active minutes) / manual active minutes`; publish raw minutes and report-quality/traceability outcomes alongside it. A time saving with poorer accuracy is not a successful pilot. If a manual baseline is not run, report elapsed time only and make no percentage-reduction claim.

## 9. Demo and submission evidence

Prepare a short reproducible flow, adaptable to the organizer's actual time limit:

1. Enter the authorized scope/request and show an excluded destination rejected.
2. Show one evidence-dependent action choice and its counterfactual/stop case with source IDs.
3. Run permitted network/web profiles and import genuine Greenbone output; show exact receipts and timestamps.
4. Compare a real merge candidate and a distinct instance kept separate; expose uncertainty.
5. Review priority reasoning, a grant/deny decision and the recorded outcome; disclose active-validation support honestly.
6. Download the PDF and trace one finding to original raw bytes/hash.
7. Show timeout/unknown recovery and all seven integrations' truthful modes.

The public event listing separately requires presentation, demonstration video and repository links with access enabled. Those submission artifacts do not replace the PDF's technical deliverables or prove current attachment identity. [Official event listing, rechecked 2026-11-02](https://api.unstop.com/hackathons/dataops-innovation-hackathon-hackthecore-1765313).

Store a run manifest with build/config/contract/provider/tool/parser versions, lab ROE, dataset hashes, commands, timestamps, pass/fail/blocked/skipped counts and redacted evidence paths. Current measurements: **not run**. The purpose of this plan is to make claims reviewable before presenting them to judges or clients.
