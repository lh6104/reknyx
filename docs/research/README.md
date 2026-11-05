# CoreVAPT — Statement 1 research dossier

Original research: **2026-11-01**, Asia/Bangkok (UTC+7). Documentation audit and English translation: **2026-11-02**. This dossier researches the competition, evaluates the preplan, and recommends a scope for a solo developer. Research proposals are not evidence of implemented scanner integrations or a deployed product.

The current interactive prototype is **[V6.4](../../corevapt_frontend_v6.4.html)**: Dashboard, Assessments and one-assistant Agents; Workflow/Findings/Report inside an assessment with a visible six-phase lifecycle. See the [UX standards/page map](UX_STANDARDS_AND_PAGE_MAP.md) and [fresh V6.4 verification](FRONTEND_V6_4_VERIFICATION.md). V6.3/V6.2/V6.1 remain preserved; their [V6.3](FRONTEND_V6_3_VERIFICATION.md) and [V6.2](FRONTEND_V6_2_VERIFICATION.md) verification records retain their original scope. V3/V4 source files are absent.

Frontend design basis: the user-approved [V6.2/V6.3 merge research and scenarios](FRONTEND_V6_2_V6_3_MERGE_RESEARCH.md), with its original [inspection evidence](sources/frontend-merge-inspection-2026-11-02.json). V6.4 implements that page composition; the research inspection and predecessor test results are not relabelled as V6.4 evidence.

## Reading order

Start with the latest [readiness decision report](READINESS_DECISION_REPORT.md). Supporting decisions cover [organizer confirmation](ORGANIZER_CONFIRMATION_PACK.md), [scanner readiness](SCANNER_READINESS_DECISIONS.md), [G0 contracts](G0_CONTRACT_DECISIONS.md), [model/provider selection](MODEL_PROVIDER_DECISIONS.md), and [safety/recovery/pilot](SAFETY_RECOVERY_PILOT_DECISIONS.md). These resolve research choices while retaining unrun implementation and external gates.

1. [Research conclusions and preplan assessment](RESEARCH_REPORT.md).
2. [Organizer requirements and acceptance evidence](REQUIREMENTS_MATRIX.md).
3. [Architecture fit review](ARCHITECTURE_FIT_REVIEW.md).
4. [Solution landscape](SOLUTION_LANDSCAPE.md).
5. [Competition metrics and practical applications](COMPETITION_METRICS_AND_REAL_WORLD.md).
6. [Scanner research](SCANNER_RESEARCH.md).
7. [Standards and bounded agent workflows](STANDARDS_AND_AGENT_RESEARCH.md).
8. [Technical recommendations and data contracts](TECHNICAL_RECOMMENDATIONS.md).
9. [Preparation and proposed implementation schedule](PREPARATION_AND_EXECUTION.md).
10. [Documentation audit](DOCUMENTATION_AUDIT.md).

The **2026-11-02** upstream review used pinned PentestGPT and Fennec commits: [comparison and recommendations](UPSTREAM_ARCHITECTURE_COMPARISON.md), [PentestGPT details](PENTESTGPT_ARCHITECTURE.md), and [Fennec details](FENNEC_ARCHITECTURE.md). These are static source reviews; upstream runtime behavior was not verified. [V4 analysis](FRONTEND_V4_ANALYSIS.md) and [V4 review](FRONTEND_V4_REVIEW.md) retain historical findings only; their old checks were not rerun during this documentation audit.

## Sources and status conventions

- **Organizer/PDF:** direct content of the user-supplied [10-page root PDF](../../1.pdf). Page references use physical PDF page order. SHA-256: `cfc55fc52fdecd8b4c65c5eec9217d39335ac4ab92461e869092fde8a33816cc`.
- **Listing:** the [official Unstop event API](https://api.unstop.com/hackathons/dataops-innovation-hackathon-hackthecore-1765313), used in the original research because the ordinary event page did not return readable content. Event dates and rules recorded from that research are historical snapshots unless explicitly refreshed.
- **Official documentation:** tool-developer or standards-body documentation linked at the relevant section. Documentation verification is separate from runtime verification; original access dates are retained.
- **Proposal:** a CoreVAPT recommendation, not a verbatim organizer requirement or an implemented capability.
- **Unverified:** a question unresolved by the sources read; it does not imply permission or prohibition.
- **Historical verification:** a recorded check against an earlier artifact. It was not rerun against v6.2 unless the v6.2 verification report explicitly says so.

The documentation audit read all ten pages of `1.pdf` using `pdftotext` and verified its hash. The original research additionally inspected the mandatory/bonus table on page 5 as a rendered image. Byte identity with the attachment currently hosted on Unstop remains unverified; the original research did not obtain an independent attachment download URL. The authoritative local source is now the repository-root `1.pdf`, replacing the original `/home/longha/Downloads/1.pdf` location.

## Original research activities and boundaries

- Copied the complete `.agents/skills` tree from `/home/longha/Desktop/aigurutop1`, including 13 skill directories, and compared contents with `diff -qr`.
- Applied `using-superpowers`, `brainstorming`, `dispatching-parallel-agents`, `codebase-design`, and `verification-before-completion` in that research session.
- Read local tool versions and machine capacity. That session did not install dependencies, build the stack, call a model, run scanners, or test targets.
- Did not register for the event, contact organizers, create a Git repository, commit, or publish the dossier.

These are records of the original session. Later frontend work is documented separately and does not establish scanner/model/platform E2E behavior.

## Open questions

Private Discord announcements, prebuild and AI coding rules, organizer-provided targets, active-validation permission, judging arrangements, PPT/video limits, eligibility, and model costs remain subject to explicit verification. See the [preparation plan](PREPARATION_AND_EXECUTION.md) for the unsent question list. Do not treat this dossier as authorization to scan a public system or a self-authorized competition lab.
