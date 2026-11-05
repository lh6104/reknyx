# Organizer confirmation pack and source conflicts

Reviewed: 2026-11-02. Status: public-source research and an **unsent** question pack. No organizer, participant or other external person was contacted. The mandatory local baseline is [1.pdf](../../1.pdf), SHA-256 `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`.

## 1. What can be established now

| Topic | Established evidence | Consequence |
| --- | --- | --- |
| Live test boundaries | PDF p2 and §13 p10 restrict testing to organizer-provided, explicitly authorized lab targets | A local replica/public sample is not automatically an accepted competition target |
| Approval | PDF §§5.7/9.5 and checklist §10 require a human checkpoint and an outcome trace for active validation | UI approval or fake-runner tests alone do not settle §9.5 acceptance |
| Integrations | PDF §6 p5 requires at least three working integrations/supported imports with network and web coverage | All three need not execute live; every claimed integration still needs actual native ingestion/execution evidence |
| Submission | Current official listing requires presentation, demo video and repository links with viewing access | These are separate from the PDF's technical deliverables |
| Coordination | Listing identifies Discord as the event coordination platform | Private/pinned announcements may resolve the unanswered lab and schedule questions |

The listing facts above were rechecked at the [official event page](https://api.unstop.com/hackathons/dataops-innovation-hackathon-hackthecore-1765313) on the review date. They do not prove that the local PDF is byte-identical to the current hosted attachment. The public download control did not expose a usable independent attachment URL in the browser extraction.

## 2. Schedule conflict: do not silently choose a source

The official listing shows a start of **2 November 2026, 14:00 IST** and an end of **7 November 2026, 23:59 IST**. Those convert to **2 November 15:30** and **8 November 01:29** in Asia/Bangkok, a window of 129 hours 59 minutes. The organizer's [specific LinkedIn countdown post](https://www.linkedin.com/posts/hackthecorein_dataopsinnovationhackathon-1daytogo-hackathon2026-activity-7522580785091198976-Y8q4) describes **24 hours**. Its public page's structured `datePublished` field was read as **2026-11-01T08:50:21.957Z** (15:50:21.957 in Asia/Bangkok); the visible feed used relative times. The timestamp establishes when that post was published, not a corrected submission deadline.

This is a source inconsistency, not proof that either deadline has been formally superseded. Maintain the listing timestamps as the public scheduling reference while marking the actual execution/submission/live-judging window **confirmation required**. The short organizer announcement is not enough to recalculate a new deadline. Defer schedule-based promises until a dated organizer response/pinned announcement is captured. Use task-based gates meanwhile.

The [organizer website](https://www.hackthecore.in/) returned no readable body through the browser tool. Public search did not establish targets, credentials, ROE or an approved active-validation profile. An inaccessible/empty page is not evidence that no private instructions exist. The similarly named `hackthecore.com` is not established as the event authority and is not used for permissions.

## 3. Exact unanswered questions and closure evidence

| ID | Question | Acceptable closure evidence | Dependent gate | Safe work that can continue |
| --- | --- | --- | --- | --- |
| O01 | What are the absolute build, submission and live-judging deadlines/timezones? How does the 24-hour announcement relate to 2–7 November? | Dated official reply or pinned announcement with timestamps | Scheduling/submission | Design, contracts and a small vertical slice plan |
| O02 | Which target IDs/IPs/hostnames/schemes/ports are supplied and explicitly authorized? What are exclusions, rate/concurrency caps and validity windows? | ROE/target manifest linked to organizer authority; credentials stored separately | Any competition live execution | Synthetic parser/policy/renderer/preview work |
| O03 | Which exact baseline and active-validation profiles are permitted? Are redirects/DNS aliases/IPv6 or authenticated sessions allowed? | Explicit allowed/denied profile and destination rules | Live scanner network setup | Fixed-profile definitions and adversarial guard tests |
| O04 | For §9.5, must a permitted validation actually execute, or is a request/grant/reject/blocked-outcome demonstration accepted when validation is unavailable? | Event-specific response describing accepted demo and outcome evidence | Active-validation acceptance | Gate implementation/tests with honest unsupported label |
| O05 | May genuine captured Greenbone exports or redacted scanner fixtures be imported/submitted, and can organizers provide them? | Artifact origin, scanner/export version, collection time, intended assessment, sharing permission and limitations | Third native integration and correlation acceptance | Public format-reference inspection, explicitly not R05 proof |
| O06 | What are the rules for pre-existing prototypes, reusable code, coding agents/model APIs, licensing and required disclosure? | Current written rules and baseline/provenance requirements | Contribution/submission representation | Research, provenance inventory and documented questions |
| O07 | What PPT/video duration/file limits, repository visibility and evidence-access requirements apply? | Submission instructions with exact constraints | Final delivery | Accessible artifact inventory and modular demo outline |

No response has been obtained in this pass. “No answer” is neither approval nor prohibition. A user's operational authorization to run a local owned test lab remains distinct from organizer authorization for the scored lab.

## 4. Draft message — not sent

> We are building CoreVAPT for Statement 1, using a bounded network/web assessment workflow with native result imports and a human-controlled action gate. Could you confirm: (1) the absolute build/submission/judging deadlines, including the relationship between the 2–7 November listing and the 24-hour announcement; (2) the authorized target/port/profile ROE and traffic limits; (3) the exact permitted validation needed for §9.5, or whether a blocked-outcome gate demonstration is sufficient; (4) availability/permission for native Greenbone exports and redacted evidence; and (5) current pre-existing-code/AI-assistance and submission-format rules? Please point us to a dated official rule or pinned announcement for the record.

Send only through a channel the user explicitly authorizes. Do not paste target credentials into public chat, the repository or this document.

## 5. Decision record shape

For each O-ID, retain `status`, `question`, `source_url_or_private_reference`, `issued_at`, `recorded_at`, `issuer_role`, `answer_summary`, `affected_profiles`, `expires_at` if applicable, and `accepted_by`. Keep private attachments outside public docs and refer to a redacted hash/ID. A public authority/reference establishes authorization; a tool profile or analyst checkbox does not.

Update only the dependent gates once evidence is obtained. A permission to execute one profile does not authorize another target, port or action; an application approval never overrides an organizer denial.
